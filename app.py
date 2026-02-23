"""GCO Office Management System - Main Flask Application."""
import os
from pathlib import Path

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from config import (
    SECRET_KEY,
    SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS,
    UPLOAD_FOLDER,
    DATABASE_DIR,
    QR_UPLOAD_FOLDER,
    MAIL_SERVER,
    MAIL_PORT,
    MAIL_USE_TLS,
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_DEFAULT_SENDER,
)
from extensions import db, login_manager, mail

# Ensure we use Postgres on Railway: env vars are sometimes not visible at config import
_db_url = (
    os.environ.get("DATABASE_URL") or
    os.environ.get("DATABASE_PUBLIC_URL") or
    os.environ.get("POSTGRES_URL") or
    os.environ.get("DATABASE_PRIVATE_URL") or
    ""
).strip()
if _db_url:
    if _db_url.startswith("postgres://"):
        _db_url = "postgresql://" + _db_url[9:]
    if "postgresql" in _db_url and "sslmode" not in _db_url:
        _db_url += "?sslmode=require" if "?" not in _db_url else "&sslmode=require"
    SQLALCHEMY_DATABASE_URI = _db_url
else:
    # On Railway, PORT is set; if DATABASE_URL is missing, app will use SQLite and fail on login
    if os.environ.get("PORT"):
        print("[GCO] WARNING: PORT is set but DATABASE_URL is not. On Railway, add variable:")
        print("[GCO]   DATABASE_URL = ${{Postgres.DATABASE_URL}}")
        print("[GCO]   (Replace 'Postgres' with your PostgreSQL service name.)")

# Ensure directories exist (SQLite uses DATABASE_DIR; uploads always used)
if "sqlite" in SQLALCHEMY_DATABASE_URI.lower():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
Path(QR_UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = str(SQLALCHEMY_DATABASE_URI).replace("\\", "/")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAIL_SERVER"] = MAIL_SERVER
app.config["MAIL_PORT"] = MAIL_PORT
app.config["MAIL_USE_TLS"] = MAIL_USE_TLS
app.config["MAIL_USERNAME"] = MAIL_USERNAME
app.config["MAIL_PASSWORD"] = MAIL_PASSWORD
app.config["MAIL_DEFAULT_SENDER"] = MAIL_DEFAULT_SENDER

db.init_app(app)
mail.init_app(app)
csrf = CSRFProtect(app)
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."

# Import models (must be after db init)
from models import (
    User,
    DocumentRequest,
    RequestStatusLog,
    Ticket,
    Appointment,
    Survey,
    SurveyQuestion,
    SurveyResponse,
    LogbookEntry,
    MonthlyReport,
    ImportLog,
    QRResource,
)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def _run_migrations():
    """Add new columns to existing SQLite tables if needed. Skipped for PostgreSQL/MySQL (use migrations there)."""
    if "sqlite" not in str(db.engine.url).lower():
        return
    from sqlalchemy import text
    try:
        with db.engine.connect() as conn:
            r = conn.execute(text("PRAGMA table_info(document_requests)"))
            cols = [row[1] for row in r.fetchall()]
            if "user_id" not in cols:
                conn.execute(text("ALTER TABLE document_requests ADD COLUMN user_id INTEGER REFERENCES users(id)"))
                conn.commit()
    except Exception:
        pass
    try:
        with db.engine.connect() as conn:
            r = conn.execute(text("PRAGMA table_info(logbook_entries)"))
            cols = [row[1] for row in r.fetchall()]
            if "document_request_id" not in cols:
                conn.execute(text("ALTER TABLE logbook_entries ADD COLUMN document_request_id INTEGER REFERENCES document_requests(id)"))
                conn.commit()
    except Exception:
        pass
    try:
        with db.engine.connect() as conn:
            r = conn.execute(text("PRAGMA table_info(users)"))
            cols = [row[1] for row in r.fetchall()]
            if "email_verified" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0"))
                conn.commit()
            if "verification_token" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN verification_token VARCHAR(64)"))
                conn.commit()
            if "verification_token_expires" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN verification_token_expires DATETIME"))
                conn.commit()
                # Existing users (no pending token) are treated as already verified
                conn.execute(text("UPDATE users SET email_verified = 1 WHERE verification_token IS NULL"))
                conn.commit()
    except Exception:
        pass


def init_db():
    """Create all database tables and seed default admin user."""
    with app.app_context():
        db.create_all()
        _run_migrations()
        if not User.query.filter_by(username="admin").first():
            admin = User(
                username="admin",
                email="admin@gco.lspu.edu.ph",
                full_name="System Administrator",
                role="Admin",
                email_verified=True,
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("Created default admin (username: admin, password: admin123)")


# Register blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.user_dashboard import user_dashboard_bp
from routes.qr_resources import qr_bp
from routes.document_requests import document_requests_bp
from routes.appointments import appointments_bp
from routes.tickets import tickets_bp
from routes.surveys import surveys_bp
from routes.logbook import logbook_bp
from routes.reports import reports_bp

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(dashboard_bp, url_prefix="/")
app.register_blueprint(user_dashboard_bp, url_prefix="/")
app.register_blueprint(qr_bp, url_prefix="/qr")
app.register_blueprint(document_requests_bp, url_prefix="/document-requests")
app.register_blueprint(appointments_bp, url_prefix="/appointments")
app.register_blueprint(tickets_bp, url_prefix="/tickets")
app.register_blueprint(surveys_bp, url_prefix="/surveys")
app.register_blueprint(logbook_bp, url_prefix="/logbook")
app.register_blueprint(reports_bp, url_prefix="/reports")


@app.route("/")
def index():
    from flask import redirect, url_for
    from flask_login import current_user
    if current_user.is_authenticated:
        dest = url_for("user_dashboard.index") if current_user.role == "User" else url_for("dashboard.index")
        return redirect(dest)
    return redirect(url_for("auth.login"))


# Create tables and seed admin when app loads (needed for Gunicorn / Railway)
_init_db_done = False


def _ensure_db():
    """Run init_db() once; used at startup and retried on first request if startup failed."""
    global _init_db_done
    if _init_db_done:
        return
    try:
        init_db()
        _init_db_done = True
        print("[GCO] Database tables ready.")
    except Exception as e:
        import traceback
        print("[GCO] DB init failed:", e)
        traceback.print_exc()


try:
    with app.app_context():
        _ensure_db()
except Exception as e:
    import traceback
    print("[GCO] DB init on startup failed:", e)
    traceback.print_exc()


@app.before_request
def ensure_db_before_request():
    """If DB init failed at startup (e.g. Postgres was not ready), try once on first request."""
    global _init_db_done
    if _init_db_done:
        return
    try:
        with app.app_context():
            _ensure_db()
    except Exception:
        pass


if __name__ == "__main__":
    app.run(debug=True, port=5000)
