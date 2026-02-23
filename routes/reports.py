"""Automated monthly reports routes."""
import csv
import json
from datetime import datetime
from io import BytesIO, StringIO

from flask import Blueprint, render_template, request, send_file
from flask_login import login_required
from sqlalchemy import func
import pandas as pd

from utils.decorators import staff_required
from extensions import db
from models import DocumentRequest, Ticket, LogbookEntry, MonthlyReport, Appointment

reports_bp = Blueprint("reports", __name__)

YM_FMT = "%Y-%m"


def _all_transactions_rows(year: int, month: int):
    """Return list of dicts with keys: Type, Date, Reference, Subject, Status for CSV/Excel."""
    ym = f"{year}-{month:02d}"
    rows = []

    for r in DocumentRequest.query.filter(
        func.strftime(YM_FMT, DocumentRequest.requested_at) == ym,
    ).order_by(DocumentRequest.requested_at).all():
        rows.append({
            "Type": "Document Request",
            "Date": r.requested_at.strftime("%Y-%m-%d %H:%M") if r.requested_at else "",
            "Reference": r.tracking_number or "",
            "Subject": r.document_type or "",
            "Status": r.status or "",
        })

    for t in Ticket.query.filter(
        func.strftime(YM_FMT, Ticket.created_at) == ym,
    ).order_by(Ticket.created_at).all():
        rows.append({
            "Type": "Ticket",
            "Date": t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "",
            "Reference": t.ticket_number or "",
            "Subject": t.subject or "",
            "Status": t.status or "",
        })

    for e in LogbookEntry.query.filter(
        func.strftime(YM_FMT, LogbookEntry.date) == ym,
    ).order_by(LogbookEntry.date, LogbookEntry.time_in).all():
        rows.append({
            "Type": "Logbook",
            "Date": f"{e.date} {e.time_in.strftime('%H:%M') if e.time_in else ''}".strip(),
            "Reference": e.visitor_name or "",
            "Subject": (e.purpose or "")[:80],
            "Status": "Out" if e.time_out else "In",
        })

    for a in Appointment.query.filter(
        func.strftime("%Y", Appointment.preferred_date) == str(year),
        func.strftime("%m", Appointment.preferred_date) == f"{month:02d}",
    ).order_by(Appointment.preferred_date, Appointment.preferred_time).all():
        rows.append({
            "Type": "Appointment",
            "Date": a.preferred_date.strftime("%Y-%m-%d") + (f" {a.preferred_time}" if a.preferred_time else ""),
            "Reference": a.requester_name or "",
            "Subject": a.appointment_type or "",
            "Status": a.status or "",
        })

    return rows


@reports_bp.route("/")
@login_required
@staff_required
def index():
    reports = MonthlyReport.query.order_by(
        MonthlyReport.report_year.desc(),
        MonthlyReport.report_month.desc(),
    ).all()
    return render_template("reports/index.html", reports=reports)


@reports_bp.route("/generate", methods=["GET", "POST"])
@login_required
@staff_required
def generate():
    if request.method == "POST":
        year = int(request.form.get("year", datetime.utcnow().year))
        month = int(request.form.get("month", datetime.utcnow().month))

        ym = f"{year}-{month:02d}"
        dr_count = DocumentRequest.query.filter(
            func.strftime(YM_FMT, DocumentRequest.requested_at) == ym,
        ).count()
        tk_count = Ticket.query.filter(
            func.strftime(YM_FMT, Ticket.created_at) == ym,
        ).count()
        lb_count = LogbookEntry.query.filter(
            func.strftime(YM_FMT, LogbookEntry.date) == ym,
        ).count()
        ap_count = db.session.query(Appointment).filter(
            func.strftime("%Y", Appointment.preferred_date) == str(year),
            func.strftime("%m", Appointment.preferred_date) == f"{month:02d}",
        ).count()

        summary = {
            "document_requests": dr_count,
            "tickets": tk_count,
            "logbook": lb_count,
            "appointments": ap_count,
            "total": dr_count + tk_count + lb_count + ap_count,
        }

        report = MonthlyReport(
            report_month=month,
            report_year=year,
            report_type="all_transactions",
            summary_data=json.dumps(summary),
        )
        db.session.add(report)
        db.session.commit()
        from flask import flash, redirect, url_for
        flash(f"Report generated for {year}-{month:02d} ({summary['total']} transactions)", "success")
        return redirect(url_for("reports.index"))

    from datetime import datetime as dt
    return render_template("reports/generate.html", now=dt.utcnow())


@reports_bp.route("/<int:rid>/download")
@login_required
@staff_required
def download(rid):
    report = MonthlyReport.query.get(rid)
    if not report:
        from flask import flash, redirect, url_for
        flash("Report not found.", "error")
        return redirect(url_for("reports.index"))

    fmt = request.args.get("format", "pdf").lower().strip()
    year, month = report.report_year, report.report_month
    base_name = f"report_{year}_{month:02d}"

    if fmt == "csv":
        rows = _all_transactions_rows(year, month)
        out = StringIO()
        if not rows:
            writer = csv.writer(out)
            writer.writerow(["Type", "Date", "Reference", "Subject", "Status"])
        else:
            writer = csv.DictWriter(out, fieldnames=["Type", "Date", "Reference", "Subject", "Status"])
            writer.writeheader()
            writer.writerows(rows)
        out.seek(0)
        return send_file(
            BytesIO(out.getvalue().encode("utf-8-sig")),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"{base_name}.csv",
        )

    if fmt == "xlsx" or fmt == "excel":
        rows = _all_transactions_rows(year, month)
        df = pd.DataFrame(rows, columns=["Type", "Date", "Reference", "Subject", "Status"])
        buf = BytesIO()
        df.to_excel(buf, index=False, sheet_name="Transactions", engine="openpyxl")
        buf.seek(0)
        return send_file(
            buf,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"{base_name}.xlsx",
        )

    # PDF
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(72, 750, f"GCO Monthly Report - {year}-{month:02d}")
    c.drawString(72, 720, "Type: All transactions")
    c.drawString(72, 690, f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M')}")
    if report.summary_data:
        try:
            data = json.loads(report.summary_data)
            y = 660
            for k, v in data.items():
                c.drawString(72, y, f"{k}: {v}")
                y -= 20
        except Exception:
            pass
    c.save()
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{base_name}.pdf",
    )
