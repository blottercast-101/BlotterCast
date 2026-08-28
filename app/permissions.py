"""
permissions.py — authoritative role permission matrix (port of api/permissions.php).
Keep this in sync with frontend/permissions.js, same as the PHP version required.
"""
from datetime import datetime, timedelta
from functools import wraps

from flask import jsonify, session

from .extensions import db
from .models import SystemSetting

PERMISSIONS = {
    "view_records":     {"System Admin": True, "Barangay Captain": True, "Desk Officer": True, "Data Encoder": True},
    "add_blotter":       {"System Admin": True, "Barangay Captain": True, "Desk Officer": True, "Data Encoder": True},
    "edit_records":      {"System Admin": True, "Barangay Captain": True, "Desk Officer": True, "Data Encoder": True},
    "delete_records":     {"System Admin": True, "Barangay Captain": False, "Desk Officer": False, "Data Encoder": False},
    "archive_records":    {"System Admin": True, "Barangay Captain": True, "Desk Officer": True, "Data Encoder": True},
    "generate_reports": {"System Admin": True, "Barangay Captain": True, "Desk Officer": True, "Data Encoder": False},
    "view_analytics":    {"System Admin": True, "Barangay Captain": True, "Desk Officer": True, "Data Encoder": False},
    "manage_users":     {"System Admin": True, "Barangay Captain": True, "Desk Officer": False, "Data Encoder": False},
    "retrain_ml":         {"System Admin": True, "Barangay Captain": True, "Desk Officer": False, "Data Encoder": False},
    "import_data":       {"System Admin": True, "Barangay Captain": True, "Desk Officer": False, "Data Encoder": True},
    "system_settings":  {"System Admin": True, "Barangay Captain": False, "Desk Officer": False, "Data Encoder": False},
}

SECURITY_DEFAULTS = {
    "is_2fa_globally_enabled": False,
    "enforce_2fa_all_users": False,
    "is_idle_timeout_enabled": False,
    "idle_timeout_enabled": False,
    "idle_timeout_duration_minutes": 120,
    "session_timeout": 120,
    "lockout_enabled": True,
    "max_failed_logins": 5,
    "min_password_length": 8,
    "password_expiry_days": 90,
}


def role_can(role: str, permission: str) -> bool:
    return PERMISSIONS.get(permission, {}).get(role, False)


def get_security_settings() -> dict:
    from .models import SystemSecuritySetting
    out = dict(SECURITY_DEFAULTS)

    try:
        rows = SystemSetting.query.filter(SystemSetting.setting_key.in_(out.keys())).all()
        for r in rows:
            if r.setting_key in ("lockout_enabled", "idle_timeout_enabled", "is_idle_timeout_enabled", "enforce_2fa_all_users", "is_2fa_globally_enabled"):
                val_bool = str(r.setting_value).lower() in ("1", "true", "yes", "on", "t")
                out[r.setting_key] = val_bool
            else:
                try:
                    out[r.setting_key] = int(r.setting_value)
                except (ValueError, TypeError):
                    pass
    except Exception:
        pass

    # SystemSecuritySetting table (single row with id=1) is the master ground truth
    try:
        sec_row = db.session.get(SystemSecuritySetting, 1)
        if sec_row:
            out["is_2fa_globally_enabled"] = bool(sec_row.is_2fa_globally_enabled)
            out["enforce_2fa_all_users"] = bool(sec_row.is_2fa_globally_enabled)
            out["is_idle_timeout_enabled"] = bool(sec_row.is_idle_timeout_enabled)
            out["idle_timeout_enabled"] = bool(sec_row.is_idle_timeout_enabled)
            out["idle_timeout_duration_minutes"] = int(sec_row.idle_timeout_duration_minutes)
            out["session_timeout"] = int(sec_row.idle_timeout_duration_minutes)
    except Exception:
        pass

    # Ensure aliases are 100% in sync
    out["enforce_2fa_all_users"] = out["is_2fa_globally_enabled"]
    out["idle_timeout_enabled"] = out["is_idle_timeout_enabled"]
    out["session_timeout"] = out["idle_timeout_duration_minutes"]

    return out


def json_error(message: str, status: int = 400):
    return jsonify({"error": message, "message": message, "success": False, "ok": False}), status


def login_required(view):
    """Port of require_login() in config.php — also enforces idle session timeout
    and the forced-password-change lock."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return json_error("Not authenticated", 401)

        settings = get_security_settings()
        if settings.get("idle_timeout_enabled", True):
            timeout_minutes = settings.get("idle_timeout_duration_minutes") or settings.get("session_timeout", 120)
            timeout_seconds = timeout_minutes * 60
            last_activity = session.get("last_activity")
            if timeout_seconds > 0 and last_activity:
                if (datetime.utcnow().timestamp() - last_activity) > timeout_seconds:
                    session.clear()
                    return json_error("Your session has expired due to inactivity. Please log in again.", 401)
        session["last_activity"] = datetime.utcnow().timestamp()

        if session.get("must_change_password") and view.__module__.split(".")[-1] != "auth":
            return json_error("Your password has expired. Please update it before continuing.", 403)

        return view(*args, **kwargs)
    return wrapped


def permission_required(permission: str):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            role = session.get("role", "")
            if not role_can(role, permission):
                msg = (
                    "Access Denied: Only System Administrators are authorized to permanently delete records."
                    if permission == "delete_records"
                    else "You do not have permission to perform this action."
                )
                return json_error(msg, 403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def log_audit(username: str, action: str, module: str, details: str):
    from .models import AuditLog
    entry = AuditLog(username=username or "system", action=action, module=module, details=details)
    db.session.add(entry)
    db.session.commit()
