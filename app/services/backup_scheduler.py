import logging
import threading
import time
from datetime import datetime, timedelta, timezone

from .backup_service import MANILA_TZ, run_database_backup

logger = logging.getLogger("backup_scheduler")

_app_instance = None
_scheduler_thread = None
_reschedule_event = threading.Event()
_is_running = False
_last_run_info = None
_next_run_time = None


def parse_schedule_settings(frequency: str, time_str: str) -> tuple:
    """Parses frequency and time string into hour and minute components."""
    try:
        parts = time_str.strip().split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
    except Exception:
        hour, minute = 2, 0  # Default: 02:00 AM

    return frequency or "Daily", hour, minute


def calculate_next_run(frequency: str, hour: int, minute: int) -> datetime:
    """Calculates next execution datetime in Asia/Manila (UTC+8) timezone."""
    now_manila = datetime.now(MANILA_TZ)
    target = now_manila.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if frequency == "Every 12 hours":
        # Check current target and target + 12h
        t1 = target
        t2 = target + timedelta(hours=12) if target.hour < 12 else target - timedelta(hours=12)
        candidates = [t for t in [t1, t2, t1 + timedelta(days=1), t2 + timedelta(days=1)] if t > now_manila]
        candidates.sort()
        return candidates[0] if candidates else now_manila + timedelta(hours=12)

    elif frequency == "Weekly":
        # Target Sunday
        days_ahead = (6 - now_manila.weekday()) % 7
        target = target + timedelta(days=days_ahead)
        if target <= now_manila:
            target += timedelta(days=7)
        return target

    elif frequency == "Monthly":
        # Target 1st day of month
        if target.day != 1:
            # Move to 1st of next month
            year = now_manila.year + 1 if now_manila.month == 12 else now_manila.year
            month = 1 if now_manila.month == 12 else now_manila.month + 1
            target = target.replace(year=year, month=month, day=1)
        elif target <= now_manila:
            year = now_manila.year + 1 if now_manila.month == 12 else now_manila.year
            month = 1 if now_manila.month == 12 else now_manila.month + 1
            target = target.replace(year=year, month=month, day=1)
        return target

    else:  # Daily (default)
        if target <= now_manila:
            target += timedelta(days=1)
        return target


def _worker_loop():
    global _last_run_info, _next_run_time, _is_running
    logger.info("[Backup Scheduler] Worker thread started in Asia/Manila timezone.")

    while _is_running:
        try:
            with _app_instance.app_context():
                from ..models import SystemSetting
                freq_row = SystemSetting.query.get("backup_frequency")
                time_row = SystemSetting.query.get("backup_time")
                frequency = freq_row.setting_value if freq_row else "Daily"
                time_str = time_row.setting_value if time_row else "02:00"

            freq, hour, minute = parse_schedule_settings(frequency, time_str)
            _next_run_time = calculate_next_run(freq, hour, minute)
            now_manila = datetime.now(MANILA_TZ)
            seconds_until_next = max(1, (_next_run_time - now_manila).total_seconds())

            logger.info(
                f"[Backup Scheduler] Next automated backup: {_next_run_time.strftime('%Y-%m-%d %I:%M %p')} PHT "
                f"({freq}, sleeping for {int(seconds_until_next)}s)"
            )

            # Wait until scheduled time or wake immediately if rescheduled by admin
            woken_early = _reschedule_event.wait(timeout=seconds_until_next)
            if woken_early:
                _reschedule_event.clear()
                logger.info("[Backup Scheduler] Settings changed. Rescheduling next job immediately.")
                continue

            if not _is_running:
                break

            # Execute scheduled backup
            logger.info("[Backup Scheduler] Cron triggered. Executing automated database backup...")
            with _app_instance.app_context():
                res = run_database_backup(triggered_by="system (automatic)")
                _last_run_info = {
                    "ran_at": datetime.now(MANILA_TZ).strftime("%Y-%m-%d %I:%M:%S %p PHT"),
                    "file": res.get("file"),
                    "size": res.get("size"),
                    "status": res.get("status"),
                    "cleaned": res.get("cleaned_old_backups"),
                }
                logger.info(f"[Backup Scheduler] Completed automated backup: {res.get('file')} ({res.get('status')})")

        except Exception as e:
            logger.error(f"[Backup Scheduler] Error in worker loop: {e}", exc_info=True)
            time.sleep(30)


def start_backup_scheduler(app):
    """Initializes and starts the autonomous background scheduler daemon."""
    global _app_instance, _scheduler_thread, _is_running
    _app_instance = app
    if _scheduler_thread is not None and _scheduler_thread.is_alive():
        return

    _is_running = True
    _scheduler_thread = threading.Thread(target=_worker_loop, daemon=True, name="BackupSchedulerThread")
    _scheduler_thread.start()


def reschedule_backup_job(app=None):
    """Signals the scheduler to immediately recalculate its next run using updated settings."""
    global _app_instance
    if app is not None:
        _app_instance = app
    _reschedule_event.set()


def get_scheduler_status() -> dict:
    """Returns the current status of the background scheduler."""
    return {
        "running": _is_running and _scheduler_thread is not None and _scheduler_thread.is_alive(),
        "timezone": "Asia/Manila (UTC+8)",
        "next_run": _next_run_time.strftime("%Y-%m-%d %I:%M %p PHT") if _next_run_time else None,
        "last_run": _last_run_info,
    }
