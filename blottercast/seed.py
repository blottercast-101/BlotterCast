"""
Creates all tables (if missing) and seeds:
  - the 8 barangay zones
  - default system_settings (security thresholds etc. used by auth)
  - the 5 demo accounts from the original README

Run with:  python seed.py
Safe to re-run — it skips anything that already exists.
"""
import bcrypt

from app import create_app
from app.extensions import db
from app.models import SystemSetting, User, Zone

ZONES = [
    ("Zone 1", "Zone 1 – Barangay Hall Area", 14.8836, 120.9655, 0.20),
    ("Zone 2", "Zone 2 – South Central", 14.8824, 120.9648, 0.11),
    ("Zone 3", "Zone 3 – Market Area", 14.8845, 120.9663, 0.18),
    ("Zone 4", "Zone 4 – Southeast Residential", 14.8818, 120.9660, 0.06),
    ("Zone 5", "Zone 5 – Northern Cluster", 14.8852, 120.9650, 0.10),
    ("Zone 6", "Zone 6 – West Interior", 14.8830, 120.9636, 0.05),
    ("Zone 7", "Zone 7 – Basketball Court Area", 14.8842, 120.9641, 0.16),
    ("Zone 8", "Zone 8 – East Road Junction", 14.8826, 120.9670, 0.14),
]

SETTINGS = {
    "barangay_name": "Barangay Mapulang Lupa",
    "municipality": "Pandi, Bulacan",
    "region": "Region III – Central Luzon",
    "captain_name": "Kapitan Jose Reyes",
    "contact_no": "0917-000-0000",
    "email": "mapulanglupa@pandi.gov.ph",
    "date_format": "MM/DD/YYYY",
    "time_format": "12-Hour (AM/PM)",
    "records_per_page": "6",
    "default_language": "English",
    "risk_threshold": "75",
    "spike_threshold": "5",
    "notif_inapp": "1",
    "notif_retrain": "1",
    "lockout_enabled": "1",
    "session_timeout": "30",
    "max_failed_logins": "5",
    "min_password_length": "8",
    "password_expiry_days": "90",
    "audit_trail": "1",
    "backup_frequency": "Daily",
    "backup_time": "02:00",
}

DEMO_USERS = [
    ("admin", "admin123", "System Administrator", "System Admin", "fileyourname@gmail.com"),
    ("kapitan", "kapitan123", "Barangay Captain", "Barangay Captain", "kapitan@blottercast.local"),
    ("jdelacuz", "officer123", "J. Dela Cruz", "Desk Officer", "jdelacuz@blottercast.local"),
    ("msantos", "officer123", "M. Santos", "Desk Officer", "msantos@blottercast.local"),
    ("pencoder", "encoder123", "P. Encoder", "Data Encoder", "pencoder@blottercast.local"),
]


def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def run():
    app = create_app()
    with app.app_context():
        db.create_all()

        for zone_id, label, lat, lng, weight in ZONES:
            if not Zone.query.get(zone_id):
                db.session.add(Zone(zone_id=zone_id, label=label, lat=lat, lng=lng, weight=weight))

        for key, value in SETTINGS.items():
            if not SystemSetting.query.get(key):
                db.session.add(SystemSetting(setting_key=key, setting_value=value))

        for username, password, full_name, role, email in DEMO_USERS:
            if not User.query.filter_by(username=username).first():
                db.session.add(User(
                    username=username, password=hash_password(password),
                    full_name=full_name, role=role, status="Active", email=email,
                ))

        db.session.commit()
        print("Seed complete. Demo accounts:")
        for username, password, _, role, email in DEMO_USERS:
            print(f"  {username:10} / {password:12} ({role}) — {email}")


if __name__ == "__main__":
    run()
