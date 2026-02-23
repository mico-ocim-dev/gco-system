"""CSV/Excel import and export with validation."""
import io
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from flask import current_app
from werkzeug.utils import secure_filename

from extensions import db
from models import (
    DocumentRequest,
    RequestStatusLog,
    Ticket,
    Survey,
    SurveyQuestion,
    SurveyResponse,
    LogbookEntry,
    ImportLog,
)


def _allowed_file(filename):
    ext = (filename or "").rsplit(".", 1)[-1].lower()
    return ext in {"csv", "xlsx", "xls"}


def _parse_file(file) -> pd.DataFrame:
    filename = getattr(file, "filename", "") or ""
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "csv":
        return pd.read_csv(file, encoding="utf-8", encoding_errors="ignore")
    return pd.read_excel(file)


def _log_import(import_type: str, filename: str, rows_imported: int, rows_failed: int, status: str, error: str, user: str):
    log = ImportLog(
        import_type=import_type,
        filename=secure_filename(filename),
        rows_imported=rows_imported,
        rows_failed=rows_failed,
        status=status,
        error_message=error[:1000] if error else None,
        imported_by=user,
    )
    db.session.add(log)


# Document Requests
REQ_COLUMNS = ["requester_name", "document_type", "purpose", "requester_email"]


def import_requests_excel(file, user: str) -> tuple[int, int, str | None]:
    """Import document requests from CSV/Excel. Returns (imported, failed, error)."""
    if not _allowed_file(getattr(file, "filename", "")):
        return 0, 0, "Invalid file type. Use .csv or .xlsx"
    try:
        df = _parse_file(file)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        missing = [c for c in REQ_COLUMNS if c not in df.columns]
        if missing:
            return 0, 0, f"Missing required columns: {', '.join(missing)}"
        imported, failed = 0, 0
        year = datetime.utcnow().year
        max_seq = 0
        for r in DocumentRequest.query.filter(DocumentRequest.tracking_number.like(f"GCO-{year}-%")).all():
            m = re.search(r"GCO-\d{4}-(\d+)", r.tracking_number)
            if m:
                max_seq = max(max_seq, int(m.group(1)))
        for idx, row in df.iterrows():
            try:
                name = str(row.get("requester_name", "")).strip()
                doc_type = str(row.get("document_type", "")).strip()
                if not name or not doc_type:
                    failed += 1
                    continue
                max_seq += 1
                tn = f"GCO-{year}-{max_seq:05d}"
                req = DocumentRequest(
                    tracking_number=tn,
                    requester_name=name,
                    requester_email=str(row.get("requester_email", "")).strip() or None,
                    document_type=doc_type,
                    purpose=str(row.get("purpose", "")).strip() or None,
                    status="Pending",
                )
                db.session.add(req)
                imported += 1
            except Exception:
                failed += 1
        db.session.commit()
        status = "Success" if failed == 0 else ("Partial" if imported else "Failed")
        _log_import("document_requests", getattr(file, "filename", "upload"), imported, failed, status, None, user)
        return imported, failed, None
    except Exception as e:
        db.session.rollback()
        _log_import("document_requests", getattr(file, "filename", "upload"), 0, 0, "Failed", str(e), user)
        return 0, 0, str(e)


def export_requests_excel() -> bytes:
    """Export document requests to Excel bytes."""
    reqs = DocumentRequest.query.order_by(DocumentRequest.requested_at.desc()).all()
    data = [
        {
            "Tracking Number": r.tracking_number,
            "Requester Name": r.requester_name,
            "Email": r.requester_email or "",
            "Document Type": r.document_type,
            "Purpose": r.purpose or "",
            "Status": r.status,
            "Requested At": r.requested_at.strftime("%Y-%m-%d %H:%M") if r.requested_at else "",
        }
        for r in reqs
    ]
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


# Tickets
TICKET_COLUMNS = ["subject", "requester_name", "description", "requester_email", "priority"]


def import_tickets_excel(file, user: str) -> tuple[int, int, str | None]:
    if not _allowed_file(getattr(file, "filename", "")):
        return 0, 0, "Invalid file type. Use .csv or .xlsx"
    try:
        df = _parse_file(file)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        if "subject" not in df.columns or "requester_name" not in df.columns:
            return 0, 0, "Missing required columns: subject, requester_name"
        imported, failed = 0, 0
        for idx, row in df.iterrows():
            try:
                subj = str(row.get("subject", "")).strip()
                name = str(row.get("requester_name", "")).strip()
                if not subj or not name:
                    failed += 1
                    continue
                last = Ticket.query.order_by(Ticket.id.desc()).first()
                tn = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{(last.id + 1) if last else 1:04d}"
                t = Ticket(
                    ticket_number=tn,
                    subject=subj,
                    description=str(row.get("description", "")).strip() or None,
                    requester_name=name,
                    requester_email=str(row.get("requester_email", "")).strip() or None,
                    priority=str(row.get("priority", "Medium")).strip() or "Medium",
                    status="Open",
                )
                db.session.add(t)
                imported += 1
            except Exception:
                failed += 1
        db.session.commit()
        status = "Success" if failed == 0 else ("Partial" if imported else "Failed")
        _log_import("tickets", getattr(file, "filename", "upload"), imported, failed, status, None, user)
        return imported, failed, None
    except Exception as e:
        db.session.rollback()
        _log_import("tickets", getattr(file, "filename", "upload"), 0, 0, "Failed", str(e), user)
        return 0, 0, str(e)


def export_tickets_excel() -> bytes:
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    data = [
        {
            "Ticket #": t.ticket_number,
            "Subject": t.subject,
            "Requester": t.requester_name,
            "Email": t.requester_email or "",
            "Status": t.status,
            "Priority": t.priority,
            "Created": t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "",
        }
        for t in tickets
    ]
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


# Logbook
LOGBOOK_COLUMNS = ["visitor_name", "purpose", "time_in", "date"]


def import_logbook_excel(file, user: str) -> tuple[int, int, str | None]:
    if not _allowed_file(getattr(file, "filename", "")):
        return 0, 0, "Invalid file type. Use .csv or .xlsx"
    try:
        df = _parse_file(file)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        if "visitor_name" not in df.columns or "date" not in df.columns:
            return 0, 0, "Missing required columns: visitor_name, date"
        imported, failed = 0, 0
        for idx, row in df.iterrows():
            try:
                name = str(row.get("visitor_name", "")).strip()
                dt_val = row.get("date") or row.get("time_in")
                if not name or pd.isna(dt_val):
                    failed += 1
                    continue
                if isinstance(dt_val, str):
                    dt_val = pd.to_datetime(dt_val)
                d = dt_val.date() if hasattr(dt_val, "date") else datetime.strptime(str(dt_val)[:10], "%Y-%m-%d").date()
                t_in = dt_val if hasattr(dt_val, "hour") else datetime.combine(d, datetime.min.time())
                if isinstance(t_in, str):
                    t_in = datetime.strptime(t_in[:19], "%Y-%m-%d %H:%M:%S")
                entry = LogbookEntry(
                    visitor_name=name,
                    purpose=str(row.get("purpose", "")).strip() or None,
                    time_in=t_in,
                    date=d,
                    remarks=str(row.get("remarks", "")).strip() or None,
                )
                db.session.add(entry)
                imported += 1
            except Exception:
                failed += 1
        db.session.commit()
        status = "Success" if failed == 0 else ("Partial" if imported else "Failed")
        _log_import("logbook", getattr(file, "filename", "upload"), imported, failed, status, None, user)
        return imported, failed, None
    except Exception as e:
        db.session.rollback()
        _log_import("logbook", getattr(file, "filename", "upload"), 0, 0, "Failed", str(e), user)
        return 0, 0, str(e)


def export_logbook_excel() -> bytes:
    entries = LogbookEntry.query.order_by(LogbookEntry.time_in.desc()).all()
    data = [
        {
            "Visitor": e.visitor_name,
            "Purpose": e.purpose or "",
            "Time In": e.time_in.strftime("%Y-%m-%d %H:%M") if e.time_in else "",
            "Time Out": e.time_out.strftime("%Y-%m-%d %H:%M") if e.time_out else "",
            "Date": str(e.date) if e.date else "",
        }
        for e in entries
    ]
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


# Survey responses
def import_survey_responses_excel(file, survey_id: int, user: str) -> tuple[int, int, str | None]:
    if not _allowed_file(getattr(file, "filename", "")):
        return 0, 0, "Invalid file type. Use .csv or .xlsx"
    survey = Survey.query.get(survey_id)
    if not survey:
        return 0, 0, "Survey not found"
    try:
        df = _parse_file(file)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        questions = SurveyQuestion.query.filter_by(survey_id=survey_id).order_by(SurveyQuestion.order_index).all()
        if not questions:
            return 0, 0, "Survey has no questions"
        imported, failed = 0, 0
        for idx, row in df.iterrows():
            try:
                for q in questions:
                    qkey = f"q{q.id}" if f"q{q.id}" in df.columns else (q.question_text[:30] if q.question_text[:30] in df.columns else None)
                    if qkey is None:
                        continue
                    val = row.get(qkey)
                    if pd.isna(val):
                        continue
                    resp = SurveyResponse(
                        survey_id=survey_id,
                        question_id=q.id,
                        response_value=float(val) if isinstance(val, (int, float)) else None,
                        response_text=str(val) if not isinstance(val, (int, float)) else None,
                    )
                    db.session.add(resp)
                    imported += 1
            except Exception:
                failed += 1
        db.session.commit()
        status = "Success" if failed == 0 else ("Partial" if imported else "Failed")
        _log_import("survey_responses", getattr(file, "filename", "upload"), imported, failed, status, None, user)
        return imported, failed, None
    except Exception as e:
        db.session.rollback()
        _log_import("survey_responses", getattr(file, "filename", "upload"), 0, 0, "Failed", str(e), user)
        return 0, 0, str(e)
