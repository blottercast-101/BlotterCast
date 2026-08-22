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

# (table, column, SQL type, DEFAULT literal, is_not_null)
ADDITIVE_COLUMNS = [
    ("users", "mfa_enabled", "BOOLEAN", "TRUE", True),
    ("users", "google_id", "VARCHAR(100)", "NULL", False),
    ("users", "auth_provider", "VARCHAR(30)", "'local'", True),
    ("blotter_records", "archived", "BOOLEAN", "FALSE", True),
]


def ensure_columns(db):
    inspector = inspect(db.engine)
    with db.engine.begin() as conn:
        for item in ADDITIVE_COLUMNS:
            table, column, coltype, default = item[0], item[1], item[2], item[3]
            is_not_null = item[4] if len(item) > 4 else True
            if not inspector.has_table(table):
                continue  # db.create_all() creates the whole table, column included
            existing = {c["name"] for c in inspector.get_columns(table)}
            if column in existing:
                continue
            if is_not_null:
                sql = f"ALTER TABLE {table} ADD COLUMN {column} {coltype} NOT NULL DEFAULT {default}"
            else:
                sql = f"ALTER TABLE {table} ADD COLUMN {column} {coltype}"
            conn.execute(text(sql))
            print(f"  migrated: added {table}.{column}")
