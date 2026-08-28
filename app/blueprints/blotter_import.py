import csv
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
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%b %d, %Y", "%B %d, %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _split_case_title(title: str):
    parts = re.split(r"\s+(?:vs\.?|laban\s+kay|v\.)\s+", title.strip(), maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return title.strip(), ""


def resolve_zone_from_address(*texts: str) -> tuple[str | None, float, float]:
    """Resolves Zone (Zone 1 - Zone 7) and coordinates using the official Barangay Zone mapping table:
    * Zone 1 -> Residence 3
    * Zone 2 -> Residence 1
    * Zone 3 -> Pandi Village 2 (Atlantica)
    * Zone 4 -> Mitay 1
    * Zone 5 -> Sitio Gubat
    * Zone 6 -> Bangko St.
    * Zone 7 -> Barangka St.
    """
    combined = " ".join([str(t or "").strip() for t in texts if t]).lower()
    if not combined:
        return None, 14.883, 120.965

    # 1. Direct Zone / Purok regex match (e.g. 'Zone 4', 'Purok 2', 'Z3')
    m = re.search(r"(?:zone|purok|z)\s*([1-7])\b", combined, re.IGNORECASE)
    if m:
        z_id = f"Zone {m.group(1)}"
        base_lat, base_lng = zone_coords(z_id)
        return z_id, base_lat, base_lng

    # 2. Match recognized landmark names & aliases from ZONE_LANDMARK_DEFINITIONS
    for z_id, info in ZONE_LANDMARK_DEFINITIONS.items():
        if info["name"].lower() in combined or any(alias in combined for alias in info.get("aliases", [])):
            return z_id, info["latitude"], info["longitude"]

    # 3. Explicit substring mapping according to the official barangay zone table
    if "residence 3" in combined or "residences 3" in combined or "res 3" in combined:
        return "Zone 1", 14.883760, 120.968420
    if "residence 1" in combined or "residences 1" in combined or "res 1" in combined or "pasong kalabaw" in combined:
        return "Zone 2", 14.882000, 120.958000
    if "atlantica" in combined or "pandi village 2" in combined or "pv2" in combined or "pv 2" in combined:
        return "Zone 3", 14.879000, 120.972000
    if "mitay" in combined or "pandi village 1" in combined or "pv1" in combined or "pv 1" in combined:
        return "Zone 4", 14.887500, 120.962000
    if "gubat" in combined or "barangay hall" in combined or "brgy hall" in combined or "barangay center" in combined:
        return "Zone 5", 14.882500, 120.964500
    if "bangko" in combined:
        return "Zone 6", 14.877500, 120.966500
    if "barangka" in combined or "pandi-angat" in combined or "pandi angat" in combined or "encampment" in combined:
        return "Zone 7", 14.878500, 120.959500

    return None, 14.883, 120.965


def _read_rows_from_upload(file_storage, ext):
    if ext == "xlsx":
        wb = load_workbook(io.BytesIO(file_storage.read()), data_only=True)
        ws = wb.active
        return [[("" if c.value is None else str(c.value)) for c in row] for row in ws.iter_rows()]
    if ext == "csv":
        text = file_storage.read().decode("utf-8-sig", errors="replace")
        return list(csv.reader(io.StringIO(text)))
    return None


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

    # Determine import type from query param, route, or form field
    import_type = request.args.get("type") or request.form.get("importType") or ("blotter-settlement" if "settlement" in request.path else "blotter-entry")

    # Find the best header row
    keywords = [
        "DOCKET", "CASE NO", "CASE_NO", "CASE TITLE", "TITLE",
        "COMPLAINANT", "RESPONDENT", "ADDRESS", "NATURE", "OFFENSE",
        "DATE FILED", "DATE", "HEARING DATE", "STAGE", "PATAWAG", "STATUS", "ZONE"
    ]
    header_row_index = 0
    best_score = 0
    for i, row in enumerate(rows[:10]):
        if not row:
            continue
        row_str = " ".join([str(c).upper() for c in row if c])
        score = sum(1 for k in keywords if k in row_str)
        if score > best_score:
            best_score = score
            header_row_index = i

    headers = [str(c).strip().upper() for c in rows[header_row_index]]
    h_clean = [re.sub(r"[^A-Z0-9]", "", h) for h in headers]

    def match_col(*patterns):
        for p in patterns:
            p_clean = re.sub(r"[^A-Z0-9]", "", p.upper())
            for idx, h in enumerate(h_clean):
                if p_clean in h:
                    return idx
        return -1

    def match_all_cols(*patterns):
        matches = []
        for idx, h in enumerate(h_clean):
            for p in patterns:
                p_clean = re.sub(r"[^A-Z0-9]", "", p.upper())
                if p_clean in h and idx not in matches:
                    matches.append(idx)
        return matches

    col_docket = match_col("DOCKETNO", "DOCKET", "CASENO", "CASENUMBER", "ENTRYNO", "BLOTTERNO")
    col_date = match_col("DATEFILED", "FILINGDATE", "DATEOFFILING", "DATEREPORTED", "HEARINGDATE", "DATE")
    col_title = match_col("CASETITLE", "TITLE")
    col_complainant = match_col("NAMEOFCOMPLAINANT", "COMPLAINANTNAME", "COMPLAINANT", "NAGREREKLAMO", "PLAINTIFF", "PETITIONER", "VICTIM")
    col_respondent = match_col("NAMEOFRESPONDENT", "RESPONDENTNAME", "RESPONDENT", "IPINAGREREKLAMO", "DEFENDANT", "ACCUSED", "SUSPECT")

    # Address columns
    col_comp_addr = match_col("COMPLAINANTADDRESS", "ADDRESSOFCOMPLAINANT", "COMPLAINANTADDR", "COMPADDR")
    col_resp_addr = match_col("RESPONDENTADDRESS", "ADDRESSOFRESPONDENT", "RESPONDENTADDR", "RESPADDR")

    # Fallback to generic ADDRESS / LOCATION columns
    addr_cols = match_all_cols("ADDRESS", "LOCATION", "TIRAHAN", "PLACEOFINCIDENT")
    if col_comp_addr < 0 and addr_cols:
        col_comp_addr = addr_cols[0]
    if col_resp_addr < 0 and len(addr_cols) > 1:
        col_resp_addr = addr_cols[1]

    col_nature = match_col("NATUREOFCASE", "NATUREOFCOMPLAINT", "COMPLAINTTITLE", "NATURE", "OFFENSE", "INCIDENTTYPE", "OFFENSECOMMITTED")
    col_case_type = match_col("CRIMCIVIL", "CRIMINALCIVIL", "CASETYPE", "CLASSIFICATION", "CATEGORY")
    col_zone = match_col("ZONE", "PUROK", "SITIO", "AREA")
    col_location = match_col("PLACEOFINCIDENT", "INCIDENTLOCATION", "LOCATION")
    col_officer = match_col("DESKOFFICER", "POLICEOFFICER", "OFFICER", "DUTYOFFICER", "INVESTIGATOR")
    col_stage = match_col("STAGE", "PATAWAG", "PROCEEDINGS")
    col_status = match_col("SETTLEMENTSTATUS", "CASESTATUS", "STATUS", "ACTIONTAKEN", "DISPOSITION")
    col_remarks = match_col("MAINPOINT", "MAINPOINTOFAGREEMENT", "AGREEMENT", "REMARKS", "NOTES", "DETAILS")
    col_settlement_date = match_col("DATEOFSETTLEMENT", "SETTLEMENTDATE", "DATESETTLED")

    data_rows = rows[header_row_index + 1:]
    imported, settlements_created, skipped = 0, 0, 0
    errors = []
    row_num = header_row_index + 1
    current_username = session.get("username") or "Desk Officer"

    # Category normalization helper
    def _map_cat(txt):
        t = (txt or "").lower()
        if any(k in t for k in ["pag-aaway", "suntukan", "sakitan", "pananakit", "assault", "physical", "bugbog"]):
            return "Physical Assault"
        if any(k in t for k in ["nakawan", "pagnanakaw", "theft", "robbery", "hold-up", "snatching", "kupit"]):
            return "Theft"
        if any(k in t for k in ["domestic", "mag-asawa", "pamilya", "family dispute", "marital", "vawc"]):
            return "Domestic Dispute"
        if any(k in t for k in ["paninira", "vandalism", "damage to property", "sirang gamit"]):
            return "Vandalism"
        if any(k in t for k in ["trespass", "trespassing", "pagpasok"]):
            return "Trespassing"
        if any(k in t for k in ["droga", "drug", "shabu", "marijuana"]):
            return "Drug-Related Activity"
        if any(k in t for k in ["aksidente", "accident", "banggaan", "vehicular", "motorcycle", "kotse"]):
            return "Vehicular Accident"
        if any(k in t for k in ["alitan", "awayan", "kapitbahay", "neighborhood dispute", "boundary dispute", "ingay", "scandal", "public disturbance", "kaguluhan", "lasing"]):
            return "Public Disturbance"
        return "Public Disturbance"

    # Route 2: Settlement import branch
    if import_type == "blotter-settlement" or (col_stage >= 0 and col_complainant < 0):
        for row in data_rows:
            row_num += 1
            if not row or all(str(c).strip() == "" for c in row):
                skipped += 1
                continue
            docket_no = (str(row[col_docket]).strip() if col_docket >= 0 and col_docket < len(row) else "")
            if not docket_no:
                skipped += 1
                continue

            record = BlotterRecord.query.filter_by(docket_no=docket_no).first()
            if not record:
                # Extract actual participant info if present in row
                raw_title = (str(row[col_title]).strip() if col_title >= 0 and col_title < len(row) else "")
                c_name, r_name = _split_case_title(raw_title) if raw_title else ("Complainant", "Respondent")
                nature_val = (str(row[col_nature]).strip() if col_nature >= 0 and col_nature < len(row) else "Settlement Case")
                zone_val = (str(row[col_zone]).strip() if col_zone >= 0 and col_zone < len(row) else "")
                z_id, _, _ = resolve_zone_from_address(zone_val, c_name, r_name)
                z_id = z_id or "Zone 1"

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

            hearing_date_raw = (str(row[col_date]).strip() if col_date >= 0 and col_date < len(row) else "")
            hearing_date = parse_date(_parse_flexible_date(hearing_date_raw)) or datetime.utcnow().date()
            stage = (str(row[col_stage]).strip() if col_stage >= 0 and col_stage < len(row) else "1st Patawag")
            status_raw = (str(row[col_status]).strip() if col_status >= 0 and col_status < len(row) else "Pending").upper()
            remarks = (str(row[col_remarks]).strip() if col_remarks >= 0 and col_remarks < len(row) else "")

            stl_status = "Complied" if ("SETTLED" in status_raw or "COMPLIED" in status_raw) else "Pending"
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

            if "SETTLED" in status_raw or "COMPLIED" in status_raw:
                record.status = "Settled"
            elif "CFA" in status_raw:
                record.status = "CFA Issued"

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
            "errors": errors[:10],
        })

    # Route 1: Blotter Entry branch (Dual Insert with Incidents)
    for row in data_rows:
        row_num += 1
        if not row or all(str(c).strip() == "" for c in row):
            skipped += 1
            continue

        raw_title = (str(row[col_title]).strip() if col_title >= 0 and col_title < len(row) else "")
        complainant = (str(row[col_complainant]).strip() if col_complainant >= 0 and col_complainant < len(row) else "")
        respondent = (str(row[col_respondent]).strip() if col_respondent >= 0 and col_respondent < len(row) else "")

        if not complainant and raw_title:
            complainant, parsed_resp = _split_case_title(raw_title)
            if not respondent:
                respondent = parsed_resp

        # Skip rows with missing critical participant data
        if not complainant and not respondent and not raw_title:
            skipped += 1
            continue

        if not complainant:
            complainant = "Unspecified Complainant"
        if not respondent:
            respondent = "Unspecified Respondent"

        comp_addr = (str(row[col_comp_addr]).strip() if col_comp_addr >= 0 and col_comp_addr < len(row) else "")
        resp_addr = (str(row[col_resp_addr]).strip() if col_resp_addr >= 0 and col_resp_addr < len(row) else "")
        location_val = (str(row[col_location]).strip() if col_location >= 0 and col_location < len(row) else "")
        zone_raw = (str(row[col_zone]).strip() if col_zone >= 0 and col_zone < len(row) else "")

        custom_docket = (str(row[col_docket]).strip() if col_docket >= 0 and col_docket < len(row) else "")
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
        if respondent_id and not comp_addr and not zone_raw:
            r_res = CensusRecord.query.get(respondent_id)
            if r_res:
                resp_addr = resp_addr or r_res.address or ""
                zone_raw = zone_raw or r_res.zone_id or ""

        # Skip rows where critical address and location information is completely missing
        if not comp_addr and not resp_addr and not location_val and not zone_raw:
            skipped += 1
            continue

        # Resolve Zone and geographic coordinates
        zone_id, base_lat, base_lng = resolve_zone_from_address(zone_raw, comp_addr, location_val, resp_addr)
        if not zone_id and complainant_id:
            c_res = CensusRecord.query.get(complainant_id)
            if c_res and c_res.zone_id:
                zone_id = c_res.zone_id
                base_lat, base_lng = zone_coords(zone_id)

        # If zone still cannot be resolved from the data, skip row instead of hardcoding to Zone 1
        if not zone_id:
            skipped += 1
            continue

        lat = round(base_lat + random.uniform(-0.0004, 0.0004), 6)
        lng = round(base_lng + random.uniform(-0.0004, 0.0004), 6)

        nature_desc = (str(row[col_nature]).strip() if col_nature >= 0 and col_nature < len(row) else "Neighborhood Dispute")
        case_type_raw = (str(row[col_case_type]).strip() if col_case_type >= 0 and col_case_type < len(row) else "")
        case_type = "CRIM" if "CRIM" in case_type_raw.upper() else ("CIVIL" if "CIVIL" in case_type_raw.upper() else ("CRIM" if "CRIMINAL" in nature_desc.upper() else "CIVIL"))

        date_filed_raw = (str(row[col_date]).strip() if col_date >= 0 and col_date < len(row) else "")
        date_filed = parse_date(_parse_flexible_date(date_filed_raw)) or datetime.utcnow().date()

        officer_raw = (str(row[col_officer]).strip() if col_officer >= 0 and col_officer < len(row) else "")
        duty_officer = officer_raw or current_username or "Desk Officer"

        category = _map_cat(nature_desc)
        custom_docket = (str(row[col_docket]).strip() if col_docket >= 0 and col_docket < len(row) else "")
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
            # Step 1: Create linked root incident report with actual parsed data
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
                description=nature_desc,
                reporter=complainant,
                is_non_resident=False if complainant_id else True,
                reporter_resident_id=complainant_id,
                reporter_address=comp_addr or effective_location,
                officer=duty_officer,
                priority="Medium",
                status="Elevated to Blotter",
                is_blotter=True,
                blotter_docket_no=docket_no,
                involved_parties=f"Complainant: {complainant} | Respondent: {respondent}",
            )
            db.session.add(incident)
            db.session.flush()

            # Step 2: Create official Blotter Record with actual parsed participant data
            record = BlotterRecord(
                docket_no=docket_no,
                date_filed=date_filed,
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
                source_incident_id=incident.id,
            )
            db.session.add(record)
            db.session.flush()

        # Step 3: Optional settlement
        settlement_date_raw = (str(row[col_settlement_date]).strip() if col_settlement_date >= 0 and col_settlement_date < len(row) else "")
        main_point = (str(row[col_remarks]).strip() if col_remarks >= 0 and col_remarks < len(row) else "")
        status_raw = (str(row[col_status]).strip() if col_status >= 0 and col_status < len(row) else "")

        if settlement_date_raw or main_point or ("COMPLIED" in status_raw.upper()) or ("SETTLED" in status_raw.upper()):
            stl_case_no = next_seq_no(Settlement, "case_no", "STL")
            stl_date = parse_date(_parse_flexible_date(settlement_date_raw)) or date_filed
            stl = Settlement(
                blotter_id=record.id,
                case_no=stl_case_no,
                case_title=f"{complainant} vs {respondent}",
                complaint_title=nature_desc,
                nature="Criminal" if case_type == "CRIM" else "Civil",
                date_filed=date_filed,
                date_settlement=stl_date,
                action_taken="Amicably Settled",
                main_point=main_point or "Settled before Lupon",
                status="Complied" if ("COMPLIED" in status_raw.upper() or "SETTLED" in status_raw.upper()) else "Pending",
                remarks="Imported blotter settlement record",
            )
            db.session.add(stl)
            settlements_created += 1

        db.session.commit()
        imported += 1

    log_audit(
        session.get("username"),
        "Imported",
        "Blotter",
        f"Imported {imported} blotter record(s) ({settlements_created} linked settlement(s)) from {original_name}",
    )

    return jsonify({
        "ok": True,
        "importType": import_type,
        "imported": imported,
        "settlementsCreated": settlements_created,
        "skipped": skipped,
        "errors": errors[:10],
    })
