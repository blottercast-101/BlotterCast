import io
from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import SystemBackup, SystemSecuritySetting, SystemSetting, User
from test_mfa_helper import login as mfa_login

app = create_app()
c = app.test_client()


def login(u, p):
    return mfa_login(c, u, p)


def logout():
    c.post("/api/auth.php?action=logout")


# ------------------------------------------------------------------
print("=== PASSWORD CHANGE FLOW ===")
with app.app_context():
    from app.blueprints.auth import _hash_password
    from app.models import PasswordHistory
    u = User.query.filter_by(username="msantos").first()
    if u:
        u.password = _hash_password("officer123")
        PasswordHistory.query.filter_by(user_id=u.id).delete()
        db.session.commit()

login("msantos", "officer123")

r = c.post("/api/auth.php?action=change_password",
           json={"currentPassword": "wrongpass", "newPassword": "newpass123"})
print("wrong current password:", r.status_code, r.get_json())
assert r.status_code == 400


r = c.post("/api/auth.php?action=change_password",
           json={"currentPassword": "officer123", "newPassword": "short"})
print("too-short new password:", r.status_code, r.get_json())
assert r.status_code == 400 or r.status_code == 422 or "error" in r.get_json()

# Password reuse test: attempting to reuse current password should fail
r = c.post("/api/auth.php?action=change_password",
           json={"currentPassword": "officer123", "newPassword": "officer123"})
print("reuse current password:", r.status_code, r.get_json())
assert r.status_code == 400

r = c.post("/api/auth.php?action=change_password",
           json={"currentPassword": "officer123", "newPassword": "newpass123"})
print("valid change:", r.status_code, r.get_json())
assert r.status_code == 200 and r.get_json()["ok"]

# Password reuse test: attempting to reuse old historical password should fail
r = c.post("/api/auth.php?action=change_password",
           json={"currentPassword": "newpass123", "newPassword": "officer123"})
print("reuse historical password:", r.status_code, r.get_json())
assert r.status_code == 400

logout()
r = c.post("/api/auth.php?action=login", json={"username": "msantos", "password": "officer123"})
print("old password after change (should fail):", r.status_code)
assert r.status_code == 401

r = c.post("/api/auth.php?action=login", json={"username": "msantos", "password": "newpass123"})
print("new password login:", r.status_code, r.get_json())
assert r.status_code == 200
logout()

# Reset msantos back for subsequent test runs
with app.app_context():
    u = User.query.filter_by(username="msantos").first()
    if u:
        u.password = _hash_password("officer123")
        PasswordHistory.query.filter_by(user_id=u.id).delete()
        db.session.commit()

# ------------------------------------------------------------------
print("\n=== SESSION TIMEOUT EXPIRY ===")
login("admin", "admin123")
with app.app_context():
    sec_row = db.session.get(SystemSecuritySetting, 1)
    if not sec_row:
        sec_row = SystemSecuritySetting(id=1, is_idle_timeout_enabled=True, idle_timeout_duration_minutes=30)
        db.session.add(sec_row)
    else:
        sec_row.is_idle_timeout_enabled = True
        sec_row.idle_timeout_duration_minutes = 30
    db.session.commit()

r = c.get("/api/auth.php?action=me")
print("me (fresh session):", r.status_code, r.get_json())
assert r.get_json()["authenticated"] is True

# force last_activity far enough in the past to exceed the 30-min timeout
with c.session_transaction() as sess:
    sess["last_activity"] = (datetime.utcnow() - timedelta(minutes=31)).timestamp()

r = c.get("/api/auth.php?action=me")
print("me (after simulated 31min idle):", r.status_code, r.get_json())
assert r.get_json()["authenticated"] is False, "session should have expired"

r = c.get("/api/records.php?type=incidents")
print("records after expiry (should 401):", r.status_code, r.get_json())
assert r.status_code == 401

with app.app_context():
    sec_row = db.session.get(SystemSecuritySetting, 1)
    if sec_row:
        sec_row.is_idle_timeout_enabled = False
        sec_row.idle_timeout_duration_minutes = 120
        db.session.commit()

# ------------------------------------------------------------------
print("\n=== SIGNATURE UPLOAD / REMOVAL ===")
login("admin", "admin123")
with app.app_context():
    target = User.query.filter_by(username="kapitan").first()
    uid = target.id

# minimal valid 1x1 PNG
png_bytes = bytes.fromhex(
    "89504e470d0a1a0a0000000d494844520000000100000001080600000"
    "01f15c4890000000a4944415478da6360000002000155bd1c2c0000000049454e44ae426082"
)

r = c.post(f"/api/users.php?action=upload_signature&id={uid}",
           data={"signature": (io.BytesIO(png_bytes), "sig.png", "image/png")},
           content_type="multipart/form-data")
print("upload signature:", r.status_code, r.get_json())
assert r.status_code == 200 and r.get_json()["ok"]
sig_path = r.get_json()["signaturePath"]

import os
full_path = os.path.join(app.static_folder, sig_path)
print("file exists on disk:", os.path.isfile(full_path))
assert os.path.isfile(full_path)

r = c.get("/api/users.php?action=captain_signature")
print("captain_signature after upload:", r.status_code, r.get_json())
assert r.get_json()["signaturePath"] == sig_path

# upload again -> old file should be replaced/removed
r2 = c.post(f"/api/users.php?action=upload_signature&id={uid}",
            data={"signature": (io.BytesIO(png_bytes), "sig2.png", "image/png")},
            content_type="multipart/form-data")
print("re-upload signature:", r2.status_code, r2.get_json())
new_sig_path = r2.get_json()["signaturePath"]
print("old file removed:", not os.path.isfile(full_path))
assert not os.path.isfile(full_path), "old signature file should have been deleted on replace"

# wrong mimetype rejected
r3 = c.post(f"/api/users.php?action=upload_signature&id={uid}",
            data={"signature": (io.BytesIO(b"not an image"), "sig.txt", "text/plain")},
            content_type="multipart/form-data")
print("wrong mimetype:", r3.status_code, r3.get_json())
assert r3.status_code == 400 or "error" in r3.get_json()

# oversized file rejected (>2MB)
big = io.BytesIO(b"\x89PNG" + b"0" * (2 * 1024 * 1024 + 100))
r4 = c.post(f"/api/users.php?action=upload_signature&id={uid}",
            data={"signature": (big, "big.png", "image/png")},
            content_type="multipart/form-data")
print("oversized file:", r4.status_code, r4.get_json())
assert "error" in r4.get_json()

r5 = c.post(f"/api/users.php?action=remove_signature&id={uid}")
print("remove signature:", r5.status_code, r5.get_json())
assert r5.status_code == 200 and r5.get_json()["ok"]

full_new_path = os.path.join(app.static_folder, new_sig_path)
print("file removed from disk:", not os.path.isfile(full_new_path))
assert not os.path.isfile(full_new_path)

with app.app_context():
    refreshed = db.session.get(User, uid)
    print("db signature_path is None:", refreshed.signature_path is None)
    assert refreshed.signature_path is None

logout()

# ------------------------------------------------------------------
print("\n=== AUTO-BACKUP-DUE SCHEDULING ===")
login("admin", "admin123")

with app.app_context():
    SystemBackup.query.delete()
    db.session.commit()

r = c.get("/api/settings.php?action=auto_backup_check")
print("auto_backup_check (no prior backups, should run):", r.status_code, r.get_json())
assert r.get_json()["ran"] is True

r2 = c.get("/api/settings.php?action=auto_backup_check")
print("auto_backup_check (immediately again, should NOT run):", r2.status_code, r2.get_json())
assert r2.get_json()["ran"] is False

# backdate the last backup by 25 hours -> should be due again under default "Daily"
with app.app_context():
    last = SystemBackup.query.order_by(SystemBackup.id.desc()).first()
    last.created_at = datetime.utcnow() - timedelta(hours=25)
    db.session.commit()

r3 = c.get("/api/settings.php?action=auto_backup_check")
print("auto_backup_check (backdated 25h, Daily freq, should run):", r3.status_code, r3.get_json())
assert r3.get_json()["ran"] is True

# switch frequency to "Every 12 hours", backdate 13h -> due
r4 = c.post("/api/settings.php?action=save", json={"backup_frequency": "Every 12 hours"})
print("save backup_frequency=Every 12 hours:", r4.status_code, r4.get_json())

with app.app_context():
    last = SystemBackup.query.order_by(SystemBackup.id.desc()).first()
    last.created_at = datetime.utcnow() - timedelta(hours=13)
    db.session.commit()

r5 = c.get("/api/settings.php?action=auto_backup_check")
print("auto_backup_check (backdated 13h, 12h freq, should run):", r5.status_code, r5.get_json())
assert r5.get_json()["ran"] is True

r6 = c.get("/api/settings.php?action=auto_backup_check")
print("auto_backup_check (immediately again, should NOT run):", r6.status_code, r6.get_json())
assert r6.get_json()["ran"] is False

print("\nALL EXTRA COVERAGE TESTS PASSED")
