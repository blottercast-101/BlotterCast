import os

from flask import Flask, send_from_directory

from .config import Config
from .extensions import db

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


def _auto_migrate_schema(app):
    """Automatically patches database schema on application startup across all environments
    (SQLite, PostgreSQL on Render, MySQL) so newly added columns like 'archived' exist."""
    with app.app_context():
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            tables = ["incidents", "settlements", "census_records", "blotter_records"]
            for table in tables:
                if table in inspector.get_table_names():
                    columns = [c["name"] for c in inspector.get_columns(table)]
                    if "archived" not in columns:
                        with db.engine.begin() as conn:
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN archived BOOLEAN DEFAULT FALSE"))
                            conn.execute(text(f"UPDATE {table} SET archived = FALSE WHERE archived IS NULL"))
        except Exception as e:
            app.logger.warning(f"Auto-migration notice: {e}")


def create_app(config_class=Config):
    app = Flask(
        __name__,
        static_folder=FRONTEND_DIR,
        static_url_path="",  # serve login.html, styles.css, app.js, assets/... at the root, same as before
    )
    app.config.from_object(config_class)

    db.init_app(app)
    _auto_migrate_schema(app)

    from .blueprints.auth import bp as auth_bp
    from .blueprints.records import bp as records_bp
    from .blueprints.documents import bp as documents_bp
    from .blueprints.analytics import bp as analytics_bp
    from .blueprints.reports import bp as reports_bp
    from .blueprints.exports import bp as exports_bp
    from .blueprints.users import bp as users_bp
    from .blueprints.settings import bp as settings_bp
    from .blueprints.notifications import bp as notifications_bp
    from .blueprints.ml_proxy import bp as ml_proxy_bp
    from .blueprints.blotter_import import bp as blotter_import_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(exports_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(ml_proxy_bp)
    app.register_blueprint(blotter_import_bp)

    @app.route("/")
    def root():
        return send_from_directory(FRONTEND_DIR, "index.html")

    return app
