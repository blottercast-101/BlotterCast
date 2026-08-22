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
from datetime import datetime, timezone

import requests
from flask import current_app

OTP_OUTBOX_LOG = os.path.join(os.path.dirname(__file__), "..", "instance", "otp_outbox.log")
BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"


def render_otp_email_html(full_name: str, otp_code: str, expire_minutes: int = 10, purpose: str = "login") -> str:
    """Generate email-client-compatible HTML with inline CSS matching the exact dark-themed BlotterCast security layout."""
    name_display = full_name.strip() if full_name and full_name.strip() else "User"

    if purpose == "reset":
        lead_text = "A password reset was requested for your account. Please enter the 6-digit verification code below to complete your password reset:"
        disclaimer_text = "If you did not attempt to reset your password, please notify your administrator."
    else:
        lead_text = "Two-Factor Authentication is enabled for your account. Please enter the 6-digit verification code below to complete your sign-in:"
        disclaimer_text = "If you did not attempt to sign in, please notify your administrator."

    # Format OTP digits with single spacing
    raw_digits = str(otp_code).strip()
    spaced_code = " ".join(raw_digits)

    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="color-scheme" content="dark" />
  <meta name="supported-color-schemes" content="dark" />
  <title>BlotterCast Security Code</title>
  <!--[if mso]>
  <style type="text/css">
    body, table, td, p, span, a {{ font-family: Arial, Helvetica, sans-serif !important; }}
  </style>
  <![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: #121316; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;">
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #121316; width: 100% !important; min-width: 100%;">
    <tr>
      <td align="center" style="padding: 32px 16px 48px 16px;">
        
        <!-- Main Card Container -->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 440px; background-color: #1e232a; border-radius: 20px; box-shadow: 0 12px 36px rgba(0, 0, 0, 0.55); overflow: hidden;">
          <tr>
            <td style="padding: 40px 32px 36px 32px;">
              
              <!-- Brand Title & Subtitle -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding-bottom: 8px;">
                    <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 27px; font-weight: 700; color: #76d89a; letter-spacing: -0.02em; line-height: 1.1; display: inline-block;">
                      BlotterCast
                    </span>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-bottom: 34px;">
                    <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 12px; font-weight: 600; color: #7e8b9b; letter-spacing: 0.16em; text-transform: uppercase; line-height: 1.5; display: inline-block; text-align: center;">
                      PAMAHALAANG BARANGAY NG<br />MAPULANG LUPA
                    </span>
                  </td>
                </tr>
              </table>

              <!-- Greeting & Body Text -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td style="padding-bottom: 14px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 16px; color: #e2e8f0; line-height: 1.4;">
                    Hello <strong style="color: #ffffff; font-weight: 700;">{name_display}</strong>,
                  </td>
                </tr>
                <tr>
                  <td style="padding-bottom: 28px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14.5px; color: #94a3b8; line-height: 1.6;">
                    {lead_text}
                  </td>
                </tr>
              </table>

              <!-- OTP Verification Code Dashed Box -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td align="center">
                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="max-width: 320px; width: 100%; border: 2px dashed #22c55e; background-color: rgba(34, 197, 94, 0.05); border-radius: 16px;">
                      <tr>
                        <td align="center" style="padding: 20px 14px;">
                          <span style="font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace; font-size: 34px; font-weight: 700; color: #76d89a; letter-spacing: 12px; line-height: 1; display: inline-block; padding-left: 12px; text-shadow: 0 0 16px rgba(118, 216, 154, 0.25);">
                            {spaced_code}
                          </span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Expiration Notice & Security Disclaimer -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding-bottom: 6px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; color: #94a3b8; line-height: 1.5;">
                    This security code expires in <strong style="color: #ffffff; font-weight: 700;">{expire_minutes} minutes</strong>.
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-bottom: 36px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 13.5px; color: #7e8b9b; line-height: 1.5;">
                    {disclaimer_text}
                  </td>
                </tr>
              </table>

              <!-- Sub-footer -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 12px; color: #5b697a; line-height: 1.5; text-align: center;">
                    BlotterCast &mdash; Official Barangay Records &amp;<br />Intelligence System
                  </td>
                </tr>
              </table>

            </td>
          </tr>
        </table>

      </td>
    </tr>
  </table>
</body>
</html>"""


def send_otp_email(to_email: str, code: str, full_name: str = "", purpose: str = "login") -> bool:
    """Send the OTP email with rich responsive HTML template and text fallback.
    Returns True if it went out over the Brevo API, False if written to local outbox log."""
    greeting = f"Hi {full_name}," if full_name else "Hi,"
    expiry = current_app.config.get("MFA_CODE_EXPIRY_MINUTES", 10)

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

    html_content = render_otp_email_html(
        full_name=full_name,
        otp_code=code,
        expire_minutes=expiry,
        purpose=purpose,
    )

    api_key = current_app.config.get("BREVO_API_KEY")
    sender_email = current_app.config.get("BREVO_SENDER_EMAIL")
    if not api_key or not sender_email:
        _write_to_outbox(to_email, subject, body, html_body=html_content)
        return False

    sender_name = current_app.config.get("BREVO_SENDER_NAME", "BlotterCast Security")
    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email, "name": full_name or "User"}],
        "subject": subject,
        "htmlContent": html_content,
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
        _write_to_outbox(to_email, subject, body, error=str(e), html_body=html_content)
        return False


def _write_to_outbox(to_email: str, subject: str, body: str, error: str = None, html_body: str = None):
    os.makedirs(os.path.dirname(OTP_OUTBOX_LOG), exist_ok=True)
    with open(OTP_OUTBOX_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n----- {datetime.now(timezone.utc).isoformat()} -----\n")
        if error:
            f.write(f"[Brevo send failed ({error}) -- logged instead of sent]\n")
        else:
            f.write("[BREVO_API_KEY not configured -- logged instead of sent]\n")
        f.write(f"To: {to_email}\nSubject: {subject}\n\n{body}\n")
