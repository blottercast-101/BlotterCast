"""
Creates all tables (if missing) and seeds:
  - the 8 barangay zones
  - default system_settings (security thresholds etc. used by auth)
  - the 5 demo accounts from the original README

Run with:  python seed.py
Safe to re-run — it skips anything that already exists.
"""
import bcrypt
from sqlalchemy import inspect, text

from app import create_app
from app.extensions import db
from app.models import SystemSetting, User, Zone

ZONES = [
    # Repositioned + relabeled to match the actual named subdivisions/
    # landmarks inside the barangay boundary (was generic "Zone N –
    # <generic area>" placeholders on a much tighter cluster of points).
    ("Zone 1", "Zone 1 – Mapulang Lupa Proper (Barangay Hall Area)", 14.8836, 120.9655, 0.20),
    ("Zone 2", "Zone 2 – Mapulang Lupa Elementary School Area", 14.8800, 120.9634, 0.11),
    ("Zone 3", "Zone 3 – Sitio Bata", 14.8863, 120.9679, 0.18),
    ("Zone 4", "Zone 4 – Pandi Village 2", 14.8782, 120.9670, 0.06),
    ("Zone 5", "Zone 5 – Silangan Corridor (Pandi–Angat Road)", 14.8884, 120.9640, 0.10),
    ("Zone 6", "Zone 6 – Pandi Residences 1", 14.8818, 120.9598, 0.05),
    ("Zone 7", "Zone 7 – Pandi Encampment One", 14.8854, 120.9613, 0.16),
    ("Zone 8", "Zone 8 – Pandi Residences 3", 14.8806, 120.9700, 0.14),
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


def sync_schema():
    """
    db.create_all() only creates tables that don't exist yet — it never
    alters a table that's already there. On a persistent DB (like the one
    Render gives this service), that means a column added to a model after
    the table was first created (e.g. users.mfa_enabled) never actually
    gets added on redeploy, and any query touching it blows up with
    "UndefinedColumn".

    This walks every model table that already exists in the live DB and
    adds whatever columns are missing from it, so re-running this script
    on an old database is safe the same way it already is for new rows.
    Safe to re-run — a column already present is left untouched.
    """
    inspector = inspect(db.engine)
    with db.engine.begin() as conn:
        for table in db.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue  # brand-new table — db.create_all() already handled it
            existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_cols:
                    continue

                col_type = column.type.compile(dialect=db.engine.dialect)
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}'))
                print(f"  schema sync: added column {table.name}.{column.name} ({col_type})")

                # Backfill existing rows so a NOT NULL constraint can be
                # applied safely. Only handles plain scalar defaults (e.g.
                # default=True/0) — callable defaults like `default=now`
                # can't be resolved generically at DDL time, so those
                # columns are left nullable in the live DB even if the
                # model says otherwise; that's a safe trade-off vs crashing.
                default = getattr(column.default, "arg", None)
                if default is not None and not callable(default):
                    conn.execute(
                        text(f'UPDATE "{table.name}" SET "{column.name}" = :default '
                             f'WHERE "{column.name}" IS NULL'),
                        {"default": default},
                    )
                    # SQLite (used for local dev) can't ALTER COLUMN at all;
                    # the production DB is always Postgres, which can.
                    if not column.nullable and db.engine.dialect.name != "sqlite":
                        conn.execute(text(f'ALTER TABLE "{table.name}" '
                                           f'ALTER COLUMN "{column.name}" SET NOT NULL'))


def run():
    app = create_app()
    with app.app_context():
        db.create_all()
        sync_schema()

        for zone_id, label, lat, lng, weight in ZONES:
            existing = Zone.query.get(zone_id)
            if not existing:
                db.session.add(Zone(zone_id=zone_id, label=label, lat=lat, lng=lng, weight=weight))
            elif existing.label != label or float(existing.lat) != lat or float(existing.lng) != lng:
                # Zones are otherwise insert-if-missing (safe to re-run), but
                # label/position specifically get kept in sync on re-run so
                # a landmark rename/reposition like this one actually takes
                # effect on a database that was already seeded, not just on
                # a fresh install. weight is left alone if already set —
                # that's tuned ML data, not identity/position.
                existing.label = label
                existing.lat = lat
                existing.lng = lng

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
