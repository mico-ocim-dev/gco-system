"""Document request business logic."""
import re
from datetime import datetime
from extensions import db
from models import DocumentRequest, RequestStatusLog


def generate_tracking_number() -> str:
    """Generate unique tracking number (e.g., GCO-2025-00001)."""
    year = datetime.utcnow().year
    last = (
        DocumentRequest.query.filter(
            DocumentRequest.tracking_number.like(f"GCO-{year}-%")
        )
        .order_by(DocumentRequest.id.desc())
        .first()
    )
    seq = 1
    if last:
        m = re.search(r"GCO-\d{4}-(\d+)", last.tracking_number)
        if m:
            seq = int(m.group(1)) + 1
    return f"GCO-{year}-{seq:05d}"


def create_request(
    requester_name: str,
    document_type: str,
    purpose: str = None,
    requester_email: str = None,
    user_id: int = None,
) -> DocumentRequest:
    """Create a new document request. Logbook entries are added by admin when they record visitor details."""
    req = DocumentRequest(
        tracking_number=generate_tracking_number(),
        requester_name=requester_name.strip(),
        requester_email=requester_email.strip() if requester_email else None,
        document_type=document_type.strip(),
        purpose=purpose.strip() if purpose else None,
        status="Pending",
        user_id=user_id,
    )
    db.session.add(req)
    db.session.flush()
    _add_status_log(req.id, "Pending", "Request created", None)
    db.session.commit()
    return req


def get_request_by_tracking(tracking_number: str):
    """Get document request by tracking number."""
    return DocumentRequest.query.filter_by(
        tracking_number=tracking_number.strip()
    ).first()


def update_request_status(
    request_id: int,
    new_status: str,
    notes: str = None,
    changed_by: str = None,
) -> bool:
    """Update request status and log change."""
    req = DocumentRequest.query.get(request_id)
    if not req:
        return False
    old_status = req.status
    req.status = new_status
    if new_status in ("Ready", "Claimed", "Cancelled"):
        req.completed_at = datetime.utcnow()
    _add_status_log(request_id, new_status, notes, changed_by)
    db.session.commit()
    return True


def _add_status_log(request_id: int, status: str, notes: str, changed_by: str):
    log = RequestStatusLog(
        document_request_id=request_id,
        status=status,
        notes=notes,
        changed_by=changed_by,
    )
    db.session.add(log)
