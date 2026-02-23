"""Import activity log."""
from datetime import datetime
from extensions import db


class ImportLog(db.Model):
    """Log of data import operations."""

    __tablename__ = "import_logs"

    id = db.Column(db.Integer, primary_key=True)
    import_type = db.Column(db.String(50), nullable=False)  # document_requests, tickets, surveys, logbook
    filename = db.Column(db.String(256), nullable=False)
    rows_imported = db.Column(db.Integer, default=0)
    rows_failed = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="Success")  # Success, Partial, Failed
    error_message = db.Column(db.Text, nullable=True)
    imported_by = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
