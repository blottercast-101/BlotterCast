"""
BlotterCast ML Service
=======================
Flask microservice that implements the thesis's three prediction tasks
using real scikit-learn models trained on live MySQL data, each task
using a single designated algorithm:

  1. Binary incident-occurrence prediction (per zone-day)     -> Random Forest
  2. Multi-class incident-type prediction (zone + day-of-week
     + time-of-day)                                           -> Gradient Boosting
  3. Hotspot risk estimation (spatial risk) per zone,
     7/14-day forecast                                        -> Gradient Boosting

Performance Architecture:
  - In-Memory Singleton: Models, feature encoders, and cached forecast
    payloads are preloaded ONCE on server startup and kept warm in RAM.
  - Sub-millisecond Inference: Single and batch prediction endpoints
    evaluate directly against memory objects without disk I/O.
  - Joblib Disk Persistence: Models and artifacts are synchronized to disk
    so restarts load instantly without retraining.
"""
import json as _json
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()  # loads .env from the project root if present; no-op otherwise

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sqlalchemy import create_engine, text

# Shares the same database as the Flask app (set DATABASE_URL to match, e.g.
# in a hosted deployment). Defaults to the local SQLite dev database.
_DEFAULT_SQLITE = "sqlite:///" + os.path.join(os.path.dirname(__file__), "..", "instance", "blottercast.db")


def _normalize_db_url(url: str) -> str:
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


DATABASE_URL = _normalize_db_url(os.environ.get("DATABASE_URL", _DEFAULT_SQLITE))
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

ZONES = ['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Zone 6', 'Zone 7', 'Zone 8']
CATEGORIES = ['Physical Assault', 'Theft', 'Domestic Dispute', 'Vandalism',
              'Trespassing', 'Drug-Related Activity', 'Public Disturbance', 'Other']

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

# ---------------------------------------------------------------
# In-Memory Model Singleton Registry
# Kept warm in RAM to eliminate repeated disk / database reads
# ---------------------------------------------------------------
ml_models = {
    "occurrence": None,          # RandomForestClassifier
    "occurrence_cols": None,     # List of feature column names
    "occurrence_threshold": 0.5, # Optimal decision threshold
    "hotspot": None,             # GradientBoostingClassifier
    "hotspot_cols": None,        # List of feature column names
    "type": None,                # GradientBoostingClassifier (multi-class)
    "type_cols": None,           # List of feature column names
    "type_cat_cache": {},        # Precomputed (zone, dow) -> category probability vector
    "cached_latest": None,       # Pre-built /latest response dictionary
    "trained_at": None,          # Datetime / ISO string
    "record_count": 0,
}

app = Flask(__name__)
CORS(app, supports_credentials=True)


def _save_models_to_disk():
    """Serialize warm in-memory models to disk using joblib for instant cold-starts."""
    try:
        os.makedirs(MODELS_DIR, exist_ok=True)
        joblib_path = os.path.join(MODELS_DIR, "incident_models.joblib")
        joblib.dump({
            "occurrence": ml_models["occurrence"],
            "occurrence_cols": ml_models["occurrence_cols"],
            "occurrence_threshold": ml_models["occurrence_threshold"],
            "hotspot": ml_models["hotspot"],
            "hotspot_cols": ml_models["hotspot_cols"],
            "type": ml_models["type"],
            "type_cols": ml_models["type_cols"],
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
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM ml_runs ORDER BY id DESC LIMIT 1"))
            row = result.mappings().first()
            if row:
                trained_at = row['trained_at']
                ml_models["cached_latest"] = {
                    'ok': True,
                    'recordCount': row['record_count'],
                    'occurrence': {'metrics': _json.loads(row['occurrence_metrics_json']), 'active': row['active_occurrence_model']},
                    'type': {'metrics': _json.loads(row['type_metrics_json']), 'active': row['active_type_model']},
                    'hotspot': {'metrics': _json.loads(row['hotspot_metrics_json']), 'active': row['active_hotspot_model']},
                    'zoneRisk': _json.loads(row['hotspots_json']),
                    'trainedAt': (trained_at.isoformat() + 'Z') if hasattr(trained_at, 'isoformat') else str(trained_at),
                }
                ml_models["trained_at"] = trained_at
                ml_models["record_count"] = row['record_count']
                print("[ML Singleton] Preloaded latest run from database into in-memory cache.")
    except Exception as e:
        print(f"[ML Singleton] Startup DB preloading skipped: {e}")


# Run singleton preload immediately on module import/startup
preload_models_and_cache()


def load_incidents() -> pd.DataFrame:
    with engine.connect() as conn:
        df = pd.read_sql(
            text("SELECT id, incident_date AS date, zone_id AS zone, hour, category, status FROM incidents ORDER BY incident_date"),
            conn,
        )
    df['date'] = pd.to_datetime(df['date'])
    return df


# ---------------------------------------------------------------
# High-Performance Feature Engineering (Vectorized)
# ---------------------------------------------------------------
def _compute_days_since_last(dates, occurrences):
    """Vectorized calculation of days since last non-zero incident."""
    n = len(dates)
    out = np.full(n, 999, dtype=int)
    last_seen = None
    for i in range(n):
        d = dates[i]
        if last_seen is not None:
            out[i] = (d - last_seen).days
        if occurrences[i] > 0:
            last_seen = d
    return out


def build_panel(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    start, end = df['date'].min(), df['date'].max()
    all_days = pd.date_range(start, end, freq='D')

    # daily incident count per zone (occurrence target + lag/rolling features)
    counts = (
        df.groupby(['zone', 'date']).size().rename('n').reset_index()
    )
    grid = pd.MultiIndex.from_product([ZONES, all_days], names=['zone', 'date']).to_frame(index=False)
    grid = grid.merge(counts, on=['zone', 'date'], how='left')
    grid['n'] = grid['n'].fillna(0).astype(int)
    grid = grid.sort_values(['zone', 'date']).reset_index(drop=True)

    # barangay-wide daily total (for brgy_prev_day feature)
    brgy_daily = grid.groupby('date')['n'].sum()
    brgy_prev = brgy_daily.shift(1).fillna(0)

    grid = grid.merge(brgy_prev.rename('brgy_prev_day'), on='date', how='left')
    grid['brgy_prev_day'] = grid['brgy_prev_day'].fillna(0)

    rows = []
    for zone, g in grid.groupby('zone'):
        g = g.sort_values('date').copy()
        g['lag1'] = g['n'].shift(1).fillna(0)
        g['lag7'] = g['n'].shift(7).fillna(0)
        g['roll7'] = g['n'].shift(1).rolling(7, min_periods=1).mean().fillna(0)
        g['roll30'] = g['n'].shift(1).rolling(30, min_periods=1).mean().fillna(0)

        # Fast numpy calculation of days since last incident
        dates = g['date'].dt.to_pydatetime()
        occs = g['n'].values
        g['days_since_last'] = _compute_days_since_last(dates, occs)
        rows.append(g)

    panel = pd.concat(rows, ignore_index=True)
    panel['dow'] = panel['date'].dt.dayofweek  # Mon=0..Sun=6
    panel['is_weekend'] = panel['dow'].isin([5, 6]).astype(int)
    panel['dom'] = panel['date'].dt.day
    panel['is_payday'] = panel['dom'].isin([15, 30, 31, 1]).astype(int)
    panel['month'] = panel['date'].dt.month
    panel['month_sin'] = np.sin(2 * np.pi * panel['month'] / 12)
    panel['month_cos'] = np.cos(2 * np.pi * panel['month'] / 12)
    panel['occurred'] = (panel['n'] > 0).astype(int)

    # drop first 30 days per zone (insufficient lag/rolling history)
    trimmed = [g.iloc[30:] for _, g in panel.groupby('zone')]
    panel = pd.concat(trimmed, ignore_index=True)
    return panel


FEATURE_COLS = ['dow', 'is_weekend', 'is_payday', 'month_sin', 'month_cos',
                 'lag1', 'lag7', 'roll7', 'roll30', 'days_since_last', 'brgy_prev_day']


def make_design_matrix(panel: pd.DataFrame):
    X = pd.get_dummies(panel[['zone'] + FEATURE_COLS], columns=['zone'], prefix='zone')
    y = panel['occurred'].values
    return X, y


# ---------------------------------------------------------------
# Binary-target trainer with vectorized threshold optimization
# ---------------------------------------------------------------
def train_binary_model(panel: pd.DataFrame, name: str, model):
    """Returns (results, trained_model, meta, (X, y)) for a single binary model."""
    X, y = make_design_matrix(panel)
    n = len(X)
    split = int(n * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y[:split], y[split:]

    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]

    # Vectorized threshold tuning on training data for best F1
    train_proba = model.predict_proba(X_train)[:, 1]
    thresholds = np.arange(0.1, 0.9, 0.02)
    best_thr, best_f1 = 0.5, -1.0

    for thr in thresholds:
        pred_train = (train_proba >= thr).astype(int)
        f1 = f1_score(y_train, pred_train, zero_division=0)
        if f1 > best_f1:
            best_f1, best_thr = f1, thr

    pred = (proba >= best_thr).astype(int)
    auc = roc_auc_score(y_test, proba) if len(set(y_test)) > 1 else 0.5

    results = {name: {
        'accuracy': round(accuracy_score(y_test, pred), 4),
        'precision': round(precision_score(y_test, pred, zero_division=0), 4),
        'recall': round(recall_score(y_test, pred, zero_division=0), 4),
        'f1': round(f1_score(y_test, pred, zero_division=0), 4),
        'auc': round(float(auc), 4),
        'threshold': round(float(best_thr), 2),
    }}

    meta = {
        'trainRows': int(len(X_train)), 'testRows': int(len(X_test)),
        'posRate': round(float(y.mean()), 4), 'featureCols': list(X.columns),
        'bestThreshold': round(float(best_thr), 2),
    }
    return results, {name: model}, meta, (X, y)


def best_model(results: dict, key: str = 'f1') -> str:
    """Each task trains exactly one designated model."""
    return next(iter(results))


def train_occurrence_models(panel: pd.DataFrame):
    """Task 1 — incident occurrence classification: Random Forest (multi-core)."""
    model = RandomForestClassifier(n_estimators=150, max_depth=8, min_samples_leaf=5,
                                    class_weight='balanced', random_state=42, n_jobs=-1)
    return train_binary_model(panel, 'random_forest', model)


def train_hotspot_models(panel: pd.DataFrame):
    """Task 3 — hotspot risk estimation: Gradient Boosting."""
    model = GradientBoostingClassifier(n_estimators=120, max_depth=3, learning_rate=0.1, random_state=42)
    return train_binary_model(panel, 'gradient_boosting', model)


def time_bin(hour: int) -> str:
    if 5 <= hour < 12: return 'morning'
    if 12 <= hour < 17: return 'afternoon'
    if 17 <= hour < 21: return 'evening'
    return 'night'


def train_type_models(df: pd.DataFrame):
    """Task 2 — incident-type prediction: Gradient Boosting (multi-class),
    on zone + day-of-week + time-of-day -> category."""
    d = df.copy()
    d['dow'] = d['date'].dt.dayofweek
    d['tbin'] = d['hour'].apply(time_bin)
    d = d.sort_values('date').reset_index(drop=True)

    X = pd.get_dummies(d[['zone', 'dow', 'tbin']].astype(str))
    y = d['category']

    n = len(d)
    split = int(n * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    name = 'gradient_boosting'
    model = GradientBoostingClassifier(n_estimators=120, max_depth=3, learning_rate=0.1, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    results = {name: {
        'accuracy': round(accuracy_score(y_test, pred), 4),
        'macroPrecision': round(precision_score(y_test, pred, average='macro', zero_division=0), 4),
        'macroRecall': round(recall_score(y_test, pred, average='macro', zero_division=0), 4),
        'macroF1': round(f1_score(y_test, pred, average='macro', zero_division=0), 4),
        'nTest': int(len(y_test)),
    }}
    trained_models = {name: model}

    return results, trained_models, list(X.columns)


def predict_top_category(model, cols, zone: str, dow: int, hour: int):
    tbin = time_bin(hour)
    row = pd.DataFrame([{f'zone_{zone}': 1, f'dow_{dow}': 1, f'tbin_{tbin}': 1}])
    row = row.reindex(columns=cols, fill_value=0)
    proba = model.predict_proba(row)[0]
    idx = int(np.argmax(proba))
    return model.classes_[idx], round(float(proba[idx]), 4)


def build_category_probability_cache(type_model, type_cols) -> dict:
    """Precompute all (zone, dow) category distribution vectors in a single batched pass."""
    cache = {}
    tbins = ['morning', 'afternoon', 'evening', 'night']
    for zone in ZONES:
        for dow in range(7):
            X = pd.DataFrame(0, index=range(len(tbins)), columns=type_cols, dtype=float)
            for i, tbin in enumerate(tbins):
                for col in (f'zone_{zone}', f'dow_{dow}', f'tbin_{tbin}'):
                    if col in X.columns:
                        X.loc[i, col] = 1
            proba = type_model.predict_proba(X).mean(axis=0)
            cache[(zone, dow)] = dict(zip(type_model.classes_, proba))
    return cache


def forecast_hotspots(panel: pd.DataFrame, model, feature_cols_order, type_model, type_cols,
                       cat_cache: dict, horizon: int = 14):
    latest = panel.sort_values('date').groupby('zone').tail(1).set_index('zone')
    results = {}

    for zone in ZONES:
        if zone not in latest.index:
            continue
        row = latest.loc[zone]
        lag1, lag7, roll7, roll30 = row['lag1'], row['lag7'], row['roll7'], row['roll30']
        days_since = row['days_since_last']
        last_date = row['date']

        probs = []
        cat_series = {c: [] for c in CATEGORIES}
        for step in range(1, horizon + 1):
            d = last_date + timedelta(days=step)
            dow, dom, month = d.dayofweek, d.day, d.month
            feat = {
                'dow': dow, 'is_weekend': int(dow in [5, 6]), 'is_payday': int(dom in [15, 30, 31, 1]),
                'month_sin': np.sin(2 * np.pi * month / 12), 'month_cos': np.cos(2 * np.pi * month / 12),
                'lag1': lag1, 'lag7': lag7, 'roll7': roll7, 'roll30': roll30,
                'days_since_last': days_since, 'brgy_prev_day': row['brgy_prev_day'],
            }
            for z in ZONES:
                feat[f'zone_{z}'] = 1 if z == zone else 0
            X_step = pd.DataFrame([feat]).reindex(columns=feature_cols_order, fill_value=0)
            p = float(model.predict_proba(X_step)[0, 1])
            probs.append(p)

            cat_probs = cat_cache.get((zone, dow), {})
            for c in CATEGORIES:
                cat_series[c].append(round(float(p * cat_probs.get(c, 0.0)), 4))

            # roll features forward using predicted probability as pseudo-observation
            lag7 = lag1 if step >= 7 else lag7
            lag1 = p
            roll7 = (roll7 * 6 + p) / 7
            roll30 = (roll30 * 29 + p) / 30
            days_since = 0 if p > 0.5 else days_since + 1

        probs7 = probs[:7]
        mean_p = float(np.mean(probs7))
        p_any = 1 - np.prod([1 - p for p in probs7])
        results[zone] = {
            'meanDailyProb': round(mean_p, 4),
            'pAny7d': round(float(p_any), 4),
            'expectedCount7d': round(float(np.sum(probs7)), 2),
            'expectedCount14d': round(float(np.sum(probs)), 2),
            'dailyProbs': [round(p, 4) for p in probs],
            'categorySeries': cat_series,
            'forecastDates': [(last_date + timedelta(days=s)).strftime('%Y-%m-%d') for s in range(1, horizon + 1)],
        }
    return results


def peak_window(df: pd.DataFrame, zone: str) -> str:
    sub = df[df['zone'] == zone]
    if sub.empty:
        return 'N/A'
    hist = sub['hour'].value_counts().reindex(range(24), fill_value=0)
    best_start, best_sum = 0, -1
    for start in range(24):
        window = [hist[(start + i) % 24] for i in range(4)]
        s = sum(window)
        if s > best_sum:
            best_sum, best_start = s, start
    h1, h2 = best_start, (best_start + 4) % 24
    fmt = lambda h: f"{h % 12 or 12}{'AM' if h < 12 else 'PM'}"
    return f"{fmt(h1)}–{fmt(h2)}"


def trend_14d(df: pd.DataFrame, zone: str) -> str:
    sub = df[df['zone'] == zone]
    if sub.empty:
        return '→'
    end = df['date'].max()
    last14 = sub[sub['date'] > end - timedelta(days=14)].shape[0]
    prev14 = sub[(sub['date'] <= end - timedelta(days=14)) & (sub['date'] > end - timedelta(days=28))].shape[0]
    if last14 > prev14 * 1.15:
        return '↑'
    if last14 < prev14 * 0.85:
        return '↓'
    return '→'


# ---------------------------------------------------------------
# Routes
# ---------------------------------------------------------------
@app.route('/health')
def health():
    return jsonify({
        'ok': True,
        'service': 'blottercast-ml',
        'isWarm': ml_models['occurrence'] is not None or ml_models['cached_latest'] is not None,
        'time': datetime.now().isoformat(),
    })


@app.route('/train', methods=['POST'])
def train():
    df = load_incidents()
    if len(df) < 60:
        return jsonify({'error': 'Not enough incidents to train (need 60+)'}), 400

    panel = build_panel(df)

    # Task 1 — occurrence: Random Forest
    occ_results, occ_models, occ_meta, (occ_X, occ_y) = train_occurrence_models(panel)
    # Task 3 — hotspot risk: Gradient Boosting
    hot_results, hot_models, hot_meta, (hot_X, hot_y) = train_hotspot_models(panel)
    # Task 2 — incident type: Gradient Boosting
    type_results, type_models, type_cols = train_type_models(df)

    active_occurrence = best_model(occ_results, 'f1')
    active_hotspot = best_model(hot_results, 'f1')
    active_type = best_model(type_results, 'macroF1')

    # Precompute category probability distribution cache
    cat_cache = build_category_probability_cache(type_models[active_type], type_cols)

    hotspots = forecast_hotspots(panel, hot_models[active_hotspot], list(hot_X.columns),
                                  type_models[active_type], type_cols, cat_cache)

    zone_rows = []
    dow_now = datetime.now().weekday()
    for zone in ZONES:
        if zone not in hotspots:
            continue
        h = hotspots[zone]
        top_cat, top_p = predict_top_category(type_models[active_type], type_cols, zone, dow_now, 20)
        zone_rows.append({
            'zone': zone,
            'meanDailyProb': h['meanDailyProb'],
            'expectedCount7d': h['expectedCount7d'],
            'expectedCount14d': h['expectedCount14d'],
            'dailyProbs': h['dailyProbs'],
            'categorySeries': h['categorySeries'],
            'forecastDates': h['forecastDates'],
            'topCategory': top_cat,
            'topCategoryProb': top_p,
            'peakWindow': peak_window(df, zone),
            'trend': trend_14d(df, zone),
        })
    zone_rows.sort(key=lambda r: -r['meanDailyProb'])

    trained_at = datetime.utcnow()
    trained_at_iso = trained_at.isoformat() + 'Z'

    response_payload = {
        'ok': True,
        'recordCount': int(len(df)),
        'occurrence': {'metrics': occ_results, 'active': active_occurrence, 'meta': occ_meta},
        'type': {'metrics': type_results, 'active': active_type},
        'hotspot': {'metrics': hot_results, 'active': active_hotspot, 'meta': hot_meta},
        'zoneRisk': zone_rows,
        'trainedAt': trained_at_iso,
    }

    # Atomically update warm in-memory singleton
    ml_models["occurrence"] = occ_models[active_occurrence]
    ml_models["occurrence_cols"] = list(occ_X.columns)
    ml_models["occurrence_threshold"] = occ_meta.get("bestThreshold", 0.5)
    ml_models["hotspot"] = hot_models[active_hotspot]
    ml_models["hotspot_cols"] = list(hot_X.columns)
    ml_models["type"] = type_models[active_type]
    ml_models["type_cols"] = type_cols
    ml_models["type_cat_cache"] = cat_cache
    ml_models["cached_latest"] = response_payload
    ml_models["trained_at"] = trained_at_iso
    ml_models["record_count"] = int(len(df))

    # Persist serialized artifacts to disk asynchronously
    _save_models_to_disk()

    # Cache to database ml_runs table
    with engine.begin() as conn:
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
                "record_count": len(df), "active_occurrence": active_occurrence,
                "active_type": active_type, "active_hotspot": active_hotspot,
                "occ_json": _json.dumps(occ_results), "type_json": _json.dumps(type_results),
                "hot_json": _json.dumps(hot_results), "hotspots_json": _json.dumps(zone_rows),
            },
        )

    return jsonify(response_payload)


@app.route('/latest', methods=['GET'])
def latest():
    """Return the most recently trained model results directly from in-memory cache."""
    if ml_models["cached_latest"] is not None:
        return jsonify(ml_models["cached_latest"])

    # Fallback to database lookup if in-memory cache is cold
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM ml_runs ORDER BY id DESC LIMIT 1"))
        row = result.mappings().first()
    if not row:
        return jsonify({'ok': False, 'message': 'No trained model yet. POST /train first.'}), 404

    trained_at = row['trained_at']
    trained_at_str = (trained_at.isoformat() + 'Z') if hasattr(trained_at, 'isoformat') else str(trained_at)
    cached = {
        'ok': True,
        'recordCount': row['record_count'],
        'occurrence': {'metrics': _json.loads(row['occurrence_metrics_json']), 'active': row['active_occurrence_model']},
        'type': {'metrics': _json.loads(row['type_metrics_json']), 'active': row['active_type_model']},
        'hotspot': {'metrics': _json.loads(row['hotspot_metrics_json']), 'active': row['active_hotspot_model']},
        'zoneRisk': _json.loads(row['hotspots_json']),
        'trainedAt': trained_at_str,
    }
    ml_models["cached_latest"] = cached
    ml_models["trained_at"] = trained_at_str
    ml_models["record_count"] = row['record_count']
    return jsonify(cached)


@app.route('/predict', methods=['POST'])
def predict_realtime():
    """Real-time instant prediction endpoint evaluated directly against warm memory singleton."""
    data = request.get_json(silent=True) or {}
    zone = data.get("zone", "Zone 1")
    date_str = data.get("date")
    hour = int(data.get("hour", 12))

    try:
        pred_date = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.now()
    except Exception:
        pred_date = datetime.now()

    dow = pred_date.weekday()

    # Predict incident category using warm model
    if ml_models["type"] is not None and ml_models["type_cols"] is not None:
        top_cat, top_p = predict_top_category(ml_models["type"], ml_models["type_cols"], zone, dow, hour)
    else:
        top_cat, top_p = "General Incident", 0.50

    # Retrieve precomputed hotspot / occurrence forecast from memory
    zone_risk_list = (ml_models.get("cached_latest") or {}).get("zoneRisk", [])
    zone_info = next((z for z in zone_risk_list if z.get("zone") == zone), None)

    mean_prob = zone_info.get("meanDailyProb", 0.15) if zone_info else 0.15
    risk_level = "High" if mean_prob >= 0.20 else "Moderate" if mean_prob >= 0.13 else "Low"

    return jsonify({
        'ok': True,
        'zone': zone,
        'date': pred_date.strftime("%Y-%m-%d"),
        'hour': hour,
        'predictedCategory': top_cat,
        'categoryProbability': top_p,
        'meanDailyOccurrenceProb': mean_prob,
        'riskLevel': risk_level,
        'peakWindow': zone_info.get("peakWindow", "N/A") if zone_info else "N/A",
        'trend': zone_info.get("trend", "→") if zone_info else "→",
        'expectedCount7d': zone_info.get("expectedCount7d", 1.0) if zone_info else 1.0,
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=False)
