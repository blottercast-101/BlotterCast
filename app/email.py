import os
import re
from datetime import datetime, timezone

import requests
from flask import current_app

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"

# In-memory development outbox store (no .log files created on disk)
DEV_OUTBOX = []


def get_latest_otp(email: str) -> str:
    """Retrieve the most recent OTP code sent to an email address in-memory."""
    for item in reversed(DEV_OUTBOX):
        if item.get("to_email") == email:
            m = re.search(r"verification code is:\s*(\d{4,8})", item.get("body", ""))
            if m:
                return m.group(1)
    return None


def clear_dev_outbox():
    """Clear in-memory development outbox entries."""
    DEV_OUTBOX.clear()



def render_otp_email_html(full_name: str, otp_code: str, expire_minutes: int = 5, purpose: str = "login") -> str:
    """Generate email-client-compatible HTML with light/dark mode responsiveness, seamless inline typography, and no-wrap digit cells."""
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
        f'<td align="center" class="code-digit" style="padding: 0 5px; font-family: \'SFMono-Regular\', Consolas, \'Liberation Mono\', Menlo, Courier, monospace, sans-serif; font-size: 32px; font-weight: 800; color: #16a34a; line-height: 1; min-width: 22px;">{d}</td>'
        for d in code_digits
    ])

    timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="color-scheme" content="light dark" />
  <meta name="supported-color-schemes" content="light dark" />
  <title>BlotterCast Security Verification</title>
  <style type="text/css">
    :root {{
      color-scheme: light dark;
      supported-color-schemes: light dark;
    }}
    body, html, table, td {{
      -webkit-text-size-adjust: 100%;
      -ms-text-size-adjust: 100%;
    }}
    body {{
      margin: 0 !important;
      padding: 0 !important;
      background-color: #f1f5f9;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
      color: #0f172a;
    }}
    @media (prefers-color-scheme: dark) {{
      body, .email-body, .email-bg {{
        background-color: #0f172a !important;
        color: #f8fafc !important;
      }}
      .email-card {{
        background-color: #1a2332 !important;
        border-color: #334155 !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
      }}
      .email-text, .dynamic-text {{
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
      }}
      .email-subtext {{
        color: #cbd5e1 !important;
        -webkit-text-fill-color: #cbd5e1 !important;
      }}
      .email-muted {{
        color: #94a3b8 !important;
        -webkit-text-fill-color: #94a3b8 !important;
      }}
      .email-divider {{
        border-color: #334155 !important;
      }}
      .code-box {{
        background-color: #0d2818 !important;
        border-color: #22c55e !important;
      }}
      .code-digit {{
        color: #4ade80 !important;
        -webkit-text-fill-color: #4ade80 !important;
      }}
      .brand-title {{
        color: #4ade80 !important;
        -webkit-text-fill-color: #4ade80 !important;
      }}
    }}
    /* Outlook.com / Web App Dark Mode Overrides */
    [data-ogsc] .email-bg {{ background-color: #0f172a !important; }}
    [data-ogsc] .email-card {{ background-color: #1a2332 !important; border-color: #334155 !important; }}
    [data-ogsc] .email-text, [data-ogsc] .dynamic-text {{ color: #ffffff !important; }}
    [data-ogsc] .email-subtext {{ color: #cbd5e1 !important; }}
    [data-ogsc] .email-muted {{ color: #94a3b8 !important; }}
    [data-ogsc] .code-digit {{ color: #4ade80 !important; }}
    [data-ogsc] .brand-title {{ color: #4ade80 !important; }}
    [data-ogsb] .email-card {{ background-color: #1a2332 !important; }}
    [data-ogsb] .code-box {{ background-color: #0d2818 !important; }}
  </style>
  <!--[if mso]>
  <style type="text/css">
    body, table, td, p, span, a, strong {{ font-family: Arial, Helvetica, sans-serif !important; }}
  </style>
  <![endif]-->
</head>
<body class="email-body" bgcolor="#f1f5f9" style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; color: #0f172a;">
  <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="email-bg" bgcolor="#f1f5f9" style="background-color: #f1f5f9; table-layout: fixed; width: 100%;">
    <tr>
      <td align="center" style="padding: 32px 12px 40px 12px;">
        
        <!-- Main Card Container -->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="email-card" bgcolor="#ffffff" style="max-width: 480px; width: 100%; background-color: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06); overflow: hidden;">
          <tr>
            <td style="padding: 32px 24px 28px 24px;">
              
              <!-- Brand Header -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding-bottom: 4px;">
                    <span class="brand-title" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 26px; font-weight: 800; color: #16a34a; letter-spacing: -0.02em; line-height: 1.1; display: inline-block;">
                      BlotterCast
                    </span>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-bottom: 24px;">
                    <span class="email-muted" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 600; color: #64748b; letter-spacing: 0.16em; text-transform: uppercase; line-height: 1.4; display: inline-block;">
                      PAMAHALAANG BARANGAY NG MAPULANG LUPA
                    </span>
                  </td>
                </tr>
              </table>

              <!-- Greeting & Body Text -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td class="email-text" style="padding-bottom: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15.5px; color: #0f172a; line-height: 1.5;">
                    Hello <strong class="dynamic-text" style="font-weight: 700; color: inherit;">{name_display}</strong>,
                  </td>
                </tr>
                <tr>
                  <td class="email-subtext" style="padding-bottom: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; color: #334155; line-height: 1.6;">
                    {lead_text}
                  </td>
                </tr>
              </table>

              <!-- OTP Verification Code Box (Single Row Guaranteed) -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="margin: 0 0 20px 0;">
                <tr>
                  <td align="center">
                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" class="code-box" bgcolor="#f0fdf4" style="width: 100%; border: 2px dashed #22c55e; background-color: #f0fdf4; border-radius: 12px;">
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
                  <td align="center" class="email-subtext" style="padding-bottom: 8px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 13.5px; color: #334155; line-height: 1.5;">
                    This security code expires in <strong class="dynamic-text" style="font-weight: 700; color: inherit;">{expire_minutes} minutes</strong>.
                  </td>
                </tr>
                <tr>
                  <td align="center" class="email-muted" style="padding-bottom: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 12.5px; color: #64748b; line-height: 1.5;">
                    {disclaimer_text}
                  </td>
                </tr>
              </table>

              <!-- Subtle Divider -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" class="email-divider" width="100%" style="border-top: 1px solid #e2e8f0; margin-bottom: 16px;">
                <tr><td></td></tr>
              </table>

              <!-- Sub-footer -->
              <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" class="email-muted" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 11px; color: #64748b; line-height: 1.4;">
                    BlotterCast &mdash; Official Barangay Records &amp; Intelligence System
                  </td>
                </tr>
              </table>

              <!-- Anti-folding token -->
              <div style="display: none; font-size: 1px; color: #f1f5f9; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">
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
    try:
        entry = {
            "to_email": to_email,
            "subject": subject,
            "body": body,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        DEV_OUTBOX.append(entry)
        if len(DEV_OUTBOX) > 200:
            del DEV_OUTBOX[:-100]

        reason = f"Brevo send failed ({error})" if error else "BREVO_API_KEY not configured"
        current_app.logger.info(
            f"[OTP OUTBOX] {reason} | To: {to_email} | Subject: {subject}"
        )
    except Exception:
        pass
