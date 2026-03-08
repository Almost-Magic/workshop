"""Constellation View API — AMTL-WKS-TDD-1.0 §6.

Endpoint:
    GET /api/constellation → node-graph data for D3.js v7 force layout.

Returns ``nodes`` (one per service) and ``edges`` (dependency links).
"""

from flask import Blueprint, current_app, jsonify

constellation_bp = Blueprint("constellation", __name__)


@constellation_bp.route("/api/constellation", methods=["GET"])
def constellation_data():
    """Return the full constellation graph payload."""
    mgr = current_app.config["SERVICE_MANAGER"]
    services = mgr.get_all()

    nodes = []
    edges = []

    for svc in services:
        node = {
            "id": svc["id"],
            "name": svc["name"],
            "group": svc["group"],
            "port": svc["port"],
            "status": svc["status"],
            "ghost": svc.get("ghost", False),
            "ghost_eta": svc.get("ghost_eta"),
            "description": svc.get("description", ""),
            "favicon": svc.get("favicon", ""),
            "dependents": 0,
        }
        nodes.append(node)

        # Build edges from dependencies
        for dep_id in svc.get("dependencies", []):
            edges.append({
                "source": dep_id,
                "target": svc["id"],
                "type": "hard",
            })

    # Calculate dependents count (how many services depend on each node)
    dependent_count = {}
    for edge in edges:
        src = edge["source"]
        dependent_count[src] = dependent_count.get(src, 0) + 1

    for node in nodes:
        node["dependents"] = dependent_count.get(node["id"], 0)

    return jsonify({"nodes": nodes, "edges": edges})
