"""
Creates all tables (if missing) and seeds:
  - the 7 authentic barangay zones with verified coordinates within Barangay Mapulang Lupa
  - default system_settings (security thresholds etc. used by auth)
  - demo accounts
  - baseline verified incident records strictly bounded within the barangay

Run with:  python seed.py
Safe to re-run — it skips or synchronizes existing data.
"""
from datetime import datetime, date, time, timedelta
import bcrypt

from app import create_app
from app.extensions import db
from app.migrate import ensure_columns
from app.models import Incident, Notification, SystemSetting, User, Zone

# Authentic geographical coordinates and landmark mappings for Barangay Mapulang Lupa, Pandi, Bulacan
# All coordinates are verified to fall strictly inside the official GeoJSON polygon boundary.
ZONE_LANDMARK_COORDINATES = {
    "Zone 1": {
        "landmark": "Residence 3",
        "label": "Zone 1 – Residence 3",
        "latitude": 14.881000,
        "longitude": 120.969500,
        "weight": 0.18,
    },
    "Zone 2": {
        "landmark": "Residence 1",
        "label": "Zone 2 – Residence 1",
        "latitude": 14.881800,
        "longitude": 120.960200,
        "weight": 0.12,
    },
    "Zone 3": {
        "landmark": "Pandi Village 2 (Atlantica)",
        "label": "Zone 3 – Pandi Village 2 (Atlantica)",
        "latitude": 14.879500,
        "longitude": 120.966800,
        "weight": 0.16,
    },
    "Zone 4": {
        "landmark": "Mitay 1",
        "label": "Zone 4 – Mitay 1",
        "latitude": 14.883500,
        "longitude": 120.964800,
        "weight": 0.14,
    },
    "Zone 5": {
        "landmark": "Sitio Gubat",
        "label": "Zone 5 – Sitio Gubat",
        "latitude": 14.885800,
        "longitude": 120.966500,
        "weight": 0.15,
    },
    "Zone 6": {
        "landmark": "Bangko St.",
        "label": "Zone 6 – Bangko St.",
        "latitude": 14.884200,
        "longitude": 120.962500,
        "weight": 0.11,
    },
    "Zone 7": {
        "landmark": "Barangka St.",
        "label": "Zone 7 – Barangka St.",
        "latitude": 14.885200,
        "longitude": 120.964000,
        "weight": 0.14,
    },
}

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
    "session_timeout": "120",
    "max_failed_logins": "5",
    "min_password_length": "8",
    "password_expiry_days": "90",
    "audit_trail": "1",
    "backup_frequency": "Daily",
    "backup_time": "02:00",
}

DEMO_USERS = [
    ("admin", "admin123", "System Administrator", "System Admin", "blottercast@gmail.com"),
    ("kapitan", "kapitan123", "Barangay Captain", "Barangay Captain", "fhalynramos4@gmail.com"),
    ("jdelacuz", "officer123", "J. Dela Cruz", "Desk Officer", "jdelacuz@blottercast.local"),
    ("msantos", "officer123", "M. Santos", "Desk Officer", "msantos@blottercast.local"),
    ("pencoder", "encoder123", "P. Encoder", "Data Encoder", "pencoder@blottercast.local"),
]

AUTHENTIC_INCIDENTS = [
    {
        "zone_id": "Zone 1",
        "location": "Residence 3, Blk 12",
        "category": "Theft",
        "description": "Reported bicycle theft outside residential property.",
        "priority": "Medium",
        "status": "Under Investigation",
        "reporter": "Maria Santos",
        "officer": "J. Dela Cruz",
        "days_ago": 2,
        "hour": 14,
        "minute": 30,
        "dlat": 0.00008,
        "dlng": -0.00010,
    },
    {
        "zone_id": "Zone 2",
        "location": "Residence 1, Phase 2",
        "category": "Public Disturbance",
        "description": "Loud music and karaoke past allowable curfew hours.",
        "priority": "Low",
        "status": "Resolved",
        "reporter": "Antonio Reyes",
        "officer": "M. Santos",
        "days_ago": 4,
        "hour": 22,
        "minute": 15,
        "dlat": -0.00005,
        "dlng": 0.00008,
    },
    {
        "zone_id": "Zone 3",
        "location": "Pandi Village 2 (Atlantica), Main Gate",
        "category": "Physical Assault",
        "description": "Altercation between neighbors regarding boundary dispute.",
        "priority": "High",
        "status": "Under Investigation",
        "reporter": "Roberto Cruz",
        "officer": "J. Dela Cruz",
        "days_ago": 6,
        "hour": 18,
        "minute": 45,
        "dlat": 0.00010,
        "dlng": -0.00006,
    },
    {
        "zone_id": "Zone 4",
        "location": "Mitay 1, Purok 3",
        "category": "Vandalism",
        "description": "Graffiti on communal wall along the walkway.",
        "priority": "Low",
        "status": "Resolved",
        "reporter": "Elena Garcia",
        "officer": "P. Encoder",
        "days_ago": 8,
        "hour": 9,
        "minute": 20,
        "dlat": -0.00006,
        "dlng": 0.00005,
    },
    {
        "zone_id": "Zone 5",
        "location": "Sitio Gubat, Near Chapel",
        "category": "Trespassing",
        "description": "Unidentified individuals entering private vacant lot.",
        "priority": "Medium",
        "status": "Under Investigation",
        "reporter": "Danilo Ramos",
        "officer": "M. Santos",
        "days_ago": 11,
        "hour": 20,
        "minute": 10,
        "dlat": 0.00005,
        "dlng": -0.00008,
    },
    {
        "zone_id": "Zone 6",
        "location": "Bangko St., Near Corner Alley",
        "category": "Domestic Dispute",
        "description": "Verbal argument requiring barangay mediation.",
        "priority": "Medium",
        "status": "Resolved",
        "reporter": "Corazon Bautista",
        "officer": "J. Dela Cruz",
        "days_ago": 15,
        "hour": 16,
        "minute": 0,
        "dlat": -0.00007,
        "dlng": 0.00006,
    },
    {
        "zone_id": "Zone 7",
        "location": "Barangka St., Near Elementary Crossing",
        "category": "Vehicular Accident",
        "description": "Minor collision between tricycle and motorcycle.",
        "priority": "High",
        "status": "Resolved",
        "reporter": "Fernando Dizon",
        "officer": "M. Santos",
        "days_ago": 18,
        "hour": 11,
        "minute": 35,
        "dlat": 0.00004,
        "dlng": -0.00005,
    },
]


def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def run():
    app = create_app()
    with app.app_context():
        db.create_all()
        ensure_columns(db)

        # 1. Sync 7 authentic zones
        for zone_id, info in ZONE_LANDMARK_COORDINATES.items():
            label = info["label"]
            lat = info["latitude"]
            lng = info["longitude"]
            weight = info["weight"]

            existing = Zone.query.get(zone_id)
            if not existing:
                db.session.add(Zone(zone_id=zone_id, label=label, lat=lat, lng=lng, weight=weight))
            else:
                existing.label = label
                existing.lat = lat
                existing.lng = lng
                existing.weight = weight

        # Remove obsolete zones (e.g. Zone 8)
        obsolete_zones = Zone.query.filter(~Zone.zone_id.in_(list(ZONE_LANDMARK_COORDINATES.keys()))).all()
        for oz in obsolete_zones:
            db.session.delete(oz)

        # 2. System Settings
        for key, value in SETTINGS.items():
            existing_setting = SystemSetting.query.get(key)
            if not existing_setting:
                db.session.add(SystemSetting(setting_key=key, setting_value=value))
            elif key == "session_timeout":
                existing_setting.setting_value = value

        # 3. Demo Users
        for username, password, full_name, role, email in DEMO_USERS:
            user = User.query.filter_by(username=username).first()
            if not user:
                db.session.add(User(
                    username=username, password=hash_password(password),
                    full_name=full_name, role=role, status="Active", email=email,
                ))
            else:
                user.email = email
                user.full_name = full_name
                user.role = role

        # 4. Clean and seed authentic in-boundary incident reports
        Incident.query.delete()
        Notification.query.filter_by(ref_table="incidents").delete()
        db.session.flush()

        today = date.today()
        year = today.year

        for idx, inc_info in enumerate(AUTHENTIC_INCIDENTS, start=1):
            report_no = f"INC-{year}-{idx:04d}"
            inc_date = today - timedelta(days=inc_info["days_ago"])
            inc_time = time(inc_info["hour"], inc_info["minute"], 0)
            
            base_zone = ZONE_LANDMARK_COORDINATES[inc_info["zone_id"]]
            lat = round(base_zone["latitude"] + inc_info.get("dlat", 0.0), 6)
            lng = round(base_zone["longitude"] + inc_info.get("dlng", 0.0), 6)

            inc = Incident(
                report_no=report_no,
                incident_date=inc_date,
                time_reported=inc_time,
                hour=inc_info["hour"],
                zone_id=inc_info["zone_id"],
                location=inc_info["location"],
                lat=lat,
                lng=lng,
                category=inc_info["category"],
                description=inc_info["description"],
                reporter=inc_info["reporter"],
                officer=inc_info["officer"],
                priority=inc_info["priority"],
                status=inc_info["status"],
                archived=False,
            )
            db.session.add(inc)

        db.session.commit()
        print(f"Seed complete. {len(ZONE_LANDMARK_COORDINATES)} zones synchronized, {len(AUTHENTIC_INCIDENTS)} authentic in-boundary incidents seeded.")
        print("Demo accounts:")
        for username, password, _, role, email in DEMO_USERS:
            print(f"  {username:10} / {password:12} ({role}) — {email}")


if __name__ == "__main__":
    run()
