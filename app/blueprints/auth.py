import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta

import bcrypt
from flask import Blueprint, current_app, jsonify, request, session
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import func

from ..email import send_otp_email
from ..extensions import db
from ..models import OtpCode, PasswordHistory, User
from ..permissions import get_security_settings, json_error, log_audit, login_required

bp = Blueprint("auth", __name__)


def _get_serializer() -> URLSafeTimedSerializer:
    secret = current_app.config.get("SECRET_KEY", "dev-secret-change-me")
    return URLSafeTimedSerializer(secret, salt="blottercast-2fa-preauth")


def _generate_pre_auth_token(user_id: int) -> str:
    s = _get_serializer()
    return s.dumps({"user_id": user_id, "created_at": datetime.utcnow().timestamp()})


def _verify_pre_auth_token(token: str, max_age: int = 300) -> int:
    if not token:
        return None
    s = _get_serializer()
    try:
        payload = s.loads(token, max_age=max_age)
        return payload.get("user_id")
    except (SignatureExpired, BadSignature, Exception):
        return None


def _check_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, AttributeError):
        return False


def _hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ---------------------------------------------------------------
# Password History & Reuse Prevention
# ---------------------------------------------------------------
PASSWORD_HISTORY_LIMIT = 5
PASSWORD_REUSE_ERROR = (
    "You cannot reuse your current or previously used password. Please choose a new, different password."
)


def _check_password_reuse(user_id: int, current_hash: str, candidate_password: str) -> bool:
    """Checks whether candidate_password matches the active password hash or any
    of the last 5 stored password history records for this user. Returns True if reused."""
    if current_hash and _check_password(candidate_password, current_hash):
        return True

    if user_id:
        try:
            histories = (
                PasswordHistory.query.filter_by(user_id=user_id)
                .order_by(PasswordHistory.id.desc())
                .limit(PASSWORD_HISTORY_LIMIT)
                .all()
            )
            for h in histories:
                if h.password_hash and _check_password(candidate_password, h.password_hash):
                    return True
        except Exception as e:
            current_app.logger.warning(f"Password history query notice: {e}")

    return False


def _record_password_history(user_id: int, old_hash: str) -> None:
    """Saves old_hash to PasswordHistory and prunes records beyond PASSWORD_HISTORY_LIMIT."""
    if not old_hash or not user_id:
        return
    try:
        db.session.add(PasswordHistory(user_id=user_id, password_hash=old_hash))
        db.session.flush()

        all_hist = (
            PasswordHistory.query.filter_by(user_id=user_id)
            .order_by(PasswordHistory.id.desc())
            .all()
        )
        if len(all_hist) > PASSWORD_HISTORY_LIMIT:
            for extra in all_hist[PASSWORD_HISTORY_LIMIT:]:
                db.session.delete(extra)
    except Exception as e:
        current_app.logger.warning(f"Password history recording notice: {e}")


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


@bp.route("/api/auth/login", methods=["POST"])
def auth_login_direct():
    return _login()


@bp.route("/api/auth/google", methods=["POST"])
def auth_google_direct():
    return _google_login()


@bp.route("/api/auth/verify-otp", methods=["POST"])
def auth_verify_otp_direct():
    return _verify_otp()


@bp.route("/api/auth/logout", methods=["GET", "POST"])
def auth_logout_direct():
    return _logout()


# Same URL contract the frontend already calls: /api/auth.php?action=...
@bp.route("/api/auth.php", methods=["GET", "POST"])
def auth_router():
    try:
        action = request.args.get("action", "")

        if action == "auth_config" and request.method == "GET":
            return _auth_config()
        if action == "google_login" and request.method == "POST":
            return _google_login()
        if request.method == "POST" and action == "login":
            return _login()
        if action == "verify_otp" and request.method == "POST":
            return _verify_otp()
        if action == "resend_otp" and request.method == "POST":
            return _resend_otp()
        if action == "heartbeat" and request.method == "POST":
            return _heartbeat()
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
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error in auth_router '{request.args.get('action')}': {e}")
        return json_error("Internal server error", 500)


def _auth_config():
    import os
    client_id = current_app.config.get("GOOGLE_CLIENT_ID") or os.environ.get("GOOGLE_CLIENT_ID", "")
    return jsonify({
        "status": "success",
        "google_client_id": client_id.strip(),
    })


def _google_login():
    data = request.get_json(silent=True) or {}
    token = data.get("credential") or data.get("id_token") or data.get("token") or ""
    if not token:
        return json_error("Google ID token required", 400)

    try:
        import urllib.parse
        import urllib.request
        import json as json_lib

        verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(token)}"
        req = urllib.request.Request(verify_url, headers={"User-Agent": "BlotterCast/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                return json_error("Failed to verify Google ID token with provider", 401)
            token_info = json_lib.loads(resp.read().decode("utf-8"))
    except Exception as e:
        current_app.logger.warning(f"Google token verification request failed: {e}")
        return json_error("Invalid or expired Google ID token", 401)

    expected_aud = current_app.config.get("GOOGLE_CLIENT_ID", "").strip()
    if expected_aud:
        token_aud = token_info.get("aud")
        if token_aud != expected_aud:
            current_app.logger.warning(f"Google token audience mismatch: expected '{expected_aud}', got '{token_aud}'")
            return json_error("Google token audience mismatch", 401)

    email = token_info.get("email")
    email_verified = token_info.get("email_verified")
    if not email:
        return json_error("Google token does not contain a verified email address", 401)
    if isinstance(email_verified, str) and email_verified.lower() != "true":
        return json_error("Google email address is not verified", 401)
    elif isinstance(email_verified, bool) and not email_verified:
        return json_error("Google email address is not verified", 401)

    google_sub = str(token_info.get("sub") or "").strip()
    clean_email = str(email or "").strip().lower()

    try:
        user = None
        if google_sub:
            user = User.query.filter_by(google_id=google_sub).first()
        if not user and clean_email:
            user = User.query.filter(func.lower(func.trim(User.email)) == clean_email).first()

        if not user:
            return json_error(
                "No BlotterCast account is associated with this Google email address. "
                "Please contact an administrator to create or link your account.", 401
            )

        # Link google_id if not already saved
        if google_sub and user.google_id != google_sub:
            user.google_id = google_sub
            db.session.commit()

        if user.status.upper() == "SUSPENDED":
            return json_error("This account has been suspended. Please contact an administrator.", 403)

        user.failed_attempts = 0
        user.locked_until = None

        # 1. Fetch the master security setting (single source of truth)
        settings = get_security_settings()
        global_2fa_enabled = bool(settings.get("is_2fa_globally_enabled", False) or settings.get("enforce_2fa_all_users", False))

        # 2. Master 2FA Enforcement Gate
        if not global_2fa_enabled:
            # If Master Switch is OFF: NO USER needs 2FA. Immediately complete login.
            db.session.commit()
            return _complete_login(user, f"Successful Google OAuth login ({email}) (Master 2FA Switch OFF)")

        # If Master Switch is ON: ALL ROLES MUST COMPLETE 2FA
        if not user.email:
            return json_error(
                "Two-Factor Authentication is required system-wide, but this account has no email on file for OTP verification. "
                "Please contact a System Administrator.", 403
            )
        db.session.commit()
        _issue_and_send_otp(user, purpose="login")

        session.clear()
        session["mfa_pending_user_id"] = user.id
        session["mfa_pending_at"] = datetime.utcnow().timestamp()

        pre_auth_token = _generate_pre_auth_token(user.id)
        log_audit(user.username, "Login", "System", "Google OAuth verified, MFA code sent (Master Switch ON)")

        return jsonify({
            "ok": True,
            "status": "2fa_required",
            "requires_2fa": True,
            "mfaRequired": True,
            "mfa_required": True,
            "user_id": user.id,
            "pre_auth_token": pre_auth_token,
            "temp_token": pre_auth_token,
            "maskedEmail": _mask_email(user.email),
            "masked_email": _mask_email(user.email),
            "enforcedGlobally": True,
            "expiresInSeconds": current_app.config["MFA_CODE_EXPIRY_MINUTES"] * 60,
            "resendCooldownSeconds": current_app.config["MFA_RESEND_COOLDOWN_SECONDS"],
            "message": "Two-factor authentication code sent. Please enter OTP to continue.",
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Database error during Google login: {e}")
        return json_error(f"Google login failed: {str(e)}", 500)


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
    user.last_seen = datetime.utcnow()
    db.session.commit()

    session.clear()
    session["user_id"] = user.id
    session["full_name"] = user.full_name
    session["role"] = user.role
    session["username"] = user.username
    session["must_change_password"] = must_change_password
    session["last_activity"] = datetime.utcnow().timestamp()

    log_audit(user.username, "Login", "System", audit_note)

    return jsonify({
        "ok": True,
        "status": "success",
        "requires_2fa": False,
        "mfaRequired": False,
        "mfa_required": False,
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "mustChangePassword": must_change_password,
        }
    })


def _login():
    try:
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

        if user.status.upper() == "SUSPENDED":
            return json_error("This account has been suspended. Please contact an administrator.", 403)

        user.failed_attempts = 0
        user.locked_until = None

        # 1. Fetch the master security setting (single source of truth)
        global_2fa_enabled = bool(settings.get("is_2fa_globally_enabled", False) or settings.get("enforce_2fa_all_users", False))

        # 2. Master 2FA Enforcement Gate
        if not global_2fa_enabled:
            # If Master Switch is OFF: NO USER needs 2FA. Immediately complete login.
            db.session.commit()
            return _complete_login(user, "Successful login (Master 2FA Switch OFF)")

        # If Master Switch is ON: ALL ROLES (Barangay Captain, Desk Officer, Data Encoder, Admin) MUST COMPLETE 2FA
        if not user.email:
            return json_error(
                "Two-Factor Authentication is required system-wide, but this account has no email on file for OTP verification. "
                "Please contact a System Administrator.", 403
            )

        db.session.commit()

        _issue_and_send_otp(user)

        session.clear()
        session["mfa_pending_user_id"] = user.id
        session["mfa_pending_at"] = datetime.utcnow().timestamp()

        pre_auth_token = _generate_pre_auth_token(user.id)
        log_audit(user.username, "Login", "System", "Password verified, MFA code sent (Master Switch ON)")

        return jsonify({
            "ok": True,
            "status": "2fa_required",
            "requires_2fa": True,
            "mfaRequired": True,
            "mfa_required": True,
            "user_id": user.id,
            "pre_auth_token": pre_auth_token,
            "temp_token": pre_auth_token,
            "maskedEmail": _mask_email(user.email),
            "masked_email": _mask_email(user.email),
            "enforcedGlobally": True,
            "expiresInSeconds": current_app.config["MFA_CODE_EXPIRY_MINUTES"] * 60,
            "resendCooldownSeconds": current_app.config["MFA_RESEND_COOLDOWN_SECONDS"],
            "message": "Two-factor authentication code sent. Please enter OTP to continue.",
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Database error during login: {e}")
        return json_error(f"Login failed: {str(e)}", 500)


def _pending_mfa_user(data=None):
    """Returns the User for a valid pending-MFA session / pre_auth_token, or None
    (clearing the session) if there isn't one or the window has lapsed."""
    data = data or {}
    token = data.get("pre_auth_token") or data.get("preAuthToken")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    if token:
        expiry_seconds = (current_app.config["MFA_CODE_EXPIRY_MINUTES"] + 5) * 60
        uid = _verify_pre_auth_token(token, max_age=expiry_seconds)
        if uid:
            return db.session.get(User, uid)

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

    return db.session.get(User, uid)


def _verify_otp():
    try:
        data = request.get_json(silent=True) or {}
        user = _pending_mfa_user(data)
        if not user:
            return json_error("Your sign-in attempt has expired. Please log in again.", 401)

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
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Database error during OTP verification: {e}")
        return json_error(f"OTP verification failed: {str(e)}", 500)


def _resend_otp():
    data = request.get_json(silent=True) or {}
    user = _pending_mfa_user(data)
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

    return db.session.get(User, uid)


def _forgot_password():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    if not username:
        return json_error("Enter your username")

    user = User.query.filter_by(username=username).first()
    if not user:
        return json_error("No account found with that username.", 404)
    if user.status.upper() == "SUSPENDED":
        return json_error("This account has been suspended. Please contact an administrator.", 403)
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

    # Password Reuse Prevention Check
    if _check_password_reuse(user.id, user.password, new_password):
        return json_error(PASSWORD_REUSE_ERROR, 400)

    # Save previous password hash into history before updating
    _record_password_history(user.id, user.password)

    user.password = _hash_password(new_password)
    user.password_changed_at = datetime.utcnow()
    user.failed_attempts = 0
    user.locked_until = None
    db.session.commit()

    session.clear()
    log_audit(user.username, "Updated", "System", "Password reset via emailed verification code")

    return jsonify({"ok": True, "message": "Your password has been reset. Please sign in."})


def _heartbeat():
    uid = session.get("user_id")
    if uid:
        user = db.session.get(User, uid)
        if user and user.status != "Suspended":
            user.last_seen = datetime.utcnow()
            db.session.commit()
            return jsonify({"ok": True, "online": True})
    return jsonify({"ok": True, "online": False})


def _logout():
    uid = session.get("user_id")
    username = session.get("username")
    if uid:
        user = db.session.get(User, uid)
        if user:
            user.last_seen = None
            db.session.commit()
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

    uid = session.get("user_id")
    if uid:
        user = db.session.get(User, uid)
        if user and user.status != "Suspended":
            user.last_seen = datetime.utcnow()
            db.session.commit()

    return jsonify({"authenticated": True, "user": {
        "full_name": session.get("full_name"), "role": session.get("role"),
        "mustChangePassword": bool(session.get("must_change_password")),
    }})


@login_required
def _change_password_impl():
    data = request.get_json(silent=True) or {}
    current_password = data.get("currentPassword") or data.get("current_password") or ""
    new_password = data.get("newPassword") or data.get("new_password") or ""
    confirm_password = data.get("confirmPassword") or data.get("confirm_password") or data.get("confirmNewPassword")

    if not current_password or not new_password:
        return json_error("Current and new password are both required.", 400)

    if confirm_password is not None and confirm_password != new_password:
        return json_error("New passwords do not match.", 400)

    user = db.session.get(User, session["user_id"])
    if not user or not _check_password(current_password, user.password):
        return json_error("Current password is incorrect.", 400)

    if current_password == new_password or _check_password(new_password, user.password):
        return json_error("New password cannot be the same as your current password.", 400)

    settings = get_security_settings()
    if len(new_password) < settings["min_password_length"]:
        return json_error(f"New password must be at least {settings['min_password_length']} characters long.", 400)

    # Password Reuse Prevention Check
    if _check_password_reuse(user.id, user.password, new_password):
        return json_error("New password cannot be the same as your current password.", 400)

    # Save previous password hash into history before updating
    _record_password_history(user.id, user.password)

    user.password = _hash_password(new_password)
    user.password_changed_at = datetime.utcnow()
    user.failed_attempts = 0
    user.locked_until = None
    db.session.commit()

    session["must_change_password"] = False
    log_audit(user.username, "Updated", "System", "Password changed")
    return jsonify({"ok": True, "message": "Password changed successfully."})



@bp.route("/api/auth/change-password", methods=["POST", "PUT"])
@bp.route("/api/auth/change_password", methods=["POST", "PUT"])
@login_required
def api_change_password_endpoint():
    return _change_password_impl()


def _change_password():
    return _change_password_impl()


def _my_security():
    """Self-service: any logged-in user can see their own 2FA state. Not
    gated by manage_users/system_settings — this is a personal preference,
    not an admin action."""
    if not session.get("user_id"):
        return json_error("Not authenticated", 401)
    user = db.session.get(User, session["user_id"])
    if not user:
        return json_error("Not authenticated", 401)
    return jsonify({"mfaEnabled": user.mfa_enabled})


def _toggle_my_mfa():
    """Self-service: any logged-in user can turn their own 2FA on/off, at
    Settings → Security. Persists to the account, so it applies from the
    very next login onward and survives logout in between."""
    if not session.get("user_id"):
        return json_error("Not authenticated", 401)
    user = db.session.get(User, session["user_id"])
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
    user = db.session.get(User, session["user_id"])
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
    user = db.session.get(User, session["user_id"])
    if not user:
        return json_error("Not authenticated", 401)

    data = request.get_json(silent=True) or {}
    full_name = (data.get("fullName") or "").strip()
    contact = (data.get("contact") or "").strip()
    email = (data.get("email") or "").strip()

    if not full_name:
        return json_error("Full Name is required.")
    if not contact:
        return json_error("Contact Number is required.")
    if not re.match(r"^09\d{9}$", contact):
        return json_error("Contact number must be a valid 11-digit Philippine mobile number starting with 09 (e.g. 09171234567).")
    if not email:
        return json_error("Email address is required.")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return json_error("Please enter a valid email address.")
    if User.query.filter(User.id != user.id, func.lower(User.email) == email.lower()).first():
        return json_error("That email address is already in use by another account", 409)

    user.full_name = full_name
    user.email = email
    user.contact_no = contact
    db.session.commit()
    log_audit(user.username, "Updated", "System", "Updated their own account details")

    return jsonify({"ok": True, "user": {
        "username": user.username, "fullName": user.full_name,
        "email": user.email, "contact": user.contact_no, "role": user.role,
    }})
