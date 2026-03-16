# Author: Mani Padisetti
"""Browser fallback web UI routes.

Serves the V2 Workshop dashboard at / (which becomes /workshop/
when mounted with the prefix).
"""

from flask import Blueprint, current_app, render_template

web_bp = Blueprint("web", __name__)


def _mgr():
    return current_app.config.get("SERVICE_MANAGER")


@web_bp.route("/", methods=["GET"])
def dashboard():
    """Render the V2 Workshop dashboard."""
    return render_template("dashboard.html")


@web_bp.route("/health", methods=["GET"])
def health_shortcut():
    """Shortcut health check at /workshop/health."""
    from flask import jsonify
    return jsonify({"status": "operational", "service": "workshop"})
