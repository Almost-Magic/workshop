"""Service registry API routes.

Endpoints:
    GET  /api/services                  → all services
    POST /api/services/{id}/start       → start a service
    POST /api/services/{id}/stop        → stop a service
    GET  /api/services/{id}/health      → health check one service
    POST /api/services/{id}/restart     → restart a service
    POST /api/groups/{group}/start      → start all in group
    POST /api/groups/{group}/stop       → stop all in group
    POST /api/command                   → command palette action
"""

from flask import Blueprint, current_app, jsonify, request

services_bp = Blueprint("services", __name__)


def _mgr():
    """Retrieve the ServiceManager from the app context."""
    return current_app.config["SERVICE_MANAGER"]


# ── Service List ───────────────────────────────────────────────────────────

@services_bp.route("/api/services", methods=["GET"])
def list_services():
    """Return all registered services."""
    return jsonify(_mgr().get_all())


# ── Single Service ─────────────────────────────────────────────────────────

@services_bp.route("/api/services/<service_id>", methods=["GET"])
def get_service(service_id):
    """Return details for a single service."""
    svc = _mgr().get(service_id)
    if svc is None:
        return jsonify({"error": f"Unknown service: {service_id}"}), 404
    return jsonify(svc)


# ── Start / Stop / Restart ─────────────────────────────────────────────────

@services_bp.route("/api/services/<service_id>/start", methods=["POST"])
def start_service(service_id):
    """Start a service (and its dependencies)."""
    result = _mgr().start_service(service_id)
    if result is None:
        return jsonify({"error": f"Unknown service: {service_id}"}), 404
    if result.get("status") == "conflict":
        return jsonify(result), 409
    if result.get("status") == "ghost":
        return jsonify(result), 400
    return jsonify(result)


@services_bp.route("/api/services/<service_id>/stop", methods=["POST"])
def stop_service(service_id):
    """Stop a running service."""
    result = _mgr().stop_service(service_id)
    if result is None:
        return jsonify({"error": f"Unknown service: {service_id}"}), 404
    if result.get("status") == "conflict":
        return jsonify(result), 409
    if result.get("status") == "ghost":
        return jsonify(result), 400
    return jsonify(result)


@services_bp.route("/api/services/<service_id>/restart", methods=["POST"])
def restart_service(service_id):
    """Restart a service."""
    result = _mgr().restart_service(service_id)
    if result is None:
        return jsonify({"error": f"Unknown service: {service_id}"}), 404
    if result.get("status") == "ghost":
        return jsonify(result), 400
    return jsonify(result)


# ── Health ─────────────────────────────────────────────────────────────────

@services_bp.route("/api/services/<service_id>/health", methods=["GET"])
def service_health(service_id):
    """Run an immediate health check on a single service."""
    result = _mgr().check_health(service_id)
    if result is None:
        return jsonify({"error": f"Unknown service: {service_id}"}), 404
    return jsonify(result)


# ── Group Operations ───────────────────────────────────────────────────────

@services_bp.route("/api/groups/<group>/start", methods=["POST"])
def start_group(group):
    """Start all non-ghost services in the given group."""
    results = _mgr().start_group(group)
    if not results:
        return jsonify({"error": f"No services found in group: {group}"}), 404
    return jsonify(results)


@services_bp.route("/api/groups/<group>/stop", methods=["POST"])
def stop_group(group):
    """Stop all services in the given group."""
    results = _mgr().stop_group(group)
    if not results:
        return jsonify({"error": f"No services found in group: {group}"}), 404
    return jsonify(results)


# ── Command Palette ────────────────────────────────────────────────────────

@services_bp.route("/api/command", methods=["POST"])
def command():
    """Execute a command palette action.

    Accepts JSON: {"query": "..."}
    Fuzzy-matches against app names, ports, and built-in commands.
    """
    body = request.get_json(silent=True) or {}
    query = body.get("query", "").strip().lower()
    if not query:
        return jsonify({"error": "No query provided."}), 400

    mgr = _mgr()

    # Built-in commands
    builtins = {
        "start all": {"action": "start_all", "display": "Start all services"},
        "stop all": {"action": "stop_all", "display": "Stop all services"},
        "health": {"action": "health", "display": "Run full health check"},
        "incidents": {"action": "navigate", "target": "incidents",
                      "display": "Open incident log"},
        "foreperson": {"action": "navigate", "target": "foreperson",
                       "display": "Open Foreperson"},
    }

    # Check built-in commands first
    for key, cmd in builtins.items():
        if query in key:
            return jsonify({"executing": True, **cmd})

    # Fuzzy match against services (name or port)
    matches = []
    for svc in mgr.get_all():
        name_lower = svc["name"].lower()
        port_str = str(svc.get("port", ""))
        if query in name_lower or query in port_str or query in svc["id"]:
            matches.append(svc)

    if len(matches) == 1:
        target = matches[0]
        return jsonify({
            "action": "open",
            "target": target["id"],
            "display": f"Open {target['name']} (:{target['port']})",
            "executing": True,
        })

    if matches:
        return jsonify({
            "action": "disambiguate",
            "matches": [
                {"id": m["id"], "name": m["name"], "port": m["port"]}
                for m in matches
            ],
            "executing": False,
        })

    return jsonify({"action": "none", "display": "No matches found.", "executing": False})
