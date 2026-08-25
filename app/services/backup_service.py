import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import inspect, text

from ..extensions import db
from ..models import SystemBackup, SystemSetting
from ..permissions import log_audit

BACKUP_DIR = (
    os.path.join("/tmp", "backup")
    if os.environ.get("VERCEL")
    else os.path.join(os.path.dirname(__file__), "..", "..", "backup")
)
os.makedirs(BACKUP_DIR, exist_ok=True)

MANILA_TZ = timezone(timedelta(hours=8))


def generate_sql_dump() -> str:
    """Dumps every table's data as SQL INSERT statements."""
    lines = [
        "-- BlotterCast database backup",
        f"-- Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"-- Local (Asia/Manila): {datetime.now(MANILA_TZ).strftime('%Y-%m-%d %I:%M:%S %p')} PHT",
        f"-- Engine: {db.engine.url.get_backend_name()}",
        "",
    ]
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    with db.engine.connect() as conn:
        for table in table_names:
            lines.append(f'-- Table: {table}')
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


def cleanup_old_backups(retain_days: int = None) -> int:
    """Prunes backup files and history records older than retain_days (default 30 days)."""
    if retain_days is None:
        try:
            row = SystemSetting.query.get("retain_backups_days")
            retain_days = int(row.setting_value) if row and row.setting_value.isdigit() else 30
        except Exception:
            retain_days = 30

    cutoff_utc = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=retain_days)
    cleaned_count = 0

    # 1. Prune database records older than cutoff
    try:
        old_records = SystemBackup.query.filter(SystemBackup.created_at < cutoff_utc).all()
        for rec in old_records:
            # Delete corresponding file on disk if still present
            rec_path = os.path.join(BACKUP_DIR, rec.file_name)
            if os.path.isfile(rec_path):
                try:
                    os.remove(rec_path)
                except Exception:
                    pass
            db.session.delete(rec)
            cleaned_count += 1
        db.session.commit()
    except Exception as e:
        db.session.rollback()

    # 2. Prune any orphaned backup files on disk older than cutoff
    try:
        if os.path.isdir(BACKUP_DIR):
            for fname in os.listdir(BACKUP_DIR):
                if fname.startswith("blottercast-backup-") and fname.endswith(".sql"):
                    fpath = os.path.join(BACKUP_DIR, fname)
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                        if mtime < cutoff_utc:
                            os.remove(fpath)
                            cleaned_count += 1
                    except Exception:
                        pass
    except Exception:
        pass

    return cleaned_count


def run_database_backup(triggered_by: str = "system (automatic)", retain_days: int = None) -> dict:
    """Generates an SQL dump, saves it to storage, logs to database, and enforces retention policy."""
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    filename = f"blottercast-backup-{now_utc.strftime('%Y%m%d-%H%M%S')}.sql"
    file_path = os.path.join(BACKUP_DIR, filename)

    success, err_msg = False, None
    try:
        sql = generate_sql_dump()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(sql)
        success = os.path.isfile(file_path) and os.path.getsize(file_path) > 0
        if not success:
            err_msg = "Could not write backup file — check storage permissions."
    except Exception as e:
        err_msg = f"Backup error: {e}"

    size = os.path.getsize(file_path) if success else 0
    status = "Success" if success else "Failed"

    try:
        backup_record = SystemBackup(
            file_name=filename,
            size_bytes=size,
            status=status,
            created_by=triggered_by,
            created_at=now_utc,
        )
        db.session.add(backup_record)
        db.session.commit()

        detail = f"Database backup created: {filename} ({size} bytes)" if success else f"Database backup failed: {err_msg}"
        log_audit(triggered_by, "Exported" if success else "Failed", "Backup", detail)
    except Exception as db_err:
        db.session.rollback()

    # Enforce retention policy after successful backup
    cleaned_count = 0
    if success:
        cleaned_count = cleanup_old_backups(retain_days)

    return {
        "success": success,
        "ok": success,
        "file": filename,
        "size": size,
        "status": status,
        "by": triggered_by,
        "cleaned_old_backups": cleaned_count,
        "error": err_msg,
    }
