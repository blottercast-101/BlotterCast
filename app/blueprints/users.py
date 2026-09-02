import os
import secrets
import time
import uuid
from datetime import datetime

import bcrypt
from flask import Blueprint, current_app, jsonify, request, session
from sqlalchemy import func
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import AuditLog, NotificationRead, OtpCode, PasswordHistory, User
from ..permissions import get_security_settings, json_error, log_audit, login_required

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
        if (action == "delete" and method in ("DELETE", "POST")) or (method == "DELETE" and action in ("", "delete")):
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


PROTECTED_ROLES = {"System Admin", "Barangay Captain"}


def _captain_signature():
    from ..models import SystemSetting
    setting_row = (
        SystemSetting.query.get("barangay_captain")
        or SystemSetting.query.get("punong_barangay")
        or SystemSetting.query.get("captain_name")
    )
    capt_name = setting_row.setting_value if (setting_row and setting_row.setting_value) else None
    row = User.query.filter_by(role="Barangay Captain").filter(User.status != "Suspended").order_by(User.id).first()
    if not capt_name and row and row.full_name:
        capt_name = row.full_name

    sig_path = None
    if row and row.signature_path:
        rel = row.signature_path.lstrip("/")
        full_p = os.path.join(current_app.static_folder, rel)
        if os.path.isfile(full_p):
            sig_path = f"/{rel}"

    if not sig_path:
        sig_path = "/assets/signatures/default-kapitan-signature.png"

    return jsonify({
        "fullName": capt_name or "Kapitan Jose Reyes",
        "signatory_captain": capt_name or "Kapitan Jose Reyes",
        "barangay_captain": capt_name or "Kapitan Jose Reyes",
        "captain_name": capt_name or "Kapitan Jose Reyes",
        "punong_barangay": capt_name or "Kapitan Jose Reyes",
        "signaturePath": sig_path,
    })


def _get_computed_status(u: User) -> str:
    if u.status == "Suspended":
        return "Suspended"
    if u.last_seen:
        elapsed = (datetime.utcnow() - u.last_seen).total_seconds()
        if elapsed <= 45:
            return "Active"
    return "Inactive"


def _list():
    rows = User.query.order_by(User.full_name).all()
    return jsonify([{
        "id": u.id, "username": u.username, "full_name": u.full_name, "email": u.email,
        "contact_no": u.contact_no, "role": u.role,
        "status": _get_computed_status(u),
        "is_online": _get_computed_status(u) == "Active",
        "is_protected": u.role in PROTECTED_ROLES,
        "signature_path": u.signature_path,
        # Naive datetimes from utcnow() have no offset — appending "Z" makes
        # the value unambiguous UTC so the browser doesn't guess it's local
        # time (which silently shifts it by the browser's own UTC offset).
        "last_login": (u.last_login.isoformat() + "Z") if u.last_login else None,
        "last_seen": (u.last_seen.isoformat() + "Z") if u.last_seen else None,
        "created_at": (u.created_at.isoformat() + "Z") if u.created_at else None,
    } for u in rows])


def _generate_temp_password(role: str) -> str:
    role_lower = (role or "").lower()
    if "desk" in role_lower:
        prefix = "DSK"
    elif "data" in role_lower or "encoder" in role_lower:
        prefix = "DTA"
    elif "admin" in role_lower:
        prefix = "ADM"
    elif "captain" in role_lower:
        prefix = "CPT"
    else:
        prefix = "USR"
    # Generate 6 random uppercase characters and digits (excluding confusing 0/O/1/I)
    suffix = "".join(secrets.choice("23456789ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(6))
    return f"{prefix}-{suffix}"


def _create():
    d = request.get_json(silent=True) or {}
    username = (d.get("username") or "").strip()
    full_name = (d.get("name") or d.get("full_name") or d.get("fullName") or "").strip()
    role = (d.get("role") or "Desk Officer").strip()
    password = (d.get("password") or "").strip()
    if not password:
        password = _generate_temp_password(role)
    email = (d.get("email") or "").strip()
    contact = (d.get("contact") or d.get("contact_no") or d.get("contactNo") or "").strip() or None
    if not username or not full_name:
        return json_error("Name and username are required")
    if not email:
        return json_error("Email is required — sign-in codes are sent there for MFA.")

    # Guard: Only Desk Officer and Data Encoder roles may be created via user management
    normalized_role = role.upper()
    if normalized_role in {"SYSTEM ADMIN", "BARANGAY CAPTAIN"} or role not in {"Desk Officer", "Data Encoder"}:
        return json_error("Creating accounts with 'System Admin' or 'Barangay Captain' roles is forbidden. Only Desk Officer and Data Encoder accounts can be created.", 403)

    min_len = get_security_settings()["min_password_length"]
    if len(password) < min_len:
        return json_error(f"Password must be at least {min_len} characters long")

    if User.query.filter_by(username=username).first():
        return json_error("That username is already taken", 409)
    if User.query.filter(func.lower(User.email) == email.lower()).first():
        return json_error("That email address is already in use by another account", 409)

    user = User(
        username=username, password=_hash_password(password), full_name=full_name,
        email=email, contact_no=contact, role=role,
        status="Inactive", password_changed_at=datetime.utcnow(),
    )
    db.session.add(user)
    db.session.commit()
    log_audit(session.get("username"), "Created", "Users", f"New account created: {username} ({user.role})")
    return jsonify({"ok": True, "id": user.id, "temp_password": password}), 201


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

    # Note: Status is purely system-managed (presence or suspension actions).
    # Any manual status in the payload is ignored.

    # Note: Admin cannot directly overwrite or change another user's password.
    # Users independently change their own password via Settings -> Security.

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
    if user.role in PROTECTED_ROLES:
        return json_error(f"{user.role} accounts are protected and cannot be suspended.", 400)
    
    if user.status == "Suspended":
        user.status = "Inactive"
        action_note = "Unsuspended"
    else:
        user.status = "Suspended"
        user.last_seen = None
        action_note = "Suspended"

    db.session.commit()
    computed = _get_computed_status(user)
    log_audit(session.get("username"), "Updated", "Users", f"{user.username} {action_note.lower()}")
    return jsonify({"ok": True, "status": computed})


def _delete():
    try:
        uid = _get_target_user_id()
        if not uid:
            return json_error("id required", 400)
        if session.get("user_id") == uid:
            return json_error("You cannot delete your own account while logged in", 400)
        user = db.session.get(User, uid)
        if not user:
            return json_error("User not found", 404)
        if user.role in PROTECTED_ROLES:
            return json_error(f"{user.role} accounts are protected and cannot be deleted.", 400)
        
        username = user.username

        # 1. Clean up user's signature file if one exists
        if user.signature_path:
            try:
                sig_file = os.path.join(current_app.static_folder, user.signature_path)
                if os.path.isfile(sig_file):
                    os.remove(sig_file)
            except Exception as e:
                current_app.logger.warning(f"Failed to remove signature file on user delete: {e}")

        # 2. Safely remove child foreign key dependencies within the transaction
        OtpCode.query.filter_by(user_id=uid).delete()
        NotificationRead.query.filter_by(user_id=uid).delete()
        PasswordHistory.query.filter_by(user_id=uid).delete()

        # 3. Hard-delete user record safely
        db.session.delete(user)
        db.session.commit()

        # 4. Safely log audit event
        try:
            log_audit(session.get("username"), "Deleted", "Users", f"Account removed: {username}")
        except Exception as e:
            current_app.logger.warning(f"Audit log failed on user delete: {e}")

        return jsonify({"ok": True, "success": True, "message": f"User '{username}' deleted successfully."})
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Failed to delete user: {e}")
        return json_error(f"Failed to delete user: {str(e)}", 500)


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
    filename = secure_filename(f"captain_signature_{uid}.{ext}")
    dest_path = os.path.join(sig_dir, filename)
    file.save(dest_path)

    relative_path = f"/assets/signatures/{filename}"
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
