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
    # Uses Brevo's transactional email HTTP API (https://api.brevo.com) so it
    # works on hosts that block outbound SMTP ports (e.g. Render's free
    # tier blocks 25/465/587 entirely -- see
    # https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports).
    # If BREVO_API_KEY is unset, outgoing OTP emails are written to
    # instance/otp_outbox.log instead of actually being sent -- lets the app
    # run end-to-end in local dev/testing without real credentials.
    BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
    BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL")
    BREVO_SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "BlotterCast")

    MFA_CODE_LENGTH = 6
    MFA_CODE_EXPIRY_MINUTES = int(os.environ.get("MFA_CODE_EXPIRY_MINUTES", "5"))
    MFA_MAX_ATTEMPTS = int(os.environ.get("MFA_MAX_ATTEMPTS", "5"))
    MFA_RESEND_COOLDOWN_SECONDS = int(os.environ.get("MFA_RESEND_COOLDOWN_SECONDS", "30"))
