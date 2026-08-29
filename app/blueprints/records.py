from datetime import datetime

from flask import Blueprint, jsonify, request, session

from ..extensions import db
from ..geocoding import forward_geocode, is_point_inside_boundary
from ..helpers import (
    compute_age,
    find_census_resident_id_by_name,
    is_name_a_census_resident,
    next_seq_no,
    parse_date,
    parse_time,
    resolve_coordinates_by_zone_and_text,
)
from ..models import (
    BarangayClearance,
    BarangayNonResidency,
    BarangayResidency,
    BlotterRecord,
    CensusRecord,
    Incident,
    IndigencyCertificate,
    Notification,
    Settlement,
)
from ..permissions import json_error, log_audit, login_required, permission_required, role_can

bp = Blueprint("records", __name__)

MIN_BLOTTER_PARTY_AGE = 15


def _blotter_party_error(resident: CensusRecord, role_label: str):
    """None if `resident` is eligible to be named as a blotter party;
    otherwise the json_error() response describing why not."""
    if resident.status == "Deceased":
        if role_label.lower() in ("respondent", "respondents"):
            return json_error("Deceased residents cannot be recorded as respondents.", 422)
        else:
            return json_error("Deceased residents cannot be filed as complainants/reporters.", 422)
    age = compute_age(resident.date_of_birth)
    if age is not None and age < MIN_BLOTTER_PARTY_AGE:
        return json_error(
            f"{role_label} \"{resident.first_name} {resident.last_name}\" is {age} years old. "
            f"Residents must be at least {MIN_BLOTTER_PARTY_AGE} to be involved in a blotter record.",
            422
        )
    return None


@bp.route("/api/<string:module>/batch-archive", methods=["POST"])
@login_required
def batch_archive_direct(module):
    return _handle_batch(module, "batch_archive")


@bp.route("/api/<string:module>/batch-permanent-delete", methods=["POST", "DELETE"])
@login_required
def batch_perm_delete_direct(module):
    return _handle_batch(module, "batch_permanent_delete")


@bp.route("/api/<string:module>/batch-restore", methods=["POST"])
@login_required
def batch_restore_direct(module):
    return _handle_batch(module, "batch_restore")


@bp.route("/api/settlements/<int:settlement_id>/status", methods=["PATCH", "PUT"])
@bp.route("/api/settlements/<int:settlement_id>/resolve", methods=["POST", "PATCH", "PUT"])
@login_required
def update_settlement_status(settlement_id):
    settlement = Settlement.query.get(settlement_id)
    if not settlement:
        return json_error("Settlement record not found.", 404)

    d = request.get_json(silent=True) or {}
    new_status = d.get("status")
    if not new_status:
        return json_error("Status is required.", 400)

    settlement.status = new_status
    if d.get("actionTaken") or d.get("action_taken"):
        settlement.action_taken = d.get("actionTaken") or d.get("action_taken")
    if d.get("dateSettlement") or d.get("date_settlement"):
        settlement.date_settlement = parse_date(d.get("dateSettlement") or d.get("date_settlement"))
    if d.get("dateExecution") or d.get("date_execution"):
        settlement.date_execution = parse_date(d.get("dateExecution") or d.get("date_execution"))
    if d.get("dateConfrontation") or d.get("date_confrontation"):
        settlement.date_confrontation = parse_date(d.get("dateConfrontation") or d.get("date_confrontation"))
    if d.get("mainPoint") or d.get("main_point"):
        settlement.main_point = d.get("mainPoint") or d.get("main_point")
    if d.get("remarks"):
        settlement.remarks = d.get("remarks")

    _sync_settlement_to_blotter_and_incident(settlement)

    actor = session.get("username") or "System"
    ts = datetime.utcnow().strftime("%b %d, %Y %I:%M %p")
    db.session.add(Notification(
        type="settlement_updated",
        title=f"Settlement Status Updated: {settlement.case_no}",
        body=f"[SETTLEMENT] Case ID: {settlement.case_no} • Status: {new_status} • Actor: {actor} • {ts}",
        severity="info" if new_status in ("Settled", "Complied", "Resolved") else "warning",
        link=f"settlement.html?highlight={settlement.case_no}",
        ref_table="settlements",
        ref_id=settlement.id,
    ))

    db.session.commit()

    b = BlotterRecord.query.get(settlement.blotter_id) if settlement.blotter_id else None
    inc = Incident.query.get(b.source_incident_id) if (b and b.source_incident_id) else None

    username = session.get("username", "System")
    log_audit(
        username,
        "STATUS_SYNC",
        "settlement",
        f"Settlement #{settlement.case_no} updated to {new_status}. Synced Blotter #{b.docket_no if b else 'N/A'} -> {b.status if b else 'N/A'}, Incident #{inc.report_no if inc else 'N/A'} -> {inc.status if inc else 'N/A'}"
    )

    return jsonify({
        "ok": True,
        "success": True,
        "settlement": settlement.to_dict(),
        "blotter_status": b.status if b else None,
        "incident_status": inc.status if inc else None,
    })


@bp.route("/api/incidents/<int:incident_id>/elevate", methods=["POST"])
@bp.route("/api/incidents/<int:incident_id>/elevate-to-blotter", methods=["POST"])
@login_required
def elevate_incident_endpoint(incident_id):
    inc = Incident.query.get(incident_id)
    if not inc:
        return json_error("Incident not found.", 404)
    if inc.is_blotter:
        return json_error("Incident is already elevated to Blotter.", 400)

    d = request.get_json(silent=True) or {}

    # Rule 1: Minor / Age Hierarchy (Under 15 Years Old)
    guardian_name = (d.get("guardianName") or d.get("guardian_name") or inc.guardian_name or "").strip()
    guardian_id = int(d["guardianResidentId"]) if d.get("guardianResidentId") else (
        int(d["guardian_id"]) if d.get("guardian_id") else (
            int(d["guardian_resident_id"]) if d.get("guardian_resident_id") else inc.guardian_resident_id
        )
    )
    guardian_addr = d.get("guardianAddress") or d.get("guardian_address") or inc.guardian_address or ""

    rep_age = None
    if inc.reporter_resident_id:
        rep_resident = CensusRecord.query.get(inc.reporter_resident_id)
        if rep_resident and rep_resident.date_of_birth:
            rep_age = compute_age(rep_resident.date_of_birth)

    is_reporter_minor = rep_age is not None and rep_age < MIN_BLOTTER_PARTY_AGE
    g_res = None
    if guardian_id:
        g_res = CensusRecord.query.get(guardian_id)

    if is_reporter_minor:
        if not guardian_id and not guardian_name:
            return json_error("Reporter is a minor (<15). A parent/guardian must be assigned as the legal Complainant.", 422)
        if guardian_id and g_res:
            if g_res.status == "Deceased":
                return json_error("Deceased residents cannot be filed as complainants/reporters.", 422)
            g_age = compute_age(g_res.date_of_birth)
            if g_age is not None and g_age < 18:
                return json_error("Guardian must be an adult (18 years or older).", 422)

    # Rule 2: Incident Category Exception (Vehicular Accident / Public Incident)
    is_vehicular_or_public = inc.category in ("Vehicular Accident", "Vehicular", "Fire Incident", "Public Hazard")

    if is_reporter_minor:
        complainant = guardian_name or (f"{g_res.first_name} {g_res.last_name}" if g_res else "Parent / Guardian")
        complainant_id = guardian_id
        complainant_addr = guardian_addr
    elif is_vehicular_or_public:
        complainant = d.get("complainant") or inc.complainant or d.get("involved_parties") or inc.involved_parties or ""
        complainant_id = int(d["complainantId"]) if d.get("complainantId") else (
            int(d["complainant_id"]) if d.get("complainant_id") else inc.complainant_resident_id
        )
        complainant_addr = d.get("complainantAddr") or d.get("complainant_addr") or ""
        if not complainant and not complainant_id:
            return json_error("For vehicular/public accidents, the reporter is treated as an eyewitness. Please specify the actual drivers/victims/involved parties.", 422)
    else:
        complainant = d.get("complainant") or inc.complainant or inc.reporter
        complainant_id = int(d["complainantId"]) if d.get("complainantId") else (
            int(d["complainant_id"]) if d.get("complainant_id") else (inc.complainant_resident_id or inc.reporter_resident_id)
        )
        complainant_addr = d.get("complainantAddr") or d.get("complainant_addr") or inc.reporter_address or ""

    respondent = d.get("respondent", "")
    respondent_id = int(d["respondentId"]) if d.get("respondentId") else None

    # Check for deceased complainant / reporter
    if complainant_id:
        c_res = CensusRecord.query.get(complainant_id)
        if c_res and c_res.status == "Deceased":
            return json_error("Deceased residents cannot be filed as complainants/reporters.", 422)
    elif complainant:
        c_dec = CensusRecord.query.filter(
            CensusRecord.status == "Deceased",
            (CensusRecord.first_name + " " + CensusRecord.last_name).ilike(f"%{complainant.strip()}%")
        ).first()
        if c_dec:
            return json_error("Deceased residents cannot be filed as complainants/reporters.", 422)

    # Check for deceased respondent
    if respondent_id:
        r_res = CensusRecord.query.get(respondent_id)
        if r_res and r_res.status == "Deceased":
            return json_error("Deceased residents cannot be recorded as respondents.", 422)
    elif respondent:
        r_dec = CensusRecord.query.filter(
            CensusRecord.status == "Deceased",
            (CensusRecord.first_name + " " + CensusRecord.last_name).ilike(f"%{respondent.strip()}%")
        ).first()
        if r_dec:
            return json_error("Deceased residents cannot be recorded as respondents.", 422)

    docket_no = d.get("docketNo") or next_seq_no(BlotterRecord, "docket_no", "BLT")
    record = BlotterRecord(
        docket_no=docket_no,
        date_filed=parse_date(d.get("dateFiled")) or datetime.utcnow().date(),
        complainant=complainant,
        complainant_id=complainant_id,
        complainant_addr=complainant_addr,
        respondent=respondent,
        respondent_id=respondent_id,
        respondent_addr=d.get("respondentAddr", ""),
        nature=d.get("nature") or inc.category or "Incident Escalation",
        case_type=d.get("type") or ("CIVIL" if is_vehicular_or_public else "CRIM"),
        status="Pending",
        zone_id=inc.zone_id,
        source_incident_id=inc.id,
        incident_time=inc.time_reported,
        narrative=d.get("narrative") or inc.description or "",
    )
    db.session.add(record)
    db.session.flush()

    inc.is_blotter = True
    inc.blotter_docket_no = docket_no
    inc.status = "Elevated to Blotter"
    inc.updated_at = datetime.utcnow()

    # Auto-initialize 1:1 Settlement
    stl_case_no = next_seq_no(Settlement, "case_no", "STL")
    stl = Settlement(
        blotter_id=record.id,
        case_no=stl_case_no,
        case_title=f"{complainant} vs. {respondent}" if respondent else f"{complainant} (Accident / Incident)",
        complaint_title=record.nature or "Blotter Case",
        nature="Civil" if (record.case_type == "CIVIL" or is_vehicular_or_public) else "Criminal",
        date_filed=record.date_filed,
        status="Pending",
        archived=False,
    )
    db.session.add(stl)
    db.session.flush()

    actor = session.get("username") or "System"
    ts = datetime.utcnow().strftime("%b %d, %Y %I:%M %p")
    db.session.add(Notification(
        type="incident_elevated",
        title=f"Incident Elevated to Blotter: {inc.report_no}",
        body=f"[ELEVATED] Case ID: {inc.report_no} ({inc.category}) • Elevated to Blotter Case {docket_no} ({stl_case_no}) • Actor: {actor} • {ts}",
        severity="warning",
        link=f"blotter.html?highlight={docket_no}",
        ref_table="blotter_records",
        ref_id=record.id,
    ))

    db.session.commit()

    return jsonify({"ok": True, "id": record.id, "docket_no": docket_no, "case_no": stl_case_no}), 201


@bp.route("/api/records", methods=["GET", "POST", "PUT", "DELETE"])
@bp.route("/api/records.php", methods=["GET", "POST", "PUT", "DELETE"])
@bp.route("/api/incidents", methods=["GET", "POST", "PUT", "DELETE"])
@bp.route("/api/blotter", methods=["GET", "POST", "PUT", "DELETE"])
@bp.route("/api/settlements", methods=["GET", "POST", "PUT", "DELETE"])
@login_required
def records_router():
    try:
        path = request.path.lower()
        rtype = request.args.get("type", "")
        if not rtype:
            if "incident" in path:
                rtype = "incidents"
            elif "blotter" in path:
                rtype = "blotter"
            elif "settlement" in path:
                rtype = "settlements"

        if rtype == "geocode":
            q = request.args.get("q", "")
            zone = request.args.get("zone", "")
            res = forward_geocode(q, zone)
            if res:
                return jsonify({"ok": True, **res})
            return jsonify({"ok": False, "message": "Location could not be geocoded within Barangay Mapulang Lupa boundary."}), 404

        action = request.args.get("action", "")
        batch = request.args.get("batch", "")
        if action.startswith("batch_") or batch:
            batch_act = action if action.startswith("batch_") else f"batch_{batch}"
            return _handle_batch(rtype, batch_act)

        if request.method == "PUT":
            resp = _enforce("edit_records")
            if resp:
                return resp
        elif request.method == "DELETE":
            is_permanent = request.args.get("permanent") == "1"
            if is_permanent:
                resp = _enforce("delete_records")
                if resp:
                    return resp
            else:
                resp = _enforce("view_records")
                if resp:
                    return resp
        elif request.method == "POST":
            perm = "add_blotter" if rtype in ("blotter", "blotters") else "edit_records"
            resp = _enforce(perm)
            if resp:
                return resp

        if rtype in ("incidents", "incident"):
            return _incidents()
        if rtype in ("blotter", "blotters"):
            return _blotter()
        if rtype in ("settlements", "settlement"):
            return _settlements()
        return json_error("Unknown type or method", 404)
    except Exception as e:
        import traceback
        current_app_logger = getattr(bp, "logger", None)
        return json_error(f"Server error processing records: {str(e)}", 500)


def _handle_batch(rtype, action):
    is_perm_delete = action in ("batch_permanent_delete", "permanent_delete", "delete")
    if is_perm_delete:
        resp = _enforce("delete_records")
    else:
        resp = _enforce("view_records")
    if resp:
        return resp

    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])
    if not ids or not isinstance(ids, list):
        return json_error("ids array is required for batch operations", 400)

    try:
        clean_ids = [int(x) for x in ids if str(x).strip().isdigit() or isinstance(x, int)]
    except (ValueError, TypeError):
        return json_error("Invalid ID format in batch request", 400)

    if not clean_ids:
        return json_error("No valid IDs provided", 400)

    if rtype in ("incidents", "incident"):
        model = Incident
        module_name = "incidents"
    elif rtype in ("blotter", "blotters"):
        model = BlotterRecord
        module_name = "blotter"
    elif rtype in ("settlements", "settlement"):
        model = Settlement
        module_name = "settlements"
    elif rtype in ("census", "residents", "resident"):
        model = CensusRecord
        module_name = "census"
    else:
        return json_error("Unknown module for batch operation", 404)

    username = session.get("username", "system")

    try:
        if action in ("batch_archive", "archive"):
            if not role_can(session.get("role", ""), "archive_records"):
                return json_error("You do not have permission to archive records.", 403)
            rows = model.query.filter(model.id.in_(clean_ids)).all()
            if not rows:
                return json_error("No matching records found to archive", 404)

            for r in rows:
                r.archived = True

            db.session.commit()
            sample_ids = clean_ids[:10]
            more_cnt = len(clean_ids) - 10
            id_desc = f"IDs: {sample_ids}" + (f"... (+{more_cnt} more)" if more_cnt > 0 else "")
            log_audit(username, "BATCH_ARCHIVE", module_name, f"Batch archived {len(rows)} records ({id_desc})")
            return jsonify({"ok": True, "count": len(rows), "archived": True})

        elif action in ("batch_restore", "restore"):
            rows = model.query.filter(model.id.in_(clean_ids)).all()
            if not rows:
                return json_error("No matching records found to restore", 404)

            for r in rows:
                r.archived = False

            db.session.commit()
            sample_ids = clean_ids[:10]
            more_cnt = len(clean_ids) - 10
            id_desc = f"IDs: {sample_ids}" + (f"... (+{more_cnt} more)" if more_cnt > 0 else "")
            log_audit(username, "BATCH_RESTORE", module_name, f"Batch restored {len(rows)} records ({id_desc})")
            return jsonify({"ok": True, "count": len(rows), "restored": True})

        elif action in ("batch_permanent_delete", "permanent_delete", "delete"):
            rows = model.query.filter(model.id.in_(clean_ids)).all()
            if not rows:
                return json_error("No matching records found to delete", 404)

            unarchived = [r.id for r in rows if not r.archived]
            if unarchived:
                return json_error(
                    f"Only archived records can be permanently deleted. {len(unarchived)} record(s) are still active.",
                    400
                )

            if model == Incident:
                BlotterRecord.query.filter(BlotterRecord.source_incident_id.in_(clean_ids)).update(
                    {"source_incident_id": None}, synchronize_session=False
                )
                Notification.query.filter(
                    Notification.ref_table == "incidents",
                    Notification.ref_id.in_(clean_ids)
                ).delete(synchronize_session=False)

            elif model == BlotterRecord:
                Settlement.query.filter(Settlement.blotter_id.in_(clean_ids)).delete(synchronize_session=False)
                dockets = [r.docket_no for r in rows if r.docket_no]
                if dockets:
                    Incident.query.filter(Incident.blotter_docket_no.in_(dockets)).update(
                        {"is_blotter": False, "blotter_docket_no": None, "status": "Pending"},
                        synchronize_session=False
                    )
                Notification.query.filter(
                    Notification.ref_table.in_(["blotter", "blotter_records"]),
                    Notification.ref_id.in_(clean_ids)
                ).delete(synchronize_session=False)

            elif model == Settlement:
                Notification.query.filter(
                    Notification.ref_table == "settlements",
                    Notification.ref_id.in_(clean_ids)
                ).delete(synchronize_session=False)

            elif model == CensusRecord:
                Incident.query.filter(Incident.reporter_resident_id.in_(clean_ids)).update(
                    {"reporter_resident_id": None}, synchronize_session=False
                )
                Incident.query.filter(Incident.complainant_resident_id.in_(clean_ids)).update(
                    {"complainant_resident_id": None}, synchronize_session=False
                )
                Incident.query.filter(Incident.guardian_resident_id.in_(clean_ids)).update(
                    {"guardian_resident_id": None}, synchronize_session=False
                )
                BlotterRecord.query.filter(BlotterRecord.complainant_id.in_(clean_ids)).update(
                    {"complainant_id": None}, synchronize_session=False
                )
                BlotterRecord.query.filter(BlotterRecord.respondent_id.in_(clean_ids)).update(
                    {"respondent_id": None}, synchronize_session=False
                )
                BarangayClearance.query.filter(BarangayClearance.resident_id.in_(clean_ids)).delete(synchronize_session=False)
                BarangayResidency.query.filter(BarangayResidency.resident_id.in_(clean_ids)).delete(synchronize_session=False)
                BarangayNonResidency.query.filter(BarangayNonResidency.resident_id.in_(clean_ids)).delete(synchronize_session=False)
                IndigencyCertificate.query.filter(IndigencyCertificate.resident_id.in_(clean_ids)).delete(synchronize_session=False)
                Notification.query.filter(
                    Notification.ref_table.in_(["census", "census_records"]),
                    Notification.ref_id.in_(clean_ids)
                ).delete(synchronize_session=False)

            for r in rows:
                db.session.delete(r)

            db.session.commit()
            sample_ids = clean_ids[:10]
            more_cnt = len(clean_ids) - 10
            id_desc = f"IDs: {sample_ids}" + (f"... (+{more_cnt} more)" if more_cnt > 0 else "")
            log_audit(
                username,
                "BATCH_PERMANENT_DELETE",
                module_name,
                f"Batch permanently deleted {len(rows)} records ({id_desc})"
            )
            return jsonify({"ok": True, "count": len(rows), "deleted": True})

        else:
            return json_error("Unknown batch action", 400)

    except Exception as e:
        db.session.rollback()
        return json_error(f"Batch operation failed: {str(e)}", 500)


def _enforce(permission):
    from ..permissions import role_can
    role = session.get("role", "")
    if not role_can(role, permission):
        msg = (
            "Access Denied: Only System Administrators are authorized to permanently delete records."
            if permission == "delete_records"
            else "You do not have permission to perform this action."
        )
        return json_error(msg, 403)
    return None


# ---------------- INCIDENTS ----------------
def _incidents():
    method = request.method

    if method == "GET":
        try:
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
            
            result = []
            for r in rows:
                try:
                    result.append(r.to_dict())
                except Exception:
                    result.append({
                        "id": getattr(r, "id", None),
                        "report_no": getattr(r, "report_no", ""),
                        "incident_date": r.incident_date.isoformat() if getattr(r, "incident_date", None) else None,
                        "time_reported": r.time_reported.isoformat() if getattr(r, "time_reported", None) else None,
                        "hour": getattr(r, "hour", 0),
                        "zone_id": getattr(r, "zone_id", "Zone 1"),
                        "location": getattr(r, "location", ""),
                        "lat": float(r.lat) if getattr(r, "lat", None) is not None else None,
                        "lng": float(r.lng) if getattr(r, "lng", None) is not None else None,
                        "category": getattr(r, "category", "Other"),
                        "description": getattr(r, "description", ""),
                        "reporter": getattr(r, "reporter", ""),
                        "officer": getattr(r, "officer", ""),
                        "priority": getattr(r, "priority", "Medium"),
                        "status": getattr(r, "status", "Under Investigation"),
                        "is_blotter": bool(getattr(r, "is_blotter", False)),
                        "blotter_docket_no": getattr(r, "blotter_docket_no", None),
                        "is_non_resident": bool(getattr(r, "is_non_resident", False)),
                        "reporter_resident_id": getattr(r, "reporter_resident_id", None),
                        "reporter_address": getattr(r, "reporter_address", "") or "",
                        "complainant": getattr(r, "complainant", "") or "",
                        "complainant_resident_id": getattr(r, "complainant_resident_id", None),
                        "guardian_name": getattr(r, "guardian_name", "") or "",
                        "guardian_resident_id": getattr(r, "guardian_resident_id", None),
                        "guardian_address": getattr(r, "guardian_address", "") or "",
                        "involved_parties": getattr(r, "involved_parties", "") or "",
                        "resolved_at": r.resolved_at.isoformat() if getattr(r, "resolved_at", None) else None,
                        "archived": bool(getattr(r, "archived", False)),
                    })
            return jsonify(result)
        except Exception as e:
            return json_error(f"Failed to fetch incident records: {str(e)}", 500)

    if method == "POST":
        d = request.get_json(silent=True) or {}
        zone_id = d.get("zone") or "Zone 1"
        loc_text = d.get("location", "")
        lat = float(d["lat"]) if d.get("lat") not in (None, "") else None
        lng = float(d["lng"]) if d.get("lng") not in (None, "") else None

        # Strict boundary validation if explicit coordinates were passed
        if lat is not None and lng is not None:
            if not is_point_inside_boundary(lat, lng):
                return json_error("Cannot file incident: Location coordinates fall outside Barangay Mapulang Lupa boundary.", 422)

        # Auto-resolve / Forward Geocode if coordinates not supplied
        if lat is None or lng is None:
            geo = forward_geocode(loc_text, zone_id)
            if geo and geo.get("lat") and geo.get("lng"):
                lat, lng = float(geo["lat"]), float(geo["lng"])

        report_no = d.get("reportNo") or next_seq_no(Incident, "report_no", "INC", 4)
        idate = parse_date(d.get("date")) or datetime.utcnow().date()
        time_reported = parse_time(d.get("timeReported")) or datetime.utcnow().time().replace(microsecond=0)
        hour = time_reported.hour

        reporter_resident_id = int(d["reporterResidentId"]) if d.get("reporterResidentId") else (int(d["reporter_resident_id"]) if d.get("reporter_resident_id") else None)
        is_non_resident = bool(d.get("isNonResident") or d.get("is_non_resident"))
        reporter_address = (d.get("reporterAddress") or d.get("reporter_address") or "").strip()

        guardian_name = (d.get("guardianName") or d.get("guardian_name") or "").strip()
        guardian_resident_id = int(d["guardianResidentId"]) if d.get("guardianResidentId") else (
            int(d["guardian_resident_id"]) if d.get("guardian_resident_id") else (
                int(d["guardian_id"]) if d.get("guardian_id") else None
            )
        )
        guardian_address = (d.get("guardianAddress") or d.get("guardian_address") or "").strip()
        complainant = (d.get("complainant") or "").strip()
        complainant_resident_id = int(d["complainantResidentId"]) if d.get("complainantResidentId") else (
            int(d["complainant_resident_id"]) if d.get("complainant_resident_id") else (
                int(d["complainant_id"]) if d.get("complainant_id") else None
            )
        )
        involved_parties = (d.get("involvedParties") or d.get("involved_parties") or "").strip()

        # Validate reporter is not deceased in Census and check age
        if reporter_resident_id and not is_non_resident:
            resident = CensusRecord.query.get(reporter_resident_id)
            if resident and resident.status == "Deceased":
                return json_error("Deceased residents cannot be filed as complainants/reporters.", 422)
            if resident:
                rep_age = compute_age(resident.date_of_birth)
                if rep_age is not None and rep_age < MIN_BLOTTER_PARTY_AGE:
                    if not guardian_name and not guardian_resident_id:
                        return json_error("Reporter is a minor (<15). A parent/guardian must be assigned as the legal Complainant.", 422)
                if not reporter_address:
                    parts = [resident.address, resident.zone_id, "Barangay Mapulang Lupa, Valenzuela City"]
                    reporter_address = ", ".join([p for p in parts if p])
        elif d.get("reporter") and not is_non_resident:
            rep_name = (d.get("reporter") or "").strip()
            dec = CensusRecord.query.filter(
                CensusRecord.status == "Deceased",
                (CensusRecord.first_name + " " + CensusRecord.last_name).ilike(f"%{rep_name}%")
            ).first()
            if dec:
                return json_error("Deceased residents cannot be filed as complainants/reporters.", 422)

        if guardian_resident_id:
            g_res = CensusRecord.query.get(guardian_resident_id)
            if g_res and g_res.status == "Deceased":
                return json_error("Deceased residents cannot be filed as complainants/reporters.", 422)
            if g_res and not guardian_address:
                parts = [g_res.address, g_res.zone_id, "Barangay Mapulang Lupa, Valenzuela City"]
                guardian_address = ", ".join([p for p in parts if p])
            if g_res:
                g_age = compute_age(g_res.date_of_birth)
                if g_age is not None and g_age < 18:
                    return json_error("Guardian must be an adult (18 years or older).", 422)

        ALLOWED_INCIDENT_STATUSES = {"Pending", "Referred", "Elevated to Blotter"}
        status_input = (d.get("status") or "Pending").strip()
        if status_input not in ALLOWED_INCIDENT_STATUSES:
            if status_input in ("Under Investigation", "Open"):
                status_input = "Pending"
            elif status_input in ("Elevated", "Elevated to Blotter Records"):
                status_input = "Elevated to Blotter"
            elif status_input not in ALLOWED_INCIDENT_STATUSES:
                return json_error("Invalid status. Allowed statuses are: Pending, Referred, Elevated to Blotter.", 400)

        incident = Incident(
            report_no=report_no, incident_date=idate, time_reported=time_reported, hour=hour,
            zone_id=zone_id, location=loc_text, lat=lat, lng=lng,
            category=d.get("category") or "Other", description=d.get("description", ""),
            reporter=d.get("reporter", ""), officer=d.get("officer", ""),
            priority=d.get("priority") or "Medium", status=status_input,
            is_non_resident=is_non_resident,
            reporter_resident_id=reporter_resident_id if not is_non_resident else None,
            reporter_address=reporter_address,
            complainant=complainant,
            complainant_resident_id=complainant_resident_id,
            guardian_name=guardian_name,
            guardian_resident_id=guardian_resident_id,
            guardian_address=guardian_address,
            involved_parties=involved_parties,
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

        if incident.is_blotter or incident.status in ("Elevated to Blotter", "ELEVATED"):
            return json_error(f"Record is an official Blotter case ({incident.blotter_docket_no or 'Elevated'}). Edits must be made in Blotter Records.", 403)

        d = request.get_json(silent=True) or {}
        zone_id = d.get("zone") or "Zone 1"
        loc_text = d.get("location", "")
        lat = float(d["lat"]) if d.get("lat") not in (None, "") else None
        lng = float(d["lng"]) if d.get("lng") not in (None, "") else None

        # Strict boundary validation if explicit coordinates were passed
        if lat is not None and lng is not None:
            if not is_point_inside_boundary(lat, lng):
                return json_error("Cannot update incident: Location coordinates fall outside Barangay Mapulang Lupa boundary.", 422)

        # Auto-resolve / Forward Geocode if coordinates not supplied
        if lat is None or lng is None:
            geo = forward_geocode(loc_text, zone_id)
            if geo and geo.get("lat") and geo.get("lng"):
                lat, lng = float(geo["lat"]), float(geo["lng"])

        time_reported = parse_time(d.get("timeReported")) or parse_time("12:00:00")

        reporter_resident_id = int(d["reporterResidentId"]) if d.get("reporterResidentId") else (int(d["reporter_resident_id"]) if d.get("reporter_resident_id") else None)
        is_non_resident = bool(d.get("isNonResident") or d.get("is_non_resident"))
        reporter_address = (d.get("reporterAddress") or d.get("reporter_address") or "").strip()

        guardian_name = (d.get("guardianName") or d.get("guardian_name") or "").strip()
        guardian_resident_id = int(d["guardianResidentId"]) if d.get("guardianResidentId") else (
            int(d["guardian_resident_id"]) if d.get("guardian_resident_id") else (
                int(d["guardian_id"]) if d.get("guardian_id") else None
            )
        )
        guardian_address = (d.get("guardianAddress") or d.get("guardian_address") or "").strip()
        complainant = (d.get("complainant") or "").strip()
        complainant_resident_id = int(d["complainantResidentId"]) if d.get("complainantResidentId") else (
            int(d["complainant_resident_id"]) if d.get("complainant_resident_id") else (
                int(d["complainant_id"]) if d.get("complainant_id") else None
            )
        )
        involved_parties = (d.get("involvedParties") or d.get("involved_parties") or "").strip()

        if reporter_resident_id and not is_non_resident:
            resident = CensusRecord.query.get(reporter_resident_id)
            if resident and resident.status == "Deceased":
                return json_error("Deceased residents cannot be filed as complainants/reporters.", 422)
            if resident:
                rep_age = compute_age(resident.date_of_birth)
                if rep_age is not None and rep_age < MIN_BLOTTER_PARTY_AGE:
                    if not guardian_name and not guardian_resident_id:
                        return json_error("Reporter is a minor (<15). A parent/guardian must be assigned as the legal Complainant.", 422)
                if not reporter_address:
                    parts = [resident.address, resident.zone_id, "Barangay Mapulang Lupa, Valenzuela City"]
                    reporter_address = ", ".join([p for p in parts if p])
        elif d.get("reporter") and not is_non_resident:
            rep_name = (d.get("reporter") or "").strip()
            dec = CensusRecord.query.filter(
                CensusRecord.status == "Deceased",
                (CensusRecord.first_name + " " + CensusRecord.last_name).ilike(f"%{rep_name}%")
            ).first()
            if dec:
                return json_error("Deceased residents cannot be filed as complainants/reporters.", 422)

        if guardian_resident_id:
            g_res = CensusRecord.query.get(guardian_resident_id)
            if g_res and g_res.status == "Deceased":
                return json_error("Deceased residents cannot be filed as complainants/reporters.", 422)
            if g_res and not guardian_address:
                parts = [g_res.address, g_res.zone_id, "Barangay Mapulang Lupa, Valenzuela City"]
                guardian_address = ", ".join([p for p in parts if p])
            if g_res:
                g_age = compute_age(g_res.date_of_birth)
                if g_age is not None and g_age < 18:
                    return json_error("Guardian must be an adult (18 years or older).", 422)

        incident.incident_date = parse_date(d.get("date")) or datetime.utcnow().date()
        incident.time_reported = time_reported
        incident.hour = time_reported.hour
        incident.zone_id = zone_id
        incident.location = loc_text
        incident.lat = lat
        incident.lng = lng
        incident.category = d.get("category") or "Other"
        incident.description = d.get("description", "")
        incident.reporter = d.get("reporter", "")
        incident.is_non_resident = is_non_resident
        incident.reporter_resident_id = reporter_resident_id if not is_non_resident else None
        incident.reporter_address = reporter_address
        incident.complainant = complainant
        incident.complainant_resident_id = complainant_resident_id
        incident.guardian_name = guardian_name
        incident.guardian_resident_id = guardian_resident_id
        incident.guardian_address = guardian_address
        incident.involved_parties = involved_parties
        incident.officer = d.get("officer", "")
        ALLOWED_INCIDENT_STATUSES = {"Pending", "Referred", "Elevated to Blotter", "Resolved", "Closed"}
        status_input = (d.get("status") or incident.status or "Pending").strip()
        if status_input not in ALLOWED_INCIDENT_STATUSES:
            if status_input in ("Under Investigation", "Open"):
                status_input = "Pending"
            elif status_input in ("Elevated", "Elevated to Blotter Records"):
                status_input = "Elevated to Blotter"
            elif status_input not in ALLOWED_INCIDENT_STATUSES:
                return json_error("Invalid status. Allowed statuses are: Pending, Referred, Elevated to Blotter, Resolved, Closed.", 400)

        incident.priority = d.get("priority") or "Medium"
        incident.status = status_input

        actor = session.get("username") or "System"
        ts = datetime.utcnow().strftime("%b %d, %Y %I:%M %p")
        if incident.status == "Elevated to Blotter":
            db.session.add(Notification(
                type="incident_elevated",
                title=f"Incident Elevated to Blotter: {incident.report_no}",
                body=f"[ELEVATED] Case ID: {incident.report_no} ({incident.category}) • Elevated to Blotter • Actor: {actor} • {ts}",
                severity="warning",
                link=f"incident.html?highlight={incident.report_no}",
                ref_table="incidents",
                ref_id=incident.id,
            ))
        else:
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

        is_permanent = request.args.get("permanent") == "1" or request.args.get("force") == "1"
        if is_permanent:
            if not incident.archived:
                return json_error("Only archived records can be permanently deleted. Please archive the record first.", 400)

            # Unlink any blotter records referencing this incident as source
            BlotterRecord.query.filter_by(source_incident_id=incident.id).update({"source_incident_id": None})

            # Clean up notifications referencing this incident
            Notification.query.filter(
                (Notification.ref_table == "incidents") & (Notification.ref_id == incident.id)
            ).delete(synchronize_session=False)

            report_no = incident.report_no
            db.session.delete(incident)
            db.session.commit()

            username = session.get("username", "system")
            log_audit(username, "PERMANENT_DELETE", "incidents", f"Permanently deleted incident report {report_no} (ID: {rid})")

            return jsonify({"ok": True, "deleted": True, "id": rid})

        if not role_can(session.get("role", ""), "archive_records"):
            return json_error("You do not have permission to archive records.", 403)

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

        # Name-based check for deceased residents
        if not complainant_id and complainant:
            dec = CensusRecord.query.filter(
                CensusRecord.status == "Deceased",
                (CensusRecord.first_name + " " + CensusRecord.last_name).ilike(f"%{complainant.strip()}%")
            ).first()
            if dec:
                return json_error("Deceased residents cannot be filed as complainants/reporters.", 422)

        if not respondent_id and respondent:
            dec = CensusRecord.query.filter(
                CensusRecord.status == "Deceased",
                (CensusRecord.first_name + " " + CensusRecord.last_name).ilike(f"%{respondent.strip()}%")
            ).first()
            if dec:
                return json_error("Deceased residents cannot be recorded as respondents.", 422)

        same_census_person = complainant_id and respondent_id and complainant_id == respondent_id
        same_name_typed = (
            complainant and respondent and complainant.strip().lower() == respondent.strip().lower()
        )
        if same_census_person or same_name_typed:
            return json_error("Complainant and respondent cannot be the same person.")

        docket_no = d.get("docketNo") or next_seq_no(BlotterRecord, "docket_no", "BLT")
        source_incident_id = d.get("sourceIncidentId") or d.get("source_incident_id")
        record = BlotterRecord(
            docket_no=docket_no, date_filed=parse_date(d.get("dateFiled")) or datetime.utcnow().date(),
            complainant=complainant, complainant_id=complainant_id, complainant_addr=d.get("complainantAddr", ""),
            respondent=respondent, respondent_id=respondent_id, respondent_addr=d.get("respondentAddr", ""),
            nature=d.get("nature", ""), case_type=d.get("type") or "CRIM", status="Pending",
            zone_id=d.get("zone"),
            source_incident_id=source_incident_id,
            incident_time=parse_time(d.get("incidentTime")) if d.get("incidentTime") else None,
            narrative=d.get("narrative", "")
        )
        db.session.add(record)
        db.session.flush()

        if source_incident_id:
            inc = Incident.query.get(source_incident_id)
            if inc:
                inc.is_blotter = True
                inc.blotter_docket_no = docket_no
                inc.status = "Elevated to Blotter"
                inc.updated_at = datetime.utcnow()

        # Auto-Forward / Auto-Initialize 1:1 Settlement Record
        existing_stl = Settlement.query.filter_by(blotter_id=record.id).first()
        stl_case_no = None
        if not existing_stl:
            stl_case_no = next_seq_no(Settlement, "case_no", "STL")
            settlement = Settlement(
                blotter_id=record.id,
                case_no=stl_case_no,
                case_title=f"{complainant} vs. {respondent}",
                complaint_title=record.nature or "Blotter Case",
                nature="Criminal" if record.case_type == "CRIM" else "Civil",
                date_filed=record.date_filed,
                status="Pending",
                archived=False,
            )
            db.session.add(settlement)
        else:
            stl_case_no = existing_stl.case_no

        if source_incident_id and inc:
            actor = session.get("username") or "System"
            ts = datetime.utcnow().strftime("%b %d, %Y %I:%M %p")
            db.session.add(Notification(
                type="incident_elevated",
                title=f"Incident Elevated to Blotter: {inc.report_no}",
                body=f"[ELEVATED] Case ID: {inc.report_no} ({inc.category}) • Elevated to Blotter Case {docket_no} ({stl_case_no}) • Actor: {actor} • {ts}",
                severity="warning",
                link=f"blotter.html?highlight={docket_no}",
                ref_table="blotter_records",
                ref_id=record.id,
            ))

        db.session.commit()
        return jsonify({"ok": True, "id": record.id, "docket_no": docket_no, "case_no": stl_case_no}), 201

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

        # Name-based check for deceased residents
        if not complainant_id and complainant:
            dec = CensusRecord.query.filter(
                CensusRecord.status == "Deceased",
                (CensusRecord.first_name + " " + CensusRecord.last_name).ilike(f"%{complainant.strip()}%")
            ).first()
            if dec:
                return json_error("Deceased residents cannot be filed as complainants/reporters.", 422)

        if not respondent_id and respondent:
            dec = CensusRecord.query.filter(
                CensusRecord.status == "Deceased",
                (CensusRecord.first_name + " " + CensusRecord.last_name).ilike(f"%{respondent.strip()}%")
            ).first()
            if dec:
                return json_error("Deceased residents cannot be recorded as respondents.", 422)

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
        record.zone_id = d.get("zone")

        # Resolution Driver: if linked to settlement, status is driven by Settlement Monitor
        stl = Settlement.query.filter_by(blotter_id=record.id, archived=False).first()
        if stl:
            if stl.status in ("Settled", "Complied", "Resolved"):
                record.status = "Resolved" if stl.status == "Resolved" else "Settled"
            elif stl.status in ("Dismissed", "CFA Issued"):
                record.status = stl.status
            elif stl.status in ("Ongoing", "Hearing Scheduled", "Under Mediation"):
                record.status = "Ongoing"
            else:
                record.status = "Pending"
        else:
            record.status = d.get("status") or "Pending"

        # Single Source of Truth (SSOT): synchronize shared fields to linked Incident Report
        if record.source_incident_id:
            inc = Incident.query.get(record.source_incident_id)
            if inc:
                if d.get("dateFiled"):
                    inc.incident_date = record.date_filed
                if d.get("nature"):
                    inc.description = record.nature
                if d.get("type"):
                    inc.category = d.get("type")
                if d.get("zone"):
                    inc.zone_id = d.get("zone")
                inc.updated_at = datetime.utcnow()

        db.session.commit()
        return jsonify({"ok": True})

    if method == "DELETE":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        record = BlotterRecord.query.get(rid)
        if not record:
            return json_error("Not found", 404)

        is_permanent = request.args.get("permanent") == "1" or request.args.get("force") == "1"
        if is_permanent:
            if not record.archived:
                return json_error("Only archived records can be permanently deleted. Please archive the record first.", 400)

            # Delete child settlements
            Settlement.query.filter_by(blotter_id=record.id).delete(synchronize_session=False)

            # Reset linked incident if any
            if record.source_incident_id:
                inc = Incident.query.get(record.source_incident_id)
                if inc:
                    inc.is_blotter = False
                    inc.blotter_docket_no = None
                    inc.status = "Pending"

            # Clean up notifications referencing this blotter record
            Notification.query.filter(
                (Notification.ref_table.in_(["blotter", "blotter_records"])) & (Notification.ref_id == record.id)
            ).delete(synchronize_session=False)

            docket_no = record.docket_no
            db.session.delete(record)
            db.session.commit()

            username = session.get("username", "System")
            log_audit(username, "PERMANENT_DELETE", "blotter", f"Permanently deleted blotter record {docket_no} (ID: {rid})")

            return jsonify({"ok": True, "deleted": True, "id": rid})

        if not role_can(session.get("role", ""), "archive_records"):
            return json_error("You do not have permission to archive records.", 403)

        record.archived = True
        db.session.commit()
        return jsonify({"ok": True, "archived": True})


def _sync_settlement_to_blotter_and_incident(settlement):
    if not settlement or not settlement.blotter_id:
        return
    b = BlotterRecord.query.get(settlement.blotter_id)
    if not b:
        return

    st = (settlement.status or "Pending").strip()
    act_lower = (settlement.action_taken or "").lower()

    if st in ("Settled", "Complied", "Resolved") or "settled" in act_lower or "amicable" in act_lower or "resolved" in act_lower:
        b.status = "Resolved" if st == "Resolved" else "Settled"
        b.resolved_at = datetime.utcnow()
        if b.source_incident_id:
            inc = Incident.query.get(b.source_incident_id)
            if inc:
                inc.status = "Resolved"
                inc.resolved_at = datetime.utcnow()
    elif st in ("Dismissed", "CFA Issued", "Repudiated") or "dismissed" in act_lower:
        b.status = st
        b.resolved_at = datetime.utcnow()
        if b.source_incident_id:
            inc = Incident.query.get(b.source_incident_id)
            if inc:
                inc.status = "Resolved"
    elif st in ("Ongoing", "Pending", "Hearing Scheduled", "Under Mediation", "Not Complied"):
        b.status = "Ongoing"
        b.resolved_at = None
        if b.source_incident_id:
            inc = Incident.query.get(b.source_incident_id)
            if inc and inc.status == "Resolved":
                inc.status = "Elevated to Blotter"


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
        _sync_settlement_to_blotter_and_incident(settlement)

        actor = session.get("username") or "System"
        ts = datetime.utcnow().strftime("%b %d, %Y %I:%M %p")
        db.session.add(Notification(
            type="settlement_created",
            title=f"New Settlement Case: {settlement.case_no}",
            body=f"[SETTLEMENT] Case ID: {settlement.case_no} • {settlement.case_title} • Status: {settlement.status} • Actor: {actor} • {ts}",
            severity="info",
            link=f"settlement.html?highlight={settlement.case_no}",
            ref_table="settlements",
            ref_id=settlement.id,
        ))

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
        _sync_settlement_to_blotter_and_incident(settlement)

        actor = session.get("username") or "System"
        ts = datetime.utcnow().strftime("%b %d, %Y %I:%M %p")
        db.session.add(Notification(
            type="settlement_updated",
            title=f"Settlement Case Updated: {settlement.case_no}",
            body=f"[SETTLEMENT] Case ID: {settlement.case_no} • Status: {settlement.status} • Action: {settlement.action_taken or 'Updated'} • Actor: {actor} • {ts}",
            severity="info" if settlement.status in ("Settled", "Complied", "Resolved") else "warning",
            link=f"settlement.html?highlight={settlement.case_no}",
            ref_table="settlements",
            ref_id=settlement.id,
        ))

        db.session.commit()
        return jsonify({"ok": True})

    if method == "DELETE":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        settlement = Settlement.query.get(rid)
        if not settlement:
            return json_error("Not found", 404)

        is_permanent = request.args.get("permanent") == "1" or request.args.get("force") == "1"
        if is_permanent:
            if not settlement.archived:
                return json_error("Only archived records can be permanently deleted. Please archive the record first.", 400)

            # Clean up notifications referencing this settlement
            Notification.query.filter(
                (Notification.ref_table == "settlements") & (Notification.ref_id == settlement.id)
            ).delete(synchronize_session=False)

            case_no = settlement.case_no
            db.session.delete(settlement)
            db.session.commit()

            username = session.get("username", "system")
            log_audit(username, "PERMANENT_DELETE", "settlements", f"Permanently deleted settlement case {case_no} (ID: {rid})")

            return jsonify({"ok": True, "deleted": True, "id": rid})

        if not role_can(session.get("role", ""), "archive_records"):
            return json_error("You do not have permission to archive records.", 403)

        settlement.archived = True
        db.session.commit()
        return jsonify({"ok": True, "archived": True})
