"""Health check endpoints for The Workshop API."""

import time

from flask import Blueprint, current_app, jsonify

import config

health_bp = Blueprint("health", __name__)

# Recorded at module load — used for uptime calculation.
_start_time = time.time()


def _mgr():
    """Retrieve the ServiceManager from the app context (may be None early)."""
    return current_app.config.get("SERVICE_MANAGER")


@health_bp.route("/api/health", methods=["GET"])
def health():
    """Return Workshop health status."""
    mgr = _mgr()
    return jsonify(
        {
            "status": "operational",
            "uptime_seconds": round(time.time() - _start_time, 1),
            "version": config.VERSION,
            "services_running": mgr.services_running if mgr else 0,
            "services_total": mgr.services_total if mgr else 0,
        }
    )


@health_bp.route("/api/health/refresh", methods=["POST"])
def health_refresh():
    """Force an immediate health-check cycle on all services."""
    mgr = _mgr()
    if mgr:
        for svc in mgr.get_all():
            mgr.check_health(svc["id"])
    return jsonify({"status": "refresh_complete"})
