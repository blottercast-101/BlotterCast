import os
import time
from datetime import datetime, timezone, timedelta

# Enforce system environment timezone to Asia/Manila (PST / UTC+8)
os.environ["TZ"] = "Asia/Manila"
if hasattr(time, "tzset"):
    try:
        time.tzset()
    except Exception:
        pass

# Philippine Standard Time (UTC+8)
try:
    from zoneinfo import ZoneInfo
    MANILA_TZ = ZoneInfo("Asia/Manila")
except Exception:
    MANILA_TZ = timezone(timedelta(hours=8), name="Asia/Manila")


def ph_now() -> datetime:
    """Return current datetime in Philippine Standard Time (UTC+8)."""
    return datetime.now(MANILA_TZ)


def ph_today():
    """Return today's date in Philippine Standard Time (UTC+8)."""
    return ph_now().date()


def ph_time():
    """Return current time in Philippine Standard Time (UTC+8) without microseconds."""
    return ph_now().time().replace(microsecond=0)
