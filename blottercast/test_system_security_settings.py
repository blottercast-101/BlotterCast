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
from app.models import OtpCode, SystemSetting, User
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

    # Reset security settings to baseline
    for key, val in [("enforce_2fa_all_users", "0"), ("idle_timeout_enabled", "1"), ("idle_timeout_duration_minutes", "120"), ("session_timeout", "120")]:
        st = SystemSetting.query.get(key)
        if st:
            st.setting_value = val
        else:
            db.session.add(SystemSetting(setting_key=key, setting_value=val))
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
r_patch = c.patch("/api/admin/security-settings", json={"enforce_2fa_all_users": True})
print("Encoder PATCH /api/admin/security-settings status:", r_patch.status_code)
assert r_patch.status_code == 403

# Logout
c.post("/api/auth.php?action=logout")


print("\n=== 2. Admin Can Read and Update System-Wide Security Settings ===")
# Login as admin
mfa_login(c, "admin", "admin123")

# Read settings
r_get = c.get("/api/admin/security-settings")
print("Admin GET status:", r_get.status_code, r_get.get_json())
assert r_get.status_code == 200
data = r_get.get_json()
assert data["enforce_2fa_all_users"] is False
assert data["idle_timeout_enabled"] is True
assert data["idle_timeout_duration_minutes"] == 120

# Update settings: enable global 2FA and adjust idle timeout
r_patch = c.patch("/api/admin/security-settings", json={
    "enforce_2fa_all_users": True,
    "idle_timeout_enabled": True,
    "idle_timeout_duration_minutes": 60,
})
print("Admin PATCH status:", r_patch.status_code, r_patch.get_json())
assert r_patch.status_code == 200
assert r_patch.get_json()["settings"]["enforce_2fa_all_users"] is True
assert r_patch.get_json()["settings"]["idle_timeout_duration_minutes"] == 60
assert r_patch.get_json()["settings"]["session_timeout"] == 60

# Logout
c.post("/api/auth.php?action=logout")


print("\n=== 3. Global 2FA Enforcement: All Users Forced into 2FA Flow ===")
# Login as msantos (who has mfa_enabled = False individually)
r_login = c.post("/api/auth.php?action=login", json={"username": "msantos", "password": "officer123"})
data = r_login.get_json()
print("msantos login status with Global 2FA ON:", r_login.status_code, data)
assert r_login.status_code == 200
assert data.get("mfaRequired") is True
assert data.get("enforcedGlobally") is True
assert data.get("pre_auth_token") is not None

# Verify that session is not authenticated yet
r_me = c.get("/api/auth.php?action=me")
assert r_me.get_json()["authenticated"] is False

# Complete OTP verification
otp = latest_otp_for("msantos@blottercast.local")
assert otp is not None

r_verify = c.post("/api/auth.php?action=verify_otp", json={
    "code": otp,
    "pre_auth_token": data.get("pre_auth_token"),
})
print("OTP verification status:", r_verify.status_code, r_verify.get_json())
assert r_verify.status_code == 200
assert r_verify.get_json()["user"]["username"] == "msantos"

# User is now fully authenticated
r_me = c.get("/api/auth.php?action=me")
assert r_me.get_json()["authenticated"] is True
c.post("/api/auth.php?action=logout")


print("\n=== 4. Disabling Global 2FA: Reverts to Individual Account Settings ===")
mfa_login(c, "admin", "admin123")
r_patch = c.patch("/api/admin/security-settings", json={"enforce_2fa_all_users": False})
assert r_patch.status_code == 200
c.post("/api/auth.php?action=logout")

# msantos (mfa_enabled = False) logs in directly without 2FA
r_login = c.post("/api/auth.php?action=login", json={"username": "msantos", "password": "officer123"})
assert r_login.status_code == 200 and r_login.get_json()["mfaRequired"] is False
c.post("/api/auth.php?action=logout")

# jdelacuz (mfa_enabled = True) still requires 2FA
r_login = c.post("/api/auth.php?action=login", json={"username": "jdelacuz", "password": "officer123"})
assert r_login.status_code == 200 and r_login.get_json()["mfaRequired"] is True


print("\n=== 5. Inactivity Auto-Logout Middleware Enforcement ===")
mfa_login(c, "admin", "admin123")

# Simulate session inactivity exceeding timeout (e.g. 3 hours ago)
with c.session_transaction() as sess:
    sess["last_activity"] = (datetime.utcnow() - timedelta(hours=3)).timestamp()

r_check = c.get("/api/settings.php?action=list")
print("Inactive session request status:", r_check.status_code, r_check.get_json())
assert r_check.status_code == 401
assert "expired due to inactivity" in r_check.get_json()["error"]


print("\n=== ALL SYSTEM-WIDE SECURITY SETTINGS TESTS PASSED ===")
