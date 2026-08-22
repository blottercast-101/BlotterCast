import os
import time
from datetime import datetime, timezone

import requests
from flask import current_app

OTP_OUTBOX_LOG = os.path.join(os.path.dirname(__file__), "..", "instance", "otp_outbox.log")
BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"


def render_otp_email_html(full_name: str, otp_code: str, expire_minutes: int = 5, purpose: str = "login") -> str:
    """Generate email-client-compatible HTML with bulletproof dark mode styles and no-wrap digit cells."""
    name_display = full_name.strip() if full_name and full_name.strip() else "User"

    if purpose == "reset":
        lead_text = "A password reset was requested for your account. Please enter the 6-digit verification code below to proceed with resetting your password:"
        disclaimer_text = "If you did not request a password reset, please notify your administrator."
    else:
        lead_text = "Two-Factor Authentication is enabled for your account. Please enter the 6-digit verification code below to complete your sign-in:"
        disclaimer_text = "If you did not attempt to sign in, please notify your administrator."

    # Build 6 individual horizontal table cells so digits NEVER break into two lines
    code_digits = [c for c in str(otp_code).strip() if c.isdigit()]
    if not code_digits:
        code_digits = list(str(otp_code).strip())

    digit_tds = "".join([
        f'<td align="center" style="padding: 0 4px; font-family: \'SFMono-Regular\', Consolas, \'Liberation Mono\', Menlo, Courier, monospace, sans-serif; font-size: 30px; font-weight: 700; color: #86efac; line-height: 1; min-width: 20px;">{d}</td>'
        for d in code_digits
    ])

    timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="color-scheme" content="dark" />
  <meta name="supported-color-schemes" content="dark" />
  <title>BlotterCast Security Verification</title>
  <style type="text/css">
    :root {{
      color-scheme: dark;
      supported-color-schemes: dark;
    }}
    body, html, table, td {{
      -webkit-text-size-adjust: 100%;
      -ms-text-size-adjust: 100%;
    }}
    body {{
      margin: 0 !important;
      padding: 0 !important;
      background-color: #121212 !important;
      background-image: linear-gradient(#121212, #121212) !important;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
      color: #94a3b8 !important;
    }}
    .dark-card {{
      background-color: #1e232a !important;
      background-image: linear-gradient(#1e232a, #1e232a) !important;
    }}
    .code-box {{
      background-color: #15271e !important;
      background-image: linear-gradient(#15271e, #15271e) !important;
      border: 2px dashed #22c55e !important;
    }}
    .brand-accent {{
      color: #86efac !important;
    }}
    [data-ogsc] .brand-accent, [data-ogsc] .code-digit {{
      color: #86efac !important;
    }}
    [data-ogsb] .dark-card {{
      background-color: #1e232a !important;
    }}
    [data-ogsb] .code-box {{
      background-color: #15271e !important;
    }}
  </style>
  <!--[if mso]>
  <style type="text/css">
    body, table, td, p, span, a {{ font-family: Arial, Helvetica, sans-serif !important; }}
  </style>
  <![endif]-->
</head>
<body bgcolor="#121212" style="margin: 0; padding: 0; background-color: #121212; background-image: linear-gradient(#121212, #121212); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; color: #94a3b8;">
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" bgcolor="#121212" style="background-color: #121212; background-image: linear-gradient(#121212, #121212); table-layout: fixed; width: 100%;">
    <tr>
      <td align="center" style="padding: 28px 12px 36px 12px; background-color: #121212; background-image: linear-gradient(#121212, #121212);">
        
        <!-- Main Card Container -->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="dark-card" bgcolor="#1e232a" style="max-width: 480px; width: 100%; background-color: #1e232a; background-image: linear-gradient(#1e232a, #1e232a); border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6); overflow: hidden;">
          <tr>
            <td style="padding: 32px 24px 28px 24px;">
              
              <!-- Brand Header -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding-bottom: 4px;">
                    <span class="brand-accent" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 26px; font-weight: 700; color: #86efac; letter-spacing: -0.02em; line-height: 1.1; display: inline-block;">
                      BlotterCast
                    </span>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-bottom: 24px;">
                    <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 600; color: #94a3b8; letter-spacing: 0.16em; text-transform: uppercase; line-height: 1.4; display: inline-block;">
                      PAMAHALAANG BARANGAY NG MAPULANG LUPA
                    </span>
                  </td>
                </tr>
              </table>

              <!-- Greeting & Body Text -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td style="padding-bottom: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15.5px; color: #e2e8f0; line-height: 1.5;">
                    Hello <strong style="color: #ffffff; font-weight: 700;">{name_display}</strong>,
                  </td>
                </tr>
                <tr>
                  <td style="padding-bottom: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; color: #94a3b8; line-height: 1.6;">
                    {lead_text}
                  </td>
                </tr>
              </table>

              <!-- OTP Verification Code Box (Single Row Guaranteed) -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="margin: 0 0 20px 0;">
                <tr>
                  <td align="center">
                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" class="code-box" bgcolor="#15271e" style="width: 100%; border: 2px dashed #22c55e; background-color: #15271e; background-image: linear-gradient(#15271e, #15271e); border-radius: 12px;">
                      <tr>
                        <td align="center" style="padding: 16px 12px;">
                          <!-- Digit table ensuring single horizontal row -->
                          <table role="presentation" border="0" cellpadding="0" cellspacing="0" align="center" style="margin: 0 auto; white-space: nowrap !important;">
                            <tr>
                              {digit_tds}
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Expiration Notice & Security Disclaimer -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding-bottom: 6px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 13.5px; color: #94a3b8; line-height: 1.5;">
                    This security code expires in <strong style="color: #ffffff; font-weight: 700;">{expire_minutes} minutes</strong>.
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-bottom: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 12.5px; color: #64748b; line-height: 1.5;">
                    {disclaimer_text}
                  </td>
                </tr>
              </table>

              <!-- Subtle Divider -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="border-top: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 16px;">
                <tr><td></td></tr>
              </table>

              <!-- Sub-footer -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 11px; color: #475569; line-height: 1.4;">
                    BlotterCast &mdash; Official Barangay Records &amp; Intelligence System
                  </td>
                </tr>
              </table>

              <!-- Anti-folding token -->
              <div style="display: none; font-size: 1px; color: #1e232a; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">
                Ref: {timestamp_str}
              </div>

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
    expiry = current_app.config.get("MFA_CODE_EXPIRY_MINUTES", 5)

    if purpose == "reset":
        subject = "Your BlotterCast password reset code"
        body = (
            f"{greeting}\n\n"
            f"Your BlotterCast password reset verification code is: {code}\n\n"
            f"This security code expires in {expiry} minutes.\n"
            f"If you did not request a password reset, please notify your administrator.\n\n"
            f"BlotterCast — Official Barangay Records & Intelligence System"
        )
    else:
        subject = "Your BlotterCast verification code"
        body = (
            f"{greeting}\n\n"
            f"Your BlotterCast sign-in verification code is: {code}\n\n"
            f"This security code expires in {expiry} minutes.\n"
            f"If you did not attempt to sign in, please notify your administrator.\n\n"
            f"BlotterCast — Official Barangay Records & Intelligence System"
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

    sender_name = current_app.config.get("BREVO_SENDER_NAME", "BlotterCast")
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
