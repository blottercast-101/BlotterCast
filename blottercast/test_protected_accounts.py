import time
from app import create_app
from app.models import User
from app.extensions import db
from test_mfa_helper import login as mfa_login

app = create_app()
c = app.test_client()

with app.app_context():
    # Ensure admin and kapitan exist
    admin_user = User.query.filter_by(role="System Admin").first()
    kapitan_user = User.query.filter_by(role="Barangay Captain").first()
    assert admin_user is not None, "System Admin account must exist"
    assert kapitan_user is not None, "Barangay Captain account must exist"
    admin_id = admin_user.id
    kapitan_id = kapitan_user.id

# Login as admin
mfa_login(c, "admin", "admin123")

# 1. Test List Users: verify is_protected field
r = c.get("/api/users.php?action=list")
assert r.status_code == 200, f"List users failed: {r.status_code}"
users = r.get_json()
admin_data = next(u for u in users if u["id"] == admin_id)
kapitan_data = next(u for u in users if u["id"] == kapitan_id)

assert admin_data["is_protected"] is True, "System Admin must have is_protected=True"
assert admin_data["status"] == "Active", "System Admin status must be Active"
assert kapitan_data["is_protected"] is True, "Barangay Captain must have is_protected=True"
assert kapitan_data["status"] == "Active", "Barangay Captain status must be Active"
print("[OK] List API correctly identifies protected accounts as is_protected=True and Active")

# 2. Test Toggle Status on Barangay Captain
r_toggle_kapitan = c.post(f"/api/users.php?action=toggle_status&id={kapitan_id}")
assert r_toggle_kapitan.status_code == 400, f"Expected 400 on toggle kapitan, got {r_toggle_kapitan.status_code}"
err = r_toggle_kapitan.get_json()
assert "protected and cannot be suspended" in err.get("error", ""), f"Unexpected error msg: {err}"
print("[OK] Backend gracefully blocks suspending Barangay Captain:", err["error"])

# 3. Test Toggle Status on System Admin
r_toggle_admin = c.post(f"/api/users.php?action=toggle_status&id={admin_id}")
assert r_toggle_admin.status_code == 400, f"Expected 400 on toggle admin, got {r_toggle_admin.status_code}"
err = r_toggle_admin.get_json()
assert "protected and cannot be suspended" in err.get("error", ""), f"Unexpected error msg: {err}"
print("[OK] Backend gracefully blocks suspending System Admin:", err["error"])

# 4. Test Delete on Barangay Captain
r_del_kapitan = c.delete(f"/api/users.php?action=delete&id={kapitan_id}")
assert r_del_kapitan.status_code == 400, f"Expected 400 on delete kapitan, got {r_del_kapitan.status_code}"
err = r_del_kapitan.get_json()
assert "protected and cannot be deleted" in err.get("error", ""), f"Unexpected error msg: {err}"
print("[OK] Backend gracefully blocks deleting Barangay Captain:", err["error"])

# 5. Test Delete on System Admin
r_del_admin = c.delete(f"/api/users.php?action=delete&id={admin_id}")
assert r_del_admin.status_code in (400, 403), f"Expected 400 or 403 on delete admin, got {r_del_admin.status_code}"
err = r_del_admin.get_json()
print("[OK] Backend gracefully blocks deleting System Admin:", err["error"])

# 6. Test Update Barangay Captain attempting to suspend
update_payload = {
    "name": kapitan_data["full_name"],
    "email": kapitan_data["email"],
    "role": "Barangay Captain",
    "status": "Suspended"
}
r_up = c.put(f"/api/users.php?action=update&id={kapitan_id}", json=update_payload)
assert r_up.status_code == 200, f"Update returned {r_up.status_code}: {r_up.get_json()}"

with app.app_context():
    kap_check = db.session.get(User, kapitan_id)
    assert kap_check.status == "Active", f"Protected user status must remain Active, got {kap_check.status}"
print("[OK] Updating a protected user ignores any attempts to set status to Suspended and keeps it Active")

# 7. Test Non-protected user lifecycle (create -> suspend -> activate -> delete)
unique_suffix = int(time.time())
test_officer = {
    "name": f"Regular Officer {unique_suffix}",
    "username": f"officer_{unique_suffix}",
    "email": f"officer_{unique_suffix}@example.com",
    "role": "Desk Officer",
    "status": "Active",
    "password": "Password123"
}
r_create = c.post("/api/users.php?action=create", json=test_officer)
assert r_create.status_code == 201, f"Failed to create test officer: {r_create.get_json()}"
officer_id = r_create.get_json()["id"]

# Toggle suspend test officer
r_tog1 = c.post(f"/api/users.php?action=toggle_status&id={officer_id}")
assert r_tog1.status_code == 200 and r_tog1.get_json()["status"] == "Suspended"

# Toggle activate test officer
r_tog2 = c.post(f"/api/users.php?action=toggle_status&id={officer_id}")
assert r_tog2.status_code == 200 and r_tog2.get_json()["status"] == "Active"

# Delete test officer
r_del = c.delete(f"/api/users.php?action=delete&id={officer_id}")
assert r_del.status_code == 200 and r_del.get_json()["ok"] is True
print("[OK] Non-protected accounts can still be suspended, activated, and deleted normally")

print("\nALL PROTECTED ACCOUNT TESTS PASSED SUCCESSFULLY!")
