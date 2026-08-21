import os
import subprocess
import sys
import time

import requests
from flask import Blueprint, jsonify, request

from ..permissions import json_error, login_required, permission_required

bp = Blueprint("ml_proxy", __name__)

ML_BASE = os.environ.get("ML_SERVICE_URL", "http://localhost:5001")
ML_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ml")
ML_SCRIPT = os.path.join(ML_DIR, "service.py")
ML_LOG = os.path.join(ML_DIR, "service.log")

_ml_process = None  # tracks a process we started, so we don't spawn duplicates


def _ml_is_running() -> bool:
    try:
        r = requests.get(f"{ML_BASE}/health", timeout=0.8)
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
        with open(ML_LOG, "a") as log:
            _ml_process = subprocess.Popen(
                [sys.executable, ML_SCRIPT], cwd=ML_DIR, stdout=log, stderr=log,
                stdin=subprocess.DEVNULL, env=env,
            )

    for _ in range(40):  # up to ~20s
        time.sleep(0.5)
        if _ml_is_running():
            return True
    return False


def _forward(path: str, method: str = "GET", body=None):
    url = f"{ML_BASE}{path}"
    try:
        if method == "POST":
            r = requests.post(url, json=body, timeout=30)
        else:
            r = requests.get(url, timeout=30)
    except requests.RequestException as e:
        return json_error(f"ML service unreachable: {e}", 502)
    return jsonify(r.json()), r.status_code


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

    if not _ml_ensure_running():
        return json_error(
            "The prediction service could not be started automatically. Make sure Python "
            "is installed and its packages are set up (see ml/requirements.txt), then "
            "check ml/service.log for details.", 503,
        )

    if action == "latest" and request.method == "GET":
        return _forward("/latest")

    if action == "train" and request.method == "POST":
        from ..permissions import json_error as _json_error, role_can
        from flask import session
        if not role_can(session.get("role", ""), "retrain_ml"):
            return _json_error("You do not have permission to perform this action.", 403)
        return _forward("/train", "POST", request.get_json(silent=True) or {})

    return json_error("Unknown action", 404)
