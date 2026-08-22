import os
import time
import uuid
from datetime import datetime

import bcrypt
from flask import Blueprint, current_app, jsonify, request, session
from sqlalchemy import func
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import AuditLog, User
from ..permissions import get_security_settings, json_error, log_audit, login_required, permission_required

bp = Blueprint("users", __name__)


def _hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@bp.route("/api/users.php", methods=["GET", "POST", "PUT", "DELETE"])
@login_required
def users_router():
    try:
        action = request.args.get("action", "")
        method = request.method

        # Readable by any signed-in user (certificates need the captain's name/signature
        # regardless of role) — everything else below requires manage_users.
        if action == "captain_signature" and method == "GET":
            return _captain_signature()

        from ..permissions import role_can
        if not role_can(session.get("role", ""), "manage_users"):
            return json_error("You do not have permission to perform this action.", 403)

        if action == "list" and method == "GET":
            return _list()
        if action == "create" and method == "POST":
            return _create()
        if action == "update" and method == "PUT":
            return _update()
        if action == "toggle_status" and method == "POST":
            return _toggle_status()
        if action == "delete" and method == "DELETE":
            return _delete()
        if action == "upload_signature" and method == "POST":
            return _upload_signature()
        if action == "remove_signature" and method == "POST":
            return _remove_signature()
        if action == "audit" and method == "GET":
            return _audit()

        return json_error("Unknown action or method", 404)
    except Exception as e:
        current_app.logger.exception(f"Error in users_router '{request.args.get('action')}': {e}")
        return json_error("Internal server error", 500)


def _get_target_user_id():
    raw_id = request.args.get("id")
    if not raw_id:
        return None
    try:
        uid = int(raw_id)
        return uid if uid > 0 else None
    except (ValueError, TypeError):
        return None


def _captain_signature():
    row = User.query.filter_by(role="Barangay Captain", status="Active").order_by(User.id).first()
    return jsonify({
        "fullName": row.full_name if row else None,
        "signaturePath": row.signature_path if row else None,
    })


def _list():
    rows = User.query.order_by(User.full_name).all()
    return jsonify([{
        "id": u.id, "username": u.username, "full_name": u.full_name, "email": u.email,
        "contact_no": u.contact_no, "role": u.role, "status": u.status,
        "signature_path": u.signature_path,
        # Naive datetimes from utcnow() have no offset — appending "Z" makes
        # the value unambiguous UTC so the browser doesn't guess it's local
        # time (which silently shifts it by the browser's own UTC offset).
        "last_login": (u.last_login.isoformat() + "Z") if u.last_login else None,
        "created_at": (u.created_at.isoformat() + "Z") if u.created_at else None,
    } for u in rows])


def _create():
    d = request.get_json(silent=True) or {}
    username = (d.get("username") or "").strip()
    full_name = (d.get("name") or d.get("full_name") or d.get("fullName") or "").strip()
    password = d.get("password") or ""
    email = (d.get("email") or "").strip()
    contact = (d.get("contact") or d.get("contact_no") or d.get("contactNo") or "").strip() or None
    if not username or not full_name or not password:
        return json_error("Name, username, and password are required")
    if not email:
        return json_error("Email is required — sign-in codes are sent there for MFA.")

    min_len = get_security_settings()["min_password_length"]
    if len(password) < min_len:
        return json_error(f"Password must be at least {min_len} characters long")

    if User.query.filter_by(username=username).first():
        return json_error("That username is already taken", 409)
    if User.query.filter(func.lower(User.email) == email.lower()).first():
        return json_error("That email address is already in use by another account", 409)

    user = User(
        username=username, password=_hash_password(password), full_name=full_name,
        email=email, contact_no=contact, role=d.get("role") or "Desk Officer",
        # New accounts always start Active — the system's default initial
        # status. Status only becomes choosable later, via Edit; whatever
        # the request body sends here is ignored so an Add User form can
        # never smuggle a different starting status through the API.
        status="Active", password_changed_at=datetime.utcnow(),
    )
    db.session.add(user)
    db.session.commit()
    log_audit(session.get("username"), "Created", "Users", f"New account created: {username} ({user.role})")
    return jsonify({"ok": True, "id": user.id}), 201


def _update():
    uid = _get_target_user_id()
    if not uid:
        return json_error("id required")
    user = db.session.get(User, uid)
    if not user:
        return json_error("User not found", 404)

    d = request.get_json(silent=True) or {}
    full_name = (d.get("name") or d.get("full_name") or d.get("fullName") or "").strip()
    email = (d.get("email") or "").strip()
    if not full_name:
        return json_error("Name is required")
    if not email:
        return json_error("Email is required — sign-in codes are sent there for MFA.")
    if User.query.filter(User.id != uid, func.lower(User.email) == email.lower()).first():
        return json_error("That email address is already in use by another account", 409)

    user.full_name = full_name
    user.email = email
    user.contact_no = (d.get("contact") or d.get("contact_no") or d.get("contactNo") or "").strip() or None
    user.role = d.get("role") or user.role
    user.status = d.get("status") or user.status

    if d.get("password"):
        min_len = get_security_settings()["min_password_length"]
        if len(d["password"]) < min_len:
            return json_error(f"Password must be at least {min_len} characters long")
        user.password = _hash_password(d["password"])
        user.password_changed_at = datetime.utcnow()
        user.failed_attempts = 0
        user.locked_until = None

    db.session.commit()
    log_audit(session.get("username"), "Updated", "Users", f"Account updated: {full_name}")
    return jsonify({"ok": True})


def _toggle_status():
    uid = _get_target_user_id()
    if not uid:
        return json_error("id required")
    user = db.session.get(User, uid)
    if not user:
        return json_error("User not found", 404)
    user.status = "Suspended" if user.status == "Active" else "Active"
    db.session.commit()
    log_audit(session.get("username"), "Updated", "Users", f"{user.username} set to {user.status}")
    return jsonify({"ok": True, "status": user.status})


def _delete():
    uid = _get_target_user_id()
    if not uid:
        return json_error("id required")
    if session.get("user_id") == uid:
        return json_error("You cannot delete your own account while logged in")
    user = db.session.get(User, uid)
    if user:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        log_audit(session.get("username"), "Deleted", "Users", f"Account removed: {username}")
    return jsonify({"ok": True})


def _upload_signature():
    uid = _get_target_user_id()
    if not uid:
        return json_error("id required")
    user = db.session.get(User, uid)
    if not user:
        return json_error("User not found", 404)

    file = request.files.get("signature")
    if not file or not file.filename:
        return json_error("No signature file uploaded, or upload failed")
    if file.mimetype not in ("image/png", "image/jpeg"):
        return json_error("Signature must be a PNG or JPEG image")

    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > 2 * 1024 * 1024:
        return json_error("Signature image must be smaller than 2MB")

    sig_dir = os.path.join(current_app.static_folder, "assets", "signatures")
    os.makedirs(sig_dir, exist_ok=True)

    ext = "png" if file.mimetype == "image/png" else "jpeg"
    filename = secure_filename(f"sig-{uid}-{int(time.time())}.{ext}")
    dest_path = os.path.join(sig_dir, filename)
    file.save(dest_path)

    if user.signature_path:
        old_file = os.path.join(current_app.static_folder, user.signature_path)
        if os.path.isfile(old_file):
            os.remove(old_file)

    relative_path = f"assets/signatures/{filename}"
    user.signature_path = relative_path
    db.session.commit()
    log_audit(session.get("username"), "Updated", "Users", f"Signature uploaded for {user.username}")
    return jsonify({"ok": True, "signaturePath": relative_path})


def _remove_signature():
    uid = _get_target_user_id()
    if not uid:
        return json_error("id required")
    user = db.session.get(User, uid)
    if not user:
        return json_error("User not found", 404)

    if user.signature_path:
        file_path = os.path.join(current_app.static_folder, user.signature_path)
        if os.path.isfile(file_path):
            os.remove(file_path)

    user.signature_path = None
    db.session.commit()
    log_audit(session.get("username"), "Updated", "Users", f"Signature removed for {user.username}")
    return jsonify({"ok": True})


def _audit():
    try:
        limit = min(100, max(1, int(request.args.get("limit", 10))))
    except (ValueError, TypeError):
        limit = 10
    rows = AuditLog.query.order_by(AuditLog.id.desc()).limit(limit).all()
    return jsonify([{
        "username": r.username, "action": r.action, "module": r.module,
        # Naive UTC — "Z" so Login events (and everything else here) show
        # the actual Philippines time they happened, not shifted by
        # whatever timezone the viewer's own browser happens to be in.
        "details": r.details, "created_at": (r.created_at.isoformat() + "Z") if r.created_at else None,
    } for r in rows])
