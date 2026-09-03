import json
import logging
import threading
from datetime import datetime, timedelta
from flask import current_app

from .extensions import db
from .models import Incident, MlRun, Notification, SystemSetting, Zone

logger = logging.getLogger(__name__)

OFFICIAL_ZONES = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Zone 6", "Zone 7"]

ANALYTICS_NOTIFICATION_TYPES = {
    "heatmap_alert",
    "heatmap_hotspot",
    "trend_alert",
    "trend_spike",
    "prediction_alert",
    "predictive_risk",
    "high_risk_zone",
    "analytics",
}


def is_encoder_role(role: str) -> bool:
    """Check if given role is a Data Encoder role."""
    if not role:
        return False
    r = str(role).strip().lower()
    return r in ("data encoder", "data_encoder", "encoder") or "encoder" in r


def get_eligible_analytics_users():
    """
    Returns active users eligible to receive analytics alerts.
    Strictly excludes users with the 'Data Encoder' role.
    """
    from .models import User
    users = User.query.filter(User.status == "Active").all()
    return [u for u in users if not is_encoder_role(u.role)]


def notify_analytics_change(alert_data):
    """
    Role-Filtered Recipient Dispatcher:
    - Filters target recipients to exclude 'Data Encoder'
    - Persists notification to database
    - Automatically marks notification as read for all Data Encoders to ensure
      their unread counters are never incremented.
    """
    eligible = get_eligible_analytics_users()
    if not eligible:
        logger.info("No active eligible users found for analytics notification.")

    title = alert_data.get("title", "")[:150]
    msg = (alert_data.get("body") or alert_data.get("message") or "")
    if len(msg) > 250:
        msg = msg[:247] + "..."

    notif = Notification(
        type=alert_data.get("type", "analytics"),
        title=title,
        body=msg[:255],
        severity=alert_data.get("severity", alert_data.get("priority", "info")).lower(),
        link=alert_data.get("link", alert_data.get("route", "")),
        ref_table=alert_data.get("ref_table", "incidents"),
        ref_id=alert_data.get("ref_id"),
    )
    db.session.add(notif)
    db.session.flush()

    # Mark as read for any Data Encoder users so their unread count remains 0
    from .models import NotificationRead, User
    all_users = User.query.all()
    for u in all_users:
        if is_encoder_role(u.role):
            if not NotificationRead.query.filter_by(user_id=u.id, notification_id=notif.id).first():
                db.session.add(NotificationRead(user_id=u.id, notification_id=notif.id))

    return notif


def calculate_zone_risk_forecast():
    """
    Evaluates current risk forecast for each of the 7 official zones.
    Returns a dict keyed by zone:
      {
         "Zone 1": {"level": "Low"|"Medium"|"Elevated"|"High", "prob": 0.12, "expectedCount14d": 1.5, "count": 2},
         ...
      }
    """
    now = datetime.utcnow().date()
    fourteen_days_ago = now - timedelta(days=14)

    # Count active incidents in the last 14 days per zone
    active_incidents = Incident.query.filter(
        (Incident.archived == False) | (Incident.archived == None),
        Incident.incident_date >= fourteen_days_ago,
        Incident.zone_id.in_(OFFICIAL_ZONES)
    ).all()

    total_incidents = len(active_incidents)
    zone_counts = {z: 0 for z in OFFICIAL_ZONES}
    for inc in active_incidents:
        if inc.zone_id in zone_counts:
            zone_counts[inc.zone_id] += 1

    max_count = max(zone_counts.values()) if zone_counts else 0

    # Retrieve latest ML Run if available
    ml_run = MlRun.query.order_by(MlRun.id.desc()).first()
    ml_hotspots = {}
    if ml_run and ml_run.hotspots_json:
        try:
            hotspot_list = json.loads(ml_run.hotspots_json) or []
            for h in hotspot_list:
                ml_hotspots[h.get("zone")] = h
        except Exception:
            ml_hotspots = {}

    forecasts = {}
    for zone in OFFICIAL_ZONES:
        cnt = zone_counts.get(zone, 0)
        ml_item = ml_hotspots.get(zone, {})
        pred_p = ml_item.get("meanDailyProb")
        if pred_p is None:
            pred_p = round((cnt / max(1, total_incidents)) * 0.45, 4) if total_incidents > 0 else 0.0

        exp_14d = ml_item.get("expectedCount14d", round(pred_p * 14, 2))

        # Determine level/tier
        if cnt == 0 and pred_p < 0.25:
            level = "Low"
        elif cnt >= max(4, int(max_count * 0.75)) or pred_p >= 0.75:
            level = "High"
        elif cnt >= max(2, int(max_count * 0.50)) or pred_p >= 0.50:
            level = "Elevated"
        elif cnt >= max(1, int(max_count * 0.25)) or pred_p >= 0.25:
            level = "Medium"
        else:
            level = "Low"

        forecasts[zone] = {
            "level": level,
            "tier": level,
            "prob": round(float(pred_p), 4),
            "expectedCount14d": exp_14d,
            "count": cnt,
        }

    return forecasts


def detect_weekly_category_surges():
    """
    Detects unusual surges in specific incident categories within a 7-day rolling window
    compared to the previous 7-day window.
    Returns list of dicts:
      [{"category": "Theft", "current": 4, "previous": 1, "percentage": 300}, ...]
    """
    now = datetime.utcnow().date()
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    # Active incidents in the last 14 days
    incidents_14d = Incident.query.filter(
        (Incident.archived == False) | (Incident.archived == None),
        Incident.incident_date >= fourteen_days_ago
    ).all()

    current_week_by_cat = {}
    prev_week_by_cat = {}

    for inc in incidents_14d:
        cat = inc.category or "Other"
        if inc.incident_date >= seven_days_ago:
            current_week_by_cat[cat] = current_week_by_cat.get(cat, 0) + 1
        else:
            prev_week_by_cat[cat] = prev_week_by_cat.get(cat, 0) + 1

    surges = []
    for cat, curr_cnt in current_week_by_cat.items():
        # Only evaluate if at least 2 incidents occurred this week
        if curr_cnt < 2:
            continue
        prev_cnt = prev_week_by_cat.get(cat, 0)
        if curr_cnt > prev_cnt:
            pct_increase = round(((curr_cnt - prev_cnt) / max(prev_cnt, 1)) * 100)
            if pct_increase >= 20:
                surges.append({
                    "category": cat,
                    "current": curr_cnt,
                    "previous": prev_cnt,
                    "percentage": pct_increase
                })

    return surges


def evaluate_trends_and_predictions():
    """
    Core change detection engine. Evaluates predictive shifts and trend spikes,
    dispatches notifications, and updates the historical baseline.
    """
    now_utc = datetime.utcnow()
    three_days_ago = now_utc - timedelta(days=3)

    # 1. Retrieve previous baseline risk levels
    setting_row = SystemSetting.query.get("purok_risk_levels")
    previous_risk = {}
    if setting_row and setting_row.setting_value:
        try:
            previous_risk = json.loads(setting_row.setting_value) or {}
        except Exception:
            previous_risk = {}

    # 2. Calculate current zone risk forecast
    current_risk = calculate_zone_risk_forecast()

    dispatched = []

    # 3. Detect critical predictive shift
    for zone, forecast in current_risk.items():
        prev_level = previous_risk.get(zone, {}).get("level", "Low")
        curr_level = forecast["level"]

        # Shift to High or Elevated from a lower baseline, or transition into High
        is_shift = (prev_level in ("Low", "Medium") and curr_level in ("High", "Elevated")) or (prev_level != curr_level and curr_level == "High")

        # Cooldown check: avoid duplicate alert for the same zone within 3 days
        recent_alert = Notification.query.filter(
            Notification.type.in_(["prediction_alert", "predictive_risk"]),
            Notification.title.like(f"%{zone}%"),
            Notification.created_at >= three_days_ago
        ).first()

        if is_shift and not recent_alert:
            title = f"Elevated Risk Forecast Alert: {zone}"
            msg = f"Predictive models project a significant increase in incidents for {zone} over the next 14 days ({curr_level} risk, {round(forecast['prob'] * 100)}% probability)."
            if len(msg) > 250:
                msg = msg[:247] + "..."

            notif = notify_analytics_change({
                "type": "prediction_alert",
                "title": title,
                "body": msg,
                "severity": "critical" if curr_level == "High" else "warning",
                "link": "predictions.html",
                "ref_table": "incidents",
                "ref_id": None,
            })
            if notif:
                dispatched.append(notif)

    # 4. Detect trend anomalies
    trend_spikes = detect_weekly_category_surges()
    for spike in trend_spikes:
        cat = spike["category"]
        pct = spike["percentage"]
        curr_cnt = spike["current"]
        prev_cnt = spike["previous"]

        # Cooldown check: avoid duplicate alert for this category within 3 days
        recent_spike_alert = Notification.query.filter(
            Notification.type.in_(["trend_alert", "trend_spike"]),
            Notification.title.like(f"%{cat}%"),
            Notification.created_at >= three_days_ago
        ).first()

        if not recent_spike_alert:
            title = f"Unusual Trend Spike Detected: {cat}"
            msg = f"{cat} incidents increased by {pct}% this week ({curr_cnt} vs {prev_cnt} prior week)."
            if len(msg) > 250:
                msg = msg[:247] + "..."

            notif = notify_analytics_change({
                "type": "trend_alert",
                "title": title,
                "body": msg,
                "severity": "warning" if pct < 60 else "critical",
                "link": "trends.html",
                "ref_table": "incidents",
                "ref_id": None,
            })
            if notif:
                dispatched.append(notif)

    # 5. Persist updated risk levels baseline
    try:
        if not setting_row:
            setting_row = SystemSetting(setting_key="purok_risk_levels", setting_value=json.dumps(current_risk))
            db.session.add(setting_row)
        else:
            setting_row.setting_value = json.dumps(current_risk)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving purok_risk_levels baseline: {e}")

    return {
        "current_risk": current_risk,
        "trend_spikes": trend_spikes,
        "dispatched_count": len(dispatched)
    }


def trigger_trend_and_prediction_check(async_mode=None):
    """
    Trigger alert dispatcher evaluation.
    If testing environment or async_mode is False, runs synchronously.
    Otherwise runs on a daemon thread with the application context.
    """
    app = None
    is_testing = False
    try:
        if current_app:
            app = current_app._get_current_object()
            is_testing = bool(app.config.get("TESTING"))
    except Exception:
        pass

    if async_mode is None:
        async_mode = not is_testing

    def _worker():
        if app:
            with app.app_context():
                try:
                    evaluate_trends_and_predictions()
                except Exception as ex:
                    logger.error(f"Background trend/prediction evaluation failed: {ex}")
        else:
            try:
                evaluate_trends_and_predictions()
            except Exception as ex:
                logger.error(f"Trend/prediction evaluation failed: {ex}")

    if async_mode:
        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t
    else:
        _worker()
        return None
