"""Briefing Service — aggregates system state into a Morning Briefing.

The briefing pulls:
  - Running / total service counts from the ServiceManager
  - Today's ELAINE item (if ELAINE is running)
  - Foreperson quality flag (if Foreperson is running)
  - Recent warnings from the Incident Logger

All external calls degrade gracefully — if ELAINE or Foreperson are
down, the briefing still returns with those fields set to None.
"""

import logging
from datetime import datetime, timezone, timedelta

import requests

import config
from app.services import incident_logger

log = logging.getLogger(__name__)

AEST = timezone(timedelta(hours=10))


def generate(service_manager):
    """Build the morning briefing payload.

    Args:
        service_manager: The active ServiceManager instance.

    Returns:
        Dict matching the GET /api/briefing response schema.
    """
    now = datetime.now(AEST)
    hour = now.hour

    # Greeting based on time of day
    if hour < 12:
        greeting = "Good morning, Mani."
    elif hour < 17:
        greeting = "Good afternoon, Mani."
    else:
        greeting = "Good evening, Mani."

    running = service_manager.services_running
    total = service_manager.services_total

    # Summary line
    if running == 0:
        summary = "No services are running yet. Let's get started."
    elif running == total:
        summary = f"All {total} services are running. Everything looks good."
    else:
        summary = f"{running} of {total} services are running."

    # ELAINE item — graceful fallback
    elaine_item = _fetch_elaine_item()

    # Foreperson flag — graceful fallback
    foreperson_flag = _fetch_foreperson_flag()

    # Recent warnings (last 5 escalated incidents)
    warnings = _recent_warnings()

    return {
        "timestamp": now.isoformat(),
        "greeting": greeting,
        "summary": summary,
        "services_running": running,
        "services_total": total,
        "elaine_item": elaine_item,
        "foreperson_flag": foreperson_flag,
        "warnings": warnings,
    }


def _fetch_elaine_item():
    """Try to get today's briefing item from ELAINE."""
    try:
        resp = requests.get(
            f"{config.ELAINE_URL}/api/briefing-item",
            timeout=3,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("item") or data.get("message")
    except Exception:
        pass
    return None


def _fetch_foreperson_flag():
    """Try to get the quality flag from Foreperson."""
    try:
        resp = requests.get(
            f"{config.FOREPERSON_URL}/api/quality-flag",
            timeout=3,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("flag") or data.get("status")
    except Exception:
        pass
    return None


def _recent_warnings(limit=5):
    """Return the most recent escalated incidents as warnings."""
    incidents = incident_logger.get_incidents(limit=limit)
    warnings = []
    for inc in incidents:
        if inc.get("outcome") == "escalated":
            warnings.append({
                "id": inc["id"],
                "app": inc["app_id"],
                "event": inc["event"],
                "timestamp": inc["timestamp"],
            })
    return warnings
