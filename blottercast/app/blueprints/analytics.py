from datetime import datetime, timedelta
import json

from flask import Blueprint, jsonify, request
from sqlalchemy import extract, func

from ..extensions import db
from ..models import BlotterRecord, Incident, MlRun, Settlement, Zone
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


@bp.route("/api/public_stats.php", methods=["GET"])
def public_stats_router():
    """Unauthenticated stats for the marketing landing page (index.html) and
    the login page (login.html). Both pages hit this single endpoint so they
    can never drift apart — same source, same calculation, every time."""
    return _public_stats()


def _public_stats():
    # Archived blotter records are kept for recordkeeping but excluded from
    # every "active" count on these pages — same rule as the Blotter Records
    # module itself.
    blotter_count = BlotterRecord.query.filter_by(archived=False).count()
    incident_count = Incident.query.count()
    settlement_count = Settlement.query.count()
    overall_records = blotter_count + incident_count + settlement_count
    zones_monitored = Zone.query.count()

    run = MlRun.query.order_by(MlRun.id.desc()).first()

    ml_accuracy = None
    last_model_train = None
    risk_alert = None
    if run:
        last_model_train = run.trained_at.isoformat() if run.trained_at else None
        try:
            occ_metrics = json.loads(run.occurrence_metrics_json)
            active = occ_metrics.get(run.active_occurrence_model) or {}
            if "accuracy" in active:
                ml_accuracy = round(active["accuracy"] * 100)
        except (ValueError, TypeError, KeyError):
            ml_accuracy = None

        try:
            zone_rows = json.loads(run.hotspots_json)
            if zone_rows:
                top = max(zone_rows, key=lambda r: r.get("meanDailyProb", 0))
                p = top.get("meanDailyProb", 0)
                level = "High" if p >= 0.20 else "Moderate" if p >= 0.13 else "Low"
                risk_alert = {"zone": top.get("zone"), "level": level, "meanDailyProb": p}
        except (ValueError, TypeError, KeyError):
            risk_alert = None

    # System status: this endpoint responding at all proves the core app and
    # its DB connection are up (the query above would have raised otherwise).
    # The ML/prediction microservice is checked separately since it's a
    # distinct process that can be down independently.
    from .ml_proxy import _ml_is_running
    ml_up = _ml_is_running()

    return jsonify({
        "blotterCount": blotter_count,
        "overallRecords": overall_records,
        "zonesMonitored": zones_monitored,
        "mlAccuracy": ml_accuracy,
        "lastModelTrain": last_model_train,
        "riskAlert": risk_alert,
        "systemStatus": {
            "database": True,
            "core": True,
            "mlService": ml_up,
        },
    })


def _zones():
    rows = Zone.query.order_by(Zone.zone_id).all()
    return jsonify([{
        "zone_id": z.zone_id, "label": z.label,
        "lat": float(z.lat), "lng": float(z.lng), "weight": float(z.weight),
    } for z in rows])


def _dashboard():
    # Archived blotter records stay in the database but drop out of every
    # active-records view/stat, same as the Blotter Records module.
    blotter_count = BlotterRecord.query.filter_by(archived=False).count()
    incident_count = Incident.query.count()
    week_ago = datetime.utcnow().date() - timedelta(days=7)
    week_count = Incident.query.filter(Incident.incident_date >= week_ago).count()
    pending_stl = Settlement.query.filter_by(status="Pending").count()
    # Resolution rate spans every applicable case/record module, not just
    # incidents — a blotter case can be "Resolved" independently of any
    # linked incident report.
    resolved_incidents = Incident.query.filter(Incident.status.in_(["Resolved", "Closed"])).count()
    resolved_blotters = BlotterRecord.query.filter_by(status="Resolved", archived=False).count()
    resolvable_total = incident_count + blotter_count
    resolved_total = resolved_incidents + resolved_blotters
    res_rate = round(resolved_total / resolvable_total * 100) if resolvable_total > 0 else 0
    recent = (
        BlotterRecord.query.filter_by(archived=False)
        .order_by(BlotterRecord.date_filed.desc(), BlotterRecord.id.desc()).limit(8).all()
    )

    return jsonify({
        "blotterCount": blotter_count, "incidentCount": incident_count, "weekCount": week_count,
        "pendingSettlements": pending_stl, "resolutionRate": res_rate, "resolvedCount": resolved_total,
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
