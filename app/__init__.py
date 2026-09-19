import os
import time

from flask import Flask, send_from_directory
from sqlalchemy import event
from sqlalchemy.engine import Engine

from .config import Config
from .extensions import db

# Enforce system environment timezone to Asia/Manila (PST / UTC+8)
os.environ.setdefault("TZ", "Asia/Manila")
if hasattr(time, "tzset"):
    try:
        time.tzset()
    except Exception:
        pass


@event.listens_for(Engine, "connect")
def _set_db_timezone(dbapi_connection, connection_record):
    """Enforce UTC+8 / Asia/Manila timezone across database sessions safely without failing connections."""
    try:
        mod = getattr(dbapi_connection.__class__, "__module__", "").lower()
        name = getattr(dbapi_connection.__class__, "__name__", "").lower()

        # SQLite does not support session timezones; skip to avoid syntax errors
        if "sqlite" in mod or "sqlite" in name:
            return

        is_postgres = any(k in mod or k in name for k in ("postgres", "psycopg", "asyncpg", "pg8000"))
        is_mysql = any(k in mod or k in name for k in ("mysql", "mariadb", "pymysql"))

        cursor = dbapi_connection.cursor()
        try:
            if is_postgres:
                # PostgreSQL timezone setting
                try:
                    cursor.execute("SET TIME ZONE 'Asia/Manila'")
                    if hasattr(dbapi_connection, "commit"):
                        try:
                            dbapi_connection.commit()
                        except Exception:
                            pass
                except Exception:
                    if hasattr(dbapi_connection, "rollback"):
                        try:
                            dbapi_connection.rollback()
                        except Exception:
                            pass
            elif is_mysql:
                # MySQL / MariaDB timezone setting
                try:
                    cursor.execute("SET time_zone = '+08:00'")
                    if hasattr(dbapi_connection, "commit"):
                        try:
                            dbapi_connection.commit()
                        except Exception:
                            pass
                except Exception:
                    if hasattr(dbapi_connection, "rollback"):
                        try:
                            dbapi_connection.rollback()
                        except Exception:
                            pass
            else:
                # Fallback: attempt timezone setting safely and rollback immediately if unsupported
                try:
                    cursor.execute("SET time_zone = '+08:00'")
                    if hasattr(dbapi_connection, "commit"):
                        try:
                            dbapi_connection.commit()
                        except Exception:
                            pass
                except Exception:
                    if hasattr(dbapi_connection, "rollback"):
                        try:
                            dbapi_connection.rollback()
                        except Exception:
                            pass
                    try:
                        cursor.execute("SET TIME ZONE 'Asia/Manila'")
                        if hasattr(dbapi_connection, "commit"):
                            try:
                                dbapi_connection.commit()
                            except Exception:
                                pass
                    except Exception:
                        if hasattr(dbapi_connection, "rollback"):
                            try:
                                dbapi_connection.rollback()
                            except Exception:
                                pass
        finally:
            try:
                cursor.close()
            except Exception:
                pass
    except Exception:
        # Guarantee database connection STILL succeeds regardless of any exception
        pass


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


def _auto_migrate_schema(app):
    """Automatically patches database schema on application startup across all environments
    (SQLite, PostgreSQL on Render/Supabase, MySQL) so newly added tables and columns exist."""
    with app.app_context():
        try:
            db.create_all()
            from .migrate import ensure_columns
            ensure_columns(db)

            from .seed import seed_data
            seed_data(app)
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

    try:
        from flask_cors import CORS
        CORS(
            app,
            supports_credentials=True,
            resources={r"/*": {"origins": "*"}},
            allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Cache-Control", "Pragma"],
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        )
    except Exception as e:
        app.logger.warning(f"CORS initialization notice: {e}")

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

    @app.before_request
    def handle_options_preflight():
        from flask import make_response, request
        if request.method == "OPTIONS":
            response = make_response("", 204)
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
            origin = request.headers.get("Origin")
            if origin:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Cache-Control, Pragma"
            return response

    @app.teardown_request
    def check_teardown(exception=None):
        if exception:
            try:
                db.session.rollback()
            except Exception:
                pass

    @app.after_request
    def add_security_and_cache_headers(response):
        """Disable caching on API endpoints and HTML pages to ensure sensitive
        authenticated views are never served stale from browser disk/memory cache."""
        from flask import request
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
        origin = request.headers.get("Origin")
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Cache-Control, Pragma"
        path = (request.path or '').lower()
        if path.startswith("/api/") or path.endswith(".html") or path.endswith(".js") or path.endswith(".css") or path.endswith(".json") or path in ("/", ""):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    @app.route("/")
    def root():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.route("/login")
    def login_route():
        return send_from_directory(FRONTEND_DIR, "login.html")

    @app.errorhandler(400)
    def handle_400(e):
        from flask import request, jsonify
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "success": False, "error": getattr(e, "description", "Bad Request"), "status": 400}), 400
        return e

    @app.errorhandler(404)
    def handle_404(e):
        from flask import request, jsonify
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "success": False, "error": "Endpoint or record not found", "status": 404}), 404
        return e

    @app.errorhandler(405)
    def handle_405(e):
        from flask import request, jsonify
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "success": False, "error": "Method not allowed", "status": 405}), 405
        return e

    @app.errorhandler(500)
    def handle_500(e):
        import traceback
        from flask import request, jsonify
        app.logger.error(f"500 Internal Server Error at {request.path}: {traceback.format_exc()}")
        if request.path.startswith("/api/"):
            err_msg = str(getattr(e, "description", None) or getattr(e, "original_exception", None) or e or "Internal server error")
            return jsonify({
                "ok": False,
                "success": False,
                "error": err_msg,
                "detail": traceback.format_exc() if app.debug or app.config.get("ENV") == "development" else None,
                "status": 500
            }), 500
        return e

    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        from flask import request, jsonify
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            if request.path.startswith("/api/"):
                return jsonify({"ok": False, "success": False, "error": e.description, "status": e.code}), e.code
            return e

        app.logger.error(f"Unhandled Exception at {request.path}: {traceback.format_exc()}")
        if request.path.startswith("/api/"):
            return jsonify({
                "ok": False,
                "success": False,
                "error": str(e) or "An internal server error occurred",
                "detail": traceback.format_exc() if app.debug or app.config.get("ENV") == "development" else None,
                "status": 500
            }), 500
        raise e

    # Start autonomous server-side backup scheduler
    if not app.config.get("TESTING"):
        from .services.backup_scheduler import start_backup_scheduler
        start_backup_scheduler(app)

    return app
