import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

import bcrypt
from flask import Blueprint, current_app, jsonify, request, session
from sqlalchemy import func

from ..email import send_otp_email
from ..extensions import db
from ..models import OtpCode, User
from ..permissions import get_security_settings, json_error, log_audit, login_required

bp = Blueprint("auth", __name__)


def _check_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, AttributeError):
        return False


def _hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ---------------------------------------------------------------
# OTP helpers
# ---------------------------------------------------------------
def _hash_otp(code: str) -> str:
    # OTPs are short-lived (minutes) and rate-limited, so a fast, salted-by-
    # secret HMAC is appropriate here -- no need for bcrypt's deliberate slowness.
    key = current_app.config["SECRET_KEY"].encode("utf-8")
    return hmac.new(key, code.encode("utf-8"), hashlib.sha256).hexdigest()


def _check_otp(code: str, code_hash: str) -> bool:
    return hmac.compare_digest(_hash_otp(code), code_hash)


def _mask_email(email: str) -> str:
    if not email or "@" not in email:
        return None
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked = local[0] + "*" * max(1, len(local) - 1)
    else:
        masked = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked}@{domain}"


def _issue_and_send_otp(user: User, purpose: str = "login") -> None:
    """Invalidate any still-pending codes of this purpose for this user,
    generate a fresh one, store its hash, and email it (or log it to the
    dev outbox -- see app/email.py)."""
    OtpCode.query.filter_by(user_id=user.id, purpose=purpose, consumed_at=None).update(
        {"consumed_at": datetime.utcnow()}
    )

    code = "".join(secrets.choice("0123456789") for _ in range(current_app.config["MFA_CODE_LENGTH"]))
    expiry_minutes = current_app.config["MFA_CODE_EXPIRY_MINUTES"]
    otp = OtpCode(
        user_id=user.id, code_hash=_hash_otp(code), purpose=purpose,
        expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes),
    )
    db.session.add(otp)
    db.session.commit()

    send_otp_email(user.email, code, user.full_name, purpose=purpose)


# Same URL contract the frontend already calls: /api/auth.php?action=...
@bp.route("/api/auth.php", methods=["GET", "POST"])
def auth_router():
    action = request.args.get("action", "")

    if request.method == "POST" and action == "login":
        return _login()
    if action == "verify_otp" and request.method == "POST":
        return _verify_otp()
    if action == "resend_otp" and request.method == "POST":
        return _resend_otp()
    if action == "logout":
        return _logout()
    if action == "me":
        return _me()
    if action == "change_password" and request.method == "POST":
        return _change_password()
    if action == "forgot_password" and request.method == "POST":
        return _forgot_password()
    if action == "resend_reset_otp" and request.method == "POST":
        return _resend_reset_otp()
    if action == "reset_password" and request.method == "POST":
        return _reset_password()
    if action == "verify_reset_otp" and request.method == "POST":
        return _verify_reset_otp()
    if action == "my_security" and request.method == "GET":
        return _my_security()
    if action == "toggle_my_mfa" and request.method == "POST":
        return _toggle_my_mfa()
    if action == "my_account" and request.method == "GET":
        return _my_account()
    if action == "update_my_account" and request.method == "POST":
        return _update_my_account()

    return json_error("Unknown action", 404)


def _complete_login(user, audit_note):
    """Finishes a successful sign-in — used both when MFA verification just
    passed, and when MFA is disabled for this account and password
    verification alone is enough. Sets last_login, starts the session, and
    returns the same response shape either way."""
    settings = get_security_settings()
    must_change_password = False
    if settings["password_expiry_days"] > 0 and user.password_changed_at:
        age_days = (datetime.utcnow() - user.password_changed_at).total_seconds() / 86400
        must_change_password = age_days > settings["password_expiry_days"]

    user.last_login = datetime.utcnow()
    db.session.commit()

    session.clear()
    session["user_id"] = user.id
    session["full_name"] = user.full_name
    session["role"] = user.role
    session["username"] = user.username
    session["must_change_password"] = must_change_password
    session["last_activity"] = datetime.utcnow().timestamp()

    log_audit(user.username, "Login", "System", audit_note)

    return jsonify({"ok": True, "mfaRequired": False, "user": {
        "username": user.username, "full_name": user.full_name, "role": user.role,
        "mustChangePassword": must_change_password,
    }})


def _login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return json_error("Username and password required")

    settings = get_security_settings()
    user = User.query.filter_by(username=username).first()

    if user and settings["lockout_enabled"] and user.locked_until and user.locked_until > datetime.utcnow():
        minutes_left = max(1, int((user.locked_until - datetime.utcnow()).total_seconds() // 60) + 1)
        return json_error(
            f"This account is locked due to too many failed login attempts. "
            f"Try again in {minutes_left} minute(s), or contact an administrator.", 403
        )

    if not user or not _check_password(password, user.password):
        if user and settings["lockout_enabled"]:
            user.failed_attempts = (user.failed_attempts or 0) + 1
            if user.failed_attempts >= settings["max_failed_logins"]:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                user.failed_attempts = 0
                db.session.commit()
                log_audit(user.username, "Locked", "System", "Account locked after too many failed login attempts")
                return json_error("Too many failed login attempts. This account has been locked for 15 minutes.", 403)
            db.session.commit()
        return json_error("Invalid username or password", 401)

    if user.status != "Active":
        return json_error(f"This account is {user.status.lower()}. Contact an administrator.", 403)

    user.failed_attempts = 0
    user.locked_until = None

    # 2FA is optional, per-account (Settings → Security → Two-Factor
    # Authentication). Only send/require a code when the account actually
    # has it turned on — otherwise password verification alone completes
    # the login, same as before 2FA existed.
    if not user.mfa_enabled:
        db.session.commit()
        return _complete_login(user, "Successful login (2FA disabled for this account)")

    if not user.email:
        return json_error(
            "This account has no email on file, so a sign-in code can't be sent. "
            "Contact an administrator to add one.", 403
        )

    db.session.commit()

    _issue_and_send_otp(user)

    session.clear()
    session["mfa_pending_user_id"] = user.id
    session["mfa_pending_at"] = datetime.utcnow().timestamp()

    log_audit(user.username, "Login", "System", "Password verified, MFA code sent")

    return jsonify({
        "ok": True, "mfaRequired": True,
        "maskedEmail": _mask_email(user.email),
        "expiresInSeconds": current_app.config["MFA_CODE_EXPIRY_MINUTES"] * 60,
        "resendCooldownSeconds": current_app.config["MFA_RESEND_COOLDOWN_SECONDS"],
    })


def _pending_mfa_user():
    """Returns the User for a valid pending-MFA session, or None (clearing
    the session) if there isn't one or the overall pending window has lapsed."""
    uid = session.get("mfa_pending_user_id")
    pending_at = session.get("mfa_pending_at")
    if not uid or not pending_at:
        return None

    # overall window a little longer than the code's own expiry, so the
    # "code expired" message (not "session expired") is what the person sees
    window_seconds = (current_app.config["MFA_CODE_EXPIRY_MINUTES"] + 5) * 60
    if (datetime.utcnow().timestamp() - pending_at) > window_seconds:
        session.clear()
        return None

    return User.query.get(uid)


def _verify_otp():
    user = _pending_mfa_user()
    if not user:
        return json_error("Your sign-in attempt has expired. Please log in again.", 401)

    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    if not code:
        return json_error("Enter the verification code sent to your email")

    otp = (
        OtpCode.query.filter_by(user_id=user.id, purpose="login", consumed_at=None)
        .order_by(OtpCode.id.desc()).first()
    )
    if not otp or otp.expires_at < datetime.utcnow():
        return json_error("This code has expired. Request a new one.", 400)

    max_attempts = current_app.config["MFA_MAX_ATTEMPTS"]
    if otp.attempts >= max_attempts:
        return json_error("Too many incorrect attempts. Request a new code.", 400)

    if not _check_otp(code, otp.code_hash):
        otp.attempts += 1
        db.session.commit()
        remaining = max_attempts - otp.attempts
        if remaining <= 0:
            return json_error("Too many incorrect attempts. Request a new code.", 400)
        return json_error(f"Incorrect code. {remaining} attempt(s) remaining.", 400)

    otp.consumed_at = datetime.utcnow()
    db.session.commit()

    return _complete_login(user, "Successful login (MFA verified)")


def _resend_otp():
    user = _pending_mfa_user()
    if not user:
        return json_error("Your sign-in attempt has expired. Please log in again.", 401)

    last = (
        OtpCode.query.filter_by(user_id=user.id, purpose="login")
        .order_by(OtpCode.id.desc()).first()
    )
    cooldown = current_app.config["MFA_RESEND_COOLDOWN_SECONDS"]
    if last:
        elapsed = (datetime.utcnow() - last.created_at).total_seconds()
        if elapsed < cooldown:
            wait = int(cooldown - elapsed) + 1
            return json_error(f"Please wait {wait}s before requesting another code.", 429)

    _issue_and_send_otp(user)
    return jsonify({"ok": True, "maskedEmail": _mask_email(user.email)})


def _pending_reset_user():
    """Returns the User for a valid pending-password-reset session, or None
    (clearing the session) if there isn't one or the window has lapsed."""
    uid = session.get("reset_pending_user_id")
    pending_at = session.get("reset_pending_at")
    if not uid or not pending_at:
        return None

    window_seconds = (current_app.config["MFA_CODE_EXPIRY_MINUTES"] + 5) * 60
    if (datetime.utcnow().timestamp() - pending_at) > window_seconds:
        session.clear()
        return None

    return User.query.get(uid)


def _forgot_password():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    if not username:
        return json_error("Enter your username")

    user = User.query.filter_by(username=username).first()
    if not user:
        return json_error("No account found with that username.", 404)
    if user.status != "Active":
        return json_error(f"This account is {user.status.lower()}. Contact an administrator.", 403)
    if not user.email:
        return json_error(
            "This account has no email on file, so a reset code can't be sent. "
            "Contact an administrator to add one.", 403
        )

    _issue_and_send_otp(user, purpose="reset")
    session.clear()
    session["reset_pending_user_id"] = user.id
    session["reset_pending_at"] = datetime.utcnow().timestamp()
    log_audit(user.username, "Requested", "System", "Password reset code requested")

    return jsonify({"ok": True, "maskedEmail": _mask_email(user.email)})


def _resend_reset_otp():
    user = _pending_reset_user()
    if not user:
        return json_error("Your password reset request has expired. Please start again.", 401)

    last = (
        OtpCode.query.filter_by(user_id=user.id, purpose="reset")
        .order_by(OtpCode.id.desc()).first()
    )
    cooldown = current_app.config["MFA_RESEND_COOLDOWN_SECONDS"]
    if last:
        elapsed = (datetime.utcnow() - last.created_at).total_seconds()
        if elapsed < cooldown:
            wait = int(cooldown - elapsed) + 1
            return json_error(f"Please wait {wait}s before requesting another code.", 429)

    _issue_and_send_otp(user, purpose="reset")
    return jsonify({"ok": True, "maskedEmail": _mask_email(user.email)})


def _verify_reset_otp():
    """Step 2 of forgot-password: verify the code by itself. Only once this
    succeeds does the New Password step become reachable (see
    _reset_password, which now requires reset_verified rather than the raw
    code) — the two steps stay genuinely sequential instead of one combined
    form."""
    user = _pending_reset_user()
    if not user:
        return json_error("Your password reset request has expired. Please start again.", 401)

    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    if not code:
        return json_error("Enter the verification code sent to your email")

    otp = (
        OtpCode.query.filter_by(user_id=user.id, purpose="reset", consumed_at=None)
        .order_by(OtpCode.id.desc()).first()
    )
    if not otp or otp.expires_at < datetime.utcnow():
        return json_error("This code has expired. Request a new one.", 400)

    max_attempts = current_app.config["MFA_MAX_ATTEMPTS"]
    if otp.attempts >= max_attempts:
        return json_error("Too many incorrect attempts. Request a new code.", 400)

    if not _check_otp(code, otp.code_hash):
        otp.attempts += 1
        db.session.commit()
        remaining = max_attempts - otp.attempts
        if remaining <= 0:
            return json_error("Too many incorrect attempts. Request a new code.", 400)
        return json_error(f"Incorrect code. {remaining} attempt(s) remaining.", 400)

    otp.consumed_at = datetime.utcnow()
    db.session.commit()

    session["reset_verified"] = True
    log_audit(user.username, "Requested", "System", "Password reset code verified")

    return jsonify({"ok": True})


def _reset_password():
    """Step 3 of forgot-password: set the new password. Only reachable
    after _verify_reset_otp() has already succeeded for this session — no
    code is accepted here, so the New Password step can't be skipped to
    directly and can't be combined with code entry into one submission."""
    user = _pending_reset_user()
    if not user:
        return json_error("Your password reset request has expired. Please start again.", 401)
    if not session.get("reset_verified"):
        return json_error("Please verify your code before setting a new password.", 401)

    data = request.get_json(silent=True) or {}
    new_password = data.get("newPassword") or ""
    if not new_password:
        return json_error("Enter a new password")

    settings = get_security_settings()
    if len(new_password) < settings["min_password_length"]:
        return json_error(f"New password must be at least {settings['min_password_length']} characters long")

    user.password = _hash_password(new_password)
    user.password_changed_at = datetime.utcnow()
    user.failed_attempts = 0
    user.locked_until = None
    db.session.commit()

    session.clear()
    log_audit(user.username, "Updated", "System", "Password reset via emailed verification code")

    return jsonify({"ok": True, "message": "Your password has been reset. Please sign in."})


def _logout():
    username = session.get("username")
    if username:
        log_audit(username, "Logout", "System", "User logged out")
    session.clear()
    return jsonify({"ok": True})


def _me():
    if not session.get("user_id"):
        return jsonify({"authenticated": False})

    settings = get_security_settings()
    timeout_seconds = settings["session_timeout"] * 60
    last_activity = session.get("last_activity")
    if timeout_seconds > 0 and last_activity and (datetime.utcnow().timestamp() - last_activity) > timeout_seconds:
        session.clear()
        return jsonify({"authenticated": False})
    session["last_activity"] = datetime.utcnow().timestamp()

    return jsonify({"authenticated": True, "user": {
        "full_name": session.get("full_name"), "role": session.get("role"),
        "mustChangePassword": bool(session.get("must_change_password")),
    }})


@login_required
def _change_password_impl():
    data = request.get_json(silent=True) or {}
    current_password = data.get("currentPassword") or ""
    new_password = data.get("newPassword") or ""
    if not current_password or not new_password:
        return json_error("Current and new password are both required")

    user = User.query.get(session["user_id"])
    if not user or not _check_password(current_password, user.password):
        return json_error("Current password is incorrect", 401)

    settings = get_security_settings()
    if len(new_password) < settings["min_password_length"]:
        return json_error(f"New password must be at least {settings['min_password_length']} characters long")

    user.password = _hash_password(new_password)
    user.password_changed_at = datetime.utcnow()
    user.failed_attempts = 0
    user.locked_until = None
    db.session.commit()

    session["must_change_password"] = False
    log_audit(user.username, "Updated", "System", "Password changed")
    return jsonify({"ok": True})


def _change_password():
    return _change_password_impl()


def _my_security():
    """Self-service: any logged-in user can see their own 2FA state. Not
    gated by manage_users/system_settings — this is a personal preference,
    not an admin action."""
    if not session.get("user_id"):
        return json_error("Not authenticated", 401)
    user = User.query.get(session["user_id"])
    if not user:
        return json_error("Not authenticated", 401)
    return jsonify({"mfaEnabled": user.mfa_enabled})


def _toggle_my_mfa():
    """Self-service: any logged-in user can turn their own 2FA on/off, at
    Settings → Security. Persists to the account, so it applies from the
    very next login onward and survives logout in between."""
    if not session.get("user_id"):
        return json_error("Not authenticated", 401)
    user = User.query.get(session["user_id"])
    if not user:
        return json_error("Not authenticated", 401)
    data = request.get_json(silent=True) or {}
    if "enabled" not in data:
        return json_error("enabled is required")
    user.mfa_enabled = bool(data["enabled"])
    db.session.commit()
    log_audit(user.username, "Updated", "System",
              f"Two-factor authentication turned {'on' if user.mfa_enabled else 'off'} for their own account")
    return jsonify({"ok": True, "mfaEnabled": user.mfa_enabled})


def _my_account():
    """Self-service: any logged-in user can see their own editable profile
    fields. Not gated by manage_users — role/status stay admin-only (via
    users.php), but a user's own name/email/contact are theirs to fix."""
    if not session.get("user_id"):
        return json_error("Not authenticated", 401)
    user = User.query.get(session["user_id"])
    if not user:
        return json_error("Not authenticated", 401)
    return jsonify({
        "username": user.username, "fullName": user.full_name,
        "email": user.email, "contact": user.contact_no, "role": user.role,
    })


def _update_my_account():
    """Self-service: any logged-in user can update their own name, email,
    and contact number at Settings → Security. Role and status are
    deliberately not editable here — those stay an admin-only action via
    users.php, same as before."""
    if not session.get("user_id"):
        return json_error("Not authenticated", 401)
    user = User.query.get(session["user_id"])
    if not user:
        return json_error("Not authenticated", 401)

    data = request.get_json(silent=True) or {}
    full_name = (data.get("fullName") or "").strip()
    email = (data.get("email") or "").strip()
    if not full_name:
        return json_error("Name is required")
    if not email:
        return json_error("Email is required — sign-in codes are sent there for MFA.")
    if User.query.filter(User.id != user.id, func.lower(User.email) == email.lower()).first():
        return json_error("That email address is already in use by another account", 409)

    user.full_name = full_name
    user.email = email
    user.contact_no = (data.get("contact") or "").strip() or None
    db.session.commit()
    log_audit(user.username, "Updated", "System", "Updated their own account details")

    return jsonify({"ok": True, "user": {
        "username": user.username, "fullName": user.full_name,
        "email": user.email, "contact": user.contact_no, "role": user.role,
    }})
