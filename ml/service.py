"""
BlotterCast ML Microservice
============================
Flask microservice serving real scikit-learn predictive analytics models:
  1. Incident Occurrence Classification  -> Random Forest (Accuracy)
  2. Multi-Class Incident Type Forecast   -> Gradient Boosting (Macro F1)
  3. Spatial Hotspot Risk Categorization   -> Gradient Boosting (Accuracy)

Synchronized with live database records, in-memory singleton for fast inference,
and joblib disk serialization for warm restarts.
"""

import json as _json
import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text

try:
    from .engine import (
        OFFICIAL_ZONES,
        CATEGORIES,
        build_spatiotemporal_panel,
        train_occurrence_model,
        train_type_model,
        train_hotspot_model,
        build_category_probability_cache,
        compute_zone_forecasts,
        predict_top_category,
        compute_peak_window,
        compute_14d_trend,
    )
except (ImportError, ValueError):
    from engine import (
        OFFICIAL_ZONES,
        CATEGORIES,
        build_spatiotemporal_panel,
        train_occurrence_model,
        train_type_model,
        train_hotspot_model,
        build_category_probability_cache,
        compute_zone_forecasts,
        predict_top_category,
        compute_peak_window,
        compute_14d_trend,
    )

# Standardized 7 official zones of Barangay Mapulang Lupa
ZONES = OFFICIAL_ZONES

_DEFAULT_SQLITE = "sqlite:///" + os.path.join(os.path.dirname(__file__), "..", "instance", "blottercast.db")


def _normalize_db_url(url: str) -> str:
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


DATABASE_URL = _normalize_db_url(os.environ.get("DATABASE_URL", _DEFAULT_SQLITE))
db_engine = create_engine(DATABASE_URL, pool_pre_ping=True)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

# ---------------------------------------------------------------
# In-Memory Singleton Registry (Kept warm in RAM)
# ---------------------------------------------------------------
ml_models = {
    "occurrence": None,          # RandomForestClassifier
    "occurrence_cols": None,     # List of feature columns
    "occurrence_threshold": 0.5,
    "occurrence_metrics": None,
    "hotspot": None,             # GradientBoostingClassifier
    "hotspot_cols": None,
    "hotspot_metrics": None,
    "type": None,                # GradientBoostingClassifier (multi-class)
    "type_cols": None,
    "type_metrics": None,
    "type_cat_cache": {},        # (zone, dow) -> category probability vector
    "cached_latest": None,       # Latest evaluated response payload
    "trained_at": None,
    "record_count": 0,
}

app = Flask(__name__)
CORS(app, supports_credentials=True)


def _save_models_to_disk():
    """Serialize in-memory models and metadata to disk using joblib for instant cold-starts."""
    try:
        os.makedirs(MODELS_DIR, exist_ok=True)
        joblib_path = os.path.join(MODELS_DIR, "incident_models.joblib")
        joblib.dump({
            "occurrence": ml_models["occurrence"],
            "occurrence_cols": ml_models["occurrence_cols"],
            "occurrence_threshold": ml_models["occurrence_threshold"],
            "occurrence_metrics": ml_models["occurrence_metrics"],
            "hotspot": ml_models["hotspot"],
            "hotspot_cols": ml_models["hotspot_cols"],
            "hotspot_metrics": ml_models["hotspot_metrics"],
            "type": ml_models["type"],
            "type_cols": ml_models["type_cols"],
            "type_metrics": ml_models["type_metrics"],
            "type_cat_cache": ml_models["type_cat_cache"],
            "cached_latest": ml_models["cached_latest"],
            "trained_at": ml_models["trained_at"],
            "record_count": ml_models["record_count"],
        }, joblib_path, compress=3)
    except Exception as e:
        print(f"[ML Singleton] Failed to persist models to disk: {e}")


def clear_models_and_cache():
    """Atomically clears all in-memory ML models and cached responses."""
    ml_models.update({
        "occurrence": None,
        "occurrence_cols": None,
        "occurrence_threshold": 0.5,
        "occurrence_metrics": None,
        "hotspot": None,
        "hotspot_cols": None,
        "hotspot_metrics": None,
        "type": None,
        "type_cols": None,
        "type_metrics": None,
        "type_cat_cache": {},
        "cached_latest": None,
        "trained_at": None,
        "record_count": 0,
    })
    joblib_path = os.path.join(MODELS_DIR, "incident_models.joblib")
    if os.path.isfile(joblib_path):
        try:
            os.remove(joblib_path)
        except Exception:
            pass


def get_active_incident_count() -> int:
    """Returns the live count of active, non-archived incident records."""
    try:
        with db_engine.connect() as conn:
            cnt_res = conn.execute(text("SELECT COUNT(*) FROM incidents WHERE archived = FALSE OR archived IS NULL"))
            return int(cnt_res.scalar() or 0)
    except Exception as e:
        print(f"[ML Service] Error querying active incident count: {e}")
        return 0


def preload_models_and_cache():
    """Preload trained models and cached forecast ONCE on startup, verifying live database records."""
    live_count = get_active_incident_count()
    if live_count < 10:
        clear_models_and_cache()
        print(f"[ML Singleton] Live database incident count is {live_count} (< 10 threshold). Initialized empty state.")
        return

    joblib_path = os.path.join(MODELS_DIR, "incident_models.joblib")
    if os.path.isfile(joblib_path):
        try:
            data = joblib.load(joblib_path)
            if data.get("record_count", 0) >= 10:
                ml_models.update(data)
                ml_models["record_count"] = live_count
                print(f"[ML Singleton] Preloaded warm models from disk (trained at {ml_models.get('trained_at')})")
                return
        except Exception as e:
            print(f"[ML Singleton] Could not load saved joblib models: {e}")

    # Fallback to database if disk artifact is not present
    try:
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM ml_runs ORDER BY id DESC LIMIT 1"))
            row = result.mappings().first()
            if row and row['record_count'] >= 10:
                trained_at = row['trained_at']
                trained_at_str = (trained_at.isoformat() + 'Z') if hasattr(trained_at, 'isoformat') else str(trained_at)
                occ_m = _json.loads(row['occurrence_metrics_json'])
                type_m = _json.loads(row['type_metrics_json'])
                hot_m = _json.loads(row['hotspot_metrics_json'])
                zone_r = _json.loads(row['hotspots_json'])

                ml_models["cached_latest"] = {
                    'ok': True,
                    'recordCount': live_count,
                    'record_count': live_count,
                    'occurrence': {'metrics': occ_m, 'active': row['active_occurrence_model']},
                    'type': {'metrics': type_m, 'active': row['active_type_model']},
                    'hotspot': {'metrics': hot_m, 'active': row['active_hotspot_model']},
                    'zoneRisk': zone_r,
                    'trainedAt': trained_at_str,
                }
                ml_models["trained_at"] = trained_at_str
                ml_models["record_count"] = live_count
                print("[ML Singleton] Preloaded latest run from database into in-memory cache.")
    except Exception as e:
        print(f"[ML Singleton] Startup DB preloading skipped: {e}")


# Initialize warm models immediately on import
preload_models_and_cache()


def load_incidents() -> pd.DataFrame:
    """Loads active, verified incident reports from the database with PostgreSQL boolean compatibility."""
    try:
        with db_engine.connect() as conn:
            df = pd.read_sql(
                text(
                    "SELECT id, incident_date AS date, time_reported, zone_id AS zone, hour, category, priority, status "
                    "FROM incidents WHERE archived = FALSE OR archived IS NULL ORDER BY incident_date"
                ),
                conn,
            )
        if not df.empty:
            df = df.dropna(subset=['date', 'zone']).copy()
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date']).copy()
            df = df[df['zone'].isin(ZONES)].copy()
            df['category'] = df['category'].fillna('Physical Assault').astype(str).str.strip()
            df = df[df['category'] != ''].copy()
            # Filter out non-incident case classifications / legacy dispute markers
            excluded = {'civil', 'crim', 'criminal', 'neighborhood dispute', 'other', 'others', 'neighborhood dispute (others)', 'unknown', 'none'}
            df = df[~df['category'].str.lower().isin(excluded)].copy()
            df['hour'] = pd.to_numeric(df['hour'], errors='coerce').fillna(12).astype(int)
        return df
    except Exception as e:
        print(f"[ML Service] Database load_incidents error: {e}")
        return pd.DataFrame()


@app.route('/', methods=['GET', 'HEAD'])
def root_health():
    is_warm = (
        ml_models['occurrence'] is not None or
        (ml_models['cached_latest'] is not None and ml_models.get('record_count', 0) >= 10)
    )
    return jsonify({
        'ok': True,
        'status': 'ok',
        'service': 'blottercast-ml',
        'isWarm': is_warm,
        'time': datetime.now().isoformat(),
    }), 200


@app.route('/health', methods=['GET', 'HEAD'])
def health():
    is_warm = (
        ml_models['occurrence'] is not None or
        (ml_models['cached_latest'] is not None and ml_models.get('record_count', 0) >= 10)
    )
    return jsonify({
        'ok': True,
        'status': 'healthy',
        'service': 'blottercast-ml',
        'isWarm': is_warm,
        'time': datetime.now().isoformat(),
    }), 200


@app.route('/train', methods=['POST'])
@app.route('/api/ml/retrain', methods=['POST'])
def train():
    try:
        df = load_incidents()
        rec_count = int(len(df))
        if rec_count < 10:
            clear_models_and_cache()
            return jsonify({
                'ok': False,
                'status': 'insufficient_data',
                'record_count': rec_count,
                'recordCount': rec_count,
                'message': 'Not enough incident records to generate predictions.',
            }), 200

        panel = build_spatiotemporal_panel(df)
        if panel.empty or len(panel) < 10:
            clear_models_and_cache()
            return jsonify({
                'ok': False,
                'status': 'insufficient_data',
                'record_count': rec_count,
                'recordCount': rec_count,
                'message': 'Not enough incident records to generate predictions.',
            }), 200

        # 1. Task 1: Incident Occurrence (Random Forest) -> Evaluates Accuracy: (TP + TN) / (TP + TN + FP + FN)
        occ_metrics, occ_model, occ_cols = train_occurrence_model(panel)

        # 2. Task 2: Incident Type (Gradient Boosting) -> Evaluates Macro F1: 2 * (Prec * Rec) / (Prec + Rec)
        type_metrics, type_model, type_cols = train_type_model(df)

        # 3. Task 3: Hotspot Spatial Risk (Gradient Boosting) -> Evaluates Spatial Classification Accuracy
        hot_metrics, hot_model, hot_cols = train_hotspot_model(panel)

        # Precompute multi-class category distribution vectors
        cat_cache = build_category_probability_cache(type_model, type_cols)

        # Generate 7-day and 14-day dynamic forecasts for all 7 zones
        zone_rows = compute_zone_forecasts(
            panel=panel,
            hotspot_model=hot_model,
            hotspot_cols=hot_cols,
            type_model=type_model,
            type_cols=type_cols,
            cat_cache=cat_cache,
            raw_df=df,
            horizon=14
        )

        trained_at = datetime.now(timezone.utc)
        trained_at_iso = trained_at.isoformat()

        occ_results = {'random_forest': occ_metrics}
        type_results = {'gradient_boosting': type_metrics}
        hot_results = {'gradient_boosting': hot_metrics}

        type_f1_score = type_metrics.get('incident_type_f1') or type_metrics.get('macro_f1')
        if type_f1_score is None and type_metrics.get('macroF1') is not None:
            type_f1_score = round(float(type_metrics.get('macroF1', 0.0) * 100), 1)

        response_payload = {
            'ok': True,
            'status': 'success',
            'recordCount': rec_count,
            'record_count': rec_count,
            'records_evaluated': rec_count,
            'metrics': {
                'incident_type_f1': type_f1_score,
                'macro_f1': type_f1_score,
                'f1_score': type_f1_score,
                'occurrence_accuracy': occ_metrics.get('accuracy'),
                'hotspot_accuracy': hot_metrics.get('accuracy'),
            },
            'incident_type_f1': type_f1_score,
            'macro_f1': type_f1_score,
            'occurrence': {
                'metrics': occ_results,
                'active': 'random_forest',
                'meta': {
                    'accuracy': occ_metrics.get('accuracy'),
                    'f1': occ_metrics.get('f1'),
                    'auc': occ_metrics.get('auc'),
                    'bestThreshold': occ_metrics.get('threshold'),
                }
            },
            'type': {
                'metrics': type_results,
                'active': 'gradient_boosting',
                'meta': {
                    'macroF1': type_metrics.get('macroF1'),
                    'macro_f1': type_f1_score,
                    'weightedF1': type_metrics.get('weightedF1'),
                    'f1': type_metrics.get('f1'),
                    'f1_score': type_metrics.get('f1_score'),
                    'incident_type_f1': type_f1_score,
                    'accuracy': type_metrics.get('accuracy'),
                }
            },
            'hotspot': {
                'metrics': hot_results,
                'active': 'gradient_boosting',
                'meta': {
                    'accuracy': hot_metrics.get('accuracy'),
                    'f1': hot_metrics.get('f1'),
                }
            },
            'zoneRisk': zone_rows,
            'trainedAt': trained_at_iso,
        }

        # Update in-memory warm singleton atomically
        ml_models["occurrence"] = occ_model
        ml_models["occurrence_cols"] = occ_cols
        ml_models["occurrence_threshold"] = occ_metrics.get('threshold', 0.5)
        ml_models["occurrence_metrics"] = occ_metrics
        ml_models["hotspot"] = hot_model
        ml_models["hotspot_cols"] = hot_cols
        ml_models["hotspot_metrics"] = hot_metrics
        ml_models["type"] = type_model
        ml_models["type_cols"] = type_cols
        ml_models["type_metrics"] = type_metrics
        ml_models["type_cat_cache"] = cat_cache
        ml_models["cached_latest"] = response_payload
        ml_models["trained_at"] = trained_at_iso
        ml_models["record_count"] = rec_count

        # Persist serialized model artifacts to disk
        _save_models_to_disk()

        # Cache run to database
        try:
            with db_engine.begin() as conn:
                conn.execute(
                    text(
                        """INSERT INTO ml_runs
                           (trained_at, record_count, active_occurrence_model, active_type_model, active_hotspot_model,
                            occurrence_metrics_json, type_metrics_json, hotspot_metrics_json, hotspots_json)
                           VALUES (:trained_at, :record_count, :active_occurrence, :active_type, :active_hotspot,
                                    :occ_json, :type_json, :hot_json, :hotspots_json)"""
                    ),
                    {
                        "trained_at": trained_at,
                        "record_count": rec_count,
                        "active_occurrence": "random_forest",
                        "active_type": "gradient_boosting",
                        "active_hotspot": "gradient_boosting",
                        "occ_json": _json.dumps(occ_results),
                        "type_json": _json.dumps(type_results),
                        "hot_json": _json.dumps(hot_results),
                        "hotspots_json": _json.dumps(zone_rows),
                    },
                )
        except Exception as e:
            print(f"[ML Service] Could not log ml_run to DB: {e}")

        return jsonify(response_payload), 200

    except Exception as e:
        print(f"[ML Service] Training exception: {e}")
        return jsonify({
            'ok': False,
            'status': 'error',
            'message': f'ML pipeline error: {str(e)}',
        }), 500


@app.route('/latest', methods=['GET'])
@app.route('/insights', methods=['GET'])
@app.route('/api/predict/insights', methods=['GET'])
@app.route('/api/heatmap/risk-zones', methods=['GET'])
def latest():
    """Returns the evaluated model insights and forecasts directly from memory or database fallback."""
    live_count = get_active_incident_count()
    if live_count < 10:
        clear_models_and_cache()
        return jsonify({
            'ok': False,
            'status': 'insufficient_data',
            'record_count': live_count,
            'recordCount': live_count,
            'message': 'Not enough incident records to generate predictions.',
        }), 200

    if ml_models["cached_latest"] is not None and ml_models.get("record_count", 0) >= 10:
        payload = dict(ml_models["cached_latest"])
        payload['record_count'] = live_count
        payload['recordCount'] = live_count
        return jsonify(payload), 200

    # Fallback to database lookup if memory is uninitialized
    try:
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM ml_runs ORDER BY id DESC LIMIT 1"))
            row = result.mappings().first()
        if row and row['record_count'] >= 10:
            trained_at = row['trained_at']
            trained_at_str = (trained_at.isoformat() + 'Z') if hasattr(trained_at, 'isoformat') else str(trained_at)
            type_m = _json.loads(row['type_metrics_json'])
            type_gb = type_m.get('gradient_boosting', {}) if isinstance(type_m, dict) else {}
            type_f1_score = (
                type_gb.get('incident_type_f1') or
                type_gb.get('macro_f1') or
                type_m.get('incident_type_f1') or
                type_m.get('macro_f1')
            )
            if type_f1_score is None and (type_gb.get('macroF1') is not None or type_m.get('macroF1') is not None):
                type_f1_score = round(float((type_gb.get('macroF1') or type_m.get('macroF1') or 0.0) * 100), 1)

            cached = {
                'ok': True,
                'status': 'success',
                'recordCount': live_count,
                'record_count': live_count,
                'metrics': {
                    'incident_type_f1': type_f1_score,
                    'macro_f1': type_f1_score,
                    'f1_score': type_f1_score,
                },
                'incident_type_f1': type_f1_score,
                'macro_f1': type_f1_score,
                'occurrence': {'metrics': _json.loads(row['occurrence_metrics_json']), 'active': row['active_occurrence_model']},
                'type': {
                    'metrics': type_m,
                    'active': row['active_type_model'],
                    'meta': {
                        'incident_type_f1': type_f1_score,
                        'macro_f1': type_f1_score,
                        'macroF1': type_gb.get('macroF1'),
                        'accuracy': type_gb.get('accuracy'),
                    }
                },
                'hotspot': {'metrics': _json.loads(row['hotspot_metrics_json']), 'active': row['active_hotspot_model']},
                'zoneRisk': _json.loads(row['hotspots_json']),
                'trainedAt': trained_at_str,
            }
            ml_models["cached_latest"] = cached
            ml_models["trained_at"] = trained_at_str
            ml_models["record_count"] = live_count
            return jsonify(cached), 200
    except Exception as e:
        print(f"[ML Service] DB fallback read error: {e}")

    return jsonify({
        'ok': False,
        'status': 'insufficient_data',
        'record_count': live_count,
        'recordCount': live_count,
        'message': 'Not enough incident records to generate predictions.'
    }), 200


@app.route('/predict', methods=['POST'])
@app.route('/api/ml/predict', methods=['POST'])
def predict_realtime():
    """Evaluates real-time incident category and zone occurrence probability against warm in-memory models."""
    try:
        live_count = get_active_incident_count()
        if live_count < 10 or ml_models["type"] is None or ml_models["hotspot"] is None:
            return jsonify({
                'ok': False,
                'status': 'insufficient_data',
                'record_count': live_count,
                'recordCount': live_count,
                'message': 'Not enough incident records to generate predictions.'
            }), 200

        data = request.get_json(silent=True) or {}
        zone = data.get("zone", "Zone 1")
        if zone not in ZONES:
            zone = "Zone 1"

        date_str = data.get("date")
        hour = int(data.get("hour", 12))

        try:
            pred_date = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.now()
        except Exception:
            pred_date = datetime.now()

        dow = pred_date.weekday()

        # Predict incident category using warm Gradient Boosting model
        top_cat, top_p = predict_top_category(ml_models["type"], ml_models["type_cols"], zone, dow, hour)
        if top_cat is None:
            return jsonify({
                'ok': False,
                'status': 'insufficient_data',
                'record_count': live_count,
                'recordCount': live_count,
                'message': 'Not enough incident records to generate predictions.'
            }), 200

        # Retrieve precomputed hotspot / occurrence forecast from memory
        zone_risk_list = (ml_models.get("cached_latest") or {}).get("zoneRisk", [])
        zone_info = next((z for z in zone_risk_list if z.get("zone") == zone), None)

        mean_prob = zone_info.get("meanDailyProb", 0.0) if zone_info else 0.0
        risk_level = "High" if mean_prob >= 0.20 else "Moderate" if mean_prob >= 0.13 else "Low"

        return jsonify({
            'ok': True,
            'status': 'success',
            'zone': zone,
            'date': pred_date.strftime("%Y-%m-%d"),
            'hour': hour,
            'predictedCategory': top_cat,
            'categoryProbability': round(float(top_p), 4) if top_p is not None else None,
            'meanDailyOccurrenceProb': round(float(mean_prob), 4),
            'riskLevel': risk_level,
            'peakWindow': zone_info.get("peakWindow", "8PM–12AM") if zone_info else "8PM–12AM",
            'trend': zone_info.get("trend", "→") if zone_info else "→",
            'expectedCount7d': zone_info.get("expectedCount7d", 0.0) if zone_info else 0.0,
            'expectedCount14d': zone_info.get("expectedCount14d", 0.0) if zone_info else 0.0,
        }), 200
    except Exception as e:
        return jsonify({
            'ok': False,
            'status': 'error',
            'message': f'Prediction error: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=False)
