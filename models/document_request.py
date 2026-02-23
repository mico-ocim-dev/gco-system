"""Document request and status log models."""
from datetime import datetime
from extensions import db


class DocumentRequest(db.Model):
    """Document request records."""

    __tablename__ = "document_requests"

    id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    requester_name = db.Column(db.String(120), nullable=False)
    requester_email = db.Column(db.String(120), nullable=True)
    document_type = db.Column(db.String(100), nullable=False)
    purpose = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="Pending")  # Pending, Processing, Ready, Claimed, Cancelled
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # requester if logged in
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    status_logs = db.relationship("RequestStatusLog", backref="document_request", lazy="dynamic", cascade="all, delete-orphan")


class RequestStatusLog(db.Model):
    """Status change history for document requests."""

    __tablename__ = "request_status_logs"

    id = db.Column(db.Integer, primary_key=True)
    document_request_id = db.Column(db.Integer, db.ForeignKey("document_requests.id"), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    changed_by = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
