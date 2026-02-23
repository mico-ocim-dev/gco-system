"""Help desk / ticketing routes."""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from utils.decorators import staff_required
from werkzeug.utils import secure_filename
import os

from extensions import db
from models import Ticket
from services.import_export import import_tickets_excel, export_tickets_excel

tickets_bp = Blueprint("tickets", __name__)


def _next_ticket_number():
    last = Ticket.query.order_by(Ticket.id.desc()).first()
    n = (last.id + 1) if last else 1
    return f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{n:04d}"


@tickets_bp.route("/")
@login_required
@staff_required
def index():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return render_template("tickets/index.html", tickets=tickets)


@tickets_bp.route("/create", methods=["GET", "POST"])
@login_required
@staff_required
def create():
    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()
        requester = request.form.get("requester_name", "").strip()
        email = request.form.get("requester_email", "").strip()
        priority = request.form.get("priority", "Medium").strip()
        if not subject or not requester:
            flash("Subject and requester name are required.", "error")
            return render_template("tickets/form.html")
        t = Ticket(
            ticket_number=_next_ticket_number(),
            subject=subject,
            description=description or None,
            requester_name=requester,
            requester_email=email or None,
            priority=priority or "Medium",
            status="Open",
        )
        # Optional attachment
        f = request.files.get("attachment")
        if f and f.filename:
            from flask import current_app
            ext = (f.filename or "").rsplit(".", 1)[-1]
            fn = secure_filename(f"{t.ticket_number}_{datetime.utcnow().timestamp():.0f}.{ext}")
            path = os.path.join(current_app.config["UPLOAD_FOLDER"], fn)
            f.save(path)
            t.attachment_path = fn
        db.session.add(t)
        db.session.commit()
        flash(f"Ticket created: {t.ticket_number}", "success")
        return redirect(url_for("tickets.index"))
    return render_template("tickets/form.html")


@tickets_bp.route("/<int:tid>/update", methods=["POST"])
@login_required
@staff_required
def update_ticket(tid):
    t = Ticket.query.get(tid)
    if not t:
        flash("Ticket not found.", "error")
        return redirect(url_for("tickets.index"))
    status = request.form.get("status", t.status)
    assigned = request.form.get("assigned_to", "").strip()
    t.status = status
    t.assigned_to = assigned or None
    if status in ("Resolved", "Closed"):
        t.resolved_at = datetime.utcnow()
    db.session.commit()
    flash("Ticket updated.", "success")
    return redirect(url_for("tickets.index"))


@tickets_bp.route("/import", methods=["GET", "POST"])
@login_required
@staff_required
def import_tickets():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename:
            flash("Please select a file.", "error")
            return redirect(url_for("tickets.import_tickets"))
        imp, failed, err = import_tickets_excel(file, current_user.username)
        if err:
            flash(err, "error")
        else:
            flash(f"Imported {imp} rows. Failed: {failed}", "success" if failed == 0 else "warning")
        return redirect(url_for("tickets.index"))
    return render_template("tickets/import.html")


@tickets_bp.route("/export")
@login_required
@staff_required
def export_tickets():
    buf = export_tickets_excel()
    from io import BytesIO
    fn = f"tickets_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(
        BytesIO(buf),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=fn,
    )
