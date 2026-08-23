from datetime import datetime

from flask import Blueprint, jsonify, request, session

from ..extensions import db
from ..helpers import (
    compute_age,
    find_census_resident_id_by_name,
    is_name_a_census_resident,
    next_seq_no,
    parse_date,
    parse_time,
    zone_coords,
)
from ..models import BlotterRecord, CensusRecord, Incident, Notification, Settlement
from ..permissions import json_error, login_required, permission_required

bp = Blueprint("records", __name__)

MIN_BLOTTER_PARTY_AGE = 15


def _blotter_party_error(resident: CensusRecord, role_label: str):
    """None if `resident` is eligible to be named as a blotter party;
    otherwise the json_error() response describing why not."""
    if resident.status == "Deceased":
        return json_error(
            f"{role_label} \"{resident.first_name} {resident.last_name}\" is recorded as deceased "
            "and cannot be used for a new blotter record."
        )
    age = compute_age(resident.date_of_birth)
    if age is not None and age < MIN_BLOTTER_PARTY_AGE:
        return json_error(
            f"{role_label} \"{resident.first_name} {resident.last_name}\" is {age} years old. "
            f"Residents must be at least {MIN_BLOTTER_PARTY_AGE} to be involved in a blotter record."
        )
    return None


@bp.route("/api/records.php", methods=["GET", "POST", "PUT", "DELETE"])
@login_required
def records_router():
    if request.method == "PUT":
        resp = _enforce("edit_records")
        if resp:
            return resp
    if request.method == "DELETE":
        resp = _enforce("delete_records")
        if resp:
            return resp

    rtype = request.args.get("type", "")
    if rtype == "incidents":
        return _incidents()
    if rtype == "blotter":
        return _blotter()
    if rtype == "settlements":
        return _settlements()
    return json_error("Unknown type or method", 404)


def _enforce(permission):
    from ..permissions import role_can
    role = session.get("role", "")
    if not role_can(role, permission):
        return json_error("You do not have permission to perform this action.", 403)
    return None


# ---------------- INCIDENTS ----------------
def _incidents():
    method = request.method

    if method == "GET":
        if request.args.get("peek"):
            return jsonify({"seqNo": next_seq_no(Incident, "report_no", "INC", 4)})
        show_archived = request.args.get("archived") == "1"
        if show_archived:
            q = Incident.query.filter(Incident.archived == True)
        else:
            q = Incident.query.filter((Incident.archived == False) | (Incident.archived == None))
        if request.args.get("from"):
            q = q.filter(Incident.incident_date >= request.args["from"])
        if request.args.get("to"):
            q = q.filter(Incident.incident_date <= request.args["to"])
        if request.args.get("zone"):
            q = q.filter(Incident.zone_id == request.args["zone"])
        if request.args.get("category"):
            q = q.filter(Incident.category == request.args["category"])
        rows = q.order_by(Incident.incident_date.desc(), Incident.id.desc()).all()
        return jsonify([r.to_dict() for r in rows])

    if method == "POST":
        d = request.get_json(silent=True) or {}
        zone_id = d.get("zone") or "Zone 1"
        lat = float(d["lat"]) if d.get("lat") not in (None, "") else None
        lng = float(d["lng"]) if d.get("lng") not in (None, "") else None

        report_no = d.get("reportNo") or next_seq_no(Incident, "report_no", "INC", 4)
        idate = parse_date(d.get("date")) or datetime.utcnow().date()
        time_reported = parse_time(d.get("timeReported")) or datetime.utcnow().time().replace(microsecond=0)
        hour = time_reported.hour

        incident = Incident(
            report_no=report_no, incident_date=idate, time_reported=time_reported, hour=hour,
            zone_id=zone_id, location=d.get("location", ""), lat=lat, lng=lng,
            category=d.get("category") or "Other", description=d.get("description", ""),
            reporter=d.get("reporter", ""), officer=d.get("officer", ""),
            priority=d.get("priority") or "Medium", status=d.get("status") or "Under Investigation",
            archived=False,
        )
        db.session.add(incident)
        db.session.flush()

        actor = session.get("username") or "System"
        ts = datetime.utcnow().strftime("%b %d, %Y %I:%M %p")
        db.session.add(Notification(
            type="incident_crud",
            title=f"New Incident Report Filed: {incident.report_no}",
            body=f"[ADD] Case ID: {incident.report_no} • {incident.category} at {incident.location} ({incident.zone_id}) • Actor: {actor} • {ts}",
            severity="critical" if incident.priority == "High" else "info",
            link=f"incident.html?highlight={incident.report_no}",
            ref_table="incidents",
            ref_id=incident.id,
        ))

        db.session.commit()
        return jsonify({"ok": True, "id": incident.id}), 201

    if method == "PUT":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        incident = Incident.query.get(rid)
        if not incident:
            return json_error("Not found", 404)

        if request.args.get("restore") == "1":
            incident.archived = False
            db.session.commit()
            return jsonify({"ok": True})

        d = request.get_json(silent=True) or {}
        zone_id = d.get("zone") or "Zone 1"
        lat = float(d["lat"]) if d.get("lat") not in (None, "") else None
        lng = float(d["lng"]) if d.get("lng") not in (None, "") else None
        time_reported = parse_time(d.get("timeReported")) or parse_time("12:00:00")

        incident.incident_date = parse_date(d.get("date")) or datetime.utcnow().date()
        incident.time_reported = time_reported
        incident.hour = time_reported.hour
        incident.zone_id = zone_id
        incident.location = d.get("location", "")
        incident.lat = lat
        incident.lng = lng
        incident.category = d.get("category") or "Other"
        incident.description = d.get("description", "")
        incident.reporter = d.get("reporter", "")
        incident.officer = d.get("officer", "")
        incident.priority = d.get("priority") or "Medium"
        incident.status = d.get("status") or "Under Investigation"

        actor = session.get("username") or "System"
        ts = datetime.utcnow().strftime("%b %d, %Y %I:%M %p")
        db.session.add(Notification(
            type="incident_crud",
            title=f"Incident Report Updated: {incident.report_no}",
            body=f"[EDIT] Case ID: {incident.report_no} • Status: {incident.status} • Actor: {actor} • {ts}",
            severity="warning" if incident.priority == "High" else "info",
            link=f"incident.html?highlight={incident.report_no}",
            ref_table="incidents",
            ref_id=incident.id,
        ))

        db.session.commit()
        return jsonify({"ok": True})

    if method == "DELETE":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        incident = Incident.query.get(rid)
        if not incident:
            return json_error("Not found", 404)
        incident.archived = True
        db.session.commit()
        return jsonify({"ok": True, "archived": True})


# ---------------- BLOTTER ----------------
def _blotter():
    method = request.method

    if method == "GET":
        if request.args.get("peek"):
            return jsonify({"seqNo": next_seq_no(BlotterRecord, "docket_no", "BLT")})
        # Archived records are kept for recordkeeping/audit but are removed
        # from the active view by default — pass ?archived=1 to see them.
        show_archived = request.args.get("archived") == "1"
        if show_archived:
            q = BlotterRecord.query.filter(BlotterRecord.archived == True)
        else:
            q = BlotterRecord.query.filter((BlotterRecord.archived == False) | (BlotterRecord.archived == None))
        rows = q.order_by(BlotterRecord.date_filed.desc(), BlotterRecord.id.desc()).all()
        return jsonify([r.to_dict() for r in rows])

    if method == "POST":
        d = request.get_json(silent=True) or {}
        complainant = d.get("complainant", "")
        respondent = d.get("respondent", "")
        complainant_id = int(d["complainantId"]) if d.get("complainantId") else None
        respondent_id = int(d["respondentId"]) if d.get("respondentId") else None

        complainant_is_resident = (
            bool(CensusRecord.query.get(complainant_id)) if complainant_id
            else is_name_a_census_resident(complainant)
        )
        respondent_is_resident = (
            bool(CensusRecord.query.get(respondent_id)) if respondent_id
            else is_name_a_census_resident(respondent)
        )
        if not complainant_is_resident and not respondent_is_resident:
            return json_error(
                "At least one party (complainant or respondent) must be a registered "
                "resident in Census before a blotter record can be filed."
            )

        for pid, label in ((complainant_id, "Complainant"), (respondent_id, "Respondent")):
            if not pid:
                continue
            resident = CensusRecord.query.get(pid)
            if resident:
                err = _blotter_party_error(resident, label)
                if err:
                    return err

        same_census_person = complainant_id and respondent_id and complainant_id == respondent_id
        same_name_typed = (
            complainant and respondent and complainant.strip().lower() == respondent.strip().lower()
        )
        if same_census_person or same_name_typed:
            return json_error("Complainant and respondent cannot be the same person.")

        docket_no = d.get("docketNo") or next_seq_no(BlotterRecord, "docket_no", "BLT")
        record = BlotterRecord(
            docket_no=docket_no, date_filed=parse_date(d.get("dateFiled")) or datetime.utcnow().date(),
            complainant=complainant, complainant_id=complainant_id, complainant_addr=d.get("complainantAddr", ""),
            respondent=respondent, respondent_id=respondent_id, respondent_addr=d.get("respondentAddr", ""),
            nature=d.get("nature", ""), case_type=d.get("type") or "CRIM", status=d.get("status") or "Pending",
            zone_id=d.get("zone"),
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({"ok": True, "id": record.id}), 201

    if method == "PUT":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        record = BlotterRecord.query.get(rid)
        if not record:
            return json_error("Not found", 404)

        # Restore-from-archive only ever changes the archived flag — it must
        # not touch any other field, so it's handled separately from the
        # full-record edit below (which always expects every field).
        if request.args.get("restore") == "1":
            record.archived = False
            db.session.commit()
            return jsonify({"ok": True})

        d = request.get_json(silent=True) or {}
        complainant = d.get("complainant", "")
        respondent = d.get("respondent", "")
        complainant_id = int(d["complainantId"]) if d.get("complainantId") else None
        respondent_id = int(d["respondentId"]) if d.get("respondentId") else None

        for pid, label in ((complainant_id, "Complainant"), (respondent_id, "Respondent")):
            if not pid:
                continue
            resident = CensusRecord.query.get(pid)
            if resident:
                err = _blotter_party_error(resident, label)
                if err:
                    return err

        same_census_person = complainant_id and respondent_id and complainant_id == respondent_id
        same_name_typed = (
            complainant and respondent and complainant.strip().lower() == respondent.strip().lower()
        )
        if same_census_person or same_name_typed:
            return json_error("Complainant and respondent cannot be the same person.")

        record.date_filed = parse_date(d.get("dateFiled")) or datetime.utcnow().date()
        record.complainant = complainant
        record.complainant_id = complainant_id
        record.complainant_addr = d.get("complainantAddr", "")
        record.respondent = respondent
        record.respondent_id = respondent_id
        record.respondent_addr = d.get("respondentAddr", "")
        record.nature = d.get("nature", "")
        record.case_type = d.get("type") or "CRIM"
        record.status = d.get("status") or "Pending"
        record.zone_id = d.get("zone")
        db.session.commit()
        return jsonify({"ok": True})

    if method == "DELETE":
        # Official records are never permanently deleted — this archives the
        # record instead. It stays in the database for recordkeeping/audit
        # but drops out of the active list by default (see the GET branch).
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        record = BlotterRecord.query.get(rid)
        if not record:
            return json_error("Not found", 404)
        record.archived = True
        db.session.commit()
        return jsonify({"ok": True, "archived": True})


# ---------------- SETTLEMENTS ----------------
def _settlements():
    method = request.method

    if method == "GET":
        if request.args.get("peek"):
            return jsonify({"seqNo": next_seq_no(Settlement, "case_no", "STL")})
        show_archived = request.args.get("archived") == "1"
        if show_archived:
            q = Settlement.query.filter(Settlement.archived == True)
        else:
            q = Settlement.query.filter((Settlement.archived == False) | (Settlement.archived == None))
        rows = q.order_by(Settlement.date_filed.desc(), Settlement.id.desc()).all()
        return jsonify([r.to_dict() for r in rows])

    if method == "POST":
        d = request.get_json(silent=True) or {}
        blotter_id = int(d.get("blotterId") or 0)
        if not blotter_id:
            return json_error("A settlement must be linked to an existing blotter record.")
        b = BlotterRecord.query.get(blotter_id)
        if not b:
            return json_error("That blotter record does not exist.", 404)

        case_no = d.get("caseNo") or next_seq_no(Settlement, "case_no", "STL")
        settlement = Settlement(
            blotter_id=blotter_id, case_no=case_no,
            case_title=f"{b.complainant} vs. {b.respondent}", complaint_title=b.nature,
            nature="Criminal" if b.case_type == "CRIM" else "Civil", date_filed=b.date_filed,
            date_confrontation=parse_date(d.get("dateConfrontation")) or None, action_taken=d.get("actionTaken", ""),
            date_settlement=parse_date(d.get("dateSettlement")) or None, date_execution=parse_date(d.get("dateExecution")) or None,
            main_point=d.get("mainPoint", ""), status=d.get("status") or "Pending", remarks=d.get("remarks", ""),
            archived=False,
        )
        db.session.add(settlement)
        db.session.commit()
        return jsonify({"ok": True, "id": settlement.id}), 201

    if method == "PUT":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        settlement = Settlement.query.get(rid)
        if not settlement:
            return json_error("Not found", 404)

        if request.args.get("restore") == "1":
            settlement.archived = False
            db.session.commit()
            return jsonify({"ok": True})

        d = request.get_json(silent=True) or {}
        settlement.date_confrontation = parse_date(d.get("dateConfrontation")) or None
        settlement.action_taken = d.get("actionTaken", "")
        settlement.date_settlement = parse_date(d.get("dateSettlement")) or None
        settlement.date_execution = parse_date(d.get("dateExecution")) or None
        settlement.main_point = d.get("mainPoint", "")
        settlement.status = d.get("status") or "Pending"
        settlement.remarks = d.get("remarks", "")
        db.session.commit()
        return jsonify({"ok": True})

    if method == "DELETE":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        settlement = Settlement.query.get(rid)
        if not settlement:
            return json_error("Not found", 404)
        settlement.archived = True
        db.session.commit()
        return jsonify({"ok": True, "archived": True})
