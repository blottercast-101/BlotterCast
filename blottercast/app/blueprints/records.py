from datetime import datetime

from flask import Blueprint, jsonify, request, session

from ..extensions import db
from ..helpers import (
    find_census_resident_id_by_name,
    is_name_a_census_resident,
    next_seq_no,
    parse_date,
    parse_time,
    zone_coords,
)
from ..models import BlotterRecord, CensusRecord, Incident, Settlement
from ..permissions import json_error, login_required, permission_required

bp = Blueprint("records", __name__)


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

        q = Incident.query
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
        if d.get("lat") not in (None, "") and d.get("lng") not in (None, ""):
            lat, lng = d["lat"], d["lng"]
        else:
            lat, lng = zone_coords(zone_id)

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
        )
        db.session.add(incident)
        db.session.commit()
        return jsonify({"ok": True, "id": incident.id}), 201

    if method == "PUT":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        incident = Incident.query.get(rid)
        if not incident:
            return json_error("Not found", 404)
        d = request.get_json(silent=True) or {}
        zone_id = d.get("zone") or "Zone 1"
        lat_def, lng_def = zone_coords(zone_id)
        lat = d["lat"] if d.get("lat") not in (None, "") else lat_def
        lng = d["lng"] if d.get("lng") not in (None, "") else lng_def
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
        db.session.commit()
        return jsonify({"ok": True})

    if method == "DELETE":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        incident = Incident.query.get(rid)
        if incident:
            db.session.delete(incident)
            db.session.commit()
        return jsonify({"ok": True})


# ---------------- BLOTTER ----------------
def _blotter():
    method = request.method

    if method == "GET":
        if request.args.get("peek"):
            return jsonify({"seqNo": next_seq_no(BlotterRecord, "docket_no", "BLT")})
        rows = BlotterRecord.query.order_by(BlotterRecord.date_filed.desc(), BlotterRecord.id.desc()).all()
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
        d = request.get_json(silent=True) or {}
        complainant = d.get("complainant", "")
        respondent = d.get("respondent", "")
        complainant_id = int(d["complainantId"]) if d.get("complainantId") else None
        respondent_id = int(d["respondentId"]) if d.get("respondentId") else None

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
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        record = BlotterRecord.query.get(rid)
        if record:
            db.session.delete(record)
            db.session.commit()
        return jsonify({"ok": True})


# ---------------- SETTLEMENTS ----------------
def _settlements():
    method = request.method

    if method == "GET":
        if request.args.get("peek"):
            return jsonify({"seqNo": next_seq_no(Settlement, "case_no", "STL")})
        rows = Settlement.query.order_by(Settlement.date_filed.desc(), Settlement.id.desc()).all()
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
            date_confrontation=d.get("dateConfrontation") or None, action_taken=d.get("actionTaken", ""),
            date_settlement=d.get("dateSettlement") or None, date_execution=d.get("dateExecution") or None,
            main_point=d.get("mainPoint", ""), status=d.get("status") or "Pending", remarks=d.get("remarks", ""),
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
        d = request.get_json(silent=True) or {}
        settlement.date_confrontation = d.get("dateConfrontation") or None
        settlement.action_taken = d.get("actionTaken", "")
        settlement.date_settlement = d.get("dateSettlement") or None
        settlement.date_execution = d.get("dateExecution") or None
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
        if settlement:
            db.session.delete(settlement)
            db.session.commit()
        return jsonify({"ok": True})
