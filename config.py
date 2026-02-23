"""Application configuration. Supports local (SQLite) and hosting (PostgreSQL/MySQL via DATABASE_URL)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "app.db"

# Use DATABASE_URL for hosting (e.g. PostgreSQL, MySQL); otherwise SQLite for local dev
# Examples: postgresql://user:pass@host:5432/dbname   mysql+pymysql://user:pass@host:3306/dbname
_database_url = os.environ.get("DATABASE_URL", "").strip()
if _database_url:
    # Some hosts set DATABASE_URL with postgres://; SQLAlchemy needs postgresql://
    if _database_url.startswith("postgres://"):
        _database_url = "postgresql://" + _database_url[9:]
    SQLALCHEMY_DATABASE_URI = _database_url
else:
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(DATABASE_PATH).replace("\\", "/")

SECRET_KEY = os.environ.get("SECRET_KEY", "gco-system-dev-secret-key-change-in-production")
SQLALCHEMY_TRACK_MODIFICATIONS = False
UPLOAD_FOLDER = BASE_DIR / "uploads"
QR_UPLOAD_FOLDER = UPLOAD_FOLDER / "qr"  # Created on init
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
DEBUG = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

# Optional: email on registration (welcome message). Leave unset to skip sending.
MAIL_SERVER = os.environ.get("MAIL_SERVER", "").strip()  # e.g. smtp.gmail.com
MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "1").lower() in ("1", "true", "yes")
MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "").strip()
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "").strip()
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME or "noreply@gco.lspu.edu.ph")
# True when mail is configured (server set; credentials in env if your SMTP requires them)
MAIL_ENABLED = bool(MAIL_SERVER)
