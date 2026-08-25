import os
import re
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file, session

from ..extensions import db
from ..models import SystemBackup, SystemSetting
from ..permissions import json_error, log_audit, login_required, permission_required, role_can
from ..services.backup_scheduler import get_scheduler_status, reschedule_backup_job
from ..services.backup_service import BACKUP_DIR, cleanup_old_backups, generate_sql_dump, run_database_backup

bp = Blueprint("settings", __name__)

ML_TASK_KEYS = {
    "occurrence": {"setting": "ml_occurrence_model", "default": "random_forest",
                   "allowed": ["logistic_regression", "random_forest"]},
    "type": {"setting": "ml_type_model", "default": "gradient_boosting",
             "allowed": ["decision_tree", "gradient_boosting"]},
    "hotspot": {"setting": "ml_hotspot_model", "default": "random_forest",
                "allowed": ["random_forest", "gradient_boosting"]},
}


@bp.route("/api/backup/cron-trigger", methods=["GET", "POST"])
def backup_cron_trigger():
    """Secure endpoint for external cloud cron runners (e.g. Render Cron, cron-job.org)
    to trigger scheduled automated database backups."""
    expected_secret = os.environ.get("CRON_SECRET", "blottercast-cron-secret-2026")
    provided_secret = (
        request.headers.get("X-Cron-Secret")
        or request.headers.get("Authorization", "").replace("Bearer ", "").strip()
        or request.args.get("secret", "")
    )

    if not provided_secret or provided_secret != expected_secret:
        return json_error("Unauthorized cron trigger request: invalid or missing CRON_SECRET", 401)

    result = run_database_backup(triggered_by="system (automatic)")
    if not result.get("success"):
        return jsonify({"ok": False, "status": "error", "error": result.get("error")}), 500

    return jsonify({
        "ok": True,
        "status": "success",
        "file": result.get("file"),
        "size": result.get("size"),
        "by": "system (automatic)",
        "cleaned_old_backups": result.get("cleaned_old_backups", 0),
    }), 200


@bp.route("/api/backup/status", methods=["GET"])
@login_required
@permission_required("system_settings")
def backup_scheduler_status_route():
    """Returns the current autonomous scheduler daemon status."""
    return jsonify({"ok": True, **get_scheduler_status()})


@bp.route("/api/backup/run", methods=["POST"])
@login_required
@permission_required("system_settings")
def backup_run_direct():
    """Direct alias for manual backup execution."""
    return _backup()


@bp.route("/api/settings.php", methods=["GET", "POST"])
@login_required
def settings_router():
    action = request.args.get("action", "")
    method = request.method

    if action == "auto_backup_check" and method == "GET":
        # Keep legacy route functional
        return _auto_backup_check()

    if action == "ml_model" and method == "GET":
        if not role_can(session.get("role", ""), "view_analytics"):
            return json_error("You do not have permission to perform this action.", 403)
        return _ml_model_get()
    if action == "ml_model" and method == "POST":
        if not role_can(session.get("role", ""), "retrain_ml"):
            return json_error("You do not have permission to perform this action.", 403)
        return _ml_model_set()

    if action == "letterhead" and method == "GET":
        return _letterhead()

    if action == "time_format" and method == "GET":
        row = SystemSetting.query.get("time_format")
        return jsonify({"time_format": row.setting_value if row else "12"})
    if action == "time_format" and method == "POST":
        d = request.get_json(silent=True) or {}
        tf = str(d.get("time_format") or d.get("timeFormat") or "12").strip()
        tf = "24" if tf.startswith("24") else "12"
        row = SystemSetting.query.get("time_format")
        if row:
            row.setting_value = tf
        else:
            db.session.add(SystemSetting(setting_key="time_format", setting_value=tf))
        db.session.commit()
        return jsonify({"ok": True, "time_format": tf})

    # Everything else requires full system_settings access.
    if not role_can(session.get("role", ""), "system_settings"):
        return json_error("You do not have permission to perform this action.", 403)

    if action == "list" and method == "GET":
        return _list()
    if action == "save" and method == "POST":
        return _save()
    if action == "backup" and method == "POST":
        return _backup()
    if action == "backups" and method == "GET":
        return _backups()
    if action == "download_backup" and method == "GET":
        return _download_backup()

    return json_error("Unknown action", 404)


@bp.route("/api/admin/security-settings", methods=["GET", "PATCH", "POST"])
@login_required
@permission_required("system_settings")
def admin_security_settings():
    from ..models import SystemSecuritySetting
    from ..permissions import get_security_settings
    if request.method == "GET":
        settings = get_security_settings()
        return jsonify({
            "ok": True,
            "status": "success",
            "is_2fa_globally_enabled": settings.get("is_2fa_globally_enabled", False),
            "enforce_2fa_all_users": settings.get("enforce_2fa_all_users", False),
            "is_idle_timeout_enabled": settings.get("is_idle_timeout_enabled", False),
            "idle_timeout_enabled": settings.get("idle_timeout_enabled", False),
            "idle_timeout_duration_minutes": settings.get("idle_timeout_duration_minutes", 120),
            "session_timeout": settings.get("session_timeout", 120),
            "lockout_enabled": settings.get("lockout_enabled", True),
            "max_failed_logins": settings.get("max_failed_logins", 5),
            "min_password_length": settings.get("min_password_length", 8),
            "password_expiry_days": settings.get("password_expiry_days", 90),
        })

    # PATCH or POST
    data = request.get_json(silent=True) or {}
    if not data:
        return json_error("No settings provided to update", 400)

    # 1. Update or create the single-row SystemSecuritySetting record
    sec_row = db.session.get(SystemSecuritySetting, 1)
    if not sec_row:
        sec_row = SystemSecuritySetting(id=1)
        db.session.add(sec_row)

    if "is_2fa_globally_enabled" in data or "enforce_2fa_all_users" in data:
        val = bool(data.get("is_2fa_globally_enabled", data.get("enforce_2fa_all_users", False)))
        sec_row.is_2fa_globally_enabled = val
        sec_row.enforce_2fa_all_users = val

    if "is_idle_timeout_enabled" in data or "idle_timeout_enabled" in data:
        val = bool(data.get("is_idle_timeout_enabled", data.get("idle_timeout_enabled", False)))
        sec_row.is_idle_timeout_enabled = val
        sec_row.idle_timeout_enabled = val

    if "idle_timeout_duration_minutes" in data or "session_timeout" in data:
        val = int(data.get("idle_timeout_duration_minutes", data.get("session_timeout", 120)))
        sec_row.idle_timeout_duration_minutes = val
        sec_row.session_timeout = val

    if "lockout_enabled" in data:
        sec_row.lockout_enabled = bool(data["lockout_enabled"])

    if "max_failed_logins" in data:
        sec_row.max_failed_logins = int(data["max_failed_logins"])

    if "min_password_length" in data:
        sec_row.min_password_length = int(data["min_password_length"])

    if "password_expiry_days" in data:
        sec_row.password_expiry_days = int(data["password_expiry_days"])

    # 2. Also keep system_settings table in sync
    for key, val in data.items():
        clean_key = re.sub(r"[^a-zA-Z0-9_]", "", str(key))
        str_val = "1" if val is True else ("0" if val is False else str(val))
        row = SystemSetting.query.get(clean_key)
        if row:
            row.setting_value = str_val
        else:
            db.session.add(SystemSetting(setting_key=clean_key, setting_value=str_val))

    db.session.commit()
    log_audit(session.get("username"), "Updated", "SecuritySettings", "Security and authentication settings updated")

    return jsonify({
        "ok": True,
        "status": "success",
        "message": "Security settings updated successfully",
    })


# ---------------- Helpers ----------------
def _settings_map(keys=None):
    q = SystemSetting.query
    if keys:
        q = q.filter(SystemSetting.setting_key.in_(keys))
    return {r.setting_key: r.setting_value for r in q.all()}


def _list():
    return jsonify(_settings_map())


def _save():
    d = request.get_json(silent=True) or {}
    if not d:
        return json_error("No settings provided")

    has_backup_setting_changed = False
    backup_keys = {"backup_frequency", "backup_time", "retain_backups_days"}

    for key, value in d.items():
        clean_key = re.sub(r"[^a-zA-Z0-9_]", "", str(key))
        if clean_key in backup_keys:
            has_backup_setting_changed = True

        row = SystemSetting.query.get(clean_key)
        if row:
            row.setting_value = str(value)
        else:
            db.session.add(SystemSetting(setting_key=clean_key, setting_value=str(value)))

        # Keep session_timeout and idle_timeout_duration_minutes in sync
        if clean_key == "idle_timeout_duration_minutes" and "session_timeout" not in d:
            st = SystemSetting.query.get("session_timeout")
            if st:
                st.setting_value = str(value)
            else:
                db.session.add(SystemSetting(setting_key="session_timeout", setting_value=str(value)))
        elif clean_key == "session_timeout" and "idle_timeout_duration_minutes" not in d:
            it = SystemSetting.query.get("idle_timeout_duration_minutes")
            if it:
                it.setting_value = str(value)
            else:
                db.session.add(SystemSetting(setting_key="idle_timeout_duration_minutes", setting_value=str(value)))

    db.session.commit()

    # Dynamic reschedule if backup scheduling settings were updated
    if has_backup_setting_changed:
        reschedule_backup_job()

    log_audit(session.get("username"), "Updated", "Settings", "System settings saved")
    return jsonify({"ok": True, "updated": len(d)})


def _ml_model_get():
    keys = [cfg["setting"] for cfg in ML_TASK_KEYS.values()]
    by_key = _settings_map(keys)
    return jsonify({cfg["setting"]: by_key.get(cfg["setting"], cfg["default"]) for cfg in ML_TASK_KEYS.values()})


def _ml_model_set():
    d = request.get_json(silent=True) or {}
    task, model = d.get("task", ""), d.get("model", "")
    if task not in ML_TASK_KEYS:
        return json_error("Invalid task. Expected occurrence, type, or hotspot.")
    cfg = ML_TASK_KEYS[task]
    if model not in cfg["allowed"]:
        return json_error(f"Invalid model for the {task} task. Expected one of: {', '.join(cfg['allowed'])}")

    row = SystemSetting.query.get(cfg["setting"])
    if row:
        row.setting_value = model
    else:
        db.session.add(SystemSetting(setting_key=cfg["setting"], setting_value=model))
    db.session.commit()
    return jsonify({"ok": True})


def _letterhead():
    return jsonify(_settings_map(["captain_name", "barangay_name"]))


def _auto_backup_check():
    result = run_database_backup("system (automatic)")
    return jsonify({"ran": True, **result})


def _backup():
    result = run_database_backup(session.get("username", "admin"))
    if not result.get("success"):
        return jsonify({"ok": False, "error": result.get("error")}), 500
    return jsonify({
        "ok": True, "file": result["file"], "size": result["size"],
        "url": f"api/settings.php?action=download_backup&file={result['file']}",
    })


def _backups():
    rows = SystemBackup.query.order_by(SystemBackup.id.desc()).limit(20).all()
    return jsonify([{
        "id": r.id, "file_name": r.file_name, "size_bytes": r.size_bytes,
        "status": r.status, "created_by": r.created_by,
        # Naive UTC — "Z" so the Backup History table shows the real
        # Philippines time it ran, not shifted by the viewer's own timezone.
        "created_at": (r.created_at.isoformat() + "Z") if r.created_at else None,
    } for r in rows])


def _download_backup():
    filename = os.path.basename(request.args.get("file", ""))
    path = os.path.join(BACKUP_DIR, filename)
    if not filename or not os.path.isfile(path):
        return "Backup not found.", 404
    return send_file(path, mimetype="application/sql", as_attachment=True, download_name=filename)
