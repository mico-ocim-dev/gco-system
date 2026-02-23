"""Help desk ticket model."""
from datetime import datetime
from extensions import db


class Ticket(db.Model):
    """Help desk support tickets."""

    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    requester_name = db.Column(db.String(120), nullable=False)
    requester_email = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(50), default="Open")  # Open, In Progress, Resolved, Closed
    priority = db.Column(db.String(20), default="Medium")  # Low, Medium, High
    assigned_to = db.Column(db.String(80), nullable=True)
    attachment_path = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
