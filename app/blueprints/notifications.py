import json
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, session

from ..alert_dispatcher import (
    ANALYTICS_NOTIFICATION_TYPES,
    evaluate_trends_and_predictions,
    is_encoder_role,
)
from ..extensions import db
from ..models import Incident, MlRun, Notification, NotificationRead, Settlement, SystemSetting
from ..permissions import json_error, login_required, role_can

bp = Blueprint("notifications", __name__)


@bp.route("/api/notifications.php", methods=["GET", "POST"])
@login_required
def notifications_router():
    action = request.args.get("action", "")
    method = request.method
    if action == "list" and method == "GET":
        return _list()
    if action == "unread_count" and method == "GET":
        return _unread_count()
    if action == "mark_read" and method == "POST":
        return _mark_read()
    if action == "mark_all_read" and method == "POST":
        return _mark_all_read()
    return json_error("Unknown action", 404)


def _generate_notifications():
    # Evaluate reactive predictive shifts and category trend spikes
    try:
        evaluate_trends_and_predictions()
    except Exception as e:
        pass

    now_utc = datetime.utcnow()
    three_days_ago = now_utc.date() - timedelta(days=3)
    seven_days_ago = now_utc.date() - timedelta(days=7)
    fourteen_days_ago = now_utc.date() - timedelta(days=14)

    # 1. High-Priority Incidents
    already_alerted = {
        n.ref_id for n in Notification.query.filter_by(type="new_incident", ref_table="incidents").all()
        if n.ref_id is not None
    }
    high_priority = Incident.query.filter(
        Incident.priority == "High", Incident.incident_date >= three_days_ago
    ).all()
    for r in high_priority:
        if r.id in already_alerted:
            continue
        db.session.add(Notification(
            type="new_incident", title=f"High-Priority Incident: {r.report_no}",
            body=f"{r.report_no} • {r.category} at {r.location} ({r.zone_id})", severity="critical",
            link=f"incident.html?highlight={r.report_no}", ref_table="incidents", ref_id=r.id,
        ))

    # 2. Overdue Settlements (14+ days pending)
    already_alerted_stl = {
        n.ref_id for n in Notification.query.filter_by(type="settlement_overdue", ref_table="settlements").all()
        if n.ref_id is not None
    }
    overdue = Settlement.query.filter(
        Settlement.status == "Pending", Settlement.date_filed <= fourteen_days_ago
    ).all()
    for r in overdue:
        if r.id in already_alerted_stl:
            continue
        body = r.case_no + (f" ({r.case_title})" if r.case_title else "") + " has been pending settlement for 14+ days."
        db.session.add(Notification(
            type="settlement_overdue", title="Settlement Follow-Up Overdue", body=body,
            severity="warning", link=f"settlement.html?highlight={r.case_no}", ref_table="settlements", ref_id=r.id,
        ))

    # 3. Heatmap / Geospatial Hotspot Alerts
    recent_zone_counts = db.session.query(
        Incident.zone_id, db.func.count(Incident.id)
    ).filter(
        Incident.incident_date >= fourteen_days_ago
    ).group_by(Incident.zone_id).all()

    for zone_id, cnt in recent_zone_counts:
        if not zone_id or cnt < 2:
            continue
        # Check if an alert for this zone was already generated recently
        recent_notif = Notification.query.filter(
            Notification.type == "heatmap_hotspot",
            Notification.title.like(f"%{zone_id}%"),
            Notification.created_at >= (now_utc - timedelta(days=3))
        ).first()
        if not recent_notif:
            db.session.add(Notification(
                type="heatmap_hotspot",
                title=f"Geospatial Hotspot Alert: {zone_id}",
                body=f"High incident cluster detected in {zone_id} ({cnt} incidents recorded in the last 14 days). Increased patrol presence recommended.",
                severity="critical" if cnt >= 4 else "warning",
                link="heatmap.html",
                ref_table="incidents",
                ref_id=None,
            ))

    # 4. Predictive ML Analytics (High-Risk Zone Forecasts)
    threshold_row = SystemSetting.query.get("risk_threshold")
    threshold = (float(threshold_row.setting_value) if threshold_row else 75) / 100

    run = MlRun.query.order_by(MlRun.id.desc()).first()
    if run:
        try:
            hotspots = json.loads(run.hotspots_json) or []
            for h in hotspots:
                mean_prob = h.get("meanDailyProb", 0)
                if mean_prob < threshold:
                    continue
                zone = h.get("zone", "?")
                exists = Notification.query.filter(
                    Notification.type.in_(["high_risk_zone", "predictive_risk"]),
                    Notification.ref_table == "ml_runs",
                    Notification.ref_id == run.id,
                    Notification.body.like(f"%{zone}%"),
                ).first()
                if exists:
                    continue
                pct = round(mean_prob * 100)
                db.session.add(Notification(
                    type="predictive_risk",
                    title=f"Forecasted Incident Spike: Zone {zone}",
                    body=f"ML model forecasts elevated incident probability ({pct}%) in Zone {zone}, exceeding the threshold.",
                    severity="critical" if pct >= 80 else "warning",
                    link="predictions.html",
                    ref_table="ml_runs",
                    ref_id=run.id,
                ))
        except Exception:
            pass

    # 5. Trend Analysis (Week-over-Week & Category Surges)
    curr_week_count = Incident.query.filter(
        Incident.incident_date >= seven_days_ago
    ).count()
    prev_week_count = Incident.query.filter(
        Incident.incident_date >= fourteen_days_ago,
        Incident.incident_date < seven_days_ago
    ).count()

    if curr_week_count >= 2 and curr_week_count > prev_week_count:
        pct_increase = round(((curr_week_count - prev_week_count) / max(prev_week_count, 1)) * 100)
        if pct_increase >= 20:
            recent_trend_notif = Notification.query.filter(
                Notification.type == "trend_spike",
                Notification.created_at >= (now_utc - timedelta(days=3))
            ).first()
            if not recent_trend_notif:
                db.session.add(Notification(
                    type="trend_spike",
                    title=f"Incident Trend Surge (+{pct_increase}% WoW)",
                    body=f"Incident volume rose by {pct_increase}% this week ({curr_week_count} incidents vs {prev_week_count} prior week). Review trend breakdown.",
                    severity="warning",
                    link="trends.html",
                    ref_table="incidents",
                    ref_id=None,
                ))

    db.session.commit()


def _list():
    _generate_notifications()
    limit = min(50, max(1, int(request.args.get("limit", 20))))
    user_id = session.get("user_id")
    role = session.get("role", "")
    is_encoder = is_encoder_role(role) or not role_can(role, "view_analytics")

    read_ids = {
        r.notification_id for r in NotificationRead.query.filter_by(user_id=user_id).all()
    }
    q = Notification.query
    if is_encoder:
        q = q.filter(~Notification.type.in_(ANALYTICS_NOTIFICATION_TYPES))

    rows = q.order_by(Notification.created_at.desc()).limit(limit).all()
    return jsonify([{
        "id": n.id, "type": n.type, "title": n.title, "body": n.body, "severity": n.severity,
        "link": n.link, "ref_table": n.ref_table, "ref_id": n.ref_id,
        # Naive UTC — "Z" suffix so timeAgo()'s elapsed-time math on the
        # frontend isn't off by the viewer's own UTC offset.
        "created_at": (n.created_at.isoformat() + "Z") if n.created_at else None,
        "is_read": n.id in read_ids,
    } for n in rows])


def _unread_count():
    _generate_notifications()
    user_id = session.get("user_id")
    role = session.get("role", "")
    is_encoder = is_encoder_role(role) or not role_can(role, "view_analytics")

    read_ids = {r.notification_id for r in NotificationRead.query.filter_by(user_id=user_id).all()}
    q = Notification.query
    if is_encoder:
        q = q.filter(~Notification.type.in_(ANALYTICS_NOTIFICATION_TYPES))

    total = q.count()
    count = total - q.filter(Notification.id.in_(read_ids)).count() if read_ids else total
    return jsonify({"count": count})


def _mark_read():
    nid = int(request.args.get("id", 0))
    if not nid:
        return json_error("id required")
    user_id = session.get("user_id")
    if not NotificationRead.query.filter_by(user_id=user_id, notification_id=nid).first():
        db.session.add(NotificationRead(user_id=user_id, notification_id=nid))
        db.session.commit()
    return jsonify({"ok": True})


def _mark_all_read():
    user_id = session.get("user_id")
    already = {r.notification_id for r in NotificationRead.query.filter_by(user_id=user_id).all()}
    all_ids = [n.id for n in Notification.query.with_entities(Notification.id).all()]
    for nid in all_ids:
        if nid not in already:
            db.session.add(NotificationRead(user_id=user_id, notification_id=nid))
    db.session.commit()
    return jsonify({"ok": True})
