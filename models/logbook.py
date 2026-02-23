"""Logbook entry model for visitor tracking."""
from datetime import datetime
from extensions import db


class LogbookEntry(db.Model):
    """Visitor check-in/check-out logbook entries."""

    __tablename__ = "logbook_entries"

    id = db.Column(db.Integer, primary_key=True)
    visitor_name = db.Column(db.String(120), nullable=False)
    purpose = db.Column(db.String(200), nullable=True)
    time_in = db.Column(db.DateTime, nullable=False)
    time_out = db.Column(db.DateTime, nullable=True)
    date = db.Column(db.Date, nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    document_request_id = db.Column(db.Integer, db.ForeignKey("document_requests.id"), nullable=True)  # auto-created from request
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
