"""User dashboard - displays QR forms (NSSIB, Excuse slip, etc.)."""
from flask import Blueprint, render_template
from flask_login import login_required

from models import QRResource

user_dashboard_bp = Blueprint("user_dashboard", __name__)


@user_dashboard_bp.route("/my-dashboard")
@login_required
def index():
    """User dashboard with QR codes for forms."""
    resources = QRResource.query.filter_by(is_active=True).order_by(
        QRResource.order_index,
        QRResource.name,
    ).all()
    return render_template("user_dashboard/index.html", resources=resources)
