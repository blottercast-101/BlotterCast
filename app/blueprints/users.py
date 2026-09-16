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


@bp.route("/api/users.php", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
@bp.route("/api/users", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
@login_required
def users_router():
    if request.method == "OPTIONS":
        return "", 204
    try:
        action = (
            request.args.get("action")
            or request.form.get("action")
            or (request.get_json(silent=True) or {}).get("action")
            or ""
        ).strip().lower()
        method = request.method
        if action in ("health", "ping"):
            return jsonify({"ok": True, "status": "healthy"})

        # Avatar actions accessible to any signed-in user
        if (action in ("upload_avatar", "upload_profile_photo", "avatar", "profile_photo") or bool(request.files.get("avatar") or request.files.get("photo") or request.files.get("profile_photo") or request.files.get("image") or request.files.get("file"))) and method in ("POST", "PUT"):
            return _upload_avatar_user()
        if action in ("remove_avatar", "remove_profile_photo", "delete_avatar", "delete_photo", "delete", "remove") and method in ("POST", "DELETE", "PUT") and (request.args.get("type") == "avatar" or action != "delete"):
            return _remove_avatar_user()

        # Readable by any signed-in user (certificates need the captain's name/signature
        # regardless of role; presence checks needed for real-time status sync)
        if action == "captain_signature" and method == "GET":
            return _captain_signature()
        if action == "presence" and method == "GET":
            return _presence()

        from ..permissions import role_can
        if not role_can(session.get("role", ""), "manage_users"):
            return json_error("You do not have permission to perform this action.", 403)

        if action in ("list", "") and method == "GET":
            return _list()
        if action in ("create", "") and method == "POST":
            return _create()
        if action in ("update", "") and method == "PUT":
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
    row = User.query.filter_by(role="Barangay Captain").filter(User.status != "Suspended").order_by(User.id).first()
    setting_row = (
        SystemSetting.query.get("barangay_captain")
        or SystemSetting.query.get("punong_barangay")
        or SystemSetting.query.get("captain_name")
    )
    setting_val = setting_row.setting_value if (setting_row and setting_row.setting_value) else None

    # If setting is explicitly customized beyond default "Kapitan Jose Reyes", respect it;
    # otherwise prioritize the updated Barangay Captain user record.
    if setting_val and setting_val != "Kapitan Jose Reyes":
        capt_name = setting_val
    elif row and row.full_name and row.full_name != "Barangay Captain":
        capt_name = row.full_name
    elif setting_val:
        capt_name = setting_val
    elif row and row.full_name:
        capt_name = row.full_name
    else:
        capt_name = "Barangay Captain"

    sig_path = None
    if row and row.signature_path:
        rel = row.signature_path.lstrip("/")
        full_p = os.path.join(current_app.static_folder, rel)
        if os.path.isfile(full_p):
            sig_path = f"/{rel}"

    if not sig_path:
        sig_path = "/assets/signatures/default-kapitan-signature.png"

    return jsonify({
        "fullName": capt_name,
        "signatory_captain": capt_name,
        "barangay_captain": capt_name,
        "captain_name": capt_name,
        "punong_barangay": capt_name,
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
    users = User.query.order_by(User.id.asc()).all()
    out = []
    for u in users:
        sig_url = None
        if u.signature_path:
            rel = u.signature_path.lstrip("/")
            full_p = os.path.join(current_app.static_folder, rel)
            if os.path.isfile(full_p):
                sig_url = f"/{rel}"

        is_prot = u.role in PROTECTED_ROLES
        computed_status = _get_computed_status(u)
        if is_prot and computed_status == "Suspended":
            computed_status = "Inactive"

        out.append({
            "id": u.id,
            "username": u.username,
            "name": u.full_name,
            "fullName": u.full_name,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "status": computed_status,
            "is_online": computed_status == "Active",
            "last_login": u.last_login.strftime("%Y-%m-%d %H:%M:%S") if u.last_login else None,
            "contact": u.contact_no,
            "contact_no": u.contact_no,
            "avatar": u.avatar_url or None,
            "avatar_url": u.avatar_url or None,
            "avatarUrl": u.avatar_url or None,
            "profile_photo_path": u.avatar_url or None,
            "signaturePath": sig_url,
            "is_protected": is_prot,
        })
    return jsonify(out)


def _presence():
    rows = User.query.with_entities(User.id, User.status, User.last_seen, User.last_login).all()
    now = datetime.utcnow()
    res = {}
    for uid, status, last_seen, last_login in rows:
        computed_status = "Suspended" if status == "Suspended" else ("Active" if last_seen and (now - last_seen).total_seconds() <= 45 else "Inactive")
        res[str(uid)] = {
            "id": uid,
            "status": computed_status,
            "is_online": computed_status == "Active",
            "last_seen": (last_seen.isoformat() + "Z") if last_seen else None,
            "last_login": (last_login.isoformat() + "Z") if last_login else None,
        }
    return jsonify(res)


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
    from ..permissions import role_can
    if not role_can(session.get("role", ""), "manage_users"):
        return json_error("You do not have permission to perform this action.", 403)

    d = request.get_json(silent=True) or {}
    username = (d.get("username") or "").strip()
    full_name = (d.get("name") or d.get("full_name") or d.get("fullName") or "").strip()
    email = (d.get("email") or "").strip()
    role = (d.get("role") or "").strip()
    password = d.get("password") or ""
    contact = (d.get("contact") or d.get("contact_no") or d.get("contactNo") or "").strip() or None
    if not username or not full_name:
        return json_error("Name and username are required")
    if not email:
        return json_error("Email is required — sign-in codes are sent there for MFA.")

    # Guard: Only Desk Officer and Data Encoder roles may be created via user management
    normalized_role = role.upper()
    if normalized_role in {"SYSTEM ADMIN", "BARANGAY CAPTAIN", "SYSTEM ADMINISTRATOR"}:
        return json_error("Creating accounts with 'System Admin' or 'Barangay Captain' roles is forbidden. Only Desk Officer and Data Encoder accounts can be created.", 403)
    if role not in {"Desk Officer", "Data Encoder"}:
        return json_error("Invalid role. Only Desk Officer and Data Encoder accounts can be created.", 400)

    if not password:
        password = _generate_temp_password(role)
    min_len = get_security_settings()["min_password_length"]
    if len(password) < min_len:
        return json_error(f"Password must be at least {min_len} characters long")

    if User.query.filter_by(username=username).first():
        return json_error("That username is already taken", 409)
    if User.query.filter(func.lower(User.email) == email.lower()).first():
        return json_error("That email address is already in use by another account", 409)

    user = User(
        username=username, password=_hash_password(password), full_name=full_name,
        email=email, role=role, status="Inactive", password_changed_at=datetime.utcnow(),
        contact_no=contact,
    )
    db.session.add(user)
    db.session.commit()
    log_audit(session.get("username"), "Created", "Users", f"Account created: {full_name} ({role})")

    # Automated Credential Email Delivery with Mandatory First-Login Password Change Reminder
    try:
        from ..email import send_credential_email
        send_credential_email(
            to_email=email,
            username=username,
            temp_password=password,
            full_name=full_name,
            role=role,
        )
    except Exception as e:
        current_app.logger.warning(f"Failed to dispatch credential email to {email}: {e}")

    return jsonify({"ok": True, "id": user.id, "temp_password": password}), 201


def _update():
    from ..models import SystemSetting
    uid = _get_target_user_id()
    if not uid:
        return json_error("id required")
    user = db.session.get(User, uid)
    if not user:
        return json_error("User not found", 404)

    d = request.get_json(silent=True) or {}
    full_name = (d.get("name") or d.get("full_name") or d.get("fullName") or "").strip()
    username = (d.get("username") or "").strip()
    email = (d.get("email") or "").strip()
    if not full_name:
        return json_error("Name is required")
    if not email:
        return json_error("Email is required — sign-in codes are sent there for MFA.")
    if User.query.filter(User.id != uid, func.lower(User.email) == email.lower()).first():
        return json_error("That email address is already in use by another account", 409)

    if username and username != user.username:
        if User.query.filter(User.id != uid, User.username == username).first():
            return json_error("That username is already taken", 409)
        user.username = username

    user.full_name = full_name
    user.email = email
    user.contact_no = (d.get("contact") or d.get("contact_no") or d.get("contactNo") or "").strip() or None

    # Only update password if explicitly provided and not empty
    password = (d.get("password") or "").strip()
    if password:
        from .auth import PASSWORD_POLICY_ERROR, is_password_valid
        if not is_password_valid(password):
            return json_error(PASSWORD_POLICY_ERROR, 422)
        min_len = get_security_settings()["min_password_length"]
        if len(password) < min_len:
            return json_error(f"Password must be at least {min_len} characters long", 400)
        user.password = _hash_password(password)
        user.password_changed_at = datetime.utcnow()

    # Role cannot demote protected roles
    req_role = d.get("role")
    if req_role and user.role not in PROTECTED_ROLES:
        user.role = req_role

    # Avatar update support (URL, null, or Data URL base64)
    avatar_payload = d.get("avatar") or d.get("avatar_url") or d.get("profile_photo") or d.get("profile_photo_path")
    if avatar_payload is not None:
        if isinstance(avatar_payload, str) and avatar_payload.startswith("data:image/"):
            user.avatar_url = avatar_payload
            user.profile_photo_path = avatar_payload
        elif isinstance(avatar_payload, str) and avatar_payload.strip():
            user.avatar_url = avatar_payload.strip()
            user.profile_photo_path = avatar_payload.strip()
        elif avatar_payload is None or avatar_payload == "":
            user.avatar_url = None
            user.profile_photo_path = None

    # If updating Barangay Captain, synchronize official settings keys
    if user.role == "Barangay Captain":
        for skey in ["barangay_captain", "captain_name", "punong_barangay"]:
            s_row = SystemSetting.query.get(skey)
            if s_row:
                s_row.setting_value = full_name
            else:
                db.session.add(SystemSetting(setting_key=skey, setting_value=full_name))

    # Real-time session synchronization for current user
    if session.get("user_id") == user.id:
        session["full_name"] = user.full_name
        session["username"] = user.username
        session["role"] = user.role

    db.session.commit()
    log_audit(session.get("username"), "Updated", "Users", f"Account updated: {full_name}")

    avatar_val = user.avatar_url or None
    return jsonify({
        "ok": True,
        "avatar_url": avatar_val,
        "avatarUrl": avatar_val,
        "avatar": avatar_val,
        "profile_photo_path": avatar_val,
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.full_name,
            "full_name": user.full_name,
            "fullName": user.full_name,
            "email": user.email,
            "contact": user.contact_no,
            "contact_no": user.contact_no,
            "role": user.role,
            "avatar": avatar_val,
            "avatar_url": avatar_val,
            "avatarUrl": avatar_val,
            "profile_photo_path": avatar_val,
            "is_protected": user.role in PROTECTED_ROLES,
        }
    })


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

        # 1. Clean up user's signature & avatar files if they exist
        if user.signature_path:
            try:
                sig_file = os.path.join(current_app.static_folder, user.signature_path.lstrip("/"))
                if os.path.isfile(sig_file):
                    os.remove(sig_file)
            except Exception as e:
                current_app.logger.warning(f"Failed to remove signature file on user delete: {e}")

        if user.avatar_url and user.avatar_url.startswith("/assets/avatars/"):
            try:
                av_file = os.path.join(current_app.static_folder, user.avatar_url.lstrip("/"))
                if os.path.isfile(av_file):
                    os.remove(av_file)
            except Exception as e:
                current_app.logger.warning(f"Failed to remove avatar file on user delete: {e}")

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


def _upload_avatar_user():
    uid = _get_target_user_id() or session.get("user_id")
    if not uid:
        return json_error("id required", 400)
    user = db.session.get(User, uid)
    if not user:
        return json_error("User not found", 404)

    # 1. Check Base64 payload in JSON or form body
    data = request.get_json(silent=True) or {}
    avatar_payload = (
        data.get("avatar")
        or data.get("avatar_data")
        or data.get("photo")
        or data.get("image")
        or data.get("profile_photo")
        or data.get("avatar_url")
        or data.get("profile_photo_path")
        or request.form.get("avatar")
        or request.form.get("avatar_data")
        or request.form.get("photo")
    )
    if avatar_payload and isinstance(avatar_payload, str) and avatar_payload.startswith("data:image/"):
        user.avatar_url = avatar_payload
        user.profile_photo_path = avatar_payload
        db.session.commit()
        log_audit(session.get("username"), "Updated", "Users", f"Profile photo uploaded for {user.username}")

        return jsonify({
            "ok": True,
            "success": True,
            "avatar_url": avatar_payload,
            "avatarUrl": avatar_payload,
            "avatar": avatar_payload,
            "profile_photo_path": avatar_payload,
            "user": {
                "id": user.id,
                "username": user.username,
                "fullName": user.full_name,
                "full_name": user.full_name,
                "email": user.email,
                "contact": user.contact_no,
                "role": user.role,
                "avatar": avatar_payload,
                "avatar_url": avatar_payload,
                "avatarUrl": avatar_payload,
                "profile_photo_path": avatar_payload,
            }
        }), 200

    # 2. Check multipart file upload
    file = (
        request.files.get("avatar")
        or request.files.get("photo")
        or request.files.get("signature")
        or request.files.get("profile_photo")
        or request.files.get("image")
        or request.files.get("file")
    )
    if not file or not file.filename:
        return json_error("No photo file uploaded, or upload failed", 400)

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    mimetype = (file.mimetype or "").lower()
    allowed_exts = ("png", "jpg", "jpeg", "webp", "gif", "bmp", "jfif")
    is_image_mime = mimetype.startswith("image/")
    is_image_ext = ext in allowed_exts

    if not is_image_mime and not is_image_ext:
        return json_error("Profile photo must be an image file (JPG, PNG, WEBP, GIF, BMP)", 400)

    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > 16 * 1024 * 1024:
        return json_error("Profile photo image must be smaller than 16MB", 400)

    import base64
    file_bytes = file.read()
    b64_str = base64.b64encode(file_bytes).decode("ascii")
    mime = mimetype if is_image_mime else f"image/{ext if ext != 'jpg' else 'jpeg'}"
    data_url = f"data:{mime};base64,{b64_str}"

    user.avatar_url = data_url
    user.profile_photo_path = data_url
    db.session.commit()
    log_audit(session.get("username"), "Updated", "Users", f"Profile photo uploaded for {user.username}")

    return jsonify({
        "ok": True,
        "success": True,
        "avatar_url": data_url,
        "avatarUrl": data_url,
        "avatar": data_url,
        "profile_photo_path": data_url,
        "user": {
            "id": user.id,
            "username": user.username,
            "fullName": user.full_name,
            "full_name": user.full_name,
            "email": user.email,
            "contact": user.contact_no,
            "role": user.role,
            "avatar": data_url,
            "avatar_url": data_url,
            "avatarUrl": data_url,
            "profile_photo_path": data_url,
        }
    }), 200


def _remove_avatar_user():
    uid = _get_target_user_id() or session.get("user_id")
    if not uid:
        return json_error("id required", 400)
    user = db.session.get(User, uid)
    if not user:
        return json_error("User not found", 404)

    if user.avatar_url:
        old_rel = user.avatar_url.lstrip("/")
        old_full = os.path.join(current_app.static_folder, old_rel)
        if os.path.isfile(old_full):
            try:
                os.remove(old_full)
            except Exception as e:
                current_app.logger.warning(f"Could not remove avatar file: {e}")

    user.avatar_url = None
    user.profile_photo_path = None
    db.session.commit()
    log_audit(session.get("username"), "Updated", "Users", f"Profile photo removed for {user.username}")

    return jsonify({
        "ok": True,
        "success": True,
        "avatar_url": None,
        "avatarUrl": None,
        "avatar": None,
        "profile_photo_path": None,
        "user": {
            "id": user.id,
            "username": user.username,
            "fullName": user.full_name,
            "full_name": user.full_name,
            "email": user.email,
            "contact": user.contact_no,
            "role": user.role,
            "avatar": None,
            "avatar_url": None,
            "avatarUrl": None,
            "profile_photo_path": None,
        }
    }), 200


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
