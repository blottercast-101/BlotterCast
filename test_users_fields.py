import uuid
from app import create_app
from app.extensions import db
from app.models import User
from test_mfa_helper import login as mfa_login

def run_test():
    app = create_app()
    c = app.test_client()

    mfa_login(c, "admin", "admin123")

    test_suffix = uuid.uuid4().hex[:6]
    test_username = f"to_{test_suffix}"
    test_email = f"to_{test_suffix}@example.com"

    # exact shape sent by frontend/users.html saveUser()
    vals = {
        "name": "Test Officer",
        "username": test_username,
        "email": test_email,
        "contact": "09171234567",
        "role": "Desk Officer",
        "status": "Active",
        "password": "testpass123",
    }
    r = c.post("/api/users.php?action=create", json=vals)
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.get_json()}"
    uid = r.get_json()["id"]

    try:
        vals2 = dict(vals)
        vals2["name"] = "Test Officer Updated"
        vals2["password"] = ""  # frontend sends empty string when not changing password
        r2 = c.put(f"/api/users.php?action=update&id={uid}", json=vals2)
        assert r2.status_code == 200, f"Expected 200, got {r2.status_code}: {r2.get_json()}"

        r3 = c.get("/api/users.php?action=list")
        updated = next(u for u in r3.get_json() if u["id"] == uid)
        assert updated["full_name"] == "Test Officer Updated"
        print("\nUSER FIELD-NAME CHECK PASSED")
    finally:
        c.delete(f"/api/users.php?action=delete&id={uid}")

if __name__ == "__main__":
    run_test()
