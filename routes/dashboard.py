"""Dashboard and office monitoring routes."""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from utils.decorators import staff_required
from sqlalchemy import func
from extensions import db
from models import DocumentRequest, Ticket, LogbookEntry, SurveyResponse

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
@staff_required
def index():
    return render_template("dashboard/index.html")


@dashboard_bp.route("/api/dashboard/stats")
@login_required
@staff_required
def api_stats():
    """Live counters for dashboard."""
    pending_requests = DocumentRequest.query.filter_by(status="Pending").count()
    open_tickets = Ticket.query.filter(Ticket.status.in_(["Open", "In Progress"])).count()
    completed_requests = DocumentRequest.query.filter(
        DocumentRequest.status.in_(["Ready", "Claimed"]),
    ).count()
    today = datetime.utcnow().date()
    total_visitors_today = LogbookEntry.query.filter(LogbookEntry.date == today).count()
    return jsonify({
        "pending_requests": pending_requests,
        "open_tickets": open_tickets,
        "completed_requests": completed_requests,
        "visitors_today": total_visitors_today,
    })


@dashboard_bp.route("/api/dashboard/request-status-distribution")
@login_required
@staff_required
def api_request_status():
    """Status distribution for document requests."""
    counts = (
        db.session.query(DocumentRequest.status, func.count(DocumentRequest.id))
        .group_by(DocumentRequest.status)
        .all()
    )
    return jsonify({"labels": [c[0] for c in counts], "data": [c[1] for c in counts]})


@dashboard_bp.route("/api/dashboard/monthly-trend")
@login_required
@staff_required
def api_monthly_trend():
    """Monthly trend for document requests."""
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    rows = (
        db.session.query(
            func.strftime("%Y-%m", DocumentRequest.requested_at).label("month"),
            func.count(DocumentRequest.id).label("count"),
        )
        .filter(DocumentRequest.requested_at >= six_months_ago)
        .group_by("month")
        .order_by("month")
        .all()
    )
    return jsonify({"labels": [r[0] for r in rows], "data": [r[1] for r in rows]})


@dashboard_bp.route("/api/dashboard/survey-average")
@login_required
@staff_required
def api_survey_average():
    """Average survey rating."""
    avg = db.session.query(func.avg(SurveyResponse.response_value)).scalar() or 0
    return jsonify({"average": round(float(avg), 2)})
