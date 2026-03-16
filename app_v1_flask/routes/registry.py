# Author: Mani Padisetti
"""Registry API routes for V2 Workshop.

Endpoints:
    GET  /api/registry         -> all 55 ecosystem items (filterable)
    GET  /api/health/all       -> aggregate health check across live services
    POST /api/apps/register    -> register a new app dynamically
"""

import json
import os

import requests as http_requests

from flask import Blueprint, jsonify, request

registry_bp = Blueprint("registry", __name__)

_REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "registry.json",
)


def load_registry():
    """Load the registry data from JSON file."""
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@registry_bp.route("/api/registry", methods=["GET"])
def api_registry():
    """Return registry items, optionally filtered by status and/or category."""
    items = load_registry()

    status_filter = request.args.get("status")
    cat_filter = request.args.get("cat")

    if status_filter:
        items = [i for i in items if i["status"] == status_filter]
    if cat_filter:
        items = [i for i in items if i["category"] == cat_filter]

    return jsonify(items)


@registry_bp.route("/api/health/all", methods=["GET"])
def api_health_all():
    """Aggregate health check across all live services with ports."""
    registry = load_registry()
    live_with_ports = [
        item
        for item in registry
        if item["status"] == "live"
        and item.get("port")
        and item["port"] not in ("TBD", None)
    ]

    results = {}
    for item in live_with_ports:
        try:
            port = item["port"]
            url = f"http://localhost:{port}/"
            resp = http_requests.get(url, timeout=2)
            results[item["id"]] = {
                "name": item["name"],
                "port": port,
                "healthy": resp.status_code == 200,
                "status_code": resp.status_code,
            }
        except Exception:
            results[item["id"]] = {
                "name": item["name"],
                "port": item.get("port"),
                "healthy": False,
                "status_code": None,
            }

    return jsonify(results)


@registry_bp.route("/api/apps/register", methods=["POST"])
def api_register_app():
    """Allow an app to register itself. Adds to registry if not present."""
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "name is required"}), 400

    registry = load_registry()

    # Check if already exists by name (case-insensitive)
    existing = [i for i in registry if i["name"].lower() == data["name"].lower()]
    if existing:
        return jsonify({"message": "already registered", "item": existing[0]}), 200

    new_item = {
        "id": data.get("id", data["name"].lower().replace(" ", "-")),
        "name": data["name"],
        "emoji": data.get("emoji", "\U0001f4e6"),
        "port": data.get("port"),
        "description": data.get("description", ""),
        "category": data.get("category", "internal"),
        "status": data.get("status", "live"),
        "tests": data.get("tests"),
        "tests_verified": data.get("tests_verified", False),
        "has_spec": data.get("has_spec", False),
        "github_repo": data.get("github_repo"),
    }

    registry.append(new_item)

    with open(_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    return jsonify({"message": "registered", "item": new_item}), 201
