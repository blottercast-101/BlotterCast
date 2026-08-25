import csv
import io
import re
from datetime import datetime, date

from flask import Blueprint, jsonify, request
from openpyxl import load_workbook

from ..extensions import db
from ..helpers import find_census_resident_id_by_name, is_name_a_census_resident, next_seq_no, parse_date, zone_coords
from ..models import BlotterRecord, Incident, Settlement
from ..permissions import json_error, log_audit, login_required, permission_required
from flask import session

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
    parts = re.split(r"\s+vs\.?\s+", title.strip(), maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return title.strip(), ""


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
    if size > 5 * 1024 * 1024:
        return json_error("File must be smaller than 5MB.")

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

    header_row_index = 0
    for i, row in enumerate(rows[:6]):
        row_str = " ".join([str(c).upper() for c in row if c])
        if any(k in row_str for k in ["CASE NO", "DOCKET", "CASE TITLE", "HEARING DATE", "STAGE"]):
            header_row_index = i
            break

    headers = [str(c).strip().upper() for c in rows[header_row_index]]

    def get_col(*patterns):
        for p in patterns:
            for idx, h in enumerate(headers):
                if p.upper() in h:
                    return idx
        return -1

    col_docket = get_col("DOCKET", "CASE NO", "CASE_NO")
    col_date = get_col("DATE FILED", "HEARING DATE", "DATE")
    col_title = get_col("CASE TITLE", "TITLE")
    col_complainant = get_col("NAME OF COMPLAINANT", "COMPLAINANT")
    col_comp_addr = get_col("COMPLAINANT ADDRESS", "COMPLAINANT_ADDR")
    col_respondent = get_col("NAME OF RESPONDENT", "RESPONDENT")
    col_resp_addr = get_col("RESPONDENT ADDRESS", "RESPONDENT_ADDR")
    col_nature = get_col("NATURE OF CASE", "NATURE", "COMPLAINT TITLE", "OFFENSE")
    col_case_type = get_col("CRIM / CIVIL", "CRIM/CIVIL", "CASE TYPE", "TYPE")
    col_zone = get_col("ZONE")
    col_stage = get_col("STAGE", "PATAWAG")
    col_status = get_col("SETTLEMENT STATUS", "STATUS", "ACTION TAKEN")
    col_remarks = get_col("REMARKS", "MAIN POINT", "AGREEMENT")
    col_settlement_date = get_col("DATE OF SETTLEMENT", "SETTLEMENT DATE")

    data_rows = rows[header_row_index + 1:]
    imported, settlements_created, skipped = 0, 0, 0
    errors = []
    row_num = header_row_index + 1

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
                # Fallback: create stub blotter record
                record = BlotterRecord(
                    docket_no=docket_no, date_filed=datetime.utcnow().date(),
                    complainant="Legacy Complainant", respondent="Legacy Respondent",
                    nature="Legacy Case", case_type="CIVIL", status="Ongoing", zone_id="Zone 1"
                )
                db.session.add(record)
                db.session.flush()

            hearing_date_raw = (str(row[col_date]).strip() if col_date >= 0 and col_date < len(row) else "")
            hearing_date = parse_date(_parse_flexible_date(hearing_date_raw)) or datetime.utcnow().date()
            stage = (str(row[col_stage]).strip() if col_stage >= 0 and col_stage < len(row) else "1st Patawag")
            status_raw = (str(row[col_status]).strip() if col_status >= 0 and col_status < len(row) else "Ongoing").upper()
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
                    blotter_id=record.id, case_no=stl_case_no,
                    case_title=f"{record.complainant} vs {record.respondent}",
                    complaint_title=record.nature, nature="Criminal" if record.case_type == "CRIM" else "Civil",
                    date_filed=record.date_filed, date_confrontation=hearing_date,
                    action_taken=stage, main_point=remarks or f"Status: {status_raw}",
                    status=stl_status, remarks=remarks
                )
                db.session.add(stl)

            if "SETTLED" in status_raw or "COMPLIED" in status_raw:
                record.status = "Resolved"
            elif "CFA" in status_raw:
                record.status = "CFA Issued"

            db.session.commit()
            imported += 1
            settlements_created += 1

        log_audit(session.get("username"), "Imported", "Blotter", f"Imported {imported} blotter settlement(s) from {original_name}")
        return jsonify({"ok": True, "importType": "blotter-settlement", "imported": imported, "settlementsCreated": settlements_created, "skipped": skipped, "errors": errors[:10]})

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

        if not complainant:
            complainant = "Legacy Walk-In"
        if not respondent:
            respondent = "Unspecified Respondent"

        comp_addr = (str(row[col_comp_addr]).strip() if col_comp_addr >= 0 and col_comp_addr < len(row) else "")
        resp_addr = (str(row[col_resp_addr]).strip() if col_resp_addr >= 0 and col_resp_addr < len(row) else "")
        nature_desc = (str(row[col_nature]).strip() if col_nature >= 0 and col_nature < len(row) else "Neighborhood Dispute")
        
        case_type_raw = (str(row[col_case_type]).strip() if col_case_type >= 0 and col_case_type < len(row) else "")
        case_type = "CRIM" if "CRIM" in case_type_raw.upper() else ("CIVIL" if "CIVIL" in case_type_raw.upper() else ("CRIM" if "CRIMINAL" in nature_desc.upper() else "CIVIL"))
        
        date_filed_raw = (str(row[col_date]).strip() if col_date >= 0 and col_date < len(row) else "")
        date_filed = parse_date(_parse_flexible_date(date_filed_raw)) or datetime.utcnow().date()
        
        zone_raw = (str(row[col_zone]).strip() if col_zone >= 0 and col_zone < len(row) else "")
        zone_id = "Zone 1"
        if zone_raw:
            m_zone = re.search(r"zone\s*([1-7])", zone_raw, re.IGNORECASE)
            if m_zone:
                zone_id = f"Zone {m_zone.group(1)}"

        # Category normalization
        def _map_cat(txt):
            t = (txt or "").lower()
            if any(k in t for k in ["pag-aaway", "suntukan", "sakitan", "pananakit", "assault", "physical", "bugbog"]): return "Physical Assault"
            if any(k in t for k in ["nakawan", "pagnanakaw", "theft", "robbery", "hold-up", "snatching", "kupit"]): return "Theft"
            if any(k in t for k in ["alitan", "awayan", "kapitbahay", "neighborhood dispute", "boundary dispute"]): return "Neighborhood Dispute"
            if any(k in t for k in ["domestic", "mag-asawa", "pamilya", "family dispute", "marital"]): return "Domestic Dispute"
            if any(k in t for k in ["paninira", "vandalism", "damage to property", "sirang gamit"]): return "Vandalism"
            if any(k in t for k in ["trespass", "trespassing", "pagpasok"]): return "Trespassing"
            if any(k in t for k in ["droga", "drug", "shabu", "marijuana"]): return "Drug-Related Activity"
            if any(k in t for k in ["ingay", "scandal", "public disturbance", "kaguluhan", "lasing"]): return "Public Disturbance"
            return "Other"

        category = _map_cat(nature_desc)
        custom_docket = (str(row[col_docket]).strip() if col_docket >= 0 and col_docket < len(row) else "")
        docket_no = custom_docket or next_seq_no(BlotterRecord, "docket_no", "BLT")
        inc_report_no = next_seq_no(Incident, "report_no", "INC")
        base_lat, base_lng = zone_coords(zone_id)
        
        import random
        lat = round(base_lat + random.uniform(-0.0008, 0.0008), 6)
        lng = round(base_lng + random.uniform(-0.0008, 0.0008), 6)

        complainant_id = find_census_resident_id_by_name(complainant)
        respondent_id = find_census_resident_id_by_name(respondent)

        # Step 1: Create linked root incident report
        incident = Incident(
            report_no=inc_report_no,
            incident_date=date_filed,
            time_reported=datetime.strptime("19:00:00", "%H:%M:%S").time(),
            hour=19,
            zone_id=zone_id,
            location=comp_addr or "Barangay Mapulang Lupa (Legacy Record)",
            lat=lat,
            lng=lng,
            category=category,
            description=nature_desc or "Legacy Blotter Case Record",
            reporter=complainant,
            is_non_resident=False if complainant_id else True,
            reporter_resident_id=complainant_id,
            reporter_address=comp_addr,
            officer="PO1 Legacy / Desk Officer",
            priority="Medium",
            status="Elevated to Blotter",
            is_blotter=True,
            blotter_docket_no=docket_no,
        )
        db.session.add(incident)
        db.session.flush()

        # Step 2: Create official Blotter Record
        record = BlotterRecord(
            docket_no=docket_no, date_filed=date_filed, complainant=complainant,
            complainant_id=complainant_id, complainant_addr=comp_addr, respondent=respondent,
            respondent_id=respondent_id, respondent_addr=resp_addr, nature=nature_desc,
            case_type=case_type, status="Ongoing", zone_id=zone_id,
            source_incident_id=incident.id,
        )
        db.session.add(record)
        db.session.flush()

        # Step 3: Optional settlement
        settlement_date_raw = (str(row[col_settlement_date]).strip() if col_settlement_date >= 0 and col_settlement_date < len(row) else "")
        main_point = (str(row[col_remarks]).strip() if col_remarks >= 0 and col_remarks < len(row) else "")
        status_raw = (str(row[col_status]).strip() if col_status >= 0 and col_status < len(row) else "")

        if settlement_date_raw or main_point or ("COMPLIED" in status_raw.upper()):
            stl_case_no = next_seq_no(Settlement, "case_no", "STL")
            stl_date = parse_date(_parse_flexible_date(settlement_date_raw)) or date_filed
            stl = Settlement(
                blotter_id=record.id, case_no=stl_case_no,
                case_title=f"{complainant} vs {respondent}",
                complaint_title=nature_desc, nature="Criminal" if case_type == "CRIM" else "Civil",
                date_filed=date_filed, date_settlement=stl_date,
                action_taken="Amicably Settled", main_point=main_point or "Settled before Lupon",
                status="Complied" if "COMPLIED" in status_raw.upper() else "Pending",
                remarks="Legacy imported record"
            )
            db.session.add(stl)
            settlements_created += 1

        db.session.commit()
        imported += 1

    log_audit(
        session.get("username"), "Imported", "Blotter",
        f"Imported {imported} blotter record(s) ({settlements_created} linked settlement(s)) from {original_name}",
    )

    return jsonify({
        "ok": True, "importType": import_type, "imported": imported, "settlementsCreated": settlements_created,
        "skipped": skipped, "errors": errors[:10],
    })
