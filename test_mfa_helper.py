"""
Shared helper for the *.py test scripts in this project: completes the
two-step (password + email OTP) login against a Flask test client.

Since these tests run without real SMTP configured, app/email.py writes
OTP codes to instance/otp_outbox.log instead of sending them -- this
helper reads the most recent one for the given address back out.
"""
import os
import re

DEMO_EMAIL_OVERRIDES = {
    "admin": "blottercast@gmail.com",
    "kapitan": "fhalynramos4@gmail.com",
}


def latest_otp_for(email: str) -> str:
    try:
        from app.email import get_latest_otp
        code = get_latest_otp(email)
        if code:
            return code
    except Exception:
        pass

    try:
        from app.models import OtpCode, User
        user = User.query.filter_by(email=email).first()
        if user:
            latest = OtpCode.query.filter_by(user_id=user.id, used=False).order_by(OtpCode.id.desc()).first()
            if latest:
                return latest.code
    except Exception:
        pass

    raise RuntimeError(f"No OTP found in memory or database for {email}")


def login(client, username, password, email=None):
    """Full login helper: completes password step, and if MFA is required,
    verifies the OTP code automatically."""
    if email is None:
        email = DEMO_EMAIL_OVERRIDES.get(username, f"{username}@blottercast.local")

    r = client.post("/api/auth.php?action=login", json={"username": username, "password": password})
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    if data.get("mfaRequired") is True or data.get("requires_2fa") is True:
        code = latest_otp_for(email)
        r2 = client.post("/api/auth.php?action=verify_otp", json={"code": code})
        assert r2.status_code == 200, r2.get_json()
        return r2.get_json()
    return data
