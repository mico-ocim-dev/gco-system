"""QR code / form link resources - admin uploadable images."""
from datetime import datetime
from extensions import db


class QRResource(db.Model):
    """QR code or form link images - e.g. NSSIB, Excuse Slip."""

    __tablename__ = "qr_resources"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    image_filename = db.Column(db.String(256), nullable=False)
    form_url = db.Column(db.String(500), nullable=True)  # optional link when QR is scanned
    order_index = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
