"""Appointment/booking model."""
from datetime import datetime
from extensions import db


class Appointment(db.Model):
    """Online appointment scheduling."""

    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    requester_name = db.Column(db.String(120), nullable=False)
    requester_email = db.Column(db.String(120), nullable=False)
    requester_phone = db.Column(db.String(20), nullable=True)
    appointment_type = db.Column(db.String(50), nullable=False)  # Online, Walk-in, Consultation, Counseling, Others
    purpose = db.Column(db.String(200), nullable=True)
    preferred_date = db.Column(db.Date, nullable=False)
    preferred_time = db.Column(db.String(20), nullable=True)  # e.g. "09:00", "14:00"
    status = db.Column(db.String(50), default="Pending")  # Pending, Approved, Rejected, Completed, Cancelled
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
