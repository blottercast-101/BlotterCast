from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import extract, func

from ..extensions import db
from ..models import BlotterRecord, Incident, Settlement, Zone
from ..permissions import json_error, login_required, permission_required

bp = Blueprint("analytics", __name__)


@bp.route("/api/analytics.php", methods=["GET"])
@login_required
def analytics_router():
    action = request.args.get("action", "")
    if action == "zones":
        return _zones()
    if action == "dashboard":
        return _dashboard()
    if action == "heatmap":
        return _heatmap()
    if action == "trends":
        return _trends()
    return json_error("Unknown action", 404)


def _zones():
    rows = Zone.query.order_by(Zone.zone_id).all()
    return jsonify([{
        "zone_id": z.zone_id, "label": z.label,
        "lat": float(z.lat), "lng": float(z.lng), "weight": float(z.weight),
    } for z in rows])


def _dashboard():
    blotter_count = BlotterRecord.query.count()
    incident_count = Incident.query.count()
    week_ago = datetime.utcnow().date() - timedelta(days=7)
    week_count = Incident.query.filter(Incident.incident_date >= week_ago).count()
    pending_stl = Settlement.query.filter_by(status="Pending").count()
    resolved = Incident.query.filter(Incident.status.in_(["Resolved", "Closed"])).count()
    res_rate = round(resolved / incident_count * 100) if incident_count > 0 else 0
    recent = BlotterRecord.query.order_by(BlotterRecord.date_filed.desc(), BlotterRecord.id.desc()).limit(8).all()

    return jsonify({
        "blotterCount": blotter_count, "incidentCount": incident_count, "weekCount": week_count,
        "pendingSettlements": pending_stl, "resolutionRate": res_rate,
        "recentBlotter": [r.to_dict() for r in recent],
    })


@permission_required("view_analytics")
def _heatmap_impl():
    q = Incident.query
    if request.args.get("from"):
        q = q.filter(Incident.incident_date >= request.args["from"])
    if request.args.get("to"):
        q = q.filter(Incident.incident_date <= request.args["to"])
    cat = request.args.get("category")
    if cat and cat != "all":
        q = q.filter(Incident.category == cat)
    rows = q.order_by(Incident.incident_date.desc()).all()
    return jsonify([{
        "id": r.id, "incident_date": r.incident_date.isoformat() if r.incident_date else None,
        "zone_id": r.zone_id, "lat": float(r.lat) if r.lat is not None else None,
        "lng": float(r.lng) if r.lng is not None else None, "category": r.category,
        "priority": r.priority, "status": r.status, "location": r.location,
    } for r in rows])


def _heatmap():
    return _heatmap_impl()


@permission_required("view_analytics")
def _trends_impl():
    years = [
        r[0] for r in
        db.session.query(extract("year", Incident.incident_date)).distinct()
        .order_by(extract("year", Incident.incident_date).desc()).all()
    ]
    years = [int(y) for y in years if y is not None]
    year = int(request.args.get("year") or (years[0] if years else datetime.utcnow().year))

    monthly_rows = (
        db.session.query(extract("month", Incident.incident_date).label("m"), func.count().label("c"))
        .filter(extract("year", Incident.incident_date) == year).group_by("m").order_by("m").all()
    )
    dow_rows = (
        # SQLite/Postgres both support strftime('%w')/EXTRACT(dow) differently;
        # use Python-side grouping to stay portable across both backends.
        None
    )
    # Portable day-of-week aggregation: pull dates for the year, bucket in Python.
    dates = [d[0] for d in db.session.query(Incident.incident_date).filter(
        extract("year", Incident.incident_date) == year
    ).all()]
    dow_counts = {}
    for d in dates:
        # ISO weekday: Monday=1..Sunday=7 -> convert to MySQL DAYOFWEEK (Sunday=1..Saturday=7)
        mysql_dow = (d.isoweekday() % 7) + 1
        dow_counts[mysql_dow] = dow_counts.get(mysql_dow, 0) + 1
    dow_result = [{"d": k, "c": v} for k, v in sorted(dow_counts.items())]

    cat_rows = (
        db.session.query(Incident.category, func.count().label("c"))
        .filter(extract("year", Incident.incident_date) == year)
        .group_by(Incident.category).order_by(func.count().desc()).all()
    )

    total_count = Incident.query.filter(extract("year", Incident.incident_date) == year).count()
    prev_count = Incident.query.filter(extract("year", Incident.incident_date) == year - 1).count()
    resolved_count = Incident.query.filter(
        extract("year", Incident.incident_date) == year, Incident.status.in_(["Resolved", "Closed"])
    ).count()

    return jsonify({
        "years": years, "year": year,
        "monthly": [{"m": int(r.m), "c": r.c} for r in monthly_rows],
        "dayOfWeek": dow_result,
        "categories": [{"category": r.category, "c": r.c} for r in cat_rows],
        "total": total_count, "prevYearTotal": prev_count, "resolvedCount": resolved_count,
        "resolutionRate": round(resolved_count / total_count * 100) if total_count > 0 else 0,
    })


def _trends():
    return _trends_impl()
