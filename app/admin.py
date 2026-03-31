import re
from datetime import datetime, timedelta, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for

from . import db
from .auth import admin_required
from .models import Demo, User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

SLUG_RE = re.compile(r"^[a-z0-9-]+$")


@admin_bp.route("")
@admin_bp.route("/")
@admin_required
def dashboard():
    total_users = User.query.filter_by(role="student").count()
    active_demos = Demo.query.filter_by(is_active=True).count()
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_count = Demo.query.filter(Demo.created_at >= week_ago).count()
    recent_demos = (
        Demo.query.order_by(Demo.created_at.desc()).limit(10).all()
    )
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        active_demos=active_demos,
        recent_count=recent_count,
        recent_demos=recent_demos,
    )


@admin_bp.route("/users")
@admin_required
def users():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    pagination = (
        User.query.filter_by(role="student")
        .order_by(User.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return render_template("admin/users.html", pagination=pagination)


@admin_bp.route("/users/create", methods=["POST"])
@admin_required
def create_user():
    from flask import current_app

    username = request.form.get("username", "").strip().lower()
    display_name = request.form.get("display_name", "").strip()
    password = request.form.get("password", "")

    reserved = current_app.config.get("RESERVED_SLUGS", [])

    if not username or not display_name or not password:
        flash("All fields are required.", "error")
        return redirect(url_for("admin.users"))

    if username in reserved:
        flash(f"Username '{username}' is reserved.", "error")
        return redirect(url_for("admin.users"))

    if not SLUG_RE.match(username):
        flash("Username must contain only lowercase letters, numbers, and hyphens.", "error")
        return redirect(url_for("admin.users"))

    if User.query.filter_by(username=username).first():
        flash(f"Username '{username}' is already taken.", "error")
        return redirect(url_for("admin.users"))

    user = User(username=username, display_name=display_name, role="student")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f"Student account '{username}' created successfully.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@admin_required
def reset_password(user_id):
    user = db.get_or_404(User, user_id)
    new_password = request.form.get("new_password", "")
    if not new_password:
        flash("New password is required.", "error")
        return redirect(url_for("admin.users"))
    user.set_password(new_password)
    db.session.commit()
    flash(f"Password for '{user.username}' has been reset.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_user(user_id):
    user = db.get_or_404(User, user_id)
    user.is_active = not user.is_active
    db.session.commit()
    state = "activated" if user.is_active else "deactivated"
    flash(f"Account '{user.username}' has been {state}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = db.get_or_404(User, user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f"Account '{username}' and all their demos have been deleted.", "success")
    return redirect(url_for("admin.users"))
