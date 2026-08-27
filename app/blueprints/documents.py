from datetime import datetime

from flask import Blueprint, jsonify, request, session
from sqlalchemy import func, or_

from ..extensions import db
from ..helpers import compute_age, full_name_of, next_ctrl_no, next_or_no, parse_date
from ..models import (
    BarangayClearance,
    BarangayNonResidency,
    BarangayResidency,
    BlotterRecord,
    CensusRecord,
    IndigencyCertificate,
    Settlement,
)
from ..permissions import json_error, log_audit, login_required, permission_required, role_can

bp = Blueprint("documents", __name__)

MIN_RESIDENT_REGISTRATION_AGE = 3


@bp.route("/api/documents.php", methods=["GET", "POST", "PUT", "DELETE"])
@bp.route("/api/certificates/generate", methods=["POST"])
@bp.route("/api/certificates/non-residency", methods=["GET", "POST"])
@bp.route("/api/documents/non_residency", methods=["GET", "POST", "DELETE"])
@bp.route("/api/documents/check-clearance", methods=["GET"])
@bp.route("/api/documents/issue", methods=["POST"])
@login_required
def documents_router():
    method = request.method
    dtype = request.args.get("type", "")
    if not dtype:
        if "check-clearance" in request.path:
            dtype = "blotter_clearance_check"
        elif "non-residency" in request.path or "non_residency" in request.path or "certificates" in request.path:
            dtype = "non_residency"
        elif "issue" in request.path:
            d = request.get_json(silent=True) or {}
            dtype = d.get("type", "clearance")

    if method == "PUT" and not role_can(session.get("role", ""), "edit_records"):
        return json_error("You do not have permission to perform this action.", 403)
    if method == "DELETE" and not role_can(session.get("role", ""), "delete_records"):
        return json_error("You do not have permission to perform this action.", 403)

    if dtype == "or_peek" and method == "GET":
        return jsonify({"orNo": next_or_no()})
    if dtype == "blotter_check" and method == "GET":
        return _blotter_check()
    if dtype == "blotter_clearance_check" and method == "GET":
        rid = request.args.get("residentId") or request.args.get("resident_id")
        if not rid:
            return json_error("residentId parameter is required", 400)
        return jsonify(check_resident_blotter_clearance(int(rid)))
    if dtype == "census":
        return _census()
    if dtype == "clearance":
        return _clearance()
    if dtype == "residency":
        return _residency()
    if dtype == "non_residency":
        return _non_residency()
    if dtype == "indigency":
        return _indigency()

    return json_error("Unknown type or method", 404)


# ---------------- BLOTTER CHECK ----------------
def _blotter_check():
    last_name = (request.args.get("lastName") or "").strip()
    first_name = (request.args.get("firstName") or "").strip()
    resident_id = int(request.args["residentId"]) if request.args.get("residentId") else None
    has_name = bool(last_name and first_name)
    if not has_name and not resident_id:
        return jsonify([])

    id_matches = []
    if resident_id:
        rows = BlotterRecord.query.filter(
            or_(BlotterRecord.complainant_id == resident_id, BlotterRecord.respondent_id == resident_id)
        ).order_by(BlotterRecord.date_filed.desc()).all()
        for r in rows:
            id_matches.append({
                "id": r.id, "docket_no": r.docket_no,
                "date_filed": r.date_filed.isoformat() if r.date_filed else None,
                "complainant": r.complainant, "respondent": r.respondent, "nature": r.nature,
                "case_type": r.case_type, "status": r.status,
                "role": "Complainant" if r.complainant_id == resident_id else "Respondent",
            })

    name_matches = []
    if has_name:
        last_like, first_like = f"%{last_name}%", f"%{first_name}%"
        rows = BlotterRecord.query.filter(
            BlotterRecord.complainant_id.is_(None), BlotterRecord.respondent_id.is_(None),
            or_(
                (BlotterRecord.complainant.ilike(last_like)) & (BlotterRecord.complainant.ilike(first_like)),
                (BlotterRecord.respondent.ilike(last_like)) & (BlotterRecord.respondent.ilike(first_like)),
            ),
        ).all()
        for r in rows:
            is_complainant = last_name.lower() in (r.complainant or "").lower() and first_name.lower() in (r.complainant or "").lower()
            name_matches.append({
                "id": r.id, "docket_no": r.docket_no,
                "date_filed": r.date_filed.isoformat() if r.date_filed else None,
                "complainant": r.complainant, "respondent": r.respondent, "nature": r.nature,
                "case_type": r.case_type, "status": r.status,
                "role": "Complainant" if is_complainant else "Respondent",
            })

    return jsonify(id_matches + name_matches)


# ---------------- CENSUS ----------------
def _duplicate_resident(last_name, first_name, middle_name, address, household, sex, age, exclude_id=None):
    if age is None:
        return None
    norm = lambda v: func.lower(func.trim(func.coalesce(v, "")))
    q = CensusRecord.query.filter(
        norm(CensusRecord.last_name) == (last_name or "").strip().lower(),
        norm(CensusRecord.first_name) == (first_name or "").strip().lower(),
        norm(CensusRecord.middle_name) == (middle_name or "").strip().lower(),
        norm(CensusRecord.address) == (address or "").strip().lower(),
        norm(CensusRecord.household_no) == (household or "").strip().lower(),
        CensusRecord.sex == sex,
        CensusRecord.date_of_birth.isnot(None),
    )
    if exclude_id:
        q = q.filter(CensusRecord.id != exclude_id)
    for r in q.all():
        if compute_age(r.date_of_birth) == age:
            return r
    return None


def _census():
    method = request.method

    if method == "GET":
        if request.args.get("peek"):
            max_no = db.session.query(
                func.max(func.cast(func.substr(CensusRecord.resident_no, 5), db.Integer))
            ).filter(CensusRecord.resident_no.like("RES-%")).scalar()
            return jsonify({"seqNo": f"RES-{(max_no or 0) + 1:04d}"})

        show_archived = request.args.get("archived") == "1"
        if show_archived:
            q = CensusRecord.query.filter(CensusRecord.archived == True)
        else:
            q = CensusRecord.query.filter((CensusRecord.archived == False) | (CensusRecord.archived == None))
        rows = q.order_by(CensusRecord.last_name, CensusRecord.first_name).all()
        return jsonify([r.to_dict() for r in rows])

    if method == "POST":
        if request.headers.get("X-Bulk-Import") and not role_can(session.get("role", ""), "import_data"):
            return json_error("You do not have permission to perform this action.", 403)

        d = request.get_json(silent=True) or {}
        dob = d.get("dob") or None
        last_name, first_name, middle_name = d.get("lastName", ""), d.get("firstName", ""), d.get("middleName", "")
        sex, civil_status = d.get("sex") or "Male", d.get("civilStatus") or "Single"
        nationality = d.get("nationality") or "Filipino"
        zone = d.get("zone")
        address, household, contact = d.get("address", ""), d.get("householdNo", ""), d.get("contactNo", "")
        voter = d.get("voterStatus") or "Not Registered"
        occupation, status = d.get("occupation", ""), d.get("status") or "Active"
        if status == "Deceased":
            voter = "Deactivated"

        dob = parse_date(dob)
        age = compute_age(dob)
        if age is not None and age < MIN_RESIDENT_REGISTRATION_AGE:
            return json_error(
                f"This resident is {age} year(s) old. Residents must be at least "
                f"{MIN_RESIDENT_REGISTRATION_AGE} years old to be registered in Census."
            )
        if _duplicate_resident(last_name, first_name, middle_name, address, household, sex, age):
            return json_error(
                "A resident with the same name, address, household number, age, and sex is already in Census.", 409
            )

        max_no = db.session.query(
            func.max(func.cast(func.substr(CensusRecord.resident_no, 5), db.Integer))
        ).filter(CensusRecord.resident_no.like("RES-%")).scalar()
        resident_no = d.get("residentNo") or f"RES-{(max_no or 0) + 1:04d}"

        record = CensusRecord(
            resident_no=resident_no, last_name=last_name, first_name=first_name, middle_name=middle_name,
            date_of_birth=dob, sex=sex, civil_status=civil_status, nationality=nationality, zone_id=zone,
            address=address, household_no=household, contact_no=contact, voter_status=voter,
            occupation=occupation, status=status, archived=False,
        )
        db.session.add(record)
        db.session.commit()
        log_audit(session.get("username"), "Created", "Census", f"New resident recorded: {first_name} {last_name}")
        return jsonify({"ok": True, "id": record.id}), 201

    if method == "PUT":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        record = CensusRecord.query.get(rid)
        if not record:
            return json_error("Resident not found.", 404)

        if request.args.get("restore") == "1":
            record.archived = False
            db.session.commit()
            log_audit(session.get("username"), "Restored", "Census", f"Resident record #{rid} restored to active list")
            return jsonify({"ok": True})

        d = request.get_json(silent=True) or {}
        dob = d.get("dob") or None
        last_name, first_name, middle_name = d.get("lastName", ""), d.get("firstName", ""), d.get("middleName", "")
        sex, civil_status = d.get("sex") or "Male", d.get("civilStatus") or "Single"
        nationality = d.get("nationality") or "Filipino"
        zone = d.get("zone")
        address, household, contact = d.get("address", ""), d.get("householdNo", ""), d.get("contactNo", "")
        voter = d.get("voterStatus") or "Not Registered"
        occupation, status = d.get("occupation", ""), d.get("status") or "Active"

        # Desk Officer can only change Status — every other field snaps back to
        # the existing DB value regardless of what the request body contains.
        if session.get("role") == "Desk Officer":
            last_name, first_name, middle_name = record.last_name, record.first_name, record.middle_name
            dob, sex, civil_status = record.date_of_birth, record.sex, record.civil_status
            nationality, zone, address = record.nationality, record.zone_id, record.address
            household, contact, voter = record.household_no, record.contact_no, record.voter_status
            occupation = record.occupation

        if status == "Deceased":
            voter = "Deactivated"

        dob = parse_date(dob)
        age = compute_age(dob)
        if age is not None and age < MIN_RESIDENT_REGISTRATION_AGE:
            return json_error(
                f"This resident is {age} year(s) old. Residents must be at least "
                f"{MIN_RESIDENT_REGISTRATION_AGE} years old to be registered in Census."
            )
        if _duplicate_resident(last_name, first_name, middle_name, address, household, sex, age, exclude_id=rid):
            return json_error(
                "Another resident with the same name, address, household number, age, and sex is already in Census.",
                409,
            )

        record.last_name, record.first_name, record.middle_name = last_name, first_name, middle_name
        record.date_of_birth, record.sex, record.civil_status = dob, sex, civil_status
        record.nationality, record.zone_id, record.address = nationality, zone, address
        record.household_no, record.contact_no, record.voter_status = household, contact, voter
        record.occupation, record.status = occupation, status
        db.session.commit()
        log_audit(session.get("username"), "Updated", "Census", f"Resident record #{rid} updated")
        return jsonify({"ok": True})

    if method == "DELETE":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        record = CensusRecord.query.get(rid)
        if not record:
            return json_error("Resident not found.", 404)
        record.archived = True
        db.session.commit()
        log_audit(session.get("username"), "Archived", "Census", f"Resident record #{rid} archived")
        return jsonify({"ok": True, "archived": True})


def _get_resident_or_404(resident_id, not_found_msg):
    if not resident_id:
        return None, json_error(not_found_msg[0])
    resident = CensusRecord.query.get(resident_id)
    if not resident:
        return None, json_error(not_found_msg[1], 404)
    return resident, None


def _resident_status_block(resident, cert_label, blocked_statuses):
    """None if `resident` is eligible for this certificate; otherwise the
    json_error() response explaining why not, based on their Census status."""
    if resident.status in blocked_statuses:
        return json_error(
            f"{full_name_of(resident)} is recorded as {resident.status} in Census. "
            f"A {cert_label} cannot be issued for a resident with this status."
        )
    return None


def check_resident_blotter_clearance(resident_id_or_resident):
    """
    Validates whether a resident is cleared to receive barangay certificates/clearances.
    If the resident is named as a Respondent in any open/unresolved blotter record
    (status NOT IN ('Resolved', 'Settled', 'Dismissed', 'Complied', 'Closed')),
    clearance is blocked (placed on hold).
    """
    if isinstance(resident_id_or_resident, int):
        resident = CensusRecord.query.get(resident_id_or_resident)
    else:
        resident = resident_id_or_resident

    if not resident:
        return {
            "is_cleared": False,
            "has_derogatory": False,
            "blocking_count": 0,
            "blocking_cases": [],
            "error": "Resident not found.",
        }

    resolved_statuses = {
        "Resolved", "Settled", "Dismissed", "Complied", "Closed", "CFA Issued",
        "RESOLVED", "SETTLED", "DISMISSED", "COMPLIED", "CLOSED"
    }

    # 1. Direct FK matches where resident is respondent
    unresolved = BlotterRecord.query.filter(
        BlotterRecord.respondent_id == resident.id,
        ~BlotterRecord.status.in_(resolved_statuses),
        (BlotterRecord.archived == False) | (BlotterRecord.archived.is_(None)),
    ).order_by(BlotterRecord.date_filed.desc()).all()

    # 2. Name-based match fallback
    if not unresolved:
        last, first = (resident.last_name or "").strip(), (resident.first_name or "").strip()
        if last and first:
            unresolved = BlotterRecord.query.filter(
                BlotterRecord.respondent_id.is_(None),
                BlotterRecord.respondent.ilike(f"%{last}%"),
                BlotterRecord.respondent.ilike(f"%{first}%"),
                ~BlotterRecord.status.in_(resolved_statuses),
                (BlotterRecord.archived == False) | (BlotterRecord.archived.is_(None)),
            ).order_by(BlotterRecord.date_filed.desc()).all()

    blocking_cases = []
    for b in unresolved:
        # Check linked settlement status
        stl = Settlement.query.filter_by(blotter_id=b.id, archived=False).first()
        stl_status = stl.status if stl else None
        if stl_status in ("Settled", "Complied", "Resolved"):
            continue

        blocking_cases.append({
            "blotter_id": b.id,
            "docket_no": b.docket_no,
            "date_filed": b.date_filed.isoformat() if b.date_filed else None,
            "complainant": b.complainant,
            "respondent": b.respondent,
            "nature": b.nature,
            "case_type": b.case_type,
            "status": b.status,
            "settlement_status": stl_status,
            "hold_reason": f"Active Blotter Case ({b.docket_no}) - {b.nature}",
        })

    is_cleared = len(blocking_cases) == 0
    first_docket = blocking_cases[0]["docket_no"] if blocking_cases else ""
    return {
        "is_cleared": is_cleared,
        "has_derogatory": not is_cleared,
        "blocking_count": len(blocking_cases),
        "blocking_cases": blocking_cases,
        "message": (
            "No derogatory record found. Clearance allowed."
            if is_cleared
            else f"Cannot issue Barangay Clearance: Resident has {len(blocking_cases)} active Blotter case(s) under mediation (Blotter #{first_docket})."
        ),
    }


def _has_unresolved_blotter_as_respondent(resident):
    res = check_resident_blotter_clearance(resident)
    return res["blocking_cases"] if not res["is_cleared"] else []


# ---------------- BARANGAY CLEARANCE ----------------
def _clearance():
    method = request.method
    if method == "GET":
        rows = BarangayClearance.query.order_by(BarangayClearance.date_issued.desc(), BarangayClearance.id.desc()).all()
        return jsonify([r.to_dict() for r in rows])

    if method == "POST":
        d = request.get_json(silent=True) or {}
        resident_id = int(d.get("residentId") or 0)
        resident, err = _get_resident_or_404(
            resident_id, ("A clearance must be issued to an existing census resident.", "That resident does not exist in Census.")
        )
        if err:
            return err
        err = _resident_status_block(resident, "Certificate of Clearance", {"Deceased", "Transferred"})
        if err:
            return err

        clearance_check = check_resident_blotter_clearance(resident)
        if not clearance_check["is_cleared"]:
            return jsonify({
                "error": clearance_check["message"],
                "message": clearance_check["message"],
                "on_hold": True,
                "blocking_cases": clearance_check["blocking_cases"],
                "ok": False,
            }), 403

        ctrl_no = d.get("ctrlNo") or next_ctrl_no(BarangayClearance, "BC")
        or_no = d.get("orNo") or next_or_no()
        record = BarangayClearance(
            resident_id=resident_id, ctrl_no=ctrl_no, full_name=full_name_of(resident),
            age=compute_age(resident.date_of_birth), civil_status=resident.civil_status,
            address=resident.address, voter_status=resident.voter_status, purpose=d.get("purpose", ""),
            or_no=or_no, fee=d.get("fee") or 20.00,
            date_issued=parse_date(d.get("dateIssued")) or datetime.utcnow().date(),
            issued_by=session.get("full_name", "System"),
        )
        db.session.add(record)
        db.session.commit()
        log_audit(session.get("username"), "Created", "Clearance", f"Clearance issued: {ctrl_no} for {record.full_name}")
        return jsonify({"ok": True, "id": record.id, "ctrlNo": ctrl_no, "orNo": or_no}), 201

    if method == "DELETE":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        record = BarangayClearance.query.get(rid)
        if record:
            db.session.delete(record)
            db.session.commit()
        log_audit(session.get("username"), "Deleted", "Clearance", f"Clearance record #{rid} deleted")
        return jsonify({"ok": True})

    return json_error("Unknown type or method", 404)


# ---------------- CERTIFICATE OF RESIDENCY ----------------
def _residency():
    method = request.method
    if method == "GET":
        rows = BarangayResidency.query.order_by(BarangayResidency.date_issued.desc(), BarangayResidency.id.desc()).all()
        return jsonify([r.to_dict() for r in rows])

    if method == "POST":
        d = request.get_json(silent=True) or {}
        resident_id = int(d.get("residentId") or 0)
        resident, err = _get_resident_or_404(
            resident_id,
            ("A certificate of residency must be issued to an existing census resident.", "That resident does not exist in Census."),
        )
        if err:
            return err
        err = _resident_status_block(resident, "Certificate of Residency", {"Transferred"})
        if err:
            return err
        if _has_unresolved_blotter_as_respondent(resident):
            return json_error(
                "Issuance blocked: Resident has active pending or ongoing blotter records as a respondent.",
                403,
            )

        years_residency = int(d["yearsResidency"]) if d.get("yearsResidency") not in (None, "") else None
        duration_unit = "months" if d.get("durationUnit") == "months" else "years"
        if duration_unit == "months" and years_residency is not None and not (2 <= years_residency <= 11):
            return json_error("Months of residency must be between 2 and 11 (11 months and up should be issued in years).")

        ctrl_no = d.get("ctrlNo") or next_ctrl_no(BarangayResidency, "BR")
        or_no = d.get("orNo") or next_or_no()
        record = BarangayResidency(
            resident_id=resident_id, ctrl_no=ctrl_no, full_name=full_name_of(resident),
            age=compute_age(resident.date_of_birth), civil_status=resident.civil_status,
            address=resident.address, years_residency=years_residency, duration_unit=duration_unit,
            purpose=d.get("purpose", ""), or_no=or_no, fee=d.get("fee") or 20.00,
            date_issued=parse_date(d.get("dateIssued")) or datetime.utcnow().date(),
            issued_by=session.get("full_name", "System"),
        )
        db.session.add(record)
        db.session.commit()
        log_audit(session.get("username"), "Created", "Residency", f"Certificate of Residency issued: {ctrl_no} for {record.full_name}")
        return jsonify({"ok": True, "id": record.id, "ctrlNo": ctrl_no, "orNo": or_no}), 201

    if method == "DELETE":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        record = BarangayResidency.query.get(rid)
        if record:
            db.session.delete(record)
            db.session.commit()
        log_audit(session.get("username"), "Deleted", "Residency", f"Certificate of Residency record #{rid} deleted")
        return jsonify({"ok": True})

    return json_error("Unknown type or method", 404)


# ---------------- CERTIFICATE OF NON-RESIDENCY ----------------
def _non_residency():
    method = request.method
    if method == "GET":
        rows = BarangayNonResidency.query.order_by(BarangayNonResidency.date_issued.desc(), BarangayNonResidency.id.desc()).all()
        return jsonify([r.to_dict() for r in rows])

    if method == "POST":
        d = request.get_json(silent=True) or {}
        resident_id = int(d.get("residentId") or 0)
        resident, err = _get_resident_or_404(
            resident_id,
            ("A certificate of non-residency must reference an existing Census record.", "That person does not exist in Census."),
        )
        if err:
            return err
        pending_cases = _has_unresolved_blotter_as_respondent(resident)
        if pending_cases:
            return jsonify({
                "ok": False,
                "success": False,
                "blocked": True,
                "error": "CERTIFICATE_ISSUANCE_BLOCKED",
                "message": "Cannot issue Certificate of Non-Residency. Resident has active/unsettled blotter cases.",
                "pendingCases": [{"docketNo": c.docket_no, "status": c.status, "nature": c.nature} for c in pending_cases]
            }), 422

        ctrl_no = d.get("ctrlNo") or next_ctrl_no(BarangayNonResidency, "NR")
        or_no = d.get("orNo") or next_or_no()
        record = BarangayNonResidency(
            resident_id=resident_id, ctrl_no=ctrl_no, full_name=full_name_of(resident),
            previous_address=d.get("previousAddress", ""), purpose=d.get("purpose", ""), or_no=or_no,
            fee=d.get("fee") or 20.00, date_issued=parse_date(d.get("dateIssued")) or datetime.utcnow().date(),
            issued_by=session.get("full_name", "System"),
        )
        db.session.add(record)
        db.session.commit()
        log_audit(session.get("username"), "Created", "NonResidency", f"Certificate of Non-Residency issued: {ctrl_no} for {record.full_name}")
        return jsonify({"ok": True, "id": record.id, "ctrlNo": ctrl_no, "orNo": or_no}), 201

    if method == "DELETE":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        record = BarangayNonResidency.query.get(rid)
        if record:
            db.session.delete(record)
            db.session.commit()
        log_audit(session.get("username"), "Deleted", "NonResidency", f"Certificate of Non-Residency record #{rid} deleted")
        return jsonify({"ok": True})

    return json_error("Unknown type or method", 404)


# ---------------- INDIGENCY ----------------
def _indigency():
    method = request.method
    if method == "GET":
        rows = IndigencyCertificate.query.order_by(IndigencyCertificate.date_issued.desc(), IndigencyCertificate.id.desc()).all()
        return jsonify([r.to_dict() for r in rows])

    if method == "POST":
        d = request.get_json(silent=True) or {}
        resident_id = int(d.get("residentId") or 0)
        resident, err = _get_resident_or_404(
            resident_id, ("A certificate must be issued to an existing census resident.", "That resident does not exist in Census.")
        )
        if err:
            return err
        err = _resident_status_block(resident, "Certificate of Indigency", {"Transferred"})
        if err:
            return err
        clearance_check = check_resident_blotter_clearance(resident)
        if not clearance_check["is_cleared"]:
            return jsonify({
                "error": clearance_check["message"],
                "message": clearance_check["message"],
                "on_hold": True,
                "blocking_cases": clearance_check["blocking_cases"],
                "ok": False,
            }), 403

        ctrl_no = d.get("ctrlNo") or next_ctrl_no(IndigencyCertificate, "CI")
        record = IndigencyCertificate(
            resident_id=resident_id, ctrl_no=ctrl_no, full_name=full_name_of(resident),
            age=compute_age(resident.date_of_birth), civil_status=resident.civil_status,
            address=resident.address, purpose=d.get("purpose", ""),
            date_issued=parse_date(d.get("dateIssued")) or datetime.utcnow().date(),
            issued_by=session.get("full_name", "System"),
        )
        db.session.add(record)
        db.session.commit()
        log_audit(session.get("username"), "Created", "Indigency", f"Certificate issued: {ctrl_no} for {record.full_name}")
        return jsonify({"ok": True, "id": record.id, "ctrlNo": ctrl_no}), 201

    if method == "DELETE":
        rid = int(request.args.get("id", 0))
        if not rid:
            return json_error("id required")
        record = IndigencyCertificate.query.get(rid)
        if record:
            db.session.delete(record)
            db.session.commit()
        log_audit(session.get("username"), "Deleted", "Indigency", f"Certificate record #{rid} deleted")
        return jsonify({"ok": True})

    return json_error("Unknown type or method", 404)
