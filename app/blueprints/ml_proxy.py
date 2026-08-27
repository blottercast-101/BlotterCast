import os
import subprocess
import sys
import time

import requests
from flask import Blueprint, jsonify, request

from ..permissions import json_error, login_required, permission_required

bp = Blueprint("ml_proxy", __name__)

ML_BASE = os.environ.get("ML_SERVICE_URL", "http://127.0.0.1:5001").replace("localhost", "127.0.0.1")
ML_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ml")
ML_SCRIPT = os.path.join(ML_DIR, "service.py")

_ml_process = None  # tracks a process we started, so we don't spawn duplicates

# Persistent HTTP connection pool for sub-millisecond proxy forwarding
_session = requests.Session()
_adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=1)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)


def _ml_is_running() -> bool:
    try:
        r = _session.get(f"{ML_BASE}/health", timeout=0.8)
        return r.status_code == 200
    except requests.RequestException:
        return False


def _ml_ensure_running() -> bool:
    """Launch ml/service.py in the background if it isn't already up, then
    poll briefly for it to come online (cold start: scikit-learn/pandas
    import + Flask bind can take a few seconds on first run)."""
    global _ml_process
    if _ml_is_running():
        return True
    if not os.path.isfile(ML_SCRIPT):
        return False

    if _ml_process is None or _ml_process.poll() is not None:
        env = dict(os.environ)
        # Give the ML service the same DATABASE_URL as the main app, and a
        # distinct port so it doesn't collide with the Flask app itself.
        env.setdefault("PORT", ML_BASE.rsplit(":", 1)[-1])
        _ml_process = subprocess.Popen(
            [sys.executable, ML_SCRIPT],
            cwd=ML_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            env=env,
        )

    for _ in range(40):  # up to ~20s
        time.sleep(0.5)
        if _ml_is_running():
            return True
    return False


def _forward(path: str, method: str = "GET", body=None):
    url = f"{ML_BASE}{path}"
    # Fast path: attempt direct pooled request without redundant health check
    try:
        if method == "POST":
            r = _session.post(url, json=body, timeout=30)
        else:
            r = _session.get(url, timeout=30)
        return jsonify(r.json()), r.status_code
    except requests.RequestException:
        # Slow path / cold start: service is down, attempt auto-spawn
        if _ml_ensure_running():
            try:
                if method == "POST":
                    r = _session.post(url, json=body, timeout=30)
                else:
                    r = _session.get(url, timeout=30)
                return jsonify(r.json()), r.status_code
            except requests.RequestException as e:
                return json_error(f"ML service unreachable: {e}", 502)
        return json_error(
            "The prediction service could not be started automatically. Make sure Python "
            "is installed and its packages are set up (see ml/requirements.txt).", 503,
        )


@bp.route("/api/predict/insights", methods=["GET"])
@bp.route("/api/predictions/latest", methods=["GET"])
@login_required
@permission_required("view_analytics")
def predict_insights_direct():
    return _forward("/latest")


@bp.route("/api/ml/warmup", methods=["GET", "POST"])
def ml_warmup():
    """Non-blocking background ping to keep ML microservice warm."""
    if _ml_is_running():
        return jsonify({"ok": True, "status": "warm"}), 200
    return jsonify({"ok": False, "status": "cold"}), 200


@bp.route("/api/ml_proxy.php", methods=["GET", "POST"])
@login_required
@permission_required("view_analytics")
def ml_proxy_router():
    action = request.args.get("action", "")

    # health stays a fast, no-autostart check so the frontend can poll it
    # while showing a "starting up..." state.
    if action == "health" and request.method == "GET":
        if _ml_is_running():
            return _forward("/health")
        return jsonify({"status": "down"}), 200

    if action in ("latest", "insights") and request.method == "GET":
        return _forward("/latest")

    if action == "predict" and request.method == "POST":
        return _forward("/predict", "POST", request.get_json(silent=True) or {})

    if action == "train" and request.method == "POST":
        from ..permissions import json_error as _json_error, role_can
        from flask import session
        if not role_can(session.get("role", ""), "retrain_ml"):
            return _json_error("You do not have permission to perform this action.", 403)
        return _forward("/train", "POST", request.get_json(silent=True) or {})

    return json_error("Unknown action", 404)
