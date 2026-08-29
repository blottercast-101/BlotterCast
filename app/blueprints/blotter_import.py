import csv
import hashlib
import io
import random
import re
from datetime import date, datetime

from flask import Blueprint, jsonify, request, session
from openpyxl import load_workbook

from ..extensions import db
from ..helpers import (
    ZONE_LANDMARK_DEFINITIONS,
    find_census_resident_id_by_name,
    next_seq_no,
    parse_date,
    zone_coords,
)
from ..models import BlotterRecord, CensusRecord, Incident, Settlement
from ..permissions import json_error, log_audit, login_required, permission_required

bp = Blueprint("blotter_import", __name__)


def _parse_flexible_date(s: str):
    s = (s or "").strip()
    if not s:
        return None
    if s.isdigit() and 25000 < int(s) < 60000:
        # Excel serial date (days since 1899-12-30)
        from datetime import timedelta
        return (date(1899, 12, 30) + timedelta(days=int(s))).isoformat()
    formats = [
        "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d",
        "%b %d, %Y", "%B %d, %Y", "%d-%b-%Y", "%d-%b-%y",
        "%m-%d-%Y", "%d.%m.%Y", "%Y.%m.%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _split_case_title(title: str):
    parts = re.split(r"\s+(?:vs\.?|laban\s+kay|v\.|against)\s+", title.strip(), maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return title.strip(), ""


# Canonical Zone Definitions & Coordinate Defaults for Mapulang Lupa, Pandi, Bulacan
ZONE_PROPORTIONS = {
    "Zone 1": 0.18,
    "Zone 2": 0.14,
    "Zone 3": 0.16,
    "Zone 4": 0.14,
    "Zone 5": 0.15,
    "Zone 6": 0.11,
    "Zone 7": 0.12,
}


def resolve_zone_from_address(*texts: str, deterministic_seed: str = "") -> tuple[str, float, float]:
    """Adaptive, multi-tier Zone and coordinate resolver for Barangay Mapulang Lupa, Pandi, Bulacan.
    
    Tiers:
    1. Direct Zone / Purok / Sector / Area token matching (e.g. 'Zone 4', 'Purok 2', 'P-3', 'Z5').
    2. Landmark, Subdivision, Sitio, and Street name matching from the authentic Barangay registry.
    3. Block/Lot & Phase token matching (e.g. 'Phase 3' -> Zone 1, 'Phase 1' -> Zone 2, 'Phase 2' -> Zone 3).
    4. Proportional deterministic hash distribution for external towns or unmapped entries, preventing Zone 1 bias.
    """
    combined = " ".join([str(t or "").strip() for t in texts if t]).lower()
    combined_clean = re.sub(r"[^\w\s]", " ", combined)

    # Tier 1: Direct Zone / Purok / Sector / Area Regex
    m = re.search(r"\b(?:zone|purok|sector|area|p|z)\s*[:#-]?\s*([1-7])\b", combined, re.IGNORECASE)
    if not m:
        m = re.search(r"\b([1-7])(?:st|nd|rd|th)?\s*(?:zone|purok|sector|area)\b", combined, re.IGNORECASE)
    if m:
        z_id = f"Zone {m.group(1)}"
        base_lat, base_lng = zone_coords(z_id)
        return z_id, base_lat, base_lng

    # Tier 2: Landmark & Street Substring Matching from ZONE_LANDMARK_DEFINITIONS (longest aliases first)
    all_landmarks = []
    for z_id, info in ZONE_LANDMARK_DEFINITIONS.items():
        all_landmarks.append((info["name"].lower(), z_id, info["latitude"], info["longitude"]))
        for alias in info.get("aliases", []):
            all_landmarks.append((alias.lower(), z_id, info["latitude"], info["longitude"]))
    all_landmarks.sort(key=lambda x: len(x[0]), reverse=True)

    for alias, z_id, lat, lng in all_landmarks:
        if alias in combined:
            return z_id, lat, lng

    # Tier 2b: Explicit Local Landmarks, Streets & Subdivisions
    # Zone 1 – Residence 3 / Barangay Hall
    if any(k in combined for k in ["residence 3", "residences 3", "res 3", "res3", "bagtasan", "barangay hall", "brgy hall", "health center", "covered court", "daycare center", "residens 3"]):
        return "Zone 1", 14.883760, 120.968420

    # Zone 2 – Residence 1 / Pasong Kalabaw
    if any(k in combined for k in ["residence 1", "residences 1", "res 1", "res1", "pasong kalabaw", "kalabaw", "pasung kalabaw", "residens 1"]):
        return "Zone 2", 14.882000, 120.958000

    # Zone 3 – Pandi Village 2 / Atlantica
    if any(k in combined for k in ["atlantica", "pandi village 2", "pv2", "pv 2", "atlantica homes", "atlantica subdivision", "atalantica", "pandi village ph 2"]):
        return "Zone 3", 14.879000, 120.972000

    # Zone 4 – Mitay 1 / Pandi Village 1
    if any(k in combined for k in ["mitay", "sitio mitay", "pandi village 1", "pv1", "pv 1", "mitay st", "mytay", "pandi village ph 1"]):
        return "Zone 4", 14.887500, 120.962000

    # Zone 5 – Sitio Gubat / Mapulang Lupa Center
    if any(k in combined for k in ["gubat", "sitio gubat", "purok gubat", "barangay center", "mapulang lupa center", "main road", "elementary school", "central sitio", "gubatt"]):
        return "Zone 5", 14.882500, 120.964500

    # Zone 6 – Bangko St.
    if any(k in combined for k in ["bangko", "calle bangko", "sitio bangko", "bangco"]):
        return "Zone 6", 14.877500, 120.966500

    # Zone 7 – Barangka St. / Pandi-Angat Road
    if any(k in combined for k in ["barangka", "pandi-angat", "pandi angat", "encampment", "calle barangka", "sitio barangka", "barangca", "boundary angat"]):
        return "Zone 7", 14.878500, 120.959500

    # Tier 3: Block & Lot / Phase Indicators
    if re.search(r"\b(?:phase|ph)\s*3\b", combined, re.IGNORECASE):
        return "Zone 1", 14.883760, 120.968420
    if re.search(r"\b(?:phase|ph)\s*1\b", combined, re.IGNORECASE):
        return "Zone 2", 14.882000, 120.958000
    if re.search(r"\b(?:phase|ph)\s*2\b", combined, re.IGNORECASE):
        return "Zone 3", 14.879000, 120.972000

    # Tier 4: External / Non-Resident or Unmatched Fallback with Proportional Spatial Dispersion
    # Calculate a deterministic zone hash based on seed/address text to ensure even spatial distribution
    seed_str = deterministic_seed or combined or "mapulang_lupa"
    hash_val = int(hashlib.md5(seed_str.encode("utf-8", errors="ignore")).hexdigest(), 16)
    zone_index = (hash_val % 7) + 1
    selected_zone = f"Zone {zone_index}"
    base_lat, base_lng = zone_coords(selected_zone)
    return selected_zone, base_lat, base_lng


def _read_rows_from_upload(file_storage, ext):
    if ext == "xlsx":
        wb = load_workbook(io.BytesIO(file_storage.read()), data_only=True)
        ws = wb.active
        return [[("" if c.value is None else str(c.value)) for c in row] for row in ws.iter_rows()]
    if ext == "csv":
        text = file_storage.read().decode("utf-8-sig", errors="replace")
        return list(csv.reader(io.StringIO(text)))
    return None


COLUMN_ALIASES = {
    "docket_no": [
        "DOCKETNO", "DOCKETNUMBER", "DOCKET", "CASENO", "CASENUMBER", "CASE_NO",
        "ENTRYNO", "ENTRYNUMBER", "BLOTTERNO", "BLOTTERNUMBER", "RECORDNO", "CONTROLNO",
        "BLOTTERID", "NO", "REFNO", "REFERENCENO", "RECORDFILE", "BLOTTERENTRYNO"
    ],
    "date_filed": [
        "DATEFILED", "FILINGDATE", "DATEOFFILING", "DATEREPORTED", "REPORTEDDATE",
        "DATEOFINCIDENT", "INCIDENTDATE", "HEARINGDATE", "PETSA", "DATE", "FILEDDATE",
        "PETSANGPAGPUPULONG", "PETSANGPAGHAIN", "DATEENTERED"
    ],
    "case_title": [
        "CASETITLE", "TITLE", "TITLEOFCASE", "PANGALANNGKASO", "CASE_TITLE", "NAME",
        "PAMAGATNGKASO", "RECORDSUBJECT", "SUBJECT"
    ],
    "complainant": [
        "NAMEOFCOMPLAINANT", "COMPLAINANTNAME", "COMPLAINANT", "NAGREREKLAMO", "PLAINTIFF",
        "PETITIONER", "VICTIM", "REPORTER", "REPORTERNAME", "COMPLAINANTPARTY", "PARTY1",
        "FIRSTPARTY", "NAGSUMBONG", "COMPLAINANTREPORTER", "OFFENDEDPARTY", "COMPLAINANTS"
    ],
    "respondent": [
        "NAMEOFRESPONDENT", "RESPONDENTNAME", "RESPONDENT", "IPINAGREREKLAMO", "DEFENDANT",
        "ACCUSED", "SUSPECT", "PERPETRATOR", "RESPONDENTPARTY", "PARTY2", "SECONDPARTY",
        "INIREREKLAMO", "INVOLVEDPARTY", "RESPONDENTS"
    ],
    "complainant_addr": [
        "COMPLAINANTADDRESS", "ADDRESSOFCOMPLAINANT", "COMPLAINANTADDR", "COMPADDR",
        "TIRAHANNGNAGREREKLAMO", "REPORTERADDRESS", "PLAINTIFFADDRESS", "VICTIMADDRESS",
        "COMPLAINANTLOCATION"
    ],
    "respondent_addr": [
        "RESPONDENTADDRESS", "ADDRESSOFRESPONDENT", "RESPONDENTADDR", "RESPADDR",
        "TIRAHANNGIPINAGREREKLAMO", "DEFENDANTADDRESS", "SUSPECTADDRESS", "ACCUSEDADDRESS",
        "RESPONDENTLOCATION"
    ],
    "location": [
        "PLACEOFINCIDENT", "INCIDENTLOCATION", "LOCATIONOFINCIDENT", "CRIMESCENE",
        "LUGAR", "LUGARNGPANGYAYARI", "LOCATION", "STREET", "ADDRESS", "TIRAHAN",
        "SITIO", "PUROK", "AREA", "INCIDENTPLACE"
    ],
    "nature": [
        "NATUREOFCASE", "NATUREOFCOMPLAINT", "COMPLAINTTITLE", "NATURE", "OFFENSE",
        "INCIDENTTYPE", "OFFENSECOMMITTED", "KASO", "URI", "REKLAMO", "DESCRIPTION",
        "DETAILS", "NARRATIVE", "INCIDENT", "CASE", "VIOLATION", "CHARGES"
    ],
    "case_type": [
        "CRIMCIVIL", "CRIMINALCIVIL", "CASETYPE", "CLASSIFICATION", "CATEGORY", "TYPE", "URIKASO", "CASECLASSIFICATION"
    ],
    "zone": [
        "ZONE", "ZONENO", "ZONENUMBER", "PUROK", "PUROKNO", "BARANGAYZONE", "AREA", "SECTOR", "ZONEID"
    ],
    "officer": [
        "DESKOFFICER", "POLICEOFFICER", "OFFICER", "DUTYOFFICER", "INVESTIGATOR", "ENCODEDBY",
        "OFFICERONDUTY", "NAGTALA", "TAGAPAGTAGUYOD", "PERSONNEL"
    ],
    "stage": [
        "STAGE", "PATAWAG", "PROCEEDINGS", "HEARINGSTAGE", "STEP", "PAGDINIG", "ACTIONTAKEN"
    ],
    "status": [
        "SETTLEMENTSTATUS", "CASESTATUS", "STATUS", "DISPOSITION", "KATAYUAN",
        "RESOLUSYON", "STATUSOFCOMPLIANCE", "COMPLIANCESTATUS"
    ],
    "remarks": [
        "MAINPOINT", "MAINPOINTOFAGREEMENT", "AGREEMENT", "REMARKS", "NOTES",
        "OBSERVATIONS", "KASUNDUAN", "PUNTONGKASUNDUAN", "SUMMARY", "COMMENTS"
    ],
    "settlement_date": [
        "DATEOFSETTLEMENT", "SETTLEMENTDATE", "DATESETTLED", "DATEOFEXECUTION", "EXECUTIONDATE"
    ],
}


@bp.route("/api/blotter_import.php", methods=["POST"])
@bp.route("/api/import/blotter-entry", methods=["POST"])
@bp.route("/api/import/blotter-settlement", methods=["POST"])
@login_required
@permission_required("import_data")
def blotter_import():
    file = request.files.get("file")
    if not file or not file.filename:
        return json_error("No file uploaded, or the upload failed.")

    original_name = file.filename
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""

    file.stream.seek(0, 2)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > 10 * 1024 * 1024:
        return json_error("File must be smaller than 10MB.")

    if ext not in ("xlsx", "csv"):
        return json_error("Please upload a .xlsx or .csv file.")

    try:
        rows = _read_rows_from_upload(file, ext)
    except Exception as e:
        return json_error(f"Could not read that file: {e}")

    if not rows or len(rows) < 2:
        return json_error("No data rows found in that file.")

    import_type = request.args.get("type") or request.form.get("importType") or ("blotter-settlement" if "settlement" in request.path else "blotter-entry")

    # Step 1: Scan for the optimal header row across the first 15 rows
    all_keywords = []
    for alias_list in COLUMN_ALIASES.values():
        all_keywords.extend(alias_list)

    header_row_index = 0
    best_score = 0
    for i, row in enumerate(rows[:15]):
        if not row:
            continue
        row_str = " ".join([re.sub(r"[^A-Z0-9]", "", str(c).upper()) for c in row if c])
        score = sum(1 for k in all_keywords if k in row_str)
        if score > best_score:
            best_score = score
            header_row_index = i

    headers = [str(c).strip() for c in rows[header_row_index]]
    h_clean = [re.sub(r"[^A-Z0-9]", "", h.upper()) for h in headers]

    # Step 2: Match columns against aliases dictionary
    matched_cols = {}
    used_indices = set()

    for col_key, aliases in COLUMN_ALIASES.items():
        matched_idx = -1
        for alias in aliases:
            cleaned_alias = re.sub(r"[^A-Z0-9]", "", alias.upper())
            for idx, h in enumerate(h_clean):
                if idx not in used_indices and (cleaned_alias == h or cleaned_alias in h):
                    matched_idx = idx
                    break
            if matched_idx != -1:
                break
        if matched_idx != -1:
            matched_cols[col_key] = matched_idx
            used_indices.add(matched_idx)

    # Step 3: Generic address / location fallback mapping
    generic_addr_indices = [
        idx for idx, h in enumerate(h_clean)
        if idx not in used_indices and any(k in h for k in ["ADDRESS", "LOCATION", "TIRAHAN", "PLACE", "LUGAR", "STREET"])
    ]
    if "complainant_addr" not in matched_cols and generic_addr_indices:
        matched_cols["complainant_addr"] = generic_addr_indices[0]
        used_indices.add(generic_addr_indices[0])
    if "respondent_addr" not in matched_cols and len(generic_addr_indices) > 1:
        matched_cols["respondent_addr"] = generic_addr_indices[1]
        used_indices.add(generic_addr_indices[1])
    if "location" not in matched_cols and len(generic_addr_indices) > 2:
        matched_cols["location"] = generic_addr_indices[2]
        used_indices.add(generic_addr_indices[2])

    data_rows = rows[header_row_index + 1:]
    imported, settlements_created, skipped = 0, 0, 0
    errors = []
    zone_breakdown = {f"Zone {i}": 0 for i in range(1, 8)}
    row_num = header_row_index + 1
    current_username = session.get("username") or "Desk Officer"

    def _get_val(row, key, default=""):
        idx = matched_cols.get(key, -1)
        if idx >= 0 and idx < len(row):
            val = str(row[idx]).strip()
            return val if val != "None" else default
        return default

    def _map_cat(txt):
        t = (txt or "").lower()
        if any(k in t for k in ["pag-aaway", "suntukan", "sakitan", "pananakit", "assault", "physical", "bugbog", "frustrated"]):
            return "Physical Assault"
        if any(k in t for k in ["nakawan", "pagnanakaw", "theft", "robbery", "hold-up", "snatching", "kupit", "estafa"]):
            return "Theft"
        if any(k in t for k in ["domestic", "mag-asawa", "pamilya", "family dispute", "marital", "vawc", "asawa"]):
            return "Domestic Dispute"
        if any(k in t for k in ["paninira", "vandalism", "damage to property", "sirang gamit", "sinira"]):
            return "Vandalism"
        if any(k in t for k in ["trespass", "trespassing", "pagpasok", "boundary dispute"]):
            return "Trespassing"
        if any(k in t for k in ["droga", "drug", "shabu", "marijuana"]):
            return "Drug-Related Activity"
        if any(k in t for k in ["aksidente", "accident", "banggaan", "vehicular", "motorcycle", "kotse", "motor"]):
            return "Vehicular Accident"
        return "Public Disturbance"

    # Branch A: Settlement import branch
    if import_type == "blotter-settlement" or ("stage" in matched_cols and "complainant" not in matched_cols):
        for row in data_rows:
            row_num += 1
            if not row or all(str(c).strip() in ("", "None") for c in row):
                skipped += 1
                continue

            docket_no = _get_val(row, "docket_no")
            if not docket_no:
                skipped += 1
                continue

            record = BlotterRecord.query.filter_by(docket_no=docket_no).first()
            if not record:
                raw_title = _get_val(row, "case_title")
                c_name, r_name = _split_case_title(raw_title) if raw_title else ("Complainant", "Respondent")
                nature_val = _get_val(row, "nature", "Settlement Case")
                zone_val = _get_val(row, "zone")
                z_id, _, _ = resolve_zone_from_address(zone_val, c_name, r_name, deterministic_seed=docket_no)

                record = BlotterRecord(
                    docket_no=docket_no,
                    date_filed=datetime.utcnow().date(),
                    complainant=c_name,
                    respondent=r_name,
                    nature=nature_val,
                    case_type="CIVIL",
                    status="Pending",
                    zone_id=z_id,
                )
                db.session.add(record)
                db.session.flush()

            hearing_date_raw = _get_val(row, "date_filed")
            hearing_date = parse_date(_parse_flexible_date(hearing_date_raw)) or datetime.utcnow().date()
            stage = _get_val(row, "stage", "1st Patawag")
            status_raw = _get_val(row, "status", "Pending").upper()
            remarks = _get_val(row, "remarks")

            stl_status = "Complied" if ("SETTLED" in status_raw or "COMPLIED" in status_raw or "RESOLVED" in status_raw) else ("Not Complied" if ("NOT COMPLIED" in status_raw or "REPUDIATED" in status_raw or "CFA" in status_raw) else "Pending")
            stl = Settlement.query.filter_by(blotter_id=record.id).first()
            if stl:
                stl.date_confrontation = hearing_date
                stl.action_taken = stage
                stl.main_point = remarks or f"Status: {status_raw}"
                stl.status = stl_status
                stl.remarks = remarks
            else:
                stl_case_no = next_seq_no(Settlement, "case_no", "STL")
                stl = Settlement(
                    blotter_id=record.id,
                    case_no=stl_case_no,
                    case_title=f"{record.complainant} vs {record.respondent}",
                    complaint_title=record.nature,
                    nature="Criminal" if record.case_type == "CRIM" else "Civil",
                    date_filed=record.date_filed,
                    date_confrontation=hearing_date,
                    action_taken=stage,
                    main_point=remarks or f"Status: {status_raw}",
                    status=stl_status,
                    remarks=remarks,
                )
                db.session.add(stl)

            if stl_status == "Complied":
                record.status = "Settled"
            elif "CFA" in status_raw:
                record.status = "CFA Issued"

            if record.zone_id in zone_breakdown:
                zone_breakdown[record.zone_id] += 1

            db.session.commit()
            imported += 1
            settlements_created += 1

        log_audit(
            session.get("username"),
            "Imported",
            "Blotter",
            f"Imported {imported} blotter settlement(s) from {original_name}",
        )
        return jsonify({
            "ok": True,
            "importType": "blotter-settlement",
            "imported": imported,
            "settlementsCreated": settlements_created,
            "skipped": skipped,
            "zoneBreakdown": zone_breakdown,
            "matchedColumns": list(matched_cols.keys()),
            "errors": errors[:10],
        })

    # Branch B: Blotter Entry Branch (Dual Insert with Incidents)
    for row in data_rows:
        row_num += 1
        if not row or all(str(c).strip() in ("", "None") for c in row):
            skipped += 1
            continue

        raw_title = _get_val(row, "case_title")
        complainant = _get_val(row, "complainant")
        respondent = _get_val(row, "respondent")

        if not complainant and raw_title:
            complainant, parsed_resp = _split_case_title(raw_title)
            if not respondent:
                respondent = parsed_resp

        # Skip rows missing all participant and title data
        if not complainant and not respondent and not raw_title:
            skipped += 1
            continue

        if not complainant:
            complainant = "Unspecified Complainant"
        if not respondent:
            respondent = "Unspecified Respondent"

        comp_addr = _get_val(row, "complainant_addr")
        resp_addr = _get_val(row, "respondent_addr")
        location_val = _get_val(row, "location")
        zone_raw = _get_val(row, "zone")
        custom_docket = _get_val(row, "docket_no")

        existing_blt = BlotterRecord.query.filter_by(docket_no=custom_docket).first() if custom_docket else None
        if existing_blt:
            complainant = complainant if complainant and complainant != "Unspecified Complainant" else existing_blt.complainant
            respondent = respondent if respondent and respondent != "Unspecified Respondent" else existing_blt.respondent
            comp_addr = comp_addr or existing_blt.complainant_addr or ""
            resp_addr = resp_addr or existing_blt.respondent_addr or ""
            zone_raw = zone_raw or existing_blt.zone_id or ""

        complainant_id = find_census_resident_id_by_name(complainant)
        respondent_id = find_census_resident_id_by_name(respondent)

        if complainant_id:
            c_res = CensusRecord.query.get(complainant_id)
            if c_res:
                comp_addr = comp_addr or c_res.address or ""
                zone_raw = zone_raw or c_res.zone_id or ""
        if respondent_id:
            r_res = CensusRecord.query.get(respondent_id)
            if r_res:
                resp_addr = resp_addr or r_res.address or ""
                if not zone_raw:
                    zone_raw = r_res.zone_id or ""

        # Resolve Zone with multi-tier adaptive resolution
        deterministic_key = custom_docket or f"{complainant}_{respondent}_{row_num}"
        zone_id, base_lat, base_lng = resolve_zone_from_address(zone_raw, comp_addr, location_val, resp_addr, deterministic_seed=deterministic_key)

        lat = round(base_lat + random.uniform(-0.0004, 0.0004), 6)
        lng = round(base_lng + random.uniform(-0.0004, 0.0004), 6)

        nature_desc = _get_val(row, "nature", "Neighborhood Dispute")
        case_type_raw = _get_val(row, "case_type")
        case_type = "CRIM" if "CRIM" in case_type_raw.upper() else ("CIVIL" if "CIVIL" in case_type_raw.upper() else ("CRIM" if "CRIMINAL" in nature_desc.upper() else "CIVIL"))

        date_filed_raw = _get_val(row, "date_filed")
        date_filed = parse_date(_parse_flexible_date(date_filed_raw)) or datetime.utcnow().date()

        officer_raw = _get_val(row, "officer")
        duty_officer = officer_raw or current_username or "Desk Officer"

        category = _map_cat(nature_desc)
        docket_no = custom_docket or next_seq_no(BlotterRecord, "docket_no", "BLT")
        inc_report_no = next_seq_no(Incident, "report_no", "INC")

        effective_location = comp_addr or location_val or f"{zone_id}, Barangay Mapulang Lupa"
        if "mapulang lupa" not in effective_location.lower():
            effective_location = f"{effective_location}, Barangay Mapulang Lupa"

        if existing_blt:
            record = existing_blt
            record.date_filed = date_filed
            record.complainant = complainant
            record.complainant_id = complainant_id
            record.complainant_addr = comp_addr or effective_location
            record.respondent = respondent
            record.respondent_id = respondent_id
            record.respondent_addr = resp_addr or "Barangay Mapulang Lupa"
            record.nature = nature_desc
            record.case_type = case_type
            record.zone_id = zone_id

            if record.source_incident_id:
                inc = Incident.query.get(record.source_incident_id)
                if inc:
                    inc.incident_date = date_filed
                    inc.zone_id = zone_id
                    inc.location = effective_location
                    inc.lat = lat
                    inc.lng = lng
                    inc.category = category
                    inc.description = nature_desc
                    inc.reporter = complainant
                    inc.reporter_resident_id = complainant_id
                    inc.reporter_address = comp_addr or effective_location
                    inc.involved_parties = f"Complainant: {complainant} | Respondent: {respondent}"
            db.session.flush()
        else:
            # Create linked root incident report
            incident = Incident(
                report_no=inc_report_no,
                incident_date=date_filed,
                time_reported=datetime.strptime("08:00:00", "%H:%M:%S").time(),
                hour=8,
                zone_id=zone_id,
                location=effective_location,
                lat=lat,
                lng=lng,
                category=category,
                priority="Medium",
                description=nature_desc,
                reporter=complainant,
                reporter_resident_id=complainant_id,
                reporter_address=comp_addr or effective_location,
                involved_parties=f"Complainant: {complainant} | Respondent: {respondent}",
                officer=duty_officer,
                status="Elevated to Blotter",
                archived=False,
            )
            db.session.add(incident)
            db.session.flush()

            record = BlotterRecord(
                docket_no=docket_no,
                date_filed=date_filed,
                source_incident_id=incident.id,
                complainant=complainant,
                complainant_id=complainant_id,
                complainant_addr=comp_addr or effective_location,
                respondent=respondent,
                respondent_id=respondent_id,
                respondent_addr=resp_addr or "Barangay Mapulang Lupa",
                nature=nature_desc,
                case_type=case_type,
                status="Pending",
                zone_id=zone_id,
                archived=False,
            )
            db.session.add(record)
            db.session.flush()

        # Create or update associated settlement case
        raw_status = _get_val(row, "status", "Pending").upper()
        stl_status = "Complied" if ("SETTLED" in raw_status or "COMPLIED" in raw_status or "RESOLVED" in raw_status) else ("Not Complied" if ("NOT COMPLIED" in raw_status or "REPUDIATED" in raw_status or "CFA" in raw_status) else "Pending")
        stage_val = _get_val(row, "stage", "Mediation (M)")
        remarks_val = _get_val(row, "remarks")

        existing_stl = Settlement.query.filter_by(blotter_id=record.id).first()
        if not existing_stl:
            stl_case_no = next_seq_no(Settlement, "case_no", "STL")
            settlement = Settlement(
                blotter_id=record.id,
                case_no=stl_case_no,
                case_title=f"{complainant} vs {respondent}",
                complaint_title=nature_desc,
                nature="Criminal" if case_type == "CRIM" else "Civil",
                date_filed=date_filed,
                date_confrontation=date_filed,
                action_taken=stage_val,
                main_point=remarks_val or f"Imported Blotter Case: {nature_desc}",
                status=stl_status,
                remarks=remarks_val or "Auto-generated from imported blotter entry",
                archived=False,
            )
            db.session.add(settlement)
            settlements_created += 1

        if zone_id in zone_breakdown:
            zone_breakdown[zone_id] += 1

        db.session.commit()
        imported += 1

    log_audit(
        session.get("username"),
        "Imported",
        "Blotter",
        f"Imported {imported} blotter record(s) with linked incidents and settlements from {original_name}",
    )
    return jsonify({
        "ok": True,
        "importType": "blotter-entry",
        "imported": imported,
        "settlementsCreated": settlements_created,
        "skipped": skipped,
        "zoneBreakdown": zone_breakdown,
        "matchedColumns": list(matched_cols.keys()),
        "errors": errors[:10],
    })
