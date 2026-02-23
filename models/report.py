"""Monthly report model."""
from datetime import datetime
from extensions import db


class MonthlyReport(db.Model):
    """Aggregated monthly reports."""

    __tablename__ = "monthly_reports"

    id = db.Column(db.Integer, primary_key=True)
    report_month = db.Column(db.Integer, nullable=False)  # 1-12
    report_year = db.Column(db.Integer, nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # document_requests, tickets, surveys, logbook
    summary_data = db.Column(db.Text, nullable=True)  # JSON string
    file_path = db.Column(db.String(256), nullable=True)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
