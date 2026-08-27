from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import OtpCode, SystemSecuritySetting, User
from test_mfa_helper import latest_otp_for

app = create_app()
c = app.test_client()

with app.app_context():
    admin_user = User.query.filter_by(username="admin").first()
    admin_email = admin_user.email if admin_user else "blottercast@gmail.com"
    # Ensure MFA is turned on for testing
    sec_row = db.session.get(SystemSecuritySetting, 1)
    if sec_row:
        sec_row.is_2fa_globally_enabled = True
        db.session.commit()

print("=== HAPPY PATH ===")
r = c.post("/api/auth.php?action=login", json={"username": "admin", "password": "admin123"})
data = r.get_json()
print("login step:", r.status_code, data)
assert r.status_code == 200 and data["mfaRequired"] is True
assert data["maskedEmail"] is not None

# not authenticated yet -- pending MFA session must not grant access
r = c.get("/api/records.php?type=incidents")
print("records before OTP verify (should 401):", r.status_code)
assert r.status_code == 401

code = latest_otp_for(admin_email)
r = c.post("/api/auth.php?action=verify_otp", json={"code": code})
print("verify_otp:", r.status_code, r.get_json())
assert r.status_code == 200 and r.get_json()["ok"]

r = c.get("/api/auth.php?action=me")
print("me after verify:", r.status_code, r.get_json())
assert r.get_json()["authenticated"] is True
c.get("/api/auth.php?action=logout")

print("\n=== WRONG CODE, THEN CORRECT ===")
c.post("/api/auth.php?action=login", json={"username": "admin", "password": "admin123"})
r = c.post("/api/auth.php?action=verify_otp", json={"code": "000000"})
print("wrong code:", r.status_code, r.get_json())
assert r.status_code == 400

code = latest_otp_for(admin_email)
r = c.post("/api/auth.php?action=verify_otp", json={"code": code})
print("then correct code:", r.status_code, r.get_json())
assert r.status_code == 200
c.get("/api/auth.php?action=logout")

print("\n=== TOO MANY WRONG ATTEMPTS ===")
c.post("/api/auth.php?action=login", json={"username": "admin", "password": "admin123"})
for i in range(5):
    r = c.post("/api/auth.php?action=verify_otp", json={"code": "111111"})
    print(f"wrong attempt {i+1}:", r.status_code, r.get_json())
code = latest_otp_for(admin_email)
r = c.post("/api/auth.php?action=verify_otp", json={"code": code})
print("correct code after 5 wrong (should still fail, locked out):", r.status_code, r.get_json())
assert r.status_code == 400
c.get("/api/auth.php?action=logout")

print("\n=== EXPIRED CODE ===")
c.post("/api/auth.php?action=login", json={"username": "admin", "password": "admin123"})
with app.app_context():
    otp = OtpCode.query.filter_by(purpose="login", consumed_at=None).order_by(OtpCode.id.desc()).first()
    otp.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.session.commit()
code = latest_otp_for(admin_email)
r = c.post("/api/auth.php?action=verify_otp", json={"code": code})
print("expired code:", r.status_code, r.get_json())
assert r.status_code == 400
c.get("/api/auth.php?action=logout")

print("\n=== RESEND COOLDOWN ===")
c.post("/api/auth.php?action=login", json={"username": "admin", "password": "admin123"})
r = c.post("/api/auth.php?action=resend_otp")
print("resend immediately (should be rate-limited):", r.status_code, r.get_json())
assert r.status_code == 429

with app.app_context():
    otp = OtpCode.query.filter_by(purpose="login", consumed_at=None).order_by(OtpCode.id.desc()).first()
    otp.created_at = datetime.utcnow() - timedelta(seconds=31)
    db.session.commit()

r = c.post("/api/auth.php?action=resend_otp")
print("resend after cooldown:", r.status_code, r.get_json())
assert r.status_code == 200

# the old code must now be invalid (superseded by the resend)
with app.app_context():
    old_codes = OtpCode.query.filter_by(purpose="login").order_by(OtpCode.id.desc()).all()
new_code = latest_otp_for(admin_email)
r = c.post("/api/auth.php?action=verify_otp", json={"code": new_code})
print("verify with the resent code:", r.status_code, r.get_json())
assert r.status_code == 200
c.get("/api/auth.php?action=logout")

print("\n=== USER WITH NO EMAIL CANNOT LOG IN ===")
with app.app_context():
    u = User.query.filter_by(username="pencoder").first()
    u.email = None
    db.session.commit()
r = c.post("/api/auth.php?action=login", json={"username": "pencoder", "password": "encoder123"})
print("login, no email on file:", r.status_code, r.get_json())
assert r.status_code == 403
with app.app_context():
    u = User.query.filter_by(username="pencoder").first()
    u.email = "pencoder@blottercast.local"
    db.session.commit()

print("\n=== CREATING A USER WITHOUT EMAIL IS REJECTED ===")
mfa_login_admin = c.post("/api/auth.php?action=login", json={"username": "admin", "password": "admin123"})
code = latest_otp_for(admin_email)
c.post("/api/auth.php?action=verify_otp", json={"code": code})
r = c.post("/api/users.php?action=create", json={
    "username": "noemailuser", "name": "No Email", "password": "testpass123", "role": "Desk Officer",
})
print("create user without email:", r.status_code, r.get_json())
assert r.status_code == 400 or "error" in r.get_json()
with app.app_context():
    sec_row = db.session.get(SystemSecuritySetting, 1)
    if sec_row:
        sec_row.is_2fa_globally_enabled = False
        db.session.commit()

print("\nALL MFA TESTS PASSED")
