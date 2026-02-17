"""Incident Log API routes.

Endpoints:
    GET  /api/incidents            → list incidents (query: limit, app)
    POST /api/incidents/{id}/annotate → add a note to an incident
"""

from flask import Blueprint, jsonify, request

from app.services import incident_logger

incidents_bp = Blueprint("incidents", __name__)


@incidents_bp.route("/api/incidents", methods=["GET"])
def list_incidents():
    """Return recent incidents, optionally filtered by app."""
    limit = request.args.get("limit", 50, type=int)
    app_id = request.args.get("app")
    incidents = incident_logger.get_incidents(limit=limit, app_id=app_id)
    return jsonify(incidents)


@incidents_bp.route("/api/incidents/<incident_id>/annotate", methods=["POST"])
def annotate_incident(incident_id):
    """Add or update an annotation on an incident."""
    body = request.get_json(silent=True) or {}
    note = body.get("note", "").strip()
    if not note:
        return jsonify({"error": "No note provided."}), 400

    success = incident_logger.annotate(incident_id, note)
    if not success:
        return jsonify({"error": f"Incident {incident_id} not found."}), 404

    return jsonify({"status": "annotated", "incident_id": incident_id, "note": note})
