"""
Shared helper for the *.py test scripts in this project: completes the
two-step (password + email OTP) login against a Flask test client.

Since these tests run without real SMTP configured, app/email.py writes
OTP codes to instance/otp_outbox.log instead of sending them -- this
helper reads the most recent one for the given address back out.
"""
import os
import re

OUTBOX_PATH = os.path.join(os.path.dirname(__file__), "instance", "otp_outbox.log")

# Demo accounts whose email doesn't follow the <username>@blottercast.local
# convention (see seed.py) -- kept here so callers can keep doing
# mfa_login(client, "admin", "admin123") without knowing the exception.
DEMO_EMAIL_OVERRIDES = {
    "admin": "blottercast@gmail.com",
    "kapitan": "fhalynramos4@gmail.com",
}


def latest_otp_for(email: str) -> str:
    with open(OUTBOX_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    for block in reversed(content.split("----- ")):
        if f"To: {email}" in block:
            m = re.search(r"verification code is: (\d{4,8})", block)
            if m:
                return m.group(1)
    raise RuntimeError(f"No OTP found in outbox for {email}")


def login(client, username, password, email=None):
    """Full two-step login: password, then OTP pulled from the dev outbox.
    Returns the final verify_otp JSON body. Raises AssertionError on any
    unexpected status code (mirrors the old single-call login() helpers)."""
    if email is None:
        email = DEMO_EMAIL_OVERRIDES.get(username, f"{username}@blottercast.local")

    r = client.post("/api/auth.php?action=login", json={"username": username, "password": password})
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert data.get("mfaRequired") is True, data

    code = latest_otp_for(email)
    r2 = client.post("/api/auth.php?action=verify_otp", json={"code": code})
    assert r2.status_code == 200, r2.get_json()
    return r2.get_json()
