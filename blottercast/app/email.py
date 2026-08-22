"""
Outgoing email for BlotterCast — currently used only for MFA login OTP codes.

Sends via Brevo's transactional email HTTP API (https://api.brevo.com) over
HTTPS/443 rather than SMTP. This matters because many hosts block outbound
SMTP ports (25/465/587) on free-tier services -- e.g. Render blocks them
entirely as of Sept 2025 (see
https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports).
An HTTP API call over 443 sidesteps that since providers can't block normal
web traffic without breaking everything else.

If BREVO_API_KEY isn't configured (see app/config.py), the email is written
to instance/otp_outbox.log instead of being sent. That keeps local dev and
automated tests working end-to-end without real credentials, the same
graceful-degradation approach used elsewhere in this app (see the ML
service auto-start).
"""
import os
from datetime import datetime

import requests
from flask import current_app

OTP_OUTBOX_LOG = os.path.join(os.path.dirname(__file__), "..", "instance", "otp_outbox.log")
BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"


def send_otp_email(to_email: str, code: str, full_name: str = "", purpose: str = "login") -> bool:
    """Send the OTP email. Returns True if it went out over the Brevo API,
    False if it was written to the local outbox log instead (Brevo not
    configured, or the send failed)."""
    greeting = f"Hi {full_name}," if full_name else "Hi,"
    expiry = current_app.config["MFA_CODE_EXPIRY_MINUTES"]

    if purpose == "reset":
        subject = "Your BlotterCast password reset code"
        body = (
            f"{greeting}\n\n"
            f"Your BlotterCast password reset verification code is: {code}\n\n"
            f"This code expires in {expiry} minutes. If you did not request a "
            f"password reset, you can safely ignore this email — your password "
            f"will not be changed.\n\n"
            f"— BlotterCast"
        )
    else:
        subject = "Your BlotterCast verification code"
        body = (
            f"{greeting}\n\n"
            f"Your BlotterCast sign-in verification code is: {code}\n\n"
            f"This code expires in {expiry} minutes. If you did not attempt to "
            f"sign in, you can safely ignore this email.\n\n"
            f"— BlotterCast"
        )

    api_key = current_app.config.get("BREVO_API_KEY")
    sender_email = current_app.config.get("BREVO_SENDER_EMAIL")
    if not api_key or not sender_email:
        _write_to_outbox(to_email, subject, body)
        return False

    sender_name = current_app.config.get("BREVO_SENDER_NAME", "BlotterCast")
    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "textContent": body,
    }
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        r = requests.post(BREVO_SEND_URL, json=payload, headers=headers, timeout=10)
        if r.status_code >= 300:
            raise RuntimeError(f"Brevo API {r.status_code}: {r.text[:300]}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send {purpose} OTP email to {to_email}: {e}")
        _write_to_outbox(to_email, subject, body, error=str(e))
        return False


def _write_to_outbox(to_email: str, subject: str, body: str, error: str = None):
    os.makedirs(os.path.dirname(OTP_OUTBOX_LOG), exist_ok=True)
    with open(OTP_OUTBOX_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n----- {datetime.utcnow().isoformat()} -----\n")
        if error:
            f.write(f"[Brevo send failed ({error}) -- logged instead of sent]\n")
        else:
            f.write("[BREVO_API_KEY not configured -- logged instead of sent]\n")
        f.write(f"To: {to_email}\nSubject: {subject}\n\n{body}\n")
