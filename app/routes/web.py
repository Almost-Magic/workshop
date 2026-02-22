"""Browser fallback web UI routes.

Serves a Jinja2 HTML page at the root (/) showing the service grid
with dark theme, port numbers, and status dots.  This is the fallback
when Electron Desktop is not available.
"""

from flask import Blueprint, current_app, render_template, request

from app.services import incident_logger

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


@web_bp.route("/incidents", methods=["GET"])
def incidents_page():
    """Render the incident timeline page."""
    # Get filter parameters
    app_filter = request.args.get("app")
    date_filter = request.args.get("date", "all")

    # Get all incidents
    incidents = incident_logger.get_incidents(limit=100, app_id=app_filter)

    # Filter by date if needed
    if date_filter != "all":
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone(timedelta(hours=10)))
        if date_filter == "today":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_filter == "7days":
            cutoff = now - timedelta(days=7)
        else:
            cutoff = None

        if cutoff:
            incidents = [
                inc for inc in incidents
                if datetime.fromisoformat(inc["timestamp"]) >= cutoff
            ]

    # Get unique app IDs for filter dropdown
    mgr = _mgr()
    services = mgr.get_all() if mgr else []

    return render_template(
        "incidents.html",
        incidents=incidents,
        services=services,
        app_filter=app_filter,
        date_filter=date_filter,
    )
