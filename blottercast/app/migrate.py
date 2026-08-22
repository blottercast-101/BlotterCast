"""Lightweight, dependency-free schema migration.

This project has no Alembic/Flask-Migrate. `db.create_all()` is the only
automatic schema setup there is, and it only creates *missing tables* —
it never adds a column to a table that already exists. Render's DB is a
persistent Postgres instance that survives every deploy (see render.yaml),
so any time a model gains a new column, the live table doesn't have it
until something actually ALTERs it — and every request touching that
column crashes in the meantime.

ensure_columns() closes that gap: it checks the live database for a short
list of columns added since the original schema, and adds any that are
missing. It's called once from seed.py, which Render's build step already
runs on every deploy, before the app starts serving traffic. Safe to run
repeatedly — a column that already exists is left untouched.

Add a line here any time a model gains a column on a table that might
already exist in a deployed database.
"""

from sqlalchemy import inspect, text

# (table, column, SQL type, DEFAULT literal for existing rows, nullable)
ADDITIVE_COLUMNS = [
    ("users", "mfa_enabled", "BOOLEAN", "TRUE", False),
    ("blotter_records", "archived", "BOOLEAN", "FALSE", False),
    ("users", "google_id", "VARCHAR(255)", None, True),
    ("users", "google_email", "VARCHAR(150)", None, True),
]


def ensure_columns(db):
    inspector = inspect(db.engine)
    with db.engine.begin() as conn:
        for entry in ADDITIVE_COLUMNS:
            if len(entry) == 4:
                table, column, coltype, default = entry
                nullable = False
            else:
                table, column, coltype, default, nullable = entry
            if not inspector.has_table(table):
                continue  # db.create_all() creates the whole table, column included
            existing = {c["name"] for c in inspector.get_columns(table)}
            if column in existing:
                continue
            if default is not None:
                null_clause = "NULL" if nullable else "NOT NULL"
                stmt = f"ALTER TABLE {table} ADD COLUMN {column} {coltype} {null_clause} DEFAULT {default}"
            else:
                stmt = f"ALTER TABLE {table} ADD COLUMN {column} {coltype}"
            conn.execute(text(stmt))
            print(f"  migrated: added {table}.{column}")
