import json
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import extract, func

from ..extensions import db
from ..models import (
    BarangayClearance,
    BarangayNonResidency,
    BarangayResidency,
    BlotterRecord,
    CensusRecord,
    Incident,
    IndigencyCertificate,
    MlRun,
    Settlement,
    Zone,
)
from ..permissions import json_error, login_required, permission_required

bp = Blueprint("analytics", __name__)

OFFICIAL_ZONES = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Zone 6", "Zone 7"]


@bp.route("/api/analytics.php", methods=["GET"])
@bp.route("/api/analytics", methods=["GET"])
@bp.route("/api/analytics/dashboard", methods=["GET"])
@bp.route("/api/dashboard", methods=["GET"])
@login_required
def analytics_router():
    try:
        action = request.args.get("action", "")
        path = request.path.lower()
        if "dashboard" in path or action == "dashboard":
            return _dashboard()
        if "heatmap" in path or action == "heatmap":
            return _heatmap()
        if "zones" in path or action == "zones":
            return _zones()
        if "trends" in path or action == "trends":
            return _trends()
        if "zone-density" in path or "zone_density" in path or action in ("zone-density", "zone_density"):
            return _zone_density()
        if not action and ("analytics.php" in path or path.endswith("/analytics")):
            return _dashboard()
        return json_error("Unknown action", 404)
    except Exception as e:
        return json_error(f"Analytics query failed: {str(e)}", 500)


@bp.route("/api/analytics/zones", methods=["GET"])
@bp.route("/api/zones", methods=["GET"])
@login_required
def zones_direct():
    return _zones()


@bp.route("/api/analytics/heatmap", methods=["GET"])
@bp.route("/api/heatmap", methods=["GET"])
@login_required
def heatmap_direct():
    return _heatmap()


@bp.route("/api/analytics/zone-density", methods=["GET"])
@login_required
def zone_density_direct():
    """Direct REST endpoint for spatial occurrence densities and RF forecast weights."""
    return _zone_density()


@bp.route("/api/public_stats.php", methods=["GET"])
@bp.route("/api/public_stats", methods=["GET"])
@bp.route("/api/public-stats", methods=["GET"])
def public_stats_router():
    """Unauthenticated stats for the marketing landing page (index.html) and
    the login page (login.html). Both pages hit this single endpoint so they
    can never drift apart — same source, same calculation, every time."""
    try:
        return _public_stats()
    except Exception as e:
        return json_error(f"Failed to fetch public statistics: {str(e)}", 500)


def _public_stats():
    try:
        # Primary record counts across all modules
        # Active records only (archived records excluded)
        blotter_count = BlotterRecord.query.filter((BlotterRecord.archived == False) | (BlotterRecord.archived == None)).count()
        incident_count = Incident.query.filter((Incident.archived == False) | (Incident.archived == None)).count()
        settlement_count = Settlement.query.filter((Settlement.archived == False) | (Settlement.archived == None)).count()
        census_count = CensusRecord.query.filter((CensusRecord.archived == False) | (CensusRecord.archived == None)).count()

        # Issued certificates / documents
        clearance_count = BarangayClearance.query.count()
        residency_count = BarangayResidency.query.count()
        non_residency_count = BarangayNonResidency.query.count()
        indigency_count = IndigencyCertificate.query.count()
        docs_count = clearance_count + residency_count + non_residency_count + indigency_count

        overall_records = blotter_count + incident_count + settlement_count + census_count + docs_count
        zones_monitored = Zone.query.filter(Zone.zone_id.in_(OFFICIAL_ZONES)).count()

        run = MlRun.query.order_by(MlRun.id.desc()).first()

        ml_accuracy = None
        last_model_train = None
        risk_alert = None
        if run and run.record_count and run.record_count >= 10 and incident_count >= 10:
            last_model_train = (run.trained_at.isoformat() + "Z") if run.trained_at else None
            try:
                occ_metrics = json.loads(run.occurrence_metrics_json)
                active = occ_metrics.get(run.active_occurrence_model) or {}
                if "accuracy" in active and active["accuracy"] is not None:
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

        from .ml_proxy import _ml_is_running
        ml_up = _ml_is_running()

        return jsonify({
            "ok": True,
            "success": True,
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
            "stats": {
                "blotter_count": blotter_count,
                "incident_count": incident_count,
                "settlement_count": settlement_count,
                "census_count": census_count,
                "overall_records": overall_records,
            }
        })
    except Exception as e:
        return json_error(f"Error computing public stats: {str(e)}", 500)


def _zones():
    try:
        rows = Zone.query.filter(Zone.zone_id.in_(OFFICIAL_ZONES)).order_by(Zone.zone_id).all()
        return jsonify([{
            "zone_id": z.zone_id, "label": z.label,
            "lat": float(z.lat) if z.lat is not None else 0.0,
            "lng": float(z.lng) if z.lng is not None else 0.0,
            "weight": float(z.weight) if z.weight is not None else 1.0,
        } for z in rows])
    except Exception as e:
        return json_error(f"Error loading zones: {str(e)}", 500)


def _dashboard():
    try:
        blotter_count = BlotterRecord.query.filter((BlotterRecord.archived == False) | (BlotterRecord.archived == None)).count()
        incident_count = Incident.query.filter((Incident.archived == False) | (Incident.archived == None)).count()
        week_ago = datetime.utcnow().date() - timedelta(days=7)
        week_count = Incident.query.filter(
            Incident.incident_date >= week_ago,
            (Incident.archived == False) | (Incident.archived == None)
        ).count()
        
        # Priority and Investigation breakdowns
        high_priority_incidents = Incident.query.filter(
            Incident.priority.in_(["High", "Critical"]),
            (Incident.archived == False) | (Incident.archived == None)
        ).count()
        
        under_investigation = Incident.query.filter(
            Incident.status.in_(["Under Investigation", "Pending", "Open", "Elevated to Blotter"]),
            (Incident.archived == False) | (Incident.archived == None)
        ).count()

        pending_stl = Settlement.query.filter(
            Settlement.status.in_(["Pending", "Ongoing", "Under Mediation", "Hearing Scheduled"]),
            (Settlement.archived == False) | (Settlement.archived == None)
        ).count()

        resolved_incidents = Incident.query.filter(
            Incident.status.in_(["Resolved", "Closed", "Settled"]),
            (Incident.archived == False) | (Incident.archived == None)
        ).count()
        
        resolved_blotters = BlotterRecord.query.filter(
            BlotterRecord.status.in_(["Resolved", "Settled", "Complied", "Dismissed"]),
            (BlotterRecord.archived == False) | (BlotterRecord.archived == None)
        ).count()
        
        resolvable_total = incident_count + blotter_count
        resolved_total = resolved_incidents + resolved_blotters
        res_rate = round(resolved_total / resolvable_total * 100) if resolvable_total > 0 else 0
        
        recent = (
            BlotterRecord.query.filter((BlotterRecord.archived == False) | (BlotterRecord.archived == None))
            .order_by(BlotterRecord.date_filed.desc(), BlotterRecord.id.desc()).limit(8).all()
        )
        recent_blotter_data = []
        for r in recent:
            try:
                recent_blotter_data.append(r.to_dict())
            except Exception:
                recent_blotter_data.append({
                    "id": getattr(r, "id", None),
                    "docket_no": getattr(r, "docket_no", ""),
                    "date_filed": r.date_filed.isoformat() if getattr(r, "date_filed", None) else None,
                    "complainant": getattr(r, "complainant", ""),
                    "respondent": getattr(r, "respondent", ""),
                    "nature": getattr(r, "nature", ""),
                    "status": getattr(r, "status", "Pending"),
                    "zone_id": getattr(r, "zone_id", "Zone 1")
                })

        return jsonify({
            "ok": True,
            "success": True,
            "blotterCount": blotter_count,
            "incidentCount": incident_count,
            "weekCount": week_count,
            "pendingSettlements": pending_stl,
            "resolutionRate": res_rate,
            "resolvedCount": resolved_total,
            "recentBlotter": recent_blotter_data,
            "stats": {
                "total_reports": incident_count,
                "total_incidents": incident_count,
                "total_blotter": blotter_count,
                "high_priority": high_priority_incidents,
                "under_investigation": under_investigation,
                "week_count": week_count,
                "pending_settlements": pending_stl,
                "resolved_count": resolved_total,
                "resolution_rate": res_rate,
            }
        })
    except Exception as e:
        return json_error(f"Failed to aggregate dashboard metrics: {str(e)}", 500)


@permission_required("view_analytics")
def _heatmap_impl():
    try:
        q = Incident.query.filter((Incident.archived == False) | (Incident.archived == None)).filter(Incident.zone_id.in_(OFFICIAL_ZONES))
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
    except Exception as e:
        return json_error(f"Failed to fetch heatmap data: {str(e)}", 500)


def _heatmap():
    return _heatmap_impl()


@permission_required("view_analytics")
def _zone_density():
    """
    Computes unified spatial density and occurrence weights for the 7 official zones.
    Blends real database incident counts with the Random Forest model's occurrence forecast.
    """
    try:
        # 1. Base query on active incidents
        q = Incident.query.filter((Incident.archived == False) | (Incident.archived == None)).filter(Incident.zone_id.in_(OFFICIAL_ZONES))
        if request.args.get("from"):
            q = q.filter(Incident.incident_date >= request.args["from"])
        if request.args.get("to"):
            q = q.filter(Incident.incident_date <= request.args["to"])
        cat = request.args.get("category")
        if cat and cat != "all":
            q = q.filter(Incident.category == cat)

        # 2. Count incidents per zone
        incidents = q.all()
        total_incidents = len(incidents)
        zone_counts = {z: 0 for z in OFFICIAL_ZONES}
        for inc in incidents:
            if inc.zone_id in zone_counts:
                zone_counts[inc.zone_id] += 1

        # 3. Retrieve latest ML model run for predicted occurrence probabilities
        run = MlRun.query.order_by(MlRun.id.desc()).first()
        ml_zone_data = {}
        if run and run.record_count and run.record_count >= 10 and total_incidents >= 10:
            try:
                hotspots = json.loads(run.hotspots_json)
                for item in hotspots:
                    ml_zone_data[item.get("zone")] = item
            except (ValueError, TypeError, KeyError):
                ml_zone_data = {}

        # 4. Fetch zone definitions
        zone_defs = Zone.query.filter(Zone.zone_id.in_(OFFICIAL_ZONES)).order_by(Zone.zone_id).all()
        zone_label_map = {z.zone_id: z.label for z in zone_defs}

        max_count = max(zone_counts.values()) if zone_counts else 0

        results = []
        for zone_id in OFFICIAL_ZONES:
            count = zone_counts.get(zone_id, 0)
            ml_item = ml_zone_data.get(zone_id, {})
            pred_p = ml_item.get("meanDailyProb")
            if pred_p is None:
                pred_p = round((count / max(1, total_incidents)) * 0.45, 4) if total_incidents > 0 else 0.0

            exp_7d = ml_item.get("expectedCount7d", round(pred_p * 7, 2))
            exp_14d = ml_item.get("expectedCount14d", round(pred_p * 14, 2))

            # Determine dynamic tier
            if count == 0:
                tier = "Low"
                density_score = round(pred_p * 100, 1)
            elif count >= max(4, int(max_count * 0.75)):
                tier = "High"
                density_score = round(max(75.0, pred_p * 250), 1)
            elif count >= max(2, int(max_count * 0.50)):
                tier = "Elevated"
                density_score = round(max(50.0, pred_p * 200), 1)
            elif count >= max(1, int(max_count * 0.25)):
                tier = "Medium"
                density_score = round(max(25.0, pred_p * 150), 1)
            else:
                tier = "Low"
                density_score = round(pred_p * 100, 1)

            results.append({
                "zone_id": zone_id,
                "label": zone_label_map.get(zone_id, zone_id),
                "historicalCount": count,
                "predictedOccurrenceProb": round(float(pred_p), 4),
                "expectedCount7d": exp_7d,
                "expectedCount14d": exp_14d,
                "densityScore": density_score,
                "tier": tier,
                "topCategory": ml_item.get("topCategory", "N/A" if total_incidents == 0 else "Physical Assault"),
                "peakWindow": ml_item.get("peakWindow", "N/A" if total_incidents == 0 else "8PM–12AM"),
                "trend": ml_item.get("trend", "→"),
            })

        # Sort descending by predicted occurrence probability and historical count
        results.sort(key=lambda r: (-r["predictedOccurrenceProb"], -r["historicalCount"]))
        top_zone = results[0] if results else None

        return jsonify({
            "ok": True,
            "success": True,
            "totalIncidents": total_incidents,
            "topRiskZone": top_zone["zone_id"] if top_zone else "Zone 1",
            "zones": results,
        })
    except Exception as e:
        return json_error(f"Failed to compute zone density analytics: {str(e)}", 500)


@bp.route("/api/analytics/trends", methods=["GET"])
@bp.route("/api/trends.php", methods=["GET"])
@login_required
@permission_required("view_analytics")
def trends_direct():
    """Direct REST endpoint for comparative incident-to-blotter and settlement trends."""
    return _trends()


@permission_required("view_analytics")
def _trends_impl():
    try:
        MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        # 1. Available years
        years = [
            r[0] for r in
            db.session.query(extract("year", Incident.incident_date))
            .filter((Incident.archived == False) | (Incident.archived == None))
            .distinct()
            .order_by(extract("year", Incident.incident_date).desc()).all()
        ]
        years = [int(y) for y in years if y is not None]
        current_year = datetime.utcnow().year
        if not years:
            years = [current_year]
        year = int(request.args.get("year") or years[0])

        # 2. KPI Summary Aggregation
        total_incidents = Incident.query.filter(
            extract("year", Incident.incident_date) == year,
            (Incident.archived == False) | (Incident.archived == None)
        ).count()

        total_blottered = Incident.query.filter(
            extract("year", Incident.incident_date) == year,
            Incident.is_blotter == True,
            (Incident.archived == False) | (Incident.archived == None)
        ).count()

        prev_count = Incident.query.filter(
            extract("year", Incident.incident_date) == year - 1,
            (Incident.archived == False) | (Incident.archived == None)
        ).count()

        resolved_count = Incident.query.filter(
            extract("year", Incident.incident_date) == year,
            Incident.status.in_(["Resolved", "Closed", "Settled"]),
            (Incident.archived == False) | (Incident.archived == None)
        ).count()

        total_blotter_cases = BlotterRecord.query.filter(
            extract("year", BlotterRecord.date_filed) == year,
            (BlotterRecord.archived == False) | (BlotterRecord.archived == None)
        ).count()

        total_settled_blotters = BlotterRecord.query.filter(
            extract("year", BlotterRecord.date_filed) == year,
            BlotterRecord.status.in_(["Resolved", "Settled", "Complied", "Dismissed"]),
            (BlotterRecord.archived == False) | (BlotterRecord.archived == None)
        ).count()

        elevation_rate = round((total_blottered / max(1, total_incidents)) * 100, 1) if total_incidents > 0 else 0.0
        settlement_rate = round((total_settled_blotters / max(1, total_blotter_cases)) * 100, 1) if total_blotter_cases > 0 else 0.0
        resolution_rate = round((resolved_count / max(1, total_incidents)) * 100, 1) if total_incidents > 0 else 0.0

        # 3. Monthly Timeline (Total vs Elevated Blotters vs Resolved)
        monthly_incidents_raw = (
            db.session.query(extract("month", Incident.incident_date).label("m"), func.count().label("c"))
            .filter(extract("year", Incident.incident_date) == year, (Incident.archived == False) | (Incident.archived == None))
            .group_by("m").order_by("m").all()
        )
        inc_by_month = {int(r.m): int(r.c) for r in monthly_incidents_raw}

        monthly_blottered_raw = (
            db.session.query(extract("month", Incident.incident_date).label("m"), func.count().label("c"))
            .filter(extract("year", Incident.incident_date) == year, Incident.is_blotter == True, (Incident.archived == False) | (Incident.archived == None))
            .group_by("m").order_by("m").all()
        )
        blt_by_month = {int(r.m): int(r.c) for r in monthly_blottered_raw}

        monthly_resolved_raw = (
            db.session.query(extract("month", Incident.incident_date).label("m"), func.count().label("c"))
            .filter(extract("year", Incident.incident_date) == year, Incident.status.in_(["Resolved", "Closed", "Settled"]), (Incident.archived == False) | (Incident.archived == None))
            .group_by("m").order_by("m").all()
        )
        res_by_month = {int(r.m): int(r.c) for r in monthly_resolved_raw}

        timeline = []
        monthly_compat = []
        for m in range(1, 13):
            tot_m = inc_by_month.get(m, 0)
            blt_m = blt_by_month.get(m, 0)
            res_m = res_by_month.get(m, 0)
            m_name = MONTH_NAMES[m - 1]
            timeline.append({
                "m": m,
                "month_name": m_name,
                "total_incidents": tot_m,
                "blottered_count": blt_m,
                "resolved_count": res_m,
                "elevation_rate": round((blt_m / max(1, tot_m)) * 100, 1) if tot_m > 0 else 0.0,
                "c": tot_m,
            })
            monthly_compat.append({"m": m, "c": tot_m})

        # 4. Day of Week
        dates = [d[0] for d in db.session.query(Incident.incident_date).filter(
            extract("year", Incident.incident_date) == year, (Incident.archived == False) | (Incident.archived == None)
        ).all()]
        dow_counts = {}
        for d in dates:
            if d:
                mysql_dow = (d.isoweekday() % 7) + 1
                dow_counts[mysql_dow] = dow_counts.get(mysql_dow, 0) + 1
        dow_result = [{"d": k, "c": v} for k, v in sorted(dow_counts.items())]

        # 5. Category Breakdown with Elevation Rates
        cat_total_raw = (
            db.session.query(Incident.category, func.count().label("c"))
            .filter(extract("year", Incident.incident_date) == year, (Incident.archived == False) | (Incident.archived == None))
            .group_by(Incident.category).order_by(func.count().desc()).all()
        )
        cat_elevated_raw = (
            db.session.query(Incident.category, func.count().label("c"))
            .filter(extract("year", Incident.incident_date) == year, Incident.is_blotter == True, (Incident.archived == False) | (Incident.archived == None))
            .group_by(Incident.category).all()
        )
        elevated_by_cat = {r.category: int(r.c) for r in cat_elevated_raw}

        categories = []
        for r in cat_total_raw:
            cat_name = r.category
            c_count = int(r.c)
            elev_c = elevated_by_cat.get(cat_name, 0)
            c_rate = round((elev_c / max(1, c_count)) * 100, 1) if c_count > 0 else 0.0
            categories.append({
                "category": cat_name,
                "count": c_count,
                "c": c_count,
                "elevated_count": elev_c,
                "category_elevation_rate": c_rate,
            })

        # 6. Zonal Breakdown (Zone 1 to Zone 7)
        zone_defs = Zone.query.filter(Zone.zone_id.in_(OFFICIAL_ZONES)).order_by(Zone.zone_id).all()
        zone_label_map = {z.zone_id: z.label for z in zone_defs}

        zonal_total_raw = (
            db.session.query(Incident.zone_id, func.count().label("c"))
            .filter(extract("year", Incident.incident_date) == year, (Incident.archived == False) | (Incident.archived == None))
            .group_by(Incident.zone_id).all()
        )
        tot_by_zone = {r.zone_id: int(r.c) for r in zonal_total_raw}

        zonal_elevated_raw = (
            db.session.query(Incident.zone_id, func.count().label("c"))
            .filter(extract("year", Incident.incident_date) == year, Incident.is_blotter == True, (Incident.archived == False) | (Incident.archived == None))
            .group_by(Incident.zone_id).all()
        )
        elev_by_zone = {r.zone_id: int(r.c) for r in zonal_elevated_raw}

        zonal_resolved_raw = (
            db.session.query(Incident.zone_id, func.count().label("c"))
            .filter(extract("year", Incident.incident_date) == year, Incident.status.in_(["Resolved", "Closed", "Settled"]), (Incident.archived == False) | (Incident.archived == None))
            .group_by(Incident.zone_id).all()
        )
        res_by_zone = {r.zone_id: int(r.c) for r in zonal_resolved_raw}

        zonal = []
        for zid in OFFICIAL_ZONES:
            z_tot = tot_by_zone.get(zid, 0)
            z_elev = elev_by_zone.get(zid, 0)
            z_res = res_by_zone.get(zid, 0)
            z_rate = round((z_elev / max(1, z_tot)) * 100, 1) if z_tot > 0 else 0.0
            zonal.append({
                "zone_id": zid,
                "label": zone_label_map.get(zid, zid),
                "total_incidents": z_tot,
                "elevated_count": z_elev,
                "resolved_count": z_res,
                "elevation_rate": z_rate,
                "settlement_rate": round((z_res / max(1, z_tot)) * 100, 1) if z_tot > 0 else 0.0,
            })

        summary_obj = {
            "total_incidents": total_incidents,
            "total_blottered": total_blottered,
            "elevation_rate": elevation_rate,
            "total_blotter_cases": total_blotter_cases,
            "total_settled_blotters": total_settled_blotters,
            "lupon_settlement_rate": settlement_rate,
            "resolvedCount": resolved_count,
            "resolutionRate": resolution_rate,
            "prevYearTotal": prev_count,
        }

        return jsonify({
            "status": "success",
            "ok": True,
            "success": True,
            "years": years,
            "year": year,
            "summary": summary_obj,
            "timeline": timeline,
            "categories": categories,
            "zonal": zonal,
            "monthly": monthly_compat,
            "dayOfWeek": dow_result,
            "total": total_incidents,
            "prevYearTotal": prev_count,
            "resolvedCount": resolved_count,
            "resolutionRate": resolution_rate,
        })
    except Exception as e:
        return json_error(f"Failed to fetch trends data: {str(e)}", 500)


def _trends():
    return _trends_impl()
