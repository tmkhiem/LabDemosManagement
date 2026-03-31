import requests as http_requests
from flask import Blueprint, Response, abort, current_app, request, stream_with_context

from .models import Demo, User

proxy_bp = Blueprint("proxy", __name__)

# Hop-by-hop headers that must not be forwarded between proxy and upstream
_HOP_BY_HOP = frozenset(
    h.lower()
    for h in (
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    )
)


def _build_target_url(base_url: str, remainder: str, query_string: str) -> str:
    """Construct the full upstream URL from the registered base, path remainder,
    and the original query string."""
    target = base_url.rstrip("/")
    if remainder:
        target = f"{target}/{remainder}"
    if query_string:
        target = f"{target}?{query_string}"
    return target


def _filtered_request_headers() -> dict[str, str]:
    """Return the incoming request headers with hop-by-hop headers removed and
    the Host header replaced to match the upstream target."""
    headers = {}
    for key, value in request.headers:
        if key.lower() not in _HOP_BY_HOP and key.lower() != "host":
            headers[key] = value
    return headers


@proxy_bp.route("/<student>/<demo>", defaults={"remainder": ""}, methods=[
    "GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS",
])
@proxy_bp.route("/<student>/<demo>/<path:remainder>", methods=[
    "GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS",
])
def handle_demo(student: str, demo: str, remainder: str):
    user = User.query.filter_by(username=student, is_active=True).first()
    if not user:
        abort(404)

    demo_obj = Demo.query.filter_by(
        owner_id=user.id, demo_name=demo, is_active=True
    ).first()
    if not demo_obj:
        abort(404)

    target_url = _build_target_url(
        demo_obj.target_url, remainder, request.query_string.decode("utf-8")
    )

    timeout = current_app.config.get("PROXY_TIMEOUT", 30)
    verify_ssl = current_app.config.get("PROXY_VERIFY_SSL", False)

    # Forward the request to the upstream demo app
    try:
        upstream_resp = http_requests.request(
            method=request.method,
            url=target_url,
            headers=_filtered_request_headers(),
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            stream=True,
            timeout=timeout,
            verify=verify_ssl,
        )
    except http_requests.exceptions.ConnectionError:
        abort(502)
    except http_requests.exceptions.Timeout:
        abort(504)
    except http_requests.exceptions.RequestException:
        abort(502)

    # Build the response, streaming the body from upstream
    def generate():
        for chunk in upstream_resp.raw.stream(65536, decode_content=False):
            yield chunk

    # Filter hop-by-hop headers out of the upstream response
    response_headers = {}
    for key, value in upstream_resp.headers.items():
        if key.lower() not in _HOP_BY_HOP:
            response_headers[key] = value

    return Response(
        stream_with_context(generate()),
        status=upstream_resp.status_code,
        headers=response_headers,
    )
