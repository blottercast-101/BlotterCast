import os

from flask import Flask, send_from_directory

from .config import Config
from .extensions import db

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


def _auto_migrate_schema(app):
    """Automatically patches database schema on application startup across all environments
    (SQLite, PostgreSQL on Render, MySQL) so newly added columns exist."""
    with app.app_context():
        try:
            from .migrate import ensure_columns
            ensure_columns(db)
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
