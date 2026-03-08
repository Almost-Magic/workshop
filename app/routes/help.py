"""Context-aware Help API — AMTL-ECO-CTX-1.0.

Endpoint:
    GET /api/help/<screen_id> → help content for a specific screen.

Screen IDs: dashboard, service-manager, constellation, incidents.
"""

from flask import Blueprint, jsonify

help_bp = Blueprint("help", __name__)

# Help content per screen (Phase 7 full content)
HELP_DATA = {
    "dashboard": {
        "howItWorks": (
            "The Dashboard is your home screen. It shows all registered "
            "AMTL services grouped by category, with live status dots, "
            "port numbers, and quick actions."
        ),
        "quickActions": [
            "Click any service to open it in a tab",
            "Press Space to open the Command Palette",
            "Press Ctrl+D to toggle dark/light theme",
        ],
        "tips": [
            "Services with a green dot are running and healthy.",
            "Ghost apps (marked with ✦) are planned but not yet built.",
            "The Morning Briefing card appears once when you open Workshop.",
        ],
        "shortcuts": [
            {"key": "Space", "action": "Open Command Palette"},
            {"key": "Ctrl+K", "action": "Open Command Palette (alternative)"},
            {"key": "Ctrl+D", "action": "Toggle dark/light theme"},
            {"key": "Ctrl+Shift+C", "action": "Toggle Constellation View"},
            {"key": "?", "action": "Open this help panel"},
            {"key": "Esc", "action": "Close any panel or modal"},
        ],
        "relatedScreens": ["service-manager", "constellation", "incidents"],
        "firstVisitTooltip": (
            "Welcome to The Workshop! Press Space to search for any app, "
            "or click a service in the sidebar to open it."
        ),
    },
    "service-manager": {
        "howItWorks": (
            "The Service Manager lets you control individual services. "
            "You can start, stop, and restart apps. The Workshop will "
            "automatically resolve dependencies when starting a service."
        ),
        "quickActions": [
            "Click Start to launch a stopped service",
            "Click Stop to shut down a running service",
            "Open in Browser to view outside the Workshop",
        ],
        "tips": [
            "Starting a service also starts its dependencies.",
            "If a service won't start, check the Incident Log.",
            "Resource bars show live CPU/RAM from Supervisor.",
        ],
        "shortcuts": [
            {"key": "Ctrl+1-9", "action": "Switch between open tabs"},
            {"key": "Ctrl+W", "action": "Close current tab"},
            {"key": "Ctrl+Q", "action": "Quit Workshop completely"},
        ],
        "relatedScreens": ["dashboard", "incidents"],
        "firstVisitTooltip": (
            "Each tab shows a running service. Use Ctrl+1-9 to "
            "switch tabs quickly."
        ),
    },
    "constellation": {
        "howItWorks": (
            "The Constellation View shows all services as a force-directed "
            "node graph. Thick gold lines are hard dependencies, dashed "
            "lines are soft dependencies. Running services pulse gently."
        ),
        "quickActions": [
            "Click a node to open that service",
            "Hover for service details",
            "Drag nodes to rearrange the graph",
        ],
        "tips": [
            "Ghost nodes appear at 40% opacity with a ✦ symbol.",
            "Node size is proportional to the number of dependents.",
            "Toggle back with Ctrl+Shift+C or the sidebar button.",
        ],
        "shortcuts": [
            {"key": "Ctrl+Shift+C", "action": "Toggle Constellation View"},
        ],
        "relatedScreens": ["dashboard"],
        "firstVisitTooltip": (
            "This is the Constellation View — a visual map of your "
            "entire AMTL ecosystem."
        ),
    },
    "incidents": {
        "howItWorks": (
            "The Incident Log records every start, stop, crash, restart, "
            "and health degradation event. You can filter by app and "
            "annotate incidents with notes."
        ),
        "quickActions": [
            "Click an incident to see details",
            "Click 'Add note' to annotate",
            "Filter by app using the dropdown",
        ],
        "tips": [
            "Escalated incidents appear as warnings in the Morning Briefing.",
            "The self-healer logs all recovery attempts automatically.",
            "Annotations are saved permanently in the local database.",
        ],
        "shortcuts": [
            {"key": "Space", "action": "Open Command Palette → type 'incidents'"},
        ],
        "relatedScreens": ["dashboard", "service-manager"],
        "firstVisitTooltip": (
            "The Incident Log shows everything that's happened to your "
            "services. Look here when something goes wrong."
        ),
    },
}


@help_bp.route("/api/help/<screen_id>", methods=["GET"])
def get_help(screen_id):
    """Return context-aware help data for a screen."""
    data = HELP_DATA.get(screen_id)
    if data is None:
        return jsonify({"error": f"No help available for screen: {screen_id}"}), 404
    return jsonify(data)
