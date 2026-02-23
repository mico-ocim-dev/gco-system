"""Authentication routes."""
import re
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from config import MAIL_ENABLED
from extensions import db, mail
from models import User

# Valid email format (standard pattern: local@domain.tld)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
# Only Gmail addresses accepted (so we can send verification to user's email)
GMAIL_DOMAINS = ("@gmail.com", "@googlemail.com")


def _is_valid_gmail(email):
    if not email or not EMAIL_REGEX.fullmatch(email):
        return False
    return email.lower().strip().endswith(GMAIL_DOMAINS)

auth_bp = Blueprint("auth", __name__)


def _redirect_after_login(user):
    """Send users to their dashboard (QR forms), staff to admin dashboard."""
    if user.role == "User":
        return url_for("user_dashboard.index")
    return url_for("dashboard.index")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration - creates User role accounts."""
    if current_user.is_authenticated:
        return redirect(_redirect_after_login(current_user))
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        mi = request.form.get("mi", "").strip().upper()[:2]
        last_name = request.form.get("last_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        # Build full name: "First M. Last" or "First Last"
        full_name = " ".join(filter(None, [first_name, (mi + ".") if mi else None, last_name])) or username
        if not username or not email or not password:
            flash("Username, email, and password are required.", "error")
            return render_template("auth/register.html")
        if not first_name or not last_name:
            flash("First name and last name are required.", "error")
            return render_template("auth/register.html")
        if not EMAIL_REGEX.fullmatch(email):
            flash("Please enter a valid email address.", "error")
            return render_template("auth/register.html")
        if not _is_valid_gmail(email):
            flash("Only Gmail addresses are accepted (e.g. yourname@gmail.com). We will send a verification link to your email.", "error")
            return render_template("auth/register.html")
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html")
        if len(password) < 8:
            flash("Valid password must be at least 8 characters (not less than 8).", "error")
            return render_template("auth/register.html")
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "error")
            return render_template("auth/register.html")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("auth/register.html")
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            role="User",
            email_verified=not MAIL_ENABLED,  # If mail disabled, allow login without verification
        )
        user.set_password(password)
        if MAIL_ENABLED:
            user.verification_token = secrets.token_urlsafe(32)
            user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
        db.session.add(user)
        db.session.commit()
        if MAIL_ENABLED and user.verification_token:
            try:
                from flask_mail import Message
                verify_url = url_for("auth.verify_email", token=user.verification_token, _external=True)
                msg = Message(
                    subject="Verify your Gmail – GCO Office Management",
                    recipients=[email],
                    body=(
                        f"Hi {full_name},\n\n"
                        "Thanks for registering. Please verify your email by clicking the link below. "
                        "After that, you can log in to your dashboard.\n\n"
                        f"{verify_url}\n\n"
                        "This link expires in 24 hours. If you did not register, please ignore this email.\n\n"
                        "— GCO Office Management – LSPU Sta. Cruz"
                    ),
                )
                mail.send(msg)
            except Exception:
                # Leave unverified so they can use "Resend verification" from login page
                pass
        if MAIL_ENABLED and not getattr(user, "email_verified", True):
            flash("Account created. Please check your Gmail and click the verification link—then you can log in.", "success")
        else:
            flash("Account created. You can now log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html")


@auth_bp.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    """Resend verification email for users who didn't receive it or link expired."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            flash("Please enter your Gmail address.", "error")
            return render_template("auth/resend_verification.html")
        if not MAIL_ENABLED:
            flash("Verification email is not configured. Please contact the administrator.", "error")
            return render_template("auth/resend_verification.html")
        user = User.query.filter_by(email=email, role="User", is_active=True).first()
        if not user:
            flash("No account found with this email. Please register first.", "error")
            return render_template("auth/resend_verification.html")
        if getattr(user, "email_verified", True):
            flash("This account is already verified. You can log in.", "success")
            return redirect(url_for("auth.login"))
        user.verification_token = secrets.token_urlsafe(32)
        user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
        try:
            from flask_mail import Message
            verify_url = url_for("auth.verify_email", token=user.verification_token, _external=True)
            msg = Message(
                subject="Verify your Gmail – GCO Office Management",
                recipients=[user.email],
                body=(
                    f"Hi {user.full_name or user.username},\n\n"
                    "You asked for a new verification link. Click the link below to verify your email and log in.\n\n"
                    f"{verify_url}\n\n"
                    "This link expires in 24 hours. If you did not request this, please ignore this email.\n\n"
                    "— GCO Office Management – LSPU Sta. Cruz"
                ),
            )
            mail.send(msg)
            flash("Verification email sent. Check your Gmail (and spam folder), then click the link to verify.", "success")
            return redirect(url_for("auth.login"))
        except Exception:
            flash("Could not send the verification email. Please try again later or contact the administrator.", "error")
    return render_template("auth/resend_verification.html")


@auth_bp.route("/verify-email")
def verify_email():
    """Verify user's Gmail via link sent to their inbox. Required before they can log in."""
    token = request.args.get("token", "").strip()
    if not token:
        flash("Invalid or missing verification link.", "error")
        return redirect(url_for("auth.login"))
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        flash("Invalid or expired verification link. Please register again or request a new link.", "error")
        return redirect(url_for("auth.login"))
    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        flash("Verification link has expired. Please register again to get a new link.", "error")
        user.verification_token = None
        user.verification_token_expires = None
        db.session.commit()
        return redirect(url_for("auth.login"))
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.session.commit()
    flash("Your email is verified. You can now log in to your dashboard.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_redirect_after_login(current_user))
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template("auth/login.html")
        user = User.query.filter_by(email=email, is_active=True).first()
        if user and user.check_password(password):
            # User role must verify Gmail before they can log in; Admin/Staff skip
            email_verified = getattr(user, "email_verified", True)
            if user.role == "User" and not email_verified:
                flash("You must verify your email before you can log in. Check your Gmail (and spam folder) for the verification link, or resend it below.", "error")
                return render_template("auth/login.html", show_resend_verification=True, resend_email=email)
            login_user(user)
            next_page = request.args.get("next") or _redirect_after_login(user)
            return redirect(next_page)
        flash("Invalid email or password.", "error")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
