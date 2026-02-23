"""Digital logbook / visitor tracking routes."""
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from utils.decorators import staff_required

from extensions import db
from models import LogbookEntry
from services.import_export import import_logbook_excel, export_logbook_excel

logbook_bp = Blueprint("logbook", __name__)


@logbook_bp.route("/")
@login_required
@staff_required
def index():
    today = date.today()
    entries = LogbookEntry.query.filter(LogbookEntry.date == today).order_by(LogbookEntry.time_in.desc()).all()
    return render_template("logbook/index.html", entries=entries)


@logbook_bp.route("/check-in", methods=["POST"])
@login_required
@staff_required
def check_in():
    name = request.form.get("visitor_name", "").strip()
    purpose = request.form.get("purpose", "").strip()
    if not name:
        flash("Visitor name is required.", "error")
        return redirect(url_for("logbook.index"))
    now = datetime.utcnow()
    entry = LogbookEntry(
        visitor_name=name,
        purpose=purpose or None,
        time_in=now,
        date=now.date(),
    )
    db.session.add(entry)
    db.session.commit()
    flash(f"{name} checked in.", "success")
    return redirect(url_for("logbook.index"))


@logbook_bp.route("/check-out/<int:eid>", methods=["POST"])
@login_required
@staff_required
def check_out(eid):
    entry = LogbookEntry.query.get(eid)
    if not entry:
        flash("Entry not found.", "error")
        return redirect(url_for("logbook.index"))
    if entry.time_out:
        flash("Already checked out.", "warning")
        return redirect(url_for("logbook.index"))
    entry.time_out = datetime.utcnow()
    db.session.commit()
    flash(f"{entry.visitor_name} checked out.", "success")
    return redirect(url_for("logbook.index"))


@logbook_bp.route("/api/active")
@login_required
@staff_required
def api_active():
    """Active visitors (checked in, not out)."""
    today = date.today()
    active = LogbookEntry.query.filter(
        LogbookEntry.date == today,
        LogbookEntry.time_out.is_(None),
    ).all()
    return jsonify([{"id": e.id, "name": e.visitor_name, "time_in": e.time_in.isoformat()} for e in active])


@logbook_bp.route("/reports")
@login_required
@staff_required
def reports():
    from_date = request.args.get("from") or str(date.today() - timedelta(days=30))
    to_date = request.args.get("to") or date.today().isoformat()
    entries = LogbookEntry.query.filter(
        LogbookEntry.date >= from_date,
        LogbookEntry.date <= to_date,
    ).order_by(LogbookEntry.time_in.desc()).all()
    return render_template("logbook/reports.html", entries=entries, from_date=from_date, to_date=to_date)


@logbook_bp.route("/import", methods=["GET", "POST"])
@login_required
@staff_required
def import_entries():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename:
            flash("Please select a file.", "error")
            return redirect(url_for("logbook.import_entries"))
        imp, failed, err = import_logbook_excel(file, current_user.username)
        if err:
            flash(err, "error")
        else:
            flash(f"Imported {imp} entries. Failed: {failed}", "success" if failed == 0 else "warning")
        return redirect(url_for("logbook.index"))
    return render_template("logbook/import.html")


@logbook_bp.route("/export")
@login_required
@staff_required
def export_entries():
    buf = export_logbook_excel()
    from io import BytesIO
    fn = f"logbook_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(
        BytesIO(buf),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=fn,
    )
