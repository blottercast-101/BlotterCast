import os

from dotenv import load_dotenv

load_dotenv()  # loads .env from the project root if present; no-op otherwise


def _normalize_db_url(url: str) -> str:
    # Render/Railway/Heroku hand out "postgres://" but SQLAlchemy needs
    # "postgresql://" (psycopg's dialect prefix).
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
        os.environ.get("DATABASE_URL", "sqlite:///blottercast.db")
    )
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session cookies. In production (behind HTTPS on your host) these get
    # flipped on automatically via FLASK_ENV=production / RENDER env var.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"

    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8MB request body cap

    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER", os.path.join(os.path.dirname(__file__), "..", "uploads")
    )

    # ---- Email OTP (multi-factor authentication) ----
    # If SMTP_HOST is unset, outgoing OTP emails are written to
    # instance/otp_outbox.log instead of actually being sent -- lets the app
    # run end-to-end in local dev/testing without real mail credentials.
    # Set these for real delivery (any standard SMTP provider works: Gmail
    # app password, SendGrid, Mailgun, Amazon SES SMTP, your host's mail
    # relay, etc).
    SMTP_HOST = os.environ.get("SMTP_HOST")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
    SMTP_FROM = os.environ.get("SMTP_FROM", "BlotterCast <no-reply@blottercast.local>")
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "1") == "1"

    MFA_CODE_LENGTH = 6
    MFA_CODE_EXPIRY_MINUTES = int(os.environ.get("MFA_CODE_EXPIRY_MINUTES", "5"))
    MFA_MAX_ATTEMPTS = int(os.environ.get("MFA_MAX_ATTEMPTS", "5"))
    MFA_RESEND_COOLDOWN_SECONDS = int(os.environ.get("MFA_RESEND_COOLDOWN_SECONDS", "30"))
