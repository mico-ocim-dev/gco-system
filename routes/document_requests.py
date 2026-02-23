"""Document request and tracking routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user

from extensions import db
from models import DocumentRequest
from services.document_request_service import (
    create_request,
    get_request_by_tracking,
    update_request_status,
    generate_tracking_number,
)
from services.import_export import import_requests_excel, export_requests_excel

document_requests_bp = Blueprint("document_requests", __name__)


def _staff_required(f):
    """Decorator: only Admin/Staff can access."""
    from functools import wraps
    @wraps(f)
    def inner(*args, **kwargs):
        if not current_user.is_staff:
            from flask import abort
            abort(403)
        return f(*args, **kwargs)
    return inner


@document_requests_bp.route("/")
@login_required
def index():
    if current_user.is_staff:
        requests = DocumentRequest.query.order_by(DocumentRequest.requested_at.desc()).all()
    else:
        requests = DocumentRequest.query.filter_by(user_id=current_user.id).order_by(DocumentRequest.requested_at.desc()).all()
    return render_template("document_requests/index.html", requests=requests)


@document_requests_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = request.form.get("requester_name", "").strip() or (current_user.full_name or current_user.username)
        doc_type = request.form.get("document_type", "").strip()
        purpose = request.form.get("purpose", "").strip()
        email = request.form.get("requester_email", "").strip() or (current_user.email if current_user.email else None)
        if not name or not doc_type:
            flash("Requester name and document type are required.", "error")
            return render_template("document_requests/form.html")
        try:
            user_id = current_user.id if current_user.role == "User" else None
            req = create_request(name, doc_type, purpose, email, user_id=user_id)
            flash(f"Request created. Tracking number: {req.tracking_number}. Staff will record your visit in the logbook when you come to the office.", "success")
            return redirect(url_for("document_requests.index"))
        except Exception as e:
            flash(str(e), "error")
    return render_template("document_requests/form.html")


@document_requests_bp.route("/track", methods=["GET", "POST"])
def track():
    """Public tracking - no login required."""
    req = None
    if request.method == "POST":
        tn = request.form.get("tracking_number", "").strip()
        if tn:
            req = get_request_by_tracking(tn) if tn else None
            if not req:
                req = DocumentRequest.query.filter_by(tracking_number=tn).first()
            if not req:
                flash("Tracking number not found.", "error")
    return render_template("document_requests/track.html", request_obj=req)


@document_requests_bp.route("/<int:req_id>/status", methods=["POST"])
@login_required
@_staff_required
def update_status(req_id):
    status = request.form.get("status", "").strip()
    notes = request.form.get("notes", "").strip()
    if not status:
        flash("Status is required.", "error")
        return redirect(url_for("document_requests.index"))
    ok = update_request_status(req_id, status, notes, current_user.username)
    if ok:
        flash("Status updated.", "success")
    else:
        flash("Request not found.", "error")
    return redirect(url_for("document_requests.index"))


@document_requests_bp.route("/api/track/<tracking_number>")
def api_track(tracking_number):
    req = get_request_by_tracking(tracking_number) or DocumentRequest.query.filter_by(tracking_number=tracking_number).first()
    if not req:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "tracking_number": req.tracking_number,
        "status": req.status,
        "requester_name": req.requester_name,
        "document_type": req.document_type,
    })


@document_requests_bp.route("/import", methods=["GET", "POST"])
@login_required
@_staff_required
def import_requests():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename:
            flash("Please select a file.", "error")
            return redirect(url_for("document_requests.import_requests"))
        imp, failed, err = import_requests_excel(file, current_user.username)
        if err:
            flash(err, "error")
        else:
            flash(f"Imported {imp} rows. Failed: {failed}", "success" if failed == 0 else "warning")
        return redirect(url_for("document_requests.index"))
    return render_template("document_requests/import.html")


@document_requests_bp.route("/export")
@login_required
@_staff_required
def export_requests():
    buf = export_requests_excel()
    from io import BytesIO
    from datetime import datetime
    fn = f"document_requests_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(
        BytesIO(buf),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=fn,
    )
