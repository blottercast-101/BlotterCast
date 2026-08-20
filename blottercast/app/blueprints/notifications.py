import json
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, session

from ..extensions import db
from ..models import Incident, MlRun, Notification, NotificationRead, Settlement, SystemSetting
from ..permissions import json_error, login_required

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
    three_days_ago = datetime.utcnow().date() - timedelta(days=3)
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
            type="new_incident", title="High-priority incident reported",
            body=f"{r.report_no} at {r.location} ({r.zone_id})", severity="critical",
            link="incident.html", ref_table="incidents", ref_id=r.id,
        ))

    fourteen_days_ago = datetime.utcnow().date() - timedelta(days=14)
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
        body = r.case_no + (f" ({r.case_title})" if r.case_title else "") + " has been pending for 14+ days"
        db.session.add(Notification(
            type="settlement_overdue", title="Settlement follow-up overdue", body=body,
            severity="warning", link="settlement.html", ref_table="settlements", ref_id=r.id,
        ))

    threshold_row = SystemSetting.query.get("risk_threshold")
    threshold = (float(threshold_row.setting_value) if threshold_row else 75) / 100

    run = MlRun.query.order_by(MlRun.id.desc()).first()
    if run:
        hotspots = json.loads(run.hotspots_json) or []
        for h in hotspots:
            if h.get("meanDailyProb", 0) < threshold:
                continue
            zone = h.get("zone", "?")
            exists = Notification.query.filter(
                Notification.type == "high_risk_zone", Notification.ref_table == "ml_runs",
                Notification.ref_id == run.id, Notification.body.like(f"%{zone}%"),
            ).first()
            if exists:
                continue
            pct = round(h.get("meanDailyProb", 0) * 100)
            db.session.add(Notification(
                type="high_risk_zone", title="Elevated incident risk forecast",
                body=f"Zone {zone} is forecast at {pct}% daily incident probability, above the configured threshold",
                severity="warning", link="predictions.html", ref_table="ml_runs", ref_id=run.id,
            ))

    db.session.commit()


def _list():
    _generate_notifications()
    limit = min(50, max(1, int(request.args.get("limit", 20))))
    user_id = session.get("user_id")
    read_ids = {
        r.notification_id for r in NotificationRead.query.filter_by(user_id=user_id).all()
    }
    rows = Notification.query.order_by(Notification.created_at.desc()).limit(limit).all()
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
    read_ids = {r.notification_id for r in NotificationRead.query.filter_by(user_id=user_id).all()}
    total = Notification.query.count()
    count = total - Notification.query.filter(Notification.id.in_(read_ids)).count() if read_ids else total
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
