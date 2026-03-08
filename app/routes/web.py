"""Browser fallback web UI routes.

Serves a Jinja2 HTML page at the root (/) showing the service grid
with dark theme, port numbers, and status dots.  This is the fallback
when Electron Desktop is not available.
"""

from flask import Blueprint, current_app, render_template

web_bp = Blueprint("web", __name__)


def _mgr():
    return current_app.config.get("SERVICE_MANAGER")


@web_bp.route("/", methods=["GET"])
def dashboard():
    """Render the browser fallback dashboard."""
    mgr = _mgr()
    services = mgr.get_all() if mgr else []

    # Group services for display
    groups = {}
    for svc in services:
        grp = svc.get("group", "other")
        groups.setdefault(grp, []).append(svc)

    return render_template("dashboard.html", groups=groups, services=services)
