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

    header_row_index = None
    for i, row in enumerate(rows[:5]):
        first = (row[0] if row else "").strip().upper()
        if first == "CASE NO.":
            header_row_index = i
            break
    if header_row_index is None:
        return json_error(
            'This doesn\'t look like a Blotter Record file — expected a "CASE NO." column header. '
            "Export a template from this page first if you need the exact format."
        )

    data_rows = rows[header_row_index + 1:]
    imported, settlements_created, skipped = 0, 0, 0
    errors = []
    row_num = header_row_index + 1

    for row in data_rows:
        row_num += 1
        row = row + [""] * (11 - len(row))  # pad short rows
        case_no = (row[0] or "").strip()
        case_title = (row[1] or "").strip()
        complaint_title = (row[2] or "").strip()
        nature_of_case = (row[3] or "").strip()
        date_filed_raw = (row[4] or "").strip()
        date_confrontation_raw = (row[5] or "").strip()
        action_taken = (row[6] or "").strip()
        date_settlement_raw = (row[7] or "").strip()
        date_execution_raw = (row[8] or "").strip()
        main_point = (row[9] or "").strip()
        status_raw = (row[10] or "").strip()

        if not case_title and not complaint_title:
            skipped += 1
            continue

        complainant, respondent = _split_case_title(case_title)
        if not complainant:
            errors.append(f"Row {row_num}: could not read a Case Title.")
            skipped += 1
            continue

        complainant_id = find_census_resident_id_by_name(complainant)
        respondent_id = find_census_resident_id_by_name(respondent)
        complainant_is_resident = complainant_id is not None or is_name_a_census_resident(complainant)
        respondent_is_resident = respondent_id is not None or is_name_a_census_resident(respondent)
        if not complainant_is_resident and not respondent_is_resident:
            errors.append(f'Row {row_num}: skipped — neither "{complainant}" nor "{respondent}" matches a resident in Census.')
            skipped += 1
            continue

        same_census_person = complainant_id is not None and respondent_id is not None and complainant_id == respondent_id
        same_name_typed = complainant.strip().lower() == respondent.strip().lower()
        if same_census_person or same_name_typed:
            errors.append(f'Row {row_num}: skipped — complainant and respondent ("{complainant}") are the same person.')
            skipped += 1
            continue

        date_filed = _parse_flexible_date(date_filed_raw) or datetime.utcnow().date().isoformat()
        date_filed = parse_date(date_filed)
        zone_id = "Zone 1"

        case_type, nature_desc = "CIVIL", nature_of_case
        m = re.match(r"^(criminal|civil)\s*[—-]\s*(.+)$", nature_of_case, re.IGNORECASE)
        if m:
            case_type = "CRIM" if m.group(1).upper() == "CRIMINAL" else "CIVIL"
            nature_desc = m.group(2).strip()
        elif complaint_title:
            nature_desc = complaint_title

        # Map incident category
        def _map_cat(txt):
            t = (txt or "").lower()
            if any(k in t for k in ["assault", "physical", "injury", "pananakit", "suntukan"]): return "Physical Assault"
            if any(k in t for k in ["theft", "robbery", "nakaw", "pagnanakaw", "hold-up"]): return "Theft"
            if any(k in t for k in ["dispute", "domestic", "away", "mag-asawa", "family"]): return "Domestic Dispute"
            if any(k in t for k in ["vandalism", "damage", "paninira"]): return "Vandalism"
            if any(k in t for k in ["trespass", "trespassing", "pagpasok"]): return "Trespassing"
            if any(k in t for k in ["drug", "droga", "shabu"]): return "Drug-Related Activity"
            if any(k in t for k in ["disturbance", "public", "ingay", "kaguluhan"]): return "Public Disturbance"
            return "Other"

        category = _map_cat(nature_desc)
        docket_no = next_seq_no(BlotterRecord, "docket_no", "BLT")
        inc_report_no = next_seq_no(Incident, "report_no", "INC")
        lat, lng = zone_coords(zone_id)

        # 1. Create linked Incident Report with standard legacy fallbacks
        incident = Incident(
            report_no=inc_report_no,
            incident_date=date_filed,
            time_reported=datetime.strptime("12:00:00", "%H:%M:%S").time(),
            hour=12,
            zone_id=zone_id,
            location="Barangay Mapulang Lupa (Legacy Record)",
            lat=lat,
            lng=lng,
            category=category,
            description=nature_desc or "Legacy Blotter Case Record",
            reporter=complainant or "Legacy Walk-In",
            is_non_resident=False if complainant_id else True,
            reporter_resident_id=complainant_id,
            reporter_address="",
            officer="PO1 Legacy / Desk Officer",
            priority="Medium",
            status="Elevated to Blotter",
            is_blotter=True,
            blotter_docket_no=docket_no,
        )
        db.session.add(incident)
        db.session.flush()

        # 2. Create official Blotter Record linked to incident
        record = BlotterRecord(
            docket_no=docket_no, date_filed=date_filed, complainant=complainant or "Legacy Walk-In",
            complainant_id=complainant_id, complainant_addr="", respondent=respondent,
            respondent_id=respondent_id, respondent_addr="", nature=nature_desc,
            case_type=case_type, status="Ongoing", zone_id=zone_id,
            source_incident_id=incident.id,
        )
        db.session.add(record)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            errors.append(f"Row {row_num}: could not save this blotter entry: {e}")
            skipped += 1
            continue
        imported += 1

        has_settlement_data = any([date_confrontation_raw, action_taken, date_settlement_raw, date_execution_raw, main_point, status_raw])
        if has_settlement_data:
            stl_case_no = case_no or next_seq_no(Settlement, "case_no", "STL")
            stl_nature = "Criminal" if case_type == "CRIM" else "Civil"
            status_upper = status_raw.upper()
            stl_status = "Pending"
            if "NOT COMPLIED" in status_upper:
                stl_status = "Not Complied"
            elif "COMPLIED" in status_upper:
                stl_status = "Complied"

            settlement = Settlement(
                blotter_id=record.id, case_no=stl_case_no, case_title=case_title,
                complaint_title=complaint_title, nature=stl_nature, date_filed=date_filed,
                date_confrontation=parse_date(_parse_flexible_date(date_confrontation_raw)),
                action_taken=action_taken, date_settlement=parse_date(_parse_flexible_date(date_settlement_raw)),
                date_execution=parse_date(_parse_flexible_date(date_execution_raw)), main_point=main_point,
                status=stl_status, remarks="",
            )
            db.session.add(settlement)
            try:
                db.session.commit()
                settlements_created += 1
            except Exception:
                db.session.rollback()
                errors.append(f"Row {row_num}: blotter entry saved, but its linked settlement could not be created.")

    log_audit(
        session.get("username"), "Imported", "Blotter",
        f"Imported {imported} blotter record(s) ({settlements_created} linked settlement(s)) from {original_name}",
    )

    return jsonify({
        "ok": True, "imported": imported, "settlementsCreated": settlements_created,
        "skipped": skipped, "errors": errors[:10],
    })
