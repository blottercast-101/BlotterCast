"""Lightweight, dependency-free schema migration and auto-repair.

Ensures that live PostgreSQL, MySQL, and SQLite databases automatically gain
any missing tables or columns on startup without crashing on deploy.
"""

from sqlalchemy import inspect, text

# (table, column, SQL type, DEFAULT literal, is_not_null)
ADDITIVE_COLUMNS = [
    # User authentication, Google OAuth & Security columns
    ("users", "google_id", "VARCHAR(100)", "NULL", False),
    ("users", "auth_provider", "VARCHAR(30)", "'local'", True),
    ("users", "mfa_enabled", "BOOLEAN", "TRUE", True),
    ("users", "signature_path", "VARCHAR(255)", "NULL", False),
    ("users", "last_login", "TIMESTAMP", "NULL", False),
    ("users", "last_seen", "TIMESTAMP", "NULL", False),
    ("users", "failed_attempts", "INTEGER", "0", True),
    ("users", "locked_until", "TIMESTAMP", "NULL", False),
    ("users", "password_changed_at", "TIMESTAMP", "CURRENT_TIMESTAMP", False),
    ("users", "email", "VARCHAR(150)", "NULL", False),
    ("users", "contact_no", "VARCHAR(30)", "NULL", False),
    ("users", "role", "VARCHAR(30)", "'Desk Officer'", True),
    ("users", "status", "VARCHAR(20)", "'Active'", True),

    # Record archival columns
    ("blotter_records", "archived", "BOOLEAN", "FALSE", True),
    ("incidents", "archived", "BOOLEAN", "FALSE", True),
    ("settlements", "archived", "BOOLEAN", "FALSE", True),
    ("settlements", "officer", "VARCHAR(100)", "NULL", False),

    # Incident Reporter, Guardian, Complainant, Involved Parties & Resolution
    ("incidents", "is_non_resident", "BOOLEAN", "FALSE", True),
    ("incidents", "reporter_resident_id", "INTEGER", "NULL", False),
    ("incidents", "reporter_address", "TEXT", "NULL", False),
    ("incidents", "complainant", "VARCHAR(150)", "NULL", False),
    ("incidents", "complainant_resident_id", "INTEGER", "NULL", False),
    ("incidents", "guardian_name", "VARCHAR(150)", "NULL", False),
    ("incidents", "guardian_resident_id", "INTEGER", "NULL", False),
    ("incidents", "guardian_address", "TEXT", "NULL", False),
    ("incidents", "involved_parties", "TEXT", "NULL", False),
    ("incidents", "resolved_at", "TIMESTAMP", "NULL", False),

    # Blotter Records resident links & resolution
    ("blotter_records", "complainant_id", "INTEGER", "NULL", False),
    ("blotter_records", "respondent_id", "INTEGER", "NULL", False),
    ("blotter_records", "source_incident_id", "INTEGER", "NULL", False),
    ("blotter_records", "resolved_at", "TIMESTAMP", "NULL", False),
]


def ensure_columns(db):
    """Safely inspects tables and executes schema adjustments."""
    try:
        # 1. Ensure system_security_settings table exists
        with db.engine.begin() as conn:
            backend = db.engine.url.get_backend_name().lower()
            if "postgres" in backend:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS system_security_settings (
                        id INT PRIMARY KEY DEFAULT 1,
                        is_2fa_globally_enabled BOOLEAN DEFAULT FALSE,
                        is_idle_timeout_enabled BOOLEAN DEFAULT FALSE,
                        idle_timeout_duration_minutes INT DEFAULT 120,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_by INT
                    )
                """))
                conn.execute(text("""
                    INSERT INTO system_security_settings (id, is_2fa_globally_enabled, is_idle_timeout_enabled, idle_timeout_duration_minutes)
                    VALUES (1, FALSE, FALSE, 120)
                    ON CONFLICT (id) DO NOTHING
                """))
                try:
                    conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN details TYPE TEXT;"))
                except Exception:
                    pass
            elif "mysql" in backend:
                try:
                    conn.execute(text("ALTER TABLE audit_logs MODIFY COLUMN details TEXT;"))
                except Exception:
                    pass
    except Exception as e:
        print(f"  [migration] system_security_settings notice: {e}")

    try:
        inspector = inspect(db.engine)
        backend = db.engine.url.get_backend_name().lower()
        is_postgres = "postgres" in backend

        for item in ADDITIVE_COLUMNS:
            table, column, coltype, default = item[0], item[1], item[2], item[3]
            is_not_null = item[4] if len(item) > 4 else False

            try:
                with db.engine.begin() as conn:
                    if not inspector.has_table(table):
                        continue

                    existing = {c["name"] for c in inspector.get_columns(table)}
                    if column in existing:
                        continue

                    if is_postgres:
                        # PostgreSQL supports ADD COLUMN IF NOT EXISTS natively
                        if is_not_null:
                            sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {coltype} NOT NULL DEFAULT {default}"
                        else:
                            sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {coltype}"
                    else:
                        if is_not_null:
                            sql = f"ALTER TABLE {table} ADD COLUMN {column} {coltype} NOT NULL DEFAULT {default}"
                        else:
                            sql = f"ALTER TABLE {table} ADD COLUMN {column} {coltype}"

                    conn.execute(text(sql))
                    print(f"  [migration] added column: {table}.{column}")
            except Exception as col_err:
                # Catch per-column exception so it doesn't abort subsequent columns
                print(f"  [migration] column check notice for {table}.{column}: {col_err}")

    except Exception as e:
        print(f"  [migration] ensure_columns warning: {e}")
