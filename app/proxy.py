from flask import Blueprint, abort, redirect

from .models import Demo, User

proxy_bp = Blueprint("proxy", __name__)


@proxy_bp.route("/<student>/<demo>", defaults={"remainder": ""})
@proxy_bp.route("/<student>/<demo>/<path:remainder>")
def handle_demo(student: str, demo: str, remainder: str):
    user = User.query.filter_by(username=student, is_active=True).first()
    if not user:
        abort(404)

    demo_obj = Demo.query.filter_by(
        owner_id=user.id, demo_name=demo, is_active=True
    ).first()
    if not demo_obj:
        abort(404)

    target = demo_obj.target_url.rstrip("/")
    if remainder:
        target = f"{target}/{remainder}"

    return redirect(target, 302)
