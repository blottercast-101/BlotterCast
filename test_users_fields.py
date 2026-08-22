from app import create_app
from test_mfa_helper import login as mfa_login

app = create_app()
c = app.test_client()

mfa_login(c, "admin", "admin123")

from app.extensions import db
from app.models import User
with app.app_context():
    existing = User.query.filter_by(username="testofficer").first()
    if existing:
        db.session.delete(existing)
        db.session.commit()

# exact shape sent by frontend/users.html saveUser()
vals = {
    "name": "Test Officer",
    "username": "testofficer",
    "email": "test@example.com",
    "contact": "09171234567",
    "role": "Desk Officer",
    "status": "Active",
    "password": "testpass123",
}
r = c.post("/api/users.php?action=create", json=vals)
print("create:", r.status_code, r.get_json())
assert r.status_code == 201
uid = r.get_json()["id"]

vals2 = dict(vals)
vals2["name"] = "Test Officer Updated"
vals2["password"] = ""  # frontend sends empty string when not changing password
r2 = c.put(f"/api/users.php?action=update&id={uid}", json=vals2)
print("update (empty password):", r2.status_code, r2.get_json())
assert r2.status_code == 200

r3 = c.get("/api/users.php?action=list")
updated = next(u for u in r3.get_json() if u["id"] == uid)
print("full_name after update:", updated["full_name"])
assert updated["full_name"] == "Test Officer Updated"

print("\nUSER FIELD-NAME CHECK PASSED")
