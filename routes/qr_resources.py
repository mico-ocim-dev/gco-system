"""QR resources management - admin upload, user dashboard display."""
import os
import uuid
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import QRResource
from utils.decorators import staff_required

qr_bp = Blueprint("qr_resources", __name__)


def _allowed_image(filename):
    ext = (filename or "").rsplit(".", 1)[-1].lower()
    return ext in {"png", "jpg", "jpeg", "gif", "webp"}


def _save_upload(file, upload_folder):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    fn = f"{uuid.uuid4().hex[:12]}.{ext}"
    Path(upload_folder).mkdir(parents=True, exist_ok=True)
    file.save(os.path.join(upload_folder, fn))
    return fn


@qr_bp.route("/uploads/qr/<filename>")
def serve_qr_image(filename):
    """Serve QR/uploaded images."""
    from flask import current_app
    folder = Path(current_app.config["UPLOAD_FOLDER"]) / "qr"
    return send_from_directory(str(folder), filename, as_attachment=False)


@qr_bp.route("/manage", methods=["GET"])
@login_required
@staff_required
def manage():
    """Admin: list all QR resources."""
    resources = QRResource.query.order_by(QRResource.order_index, QRResource.name).all()
    return render_template("qr_resources/manage.html", resources=resources)


@qr_bp.route("/manage/add", methods=["GET", "POST"])
@login_required
@staff_required
def add():
    """Admin: add new QR resource with image upload."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        form_url = request.form.get("form_url", "").strip()
        file = request.files.get("image")
        if not name:
            flash("Name is required.", "error")
            return render_template("qr_resources/form.html", resource=None)
        if not file or not file.filename:
            flash("Please upload an image (QR code).", "error")
            return render_template("qr_resources/form.html", resource=None)
        if not _allowed_image(file.filename):
            flash("Invalid image. Use PNG, JPG, GIF, or WebP.", "error")
            return render_template("qr_resources/form.html", resource=None)
        upload_folder = Path(current_app.config["UPLOAD_FOLDER"]) / "qr"
        fn = _save_upload(file, upload_folder)
        r = QRResource(
            name=name,
            description=description or None,
            image_filename=fn,
            form_url=form_url or None,
            order_index=QRResource.query.count(),
        )
        db.session.add(r)
        db.session.commit()
        flash(f"Added: {name}", "success")
        return redirect(url_for("qr_resources.manage"))
    return render_template("qr_resources/form.html", resource=None)


@qr_bp.route("/manage/<int:rid>/edit", methods=["GET", "POST"])
@login_required
@staff_required
def edit(rid):
    """Admin: edit QR resource - change image or details."""
    r = QRResource.query.get(rid)
    if not r:
        flash("Not found.", "error")
        return redirect(url_for("qr_resources.manage"))
    if request.method == "POST":
        r.name = request.form.get("name", "").strip() or r.name
        r.description = request.form.get("description", "").strip() or None
        r.form_url = request.form.get("form_url", "").strip() or None
        file = request.files.get("image")
        if file and file.filename and _allowed_image(file.filename):
            upload_folder = Path(current_app.config["UPLOAD_FOLDER"]) / "qr"
            old_path = upload_folder / r.image_filename
            if old_path.exists():
                try:
                    old_path.unlink()
                except Exception:
                    pass
            r.image_filename = _save_upload(file, upload_folder)
        db.session.commit()
        flash("Updated.", "success")
        return redirect(url_for("qr_resources.manage"))
    return render_template("qr_resources/form.html", resource=r)


@qr_bp.route("/manage/<int:rid>/delete", methods=["POST"])
@login_required
@staff_required
def delete(rid):
    r = QRResource.query.get(rid)
    if not r:
        flash("Not found.", "error")
        return redirect(url_for("qr_resources.manage"))
    from flask import current_app
    p = Path(current_app.config["UPLOAD_FOLDER"]) / "qr" / r.image_filename
    if p.exists():
        try:
            p.unlink()
        except Exception:
            pass
    db.session.delete(r)
    db.session.commit()
    flash("Deleted.", "info")
    return redirect(url_for("qr_resources.manage"))
