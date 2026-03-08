"""Morning Briefing API route.

Endpoint:
    GET /api/briefing → aggregated system state for the Morning Briefing Card
"""

from flask import Blueprint, current_app, jsonify

from app.services import briefing as briefing_service

briefing_bp = Blueprint("briefing", __name__)


@briefing_bp.route("/api/briefing", methods=["GET"])
def briefing():
    """Return the morning briefing payload."""
    mgr = current_app.config.get("SERVICE_MANAGER")
    if mgr is None:
        return jsonify({"error": "ServiceManager not initialised."}), 503
    return jsonify(briefing_service.generate(mgr))
