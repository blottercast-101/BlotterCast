"""End-to-end test of the ml_proxy blueprint against the REAL ml/service.py
subprocess (not mocked) -- covers auto-spawn, RBAC, and forwarding."""
import os
os.environ.setdefault("ML_SERVICE_URL", "http://localhost:5001")

from app import create_app
from test_mfa_helper import login as mfa_login

app = create_app()
c = app.test_client()


def login(u, p):
    mfa_login(c, u, p)


def logout():
    c.post("/api/auth.php?action=logout")


print("=== health (no ML started yet, should be down, no autostart) ===")
login("admin", "admin123")
r = c.get("/api/ml_proxy.php?action=health")
print(r.status_code, r.get_json())
assert r.status_code == 200 and r.get_json()["status"] == "down"

print("=== encoder cannot even view analytics ===")
logout()
login("pencoder", "encoder123")
r = c.get("/api/ml_proxy.php?action=health")
print(r.status_code, r.get_json())
assert r.status_code == 403
logout()

print("=== desk officer: can view (auto-spawns), cannot train ===")
login("jdelacuz", "officer123")
r = c.get("/api/ml_proxy.php?action=latest")
print("latest (pre-train):", r.status_code, r.get_json())
r = c.post("/api/ml_proxy.php?action=train", json={})
print("train as desk officer (should be 403):", r.status_code, r.get_json())
assert r.status_code == 403
logout()

print("=== admin: train for real (this will spawn ml/service.py, ~10-30s) ===")
login("admin", "admin123")
r = c.post("/api/ml_proxy.php?action=train", json={})
print("train status:", r.status_code)
data = r.get_json()
assert r.status_code == 200, data
print("recordCount:", data.get("recordCount"), "trainedAt:", data.get("trainedAt"))
assert data.get("trainedAt"), "trainedAt should not be null"

print("=== health now (should be up) ===")
r = c.get("/api/ml_proxy.php?action=health")
print(r.status_code, r.get_json())
assert r.get_json().get("ok") is True

print("=== latest (post-train, cached) ===")
r = c.get("/api/ml_proxy.php?action=latest")
data = r.get_json()
print(r.status_code, "trainedAt:", data.get("trainedAt"), "recordCount:", data.get("recordCount"))
assert data.get("trainedAt"), "latest trainedAt should not be null"

print("\nALL ML PROXY TESTS PASSED")
