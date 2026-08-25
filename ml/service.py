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
from datetime import datetime, timedelta

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


def preload_models_and_cache():
    """Preload trained models and cached forecast ONCE on startup."""
    joblib_path = os.path.join(MODELS_DIR, "incident_models.joblib")
    if os.path.isfile(joblib_path):
        try:
            data = joblib.load(joblib_path)
            ml_models.update(data)
            print(f"[ML Singleton] Preloaded warm models from disk (trained at {ml_models.get('trained_at')})")
            return
        except Exception as e:
            print(f"[ML Singleton] Could not load saved joblib models: {e}")

    # Fallback to database if disk artifact is not present
    try:
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM ml_runs ORDER BY id DESC LIMIT 1"))
            row = result.mappings().first()
            if row:
                trained_at = row['trained_at']
                trained_at_str = (trained_at.isoformat() + 'Z') if hasattr(trained_at, 'isoformat') else str(trained_at)
                occ_m = _json.loads(row['occurrence_metrics_json'])
                type_m = _json.loads(row['type_metrics_json'])
                hot_m = _json.loads(row['hotspot_metrics_json'])
                zone_r = _json.loads(row['hotspots_json'])

                ml_models["cached_latest"] = {
                    'ok': True,
                    'recordCount': row['record_count'],
                    'occurrence': {'metrics': occ_m, 'active': row['active_occurrence_model']},
                    'type': {'metrics': type_m, 'active': row['active_type_model']},
                    'hotspot': {'metrics': hot_m, 'active': row['active_hotspot_model']},
                    'zoneRisk': zone_r,
                    'trainedAt': trained_at_str,
                }
                ml_models["trained_at"] = trained_at_str
                ml_models["record_count"] = row['record_count']
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
            df['category'] = df['category'].fillna('Other').astype(str).str.strip()
            df = df[df['category'] != ''].copy()
            df['hour'] = pd.to_numeric(df['hour'], errors='coerce').fillna(12).astype(int)
        return df
    except Exception as e:
        print(f"[ML Service] Database load_incidents error: {e}")
        return pd.DataFrame()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'ok': True,
        'status': 'healthy',
        'service': 'blottercast-ml',
        'isWarm': ml_models['occurrence'] is not None or ml_models['cached_latest'] is not None,
        'time': datetime.now().isoformat(),
    })


@app.route('/train', methods=['POST'])
@app.route('/api/ml/retrain', methods=['POST'])
def train():
    try:
        df = load_incidents()
        if len(df) < 10:
            return jsonify({
                'ok': False,
                'status': 'warning',
                'message': 'Minimum 10 incident records required for training.',
                'recordCount': int(len(df)),
            }), 200

        panel = build_spatiotemporal_panel(df)
        if panel.empty or len(panel) < 10:
            return jsonify({
                'ok': False,
                'status': 'warning',
                'message': 'Insufficient temporal span across zones for panel generation.',
                'recordCount': int(len(df)),
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

        trained_at = datetime.utcnow()
        trained_at_iso = trained_at.isoformat() + 'Z'

        occ_results = {'random_forest': occ_metrics}
        type_results = {'gradient_boosting': type_metrics}
        hot_results = {'gradient_boosting': hot_metrics}

        type_f1_score = type_metrics.get('incident_type_f1') or type_metrics.get('macro_f1') or round(float(type_metrics.get('macroF1', 0.0) * 100), 1)

        response_payload = {
            'ok': True,
            'status': 'success',
            'recordCount': int(len(df)),
            'records_evaluated': int(len(df)),
            'metrics': {
                'incident_type_f1': type_f1_score,
                'macro_f1': type_f1_score,
                'f1_score': type_f1_score,
                'occurrence_accuracy': occ_metrics.get('accuracy', 0.0),
                'hotspot_accuracy': hot_metrics.get('accuracy', 0.0),
            },
            'incident_type_f1': type_f1_score,
            'macro_f1': type_f1_score,
            'occurrence': {
                'metrics': occ_results,
                'active': 'random_forest',
                'meta': {
                    'accuracy': occ_metrics['accuracy'],
                    'f1': occ_metrics['f1'],
                    'auc': occ_metrics['auc'],
                    'bestThreshold': occ_metrics['threshold'],
                }
            },
            'type': {
                'metrics': type_results,
                'active': 'gradient_boosting',
                'meta': {
                    'macroF1': type_metrics.get('macroF1', 0.0),
                    'macro_f1': type_f1_score,
                    'weightedF1': type_metrics.get('weightedF1', 0.0),
                    'f1': type_metrics.get('f1', 0.0),
                    'f1_score': type_metrics.get('f1_score', 0.0),
                    'incident_type_f1': type_f1_score,
                    'accuracy': type_metrics.get('accuracy', 0.0),
                }
            },
            'hotspot': {
                'metrics': hot_results,
                'active': 'gradient_boosting',
                'meta': {
                    'accuracy': hot_metrics['accuracy'],
                    'f1': hot_metrics['f1'],
                }
            },
            'zoneRisk': zone_rows,
            'trainedAt': trained_at_iso,
        }

        # Update in-memory warm singleton atomically
        ml_models["occurrence"] = occ_model
        ml_models["occurrence_cols"] = occ_cols
        ml_models["occurrence_threshold"] = occ_metrics['threshold']
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
        ml_models["record_count"] = int(len(df))

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
                        "record_count": len(df),
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
    if ml_models["cached_latest"] is not None:
        return jsonify(ml_models["cached_latest"]), 200

    # Fallback to database lookup if memory is uninitialized
    try:
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM ml_runs ORDER BY id DESC LIMIT 1"))
            row = result.mappings().first()
        if row:
            trained_at = row['trained_at']
            trained_at_str = (trained_at.isoformat() + 'Z') if hasattr(trained_at, 'isoformat') else str(trained_at)
            type_m = _json.loads(row['type_metrics_json'])
            type_gb = type_m.get('gradient_boosting', {}) if isinstance(type_m, dict) else {}
            type_f1_score = (
                type_gb.get('incident_type_f1') or
                type_gb.get('macro_f1') or
                type_m.get('incident_type_f1') or
                type_m.get('macro_f1') or
                round(float((type_gb.get('macroF1') or type_m.get('macroF1') or 0.0) * 100), 1)
            )

            cached = {
                'ok': True,
                'status': 'success',
                'recordCount': row['record_count'],
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
                        'macroF1': type_gb.get('macroF1', 0.0),
                        'accuracy': type_gb.get('accuracy', 0.0),
                    }
                },
                'hotspot': {'metrics': _json.loads(row['hotspot_metrics_json']), 'active': row['active_hotspot_model']},
                'zoneRisk': _json.loads(row['hotspots_json']),
                'trainedAt': trained_at_str,
            }
            ml_models["cached_latest"] = cached
            ml_models["trained_at"] = trained_at_str
            ml_models["record_count"] = row['record_count']
            return jsonify(cached), 200
    except Exception as e:
        print(f"[ML Service] DB fallback read error: {e}")

    return jsonify({
        'ok': False,
        'status': 'not_initialized',
        'message': 'No trained models available yet. Retrain model to initialize.'
    }), 404


@app.route('/predict', methods=['POST'])
@app.route('/api/ml/predict', methods=['POST'])
def predict_realtime():
    """Evaluates real-time incident category and zone occurrence probability against warm in-memory models."""
    try:
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
        if ml_models["type"] is not None and ml_models["type_cols"] is not None:
            try:
                top_cat, top_p = predict_top_category(ml_models["type"], ml_models["type_cols"], zone, dow, hour)
            except Exception:
                top_cat, top_p = "Physical Assault", 0.35
        else:
            top_cat, top_p = "Physical Assault", 0.35

        # Retrieve precomputed hotspot / occurrence forecast from memory
        zone_risk_list = (ml_models.get("cached_latest") or {}).get("zoneRisk", [])
        zone_info = next((z for z in zone_risk_list if z.get("zone") == zone), None)

        mean_prob = zone_info.get("meanDailyProb", 0.15) if zone_info else 0.15
        risk_level = "High" if mean_prob >= 0.20 else "Moderate" if mean_prob >= 0.13 else "Low"

        return jsonify({
            'ok': True,
            'status': 'success',
            'zone': zone,
            'date': pred_date.strftime("%Y-%m-%d"),
            'hour': hour,
            'predictedCategory': top_cat,
            'categoryProbability': round(float(top_p), 4),
            'meanDailyOccurrenceProb': round(float(mean_prob), 4),
            'riskLevel': risk_level,
            'peakWindow': zone_info.get("peakWindow", "8PM–12AM") if zone_info else "8PM–12AM",
            'trend': zone_info.get("trend", "→") if zone_info else "→",
            'expectedCount7d': zone_info.get("expectedCount7d", 1.0) if zone_info else 1.0,
            'expectedCount14d': zone_info.get("expectedCount14d", 2.0) if zone_info else 2.0,
        }), 200
    except Exception as e:
        return jsonify({
            'ok': False,
            'status': 'error',
            'message': f'Prediction error: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=False)
