"""
Comprehensive test suite for System-Wide Security Settings:
- Global 2FA Enforcement (enforce_2fa_all_users)
- Global Inactivity Auto-Logout (idle_timeout_enabled, idle_timeout_duration_minutes)
- Admin-Only Authorization Guards
- Session Timeout Expiry in middleware
"""
from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import OtpCode, SystemSecuritySetting, SystemSetting, User
from test_mfa_helper import latest_otp_for, login as mfa_login

app = create_app()
c = app.test_client()

with app.app_context():
    # Setup test users:
    # 1. Admin
    admin_user = User.query.filter_by(username="admin").first()
    if admin_user:
        admin_user.mfa_enabled = True
        admin_user.email = "blottercast@gmail.com"
    # 2. Desk officer with MFA enabled
    mfa_user = User.query.filter_by(username="jdelacuz").first()
    if mfa_user:
        mfa_user.mfa_enabled = True
        mfa_user.email = "jdelacuz@blottercast.local"
    # 3. Desk officer with MFA disabled
    nomfa_user = User.query.filter_by(username="msantos").first()
    if nomfa_user:
        nomfa_user.mfa_enabled = False
        nomfa_user.email = "msantos@blottercast.local"
    # 4. Encoder (non-admin)
    encoder_user = User.query.filter_by(username="pencoder").first()
    if encoder_user:
        encoder_user.mfa_enabled = False
        encoder_user.email = "pencoder@blottercast.local"

# Reset security settings to baseline (Master switches OFF)
    sec_setting = SystemSecuritySetting.query.get(1)
    if not sec_setting:
        sec_setting = SystemSecuritySetting(id=1)
        db.session.add(sec_setting)
    sec_setting.is_2fa_globally_enabled = False
    sec_setting.is_idle_timeout_enabled = False
    sec_setting.idle_timeout_duration_minutes = 120
    db.session.commit()

print("=== 1. Non-Admin Cannot Access /api/admin/security-settings (RBAC) ===")
# Login as pencoder (Data Encoder)
r = c.post("/api/auth.php?action=login", json={"username": "pencoder", "password": "encoder123"})
assert r.status_code == 200 and r.get_json()["mfaRequired"] is False

# Attempt GET
r_get = c.get("/api/admin/security-settings")
print("Encoder GET /api/admin/security-settings status:", r_get.status_code)
assert r_get.status_code == 403

# Attempt PATCH
r_patch = c.patch("/api/admin/security-settings", json={"is_2fa_globally_enabled": True})
print("Encoder PATCH /api/admin/security-settings status:", r_patch.status_code)
assert r_patch.status_code == 403

# Logout
c.post("/api/auth.php?action=logout")


print("\n=== 2. Admin Can Read and Update Master Security Settings ===")
# Login as admin (with Master 2FA OFF)
r_admin_login = c.post("/api/auth.php?action=login", json={"username": "admin", "password": "admin123"})
assert r_admin_login.status_code == 200 and r_admin_login.get_json()["mfaRequired"] is False

# Read settings
r_get = c.get("/api/admin/security-settings")
print("Admin GET status:", r_get.status_code, r_get.get_json())
assert r_get.status_code == 200
data = r_get.get_json()
assert data["is_2fa_globally_enabled"] is False
assert data["is_idle_timeout_enabled"] is False
assert data["idle_timeout_duration_minutes"] == 120

# Update settings: turn Master 2FA ON and Master Idle Timeout ON
r_patch = c.patch("/api/admin/security-settings", json={
    "is_2fa_globally_enabled": True,
    "is_idle_timeout_enabled": True,
    "idle_timeout_duration_minutes": 60,
})
print("Admin PATCH status:", r_patch.status_code, r_patch.get_json())
assert r_patch.status_code == 200
assert r_patch.get_json()["settings"]["is_2fa_globally_enabled"] is True
assert r_patch.get_json()["settings"]["is_idle_timeout_enabled"] is True
assert r_patch.get_json()["settings"]["idle_timeout_duration_minutes"] == 60

# Logout
c.post("/api/auth.php?action=logout")


print("\n=== 3. Global Master 2FA ON: Uniformly Enforced Across ALL Roles ===")
# Test Desk Officer (msantos)
r_login = c.post("/api/auth.php?action=login", json={"username": "msantos", "password": "officer123"})
data = r_login.get_json()
print("msantos login with Master 2FA ON:", r_login.status_code, data)
assert r_login.status_code == 200
assert data.get("mfaRequired") is True
assert data.get("enforcedGlobally") is True

# Complete OTP verification for msantos
otp = latest_otp_for("msantos@blottercast.local")
assert otp is not None
r_verify = c.post("/api/auth.php?action=verify_otp", json={
    "code": otp,
    "pre_auth_token": data.get("pre_auth_token"),
})
assert r_verify.status_code == 200
assert r_verify.get_json()["user"]["username"] == "msantos"
c.post("/api/auth.php?action=logout")

# Test Barangay Captain (kapitan)
r_kapitan = c.post("/api/auth.php?action=login", json={"username": "kapitan", "password": "kapitan123"})
assert r_kapitan.status_code == 200 and r_kapitan.get_json()["mfaRequired"] is True

# Test Data Encoder (pencoder)
r_encoder = c.post("/api/auth.php?action=login", json={"username": "pencoder", "password": "encoder123"})
assert r_encoder.status_code == 200 and r_encoder.get_json()["mfaRequired"] is True


print("\n=== 4. Global Master 2FA OFF: No Account Is Prompted for 2FA ===")
# Admin logs in via MFA (since master 2FA is currently on)
mfa_login(c, "admin", "admin123")
r_patch = c.patch("/api/admin/security-settings", json={"is_2fa_globally_enabled": False})
assert r_patch.status_code == 200
c.post("/api/auth.php?action=logout")

# Every role now logs in directly with username and password
for user_name, pw in [("admin", "admin123"), ("kapitan", "kapitan123"), ("jdelacuz", "officer123"), ("msantos", "officer123"), ("pencoder", "encoder123")]:
    res = c.post("/api/auth.php?action=login", json={"username": user_name, "password": pw})
    assert res.status_code == 200 and res.get_json()["mfaRequired"] is False, f"Failed for {user_name}"
    c.post("/api/auth.php?action=logout")
print("All roles logged in directly without 2FA when master switch is OFF!")


print("\n=== 5. Global Idle Timeout Master Switch Behavior ===")
# Turn Idle Timeout ON
c.post("/api/auth.php?action=login", json={"username": "admin", "password": "admin123"})
c.patch("/api/admin/security-settings", json={"is_idle_timeout_enabled": True, "idle_timeout_duration_minutes": 60})

# Inactive session triggers 401
with c.session_transaction() as sess:
    sess["last_activity"] = (datetime.utcnow() - timedelta(hours=3)).timestamp()

r_check = c.get("/api/settings.php?action=list")
print("Idle Timeout ON -> Inactive session status:", r_check.status_code)
assert r_check.status_code == 401

# Turn Idle Timeout OFF
c.post("/api/auth.php?action=login", json={"username": "admin", "password": "admin123"})
c.patch("/api/admin/security-settings", json={"is_idle_timeout_enabled": False})

# Inactive session does NOT trigger 401 when Master Idle Timeout is OFF
with c.session_transaction() as sess:
    sess["last_activity"] = (datetime.utcnow() - timedelta(hours=5)).timestamp()

r_check2 = c.get("/api/settings.php?action=list")
print("Idle Timeout OFF -> Inactive session status:", r_check2.status_code)
assert r_check2.status_code == 200

print("\n=== ALL GLOBAL MASTER SECURITY SWITCH TESTS PASSED ===")
