"""Health check endpoint for The Workshop API."""

import time

from flask import Blueprint, jsonify

import config

health_bp = Blueprint("health", __name__)

# Recorded at module load — used for uptime calculation.
_start_time = time.time()


@health_bp.route("/api/health", methods=["GET"])
def health():
    """Return Workshop health status."""
    return jsonify(
        {
            "status": "operational",
            "uptime_seconds": round(time.time() - _start_time, 1),
            "version": config.VERSION,
            "services_running": 0,  # Populated once ServiceManager exists
            "services_total": 0,
        }
    )


@health_bp.route("/api/health/refresh", methods=["POST"])
def health_refresh():
    """Force an immediate health-check cycle."""
    # Placeholder — wired up in Phase 1 when ServiceManager exists.
    return jsonify({"status": "refresh_queued"})
