import ipaddress
import re
from datetime import datetime, timedelta, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for

from . import db
from .auth import admin_required
from .models import Demo, Server, User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

SLUG_RE = re.compile(r"^[a-z0-9-]+$")

_UTC7 = timezone(timedelta(hours=7))

_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]


def _is_private_ip(ip_str: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
        return any(addr in net for net in _PRIVATE_NETWORKS)
    except ValueError:
        return False


def _validate_server_ip(ip: str) -> str | None:
    """Return error message or None if the IP is a valid private address."""
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return "Invalid IP address format."
    if not _is_private_ip(ip):
        return "Server IP must be an internal LAN address (10.x.x.x, 172.16-31.x.x, or 192.168.x.x)."
    return None


def _format_last_access(dt: datetime | None) -> dict:
    """Return a display dict for last_accessed_at."""
    if dt is None:
        return {"utc7": "Never", "relative": "—", "is_old": False, "never": True}
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt
    total_secs = diff.total_seconds()
    utc7_str = dt.astimezone(_UTC7).strftime("%Y-%m-%d %H:%M UTC+7")
    if total_secs < 60:
        relative = "just now"
    elif total_secs < 3600:
        mins = int(total_secs // 60)
        relative = f"{mins} min{'s' if mins != 1 else ''} ago"
    elif total_secs < 86400:
        hours = int(total_secs // 3600)
        relative = f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = diff.days
        relative = f"{days} day{'s' if days != 1 else ''} ago"
    return {"utc7": utc7_str, "relative": relative, "is_old": diff.days > 30, "never": False}


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

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
    total_servers = Server.query.count()
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        active_demos=active_demos,
        recent_count=recent_count,
        recent_demos=recent_demos,
        total_servers=total_servers,
    )


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Servers
# ---------------------------------------------------------------------------

@admin_bp.route("/servers")
@admin_required
def servers():
    all_servers = Server.query.order_by(Server.name).all()
    return render_template("admin/servers.html", servers=all_servers)


@admin_bp.route("/servers/create", methods=["POST"])
@admin_required
def create_server():
    name = request.form.get("name", "").strip().lower()
    ip = request.form.get("ip", "").strip()

    if not name or not ip:
        flash("Server name and IP are required.", "error")
        return redirect(url_for("admin.servers"))

    if not SLUG_RE.match(name):
        flash("Server name must contain only lowercase letters, numbers, and hyphens.", "error")
        return redirect(url_for("admin.servers"))

    ip_error = _validate_server_ip(ip)
    if ip_error:
        flash(ip_error, "error")
        return redirect(url_for("admin.servers"))

    if Server.query.filter_by(name=name).first():
        flash(f"Server name '{name}' is already taken.", "error")
        return redirect(url_for("admin.servers"))

    server = Server(name=name, ip=ip)
    db.session.add(server)
    db.session.commit()
    flash(f"Server '{name}' ({ip}) added successfully.", "success")
    return redirect(url_for("admin.servers"))


@admin_bp.route("/servers/<int:server_id>/update", methods=["POST"])
@admin_required
def update_server(server_id):
    server = db.get_or_404(Server, server_id)
    ip = request.form.get("ip", "").strip()

    if not ip:
        flash("IP address is required.", "error")
        return redirect(url_for("admin.servers"))

    ip_error = _validate_server_ip(ip)
    if ip_error:
        flash(ip_error, "error")
        return redirect(url_for("admin.servers"))

    server.ip = ip
    db.session.commit()
    flash(f"Server '{server.name}' updated to {ip}.", "success")
    return redirect(url_for("admin.servers"))


@admin_bp.route("/servers/<int:server_id>/delete", methods=["POST"])
@admin_required
def delete_server(server_id):
    server = db.get_or_404(Server, server_id)
    name = server.name
    db.session.delete(server)
    db.session.commit()
    flash(f"Server '{name}' has been deleted.", "success")
    return redirect(url_for("admin.servers"))


# ---------------------------------------------------------------------------
# Demo Report
# ---------------------------------------------------------------------------

@admin_bp.route("/demos")
@admin_required
def demo_report():
    sort = request.args.get("sort", "created_at")
    direction = request.args.get("dir", "desc")

    allowed_sorts = {
        "demo_name": Demo.demo_name,
        "hit_count": Demo.hit_count,
        "last_accessed_at": Demo.last_accessed_at,
        "created_at": Demo.created_at,
    }
    sort_col = allowed_sorts.get(sort, Demo.created_at)
    if direction == "asc":
        query = Demo.query.order_by(sort_col.asc().nullslast())
    else:
        query = Demo.query.order_by(sort_col.desc().nullslast())

    demos = query.all()
    servers = Server.query.order_by(Server.name).all()
    access_info = [_format_last_access(d.last_accessed_at) for d in demos]
    now_utc = datetime.now(timezone.utc)
    return render_template(
        "admin/demo_report.html",
        demos=demos,
        access_info=access_info,
        servers=servers,
        sort=sort,
        direction=direction,
        now_utc=now_utc,
    )


@admin_bp.route("/demos/<int:demo_id>/update", methods=["POST"])
@admin_required
def update_demo(demo_id):
    demo = db.get_or_404(Demo, demo_id)
    description = request.form.get("description", "").strip()

    # Build URL from server + port + scheme
    from .student import _url_from_form, _validate_target_url
    from flask import current_app

    target_url, url_error = _url_from_form(request.form)
    if url_error:
        flash(url_error, "error")
        return redirect(url_for("admin.demo_report"))

    allow_local = current_app.config.get("ALLOW_LOCAL_URLS", False)
    validation_error = _validate_target_url(target_url, allow_local)
    if validation_error:
        flash(validation_error, "error")
        return redirect(url_for("admin.demo_report"))

    demo.target_url = target_url
    demo.description = description or None
    demo.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    flash(f"Demo '{demo.demo_name}' updated successfully.", "success")
    return redirect(url_for("admin.demo_report"))


@admin_bp.route("/demos/<int:demo_id>/delete", methods=["POST"])
@admin_required
def delete_demo(demo_id):
    demo = db.get_or_404(Demo, demo_id)
    name = demo.demo_name
    db.session.delete(demo)
    db.session.commit()
    flash(f"Demo '{name}' has been permanently deleted.", "success")
    return redirect(url_for("admin.demo_report"))
