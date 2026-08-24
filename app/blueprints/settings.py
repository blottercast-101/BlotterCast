import os
import re
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file, session
from sqlalchemy import inspect, text

from ..extensions import db
from ..models import SystemBackup, SystemSetting
from ..permissions import json_error, log_audit, login_required, permission_required, role_can

bp = Blueprint("settings", __name__)

BACKUP_DIR = os.path.join("/tmp", "backup") if os.environ.get("VERCEL") else os.path.join(os.path.dirname(__file__), "..", "..", "backup")
try:
    os.makedirs(BACKUP_DIR, exist_ok=True)
except OSError:
    pass

ML_TASK_KEYS = {
    "occurrence": {"setting": "ml_occurrence_model", "default": "random_forest",
                   "allowed": ["logistic_regression", "random_forest"]},
    "type": {"setting": "ml_type_model", "default": "gradient_boosting",
             "allowed": ["decision_tree", "gradient_boosting"]},
    "hotspot": {"setting": "ml_hotspot_model", "default": "random_forest",
                "allowed": ["random_forest", "gradient_boosting"]},
}


@bp.route("/api/settings.php", methods=["GET", "POST"])
@login_required
def settings_router():
    action = request.args.get("action", "")
    method = request.method

    if action == "auto_backup_check" and method == "GET":
        if not role_can(session.get("role", ""), "system_settings"):
            return jsonify({"ran": False, "reason": "not_authorized"}), 200
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
        val = data.get("is_2fa_globally_enabled", data.get("enforce_2fa_all_users"))
        sec_row.is_2fa_globally_enabled = bool(str(val).lower() in ("1", "true", "yes", "on", "t") or val is True)
    if "is_idle_timeout_enabled" in data or "idle_timeout_enabled" in data:
        val = data.get("is_idle_timeout_enabled", data.get("idle_timeout_enabled"))
        sec_row.is_idle_timeout_enabled = bool(str(val).lower() in ("1", "true", "yes", "on", "t") or val is True)
    if "idle_timeout_duration_minutes" in data or "session_timeout" in data:
        val = data.get("idle_timeout_duration_minutes", data.get("session_timeout", 120))
        sec_row.idle_timeout_duration_minutes = max(1, int(val))
    sec_row.updated_by = session.get("user_id")
    sec_row.updated_at = datetime.utcnow()

    # 2. Synchronize with key-value system_settings
    updated_count = 0
    mapping = {
        "is_2fa_globally_enabled": lambda v: "1" if (str(v).lower() in ("1", "true", "yes", "on", "t") or v is True) else "0",
        "enforce_2fa_all_users": lambda v: "1" if (str(v).lower() in ("1", "true", "yes", "on", "t") or v is True) else "0",
        "is_idle_timeout_enabled": lambda v: "1" if (str(v).lower() in ("1", "true", "yes", "on", "t") or v is True) else "0",
        "idle_timeout_enabled": lambda v: "1" if (str(v).lower() in ("1", "true", "yes", "on", "t") or v is True) else "0",
        "idle_timeout_duration_minutes": lambda v: str(max(1, int(v))),
        "session_timeout": lambda v: str(max(1, int(v))),
        "lockout_enabled": lambda v: "1" if (str(v).lower() in ("1", "true", "yes", "on", "t") or v is True) else "0",
        "max_failed_logins": lambda v: str(max(1, int(v))),
        "min_password_length": lambda v: str(max(4, int(v))),
        "password_expiry_days": lambda v: str(max(0, int(v))),
    }

    for key, formatter in mapping.items():
        if key in data:
            val_str = formatter(data[key])
            row = SystemSetting.query.get(key)
            if row:
                row.setting_value = val_str
            else:
                db.session.add(SystemSetting(setting_key=key, setting_value=val_str))
            updated_count += 1

            # Sync aliases
            if key in ("is_2fa_globally_enabled", "enforce_2fa_all_users"):
                for alias in ("is_2fa_globally_enabled", "enforce_2fa_all_users"):
                    al_row = SystemSetting.query.get(alias)
                    if al_row:
                        al_row.setting_value = val_str
                    else:
                        db.session.add(SystemSetting(setting_key=alias, setting_value=val_str))
            elif key in ("is_idle_timeout_enabled", "idle_timeout_enabled"):
                for alias in ("is_idle_timeout_enabled", "idle_timeout_enabled"):
                    al_row = SystemSetting.query.get(alias)
                    if al_row:
                        al_row.setting_value = val_str
                    else:
                        db.session.add(SystemSetting(setting_key=alias, setting_value=val_str))
            elif key in ("idle_timeout_duration_minutes", "session_timeout"):
                for alias in ("idle_timeout_duration_minutes", "session_timeout"):
                    al_row = SystemSetting.query.get(alias)
                    if al_row:
                        al_row.setting_value = val_str
                    else:
                        db.session.add(SystemSetting(setting_key=alias, setting_value=val_str))

    db.session.commit()
    log_audit(session.get("username"), "Updated", "Security", f"Admin master security settings updated ({updated_count} fields)")

    settings = get_security_settings()
    return jsonify({
        "ok": True,
        "success": True,
        "message": "System-wide master security settings updated successfully.",
        "settings": settings,
    })


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

    for key, value in d.items():
        clean_key = re.sub(r"[^a-zA-Z0-9_]", "", str(key))
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


# ---------------- Backups (Postgres/SQLite-portable dump) ----------------
def _generate_sql_dump() -> str:
    """Dumps every table's data as INSERT statements (portable text format,
    not a database-specific binary dump — works the same on SQLite/Postgres
    and can be re-imported with a simple script, unlike mysqldump-style
    CREATE TABLE dumps which are engine-specific)."""
    lines = [
        "-- BlotterCast database backup",
        f"-- Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"-- Engine: {db.engine.url.get_backend_name()}",
        "",
    ]
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    with db.engine.connect() as conn:
        for table in table_names:
            lines.append(f"-- Table: {table}")
            result = conn.execute(text(f'SELECT * FROM "{table}"'))
            columns = list(result.keys())
            rows = result.fetchall()
            for row in rows:
                values = []
                for v in row:
                    if v is None:
                        values.append("NULL")
                    elif isinstance(v, (int, float)):
                        values.append(str(v))
                    else:
                        escaped = str(v).replace("'", "''")
                        values.append(f"'{escaped}'")
                col_list = ", ".join(f'"{c}"' for c in columns)
                lines.append(f'INSERT INTO "{table}" ({col_list}) VALUES ({", ".join(values)});')
            lines.append("")
    return "\n".join(lines)


def _run_database_backup(triggered_by: str) -> dict:
    filename = f"blottercast-backup-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.sql"
    file_path = os.path.join(BACKUP_DIR, filename)

    success, err_msg = False, None
    try:
        sql = _generate_sql_dump()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(sql)
        success = os.path.isfile(file_path) and os.path.getsize(file_path) > 0
        if not success:
            err_msg = "Could not write backup file — check that the backup/ folder is writable."
    except Exception as e:
        err_msg = f"Backup failed: {e}"

    size = os.path.getsize(file_path) if success else 0
    status = "Success" if success else "Failed"

    db.session.add(SystemBackup(file_name=filename, size_bytes=size, status=status, created_by=triggered_by))
    db.session.commit()

    detail = f"Database backup created: {filename}" if success else "Database backup failed"
    log_audit(triggered_by, "Exported", "Backup", detail)

    return {"success": success, "file": filename, "size": size, "error": err_msg}


def _is_backup_due() -> bool:
    settings = _settings_map(["backup_frequency", "backup_time"])
    frequency = settings.get("backup_frequency", "Daily")

    last = SystemBackup.query.filter_by(status="Success").order_by(SystemBackup.created_at.desc()).first()
    if not last:
        return True

    interval_seconds = {"Every 12 hours": 12 * 3600, "Weekly": 7 * 24 * 3600}.get(frequency, 24 * 3600)
    elapsed = (datetime.utcnow() - last.created_at).total_seconds()
    return elapsed >= interval_seconds


def _auto_backup_check():
    if not _is_backup_due():
        return jsonify({"ran": False})
    result = _run_database_backup("system (automatic)")
    return jsonify({"ran": True, **result})


def _backup():
    result = _run_database_backup(session.get("username", "system"))
    if not result["success"]:
        return jsonify({"ok": False, "error": result["error"]}), 500
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
