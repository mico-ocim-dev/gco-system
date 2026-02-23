"""Online appointment scheduling routes."""
from datetime import date, datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from models import Appointment
from utils.decorators import staff_required

appointments_bp = Blueprint("appointments", __name__)

APPOINTMENT_TYPES = ["Online", "Walk-in", "Consultation", "Counseling", "Document Request", "Others"]
TIME_SLOTS = [
    "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
]


@appointments_bp.route("/")
@login_required
def index():
    if current_user.is_staff:
        appointments = Appointment.query.order_by(
            Appointment.preferred_date.desc(),
            Appointment.preferred_time.desc(),
        ).all()
    else:
        appointments = Appointment.query.filter_by(
            user_id=current_user.id
        ).order_by(
            Appointment.preferred_date.desc(),
            Appointment.preferred_time.desc(),
        ).all()
    return render_template(
        "appointments/index.html",
        appointments=appointments,
    )


@appointments_bp.route("/book", methods=["GET", "POST"])
def book():
    """Book appointment - public (no login required) or pre-fill if logged in."""
    ctx = {"types": APPOINTMENT_TYPES, "slots": TIME_SLOTS, "now": datetime.now(timezone.utc)}
    if request.method == "POST":
        name = request.form.get("requester_name", "").strip()
        email = request.form.get("requester_email", "").strip()
        phone = request.form.get("requester_phone", "").strip()
        apt_type = request.form.get("appointment_type", "").strip()
        purpose = request.form.get("purpose", "").strip()
        pref_date = request.form.get("preferred_date", "").strip()
        pref_time = request.form.get("preferred_time", "").strip()
        ctx = {"types": APPOINTMENT_TYPES, "slots": TIME_SLOTS, "now": datetime.now(timezone.utc)}
        if not name or not email:
            flash("Name and email are required.", "error")
            return render_template("appointments/book.html", **ctx)
        if not apt_type or apt_type not in APPOINTMENT_TYPES:
            flash("Please select a valid appointment type.", "error")
            return render_template("appointments/book.html", **ctx)
        if not pref_date:
            flash("Preferred date is required.", "error")
            return render_template("appointments/book.html", **ctx)
        try:
            d = datetime.strptime(pref_date, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format.", "error")
            return render_template("appointments/book.html", **ctx)
        if d < date.today():
            flash("Please select a future date.", "error")
            return render_template("appointments/book.html", **ctx)
        apt = Appointment(
            user_id=current_user.id if current_user.is_authenticated else None,
            requester_name=name,
            requester_email=email,
            requester_phone=phone or None,
            appointment_type=apt_type,
            purpose=purpose or None,
            preferred_date=d,
            preferred_time=pref_time if pref_time in TIME_SLOTS else TIME_SLOTS[0],
            status="Pending",
        )
        db.session.add(apt)
        db.session.commit()
        flash("Appointment requested successfully! Wait for admin approval.", "success")
        if current_user.is_authenticated:
            return redirect(url_for("appointments.index"))
        return redirect(url_for("appointments.book"))
    if current_user.is_authenticated:
        return render_template("appointments/book.html", **ctx)
    return render_template("appointments/book_public.html", **ctx)


@appointments_bp.route("/<int:aid>/accept", methods=["POST"])
@login_required
@staff_required
def accept(aid):
    apt = Appointment.query.get(aid)
    if not apt:
        flash("Appointment not found.", "error")
        return redirect(url_for("appointments.index"))
    apt.status = "Approved"
    apt.admin_notes = request.form.get("admin_notes", "").strip() or apt.admin_notes
    db.session.commit()
    flash(f"Appointment for {apt.requester_name} approved.", "success")
    return redirect(url_for("appointments.index"))


@appointments_bp.route("/<int:aid>/reject", methods=["POST"])
@login_required
@staff_required
def reject(aid):
    apt = Appointment.query.get(aid)
    if not apt:
        flash("Appointment not found.", "error")
        return redirect(url_for("appointments.index"))
    apt.status = "Rejected"
    apt.admin_notes = request.form.get("admin_notes", "").strip() or apt.admin_notes
    db.session.commit()
    flash(f"Appointment for {apt.requester_name} rejected.", "info")
    return redirect(url_for("appointments.index"))


@appointments_bp.route("/<int:aid>/status", methods=["POST"])
@login_required
@staff_required
def update_status(aid):
    apt = Appointment.query.get(aid)
    if not apt:
        flash("Appointment not found.", "error")
        return redirect(url_for("appointments.index"))
    status = request.form.get("status", "").strip()
    if status in ("Pending", "Approved", "Rejected", "Completed", "Cancelled"):
        apt.status = status
        apt.admin_notes = request.form.get("admin_notes", "").strip() or apt.admin_notes
        db.session.commit()
        flash("Status updated.", "success")
    return redirect(url_for("appointments.index"))


@appointments_bp.route("/<int:aid>/edit", methods=["GET", "POST"])
@login_required
@staff_required
def edit(aid):
    """Edit/reschedule appointment - change date, time, notes (counselor availability)."""
    apt = Appointment.query.get(aid)
    if not apt:
        flash("Appointment not found.", "error")
        return redirect(url_for("appointments.index"))
    if request.method == "POST":
        pref_date = request.form.get("preferred_date", "").strip()
        pref_time = request.form.get("preferred_time", "").strip()
        status = request.form.get("status", "").strip()
        admin_notes = request.form.get("admin_notes", "").strip()
        if pref_date:
            try:
                apt.preferred_date = datetime.strptime(pref_date, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date format.", "error")
                return render_template("appointments/edit.html", appointment=apt, slots=TIME_SLOTS)
        if pref_time and pref_time in TIME_SLOTS:
            apt.preferred_time = pref_time
        if status in ("Pending", "Approved", "Rejected", "Completed", "Cancelled"):
            apt.status = status
        apt.admin_notes = admin_notes or None
        db.session.commit()
        flash("Appointment updated. Rescheduled date/time and notes saved.", "success")
        return redirect(url_for("appointments.index"))
    return render_template("appointments/edit.html", appointment=apt, slots=TIME_SLOTS)
