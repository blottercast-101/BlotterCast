"""
Outgoing email for BlotterCast — currently used only for MFA login OTP codes.

If SMTP_HOST isn't configured (see app/config.py), the email is written to
instance/otp_outbox.log instead of being sent. That keeps local dev and
automated tests working end-to-end without real mail credentials, the same
graceful-degradation approach used elsewhere in this app (see the ML
service auto-start). For a real deployment, set SMTP_HOST/PORT/USER/
PASSWORD/FROM in the environment — any standard SMTP provider works.
"""
import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage

from flask import current_app

OTP_OUTBOX_LOG = os.path.join(os.path.dirname(__file__), "..", "instance", "otp_outbox.log")


def send_otp_email(to_email: str, code: str, full_name: str = "", purpose: str = "login") -> bool:
    """Send the OTP email. Returns True if it went out over real SMTP,
    False if it was written to the local outbox log instead (SMTP not
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

    host = current_app.config.get("SMTP_HOST")
    if not host:
        _write_to_outbox(to_email, subject, body)
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = current_app.config["SMTP_FROM"]
    msg["To"] = to_email
    msg.set_content(body)

    port = current_app.config["SMTP_PORT"]
    user = current_app.config.get("SMTP_USER")
    password = current_app.config.get("SMTP_PASSWORD")
    use_tls = current_app.config["SMTP_USE_TLS"]

    try:
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context, timeout=10) as server:
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
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
            f.write(f"[SMTP send failed ({error}) -- logged instead of sent]\n")
        else:
            f.write("[SMTP not configured -- logged instead of sent]\n")
        f.write(f"To: {to_email}\nSubject: {subject}\n\n{body}\n")
