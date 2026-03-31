import ipaddress
import re
from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import db
from .models import Demo, Server

student_bp = Blueprint("student", __name__, url_prefix="/dashboard")

SLUG_RE = re.compile(r"^[a-z0-9-]+$")

BLOCKED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "0000:0000:0000:0000:0000:0000:0000:0001",
}

_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]


def _is_private_ip(ip_str: str) -> bool:
    """Return True if the string is a valid IP in a private RFC-1918 range."""
    try:
        addr = ipaddress.ip_address(ip_str)
        return any(addr in net for net in _PRIVATE_NETWORKS)
    except ValueError:
        return False


def _validate_target_url(url: str, allow_local: bool = False) -> str | None:
    """Return error message or None if valid."""
    if not url:
        return "Target URL is required."
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "Target URL must start with http:// or https://."
    hostname = (parsed.hostname or "").lower()
    if allow_local:
        return None
    if hostname in BLOCKED_HOSTS:
        return "Target URL cannot point to localhost or loopback addresses."
    if hostname.startswith("127.") or hostname.startswith("169.254."):
        return "Target URL cannot point to loopback or link-local addresses."
    # If the host looks like an IP address, enforce private range only
    try:
        ipaddress.ip_address(hostname)
        if not _is_private_ip(hostname):
            return "Target URL must point to an internal LAN IP (e.g. 10.x.x.x, 192.168.x.x)."
    except ValueError:
        pass  # hostname, not a bare IP — allow for internal FQDNs
    return None


def _url_from_form(form) -> tuple[str, str | None]:
    """Build target URL from server_id + port + scheme form fields.

    Returns (url, error_message). error_message is None on success.
    """
    server_id = form.get("server_id", "").strip()
    port = form.get("port", "").strip()
    scheme = form.get("scheme", "http").strip().lower()

    if scheme not in ("http", "https"):
        return "", "Scheme must be http or https."

    if not server_id:
        return "", "Please select a server."

    server = db.session.get(Server, int(server_id)) if server_id.isdigit() else None
    if not server:
        return "", "Selected server not found."

    if port:
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            return "", "Port must be a number between 1 and 65535."
        url = f"{scheme}://{server.ip}:{port}"
    else:
        url = f"{scheme}://{server.ip}"

    return url, None


@student_bp.route("")
@student_bp.route("/")
@login_required
def dashboard():
    if current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    demos = (
        Demo.query.filter_by(owner_id=current_user.id)
        .order_by(Demo.created_at.desc())
        .all()
    )
    servers = Server.query.order_by(Server.name).all()
    return render_template("student/dashboard.html", demos=demos, servers=servers)


@student_bp.route("/demos/create", methods=["POST"])
@login_required
def create_demo():
    from flask import current_app

    if current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))

    demo_name = request.form.get("demo_name", "").strip().lower()
    description = request.form.get("description", "").strip()

    reserved = current_app.config.get("RESERVED_SLUGS", [])

    if not demo_name:
        flash("Demo name is required.", "error")
        return redirect(url_for("student.dashboard"))

    if demo_name in reserved:
        flash(f"Demo name '{demo_name}' is reserved.", "error")
        return redirect(url_for("student.dashboard"))

    if not SLUG_RE.match(demo_name):
        flash("Demo name must contain only lowercase letters, numbers, and hyphens.", "error")
        return redirect(url_for("student.dashboard"))

    target_url, url_error = _url_from_form(request.form)
    if url_error:
        flash(url_error, "error")
        return redirect(url_for("student.dashboard"))

    allow_local = current_app.config.get("ALLOW_LOCAL_URLS", False)
    validation_error = _validate_target_url(target_url, allow_local)
    if validation_error:
        flash(validation_error, "error")
        return redirect(url_for("student.dashboard"))

    existing = Demo.query.filter_by(
        owner_id=current_user.id, demo_name=demo_name
    ).first()
    if existing:
        flash(f"You already have a demo named '{demo_name}'.", "error")
        return redirect(url_for("student.dashboard"))

    demo = Demo(
        owner_id=current_user.id,
        demo_name=demo_name,
        target_url=target_url,
        description=description or None,
    )
    db.session.add(demo)
    db.session.commit()
    flash(f"Demo '{demo_name}' registered successfully.", "success")
    return redirect(url_for("student.dashboard"))


@student_bp.route("/demos/<int:demo_id>/update", methods=["POST"])
@login_required
def update_demo(demo_id):
    from flask import current_app

    demo = db.get_or_404(Demo, demo_id)
    if demo.owner_id != current_user.id:
        flash("You do not have permission to edit this demo.", "error")
        return redirect(url_for("student.dashboard"))

    description = request.form.get("description", "").strip()

    target_url, url_error = _url_from_form(request.form)
    if url_error:
        flash(url_error, "error")
        return redirect(url_for("student.dashboard"))

    allow_local = current_app.config.get("ALLOW_LOCAL_URLS", False)
    validation_error = _validate_target_url(target_url, allow_local)
    if validation_error:
        flash(validation_error, "error")
        return redirect(url_for("student.dashboard"))

    from datetime import datetime, timezone
    demo.target_url = target_url
    demo.description = description or None
    demo.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    flash(f"Demo '{demo.demo_name}' updated successfully.", "success")
    return redirect(url_for("student.dashboard"))


@student_bp.route("/demos/<int:demo_id>/toggle", methods=["POST"])
@login_required
def toggle_demo(demo_id):
    demo = db.get_or_404(Demo, demo_id)
    if demo.owner_id != current_user.id:
        flash("You do not have permission to modify this demo.", "error")
        return redirect(url_for("student.dashboard"))

    demo.is_active = not demo.is_active
    db.session.commit()
    state = "activated" if demo.is_active else "deactivated"
    flash(f"Demo '{demo.demo_name}' has been {state}.", "success")
    return redirect(url_for("student.dashboard"))


@student_bp.route("/demos/<int:demo_id>/delete", methods=["POST"])
@login_required
def delete_demo(demo_id):
    demo = db.get_or_404(Demo, demo_id)
    if demo.owner_id != current_user.id:
        flash("You do not have permission to delete this demo.", "error")
        return redirect(url_for("student.dashboard"))

    demo.is_active = False
    db.session.commit()
    flash(f"Demo '{demo.demo_name}' has been deactivated.", "success")
    return redirect(url_for("student.dashboard"))
