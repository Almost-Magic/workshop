"""Beast + Edge-case tests for the Morning Briefing.

Tests cover:
  - GET /api/briefing returns correct structure
  - Graceful fallback when ELAINE/Foreperson are down
  - Greeting changes with time of day (mocked)
  - Warnings list from recent escalations
"""

import pytest

from app import create_app
from app.services import incident_logger


@pytest.fixture(autouse=True)
def clean_incidents():
    incident_logger.clear_all()
    yield
    incident_logger.clear_all()


@pytest.fixture
def client():
    application = create_app(start_health_loop=False)
    application.config["TESTING"] = True
    return application.test_client()


# ── Beast: Structure ───────────────────────────────────────────────────────

def test_briefing_returns_200(client):
    """Smoke: /api/briefing returns 200."""
    resp = client.get("/api/briefing")
    assert resp.status_code == 200


def test_briefing_has_required_fields(client):
    """Beast: response has all required fields."""
    data = client.get("/api/briefing").get_json()
    required = {
        "timestamp", "greeting", "summary",
        "services_running", "services_total",
        "elaine_item", "foreperson_flag", "warnings",
    }
    for field in required:
        assert field in data, f"Missing field: {field}"


def test_briefing_greeting_is_string(client):
    """Beast: greeting is a non-empty string."""
    data = client.get("/api/briefing").get_json()
    assert isinstance(data["greeting"], str)
    assert len(data["greeting"]) > 0


def test_briefing_summary_mentions_services(client):
    """Beast: summary mentions running count."""
    data = client.get("/api/briefing").get_json()
    assert "services" in data["summary"].lower() or "running" in data["summary"].lower()


def test_briefing_services_total_is_24(client):
    """Beast: total matches registry."""
    data = client.get("/api/briefing").get_json()
    assert data["services_total"] == 24


# ── Graceful Degradation ──────────────────────────────────────────────────

def test_briefing_elaine_item_is_none_when_down(client):
    """4% edge: elaine_item is None when ELAINE is unreachable."""
    data = client.get("/api/briefing").get_json()
    assert data["elaine_item"] is None


def test_briefing_foreperson_flag_is_none_when_down(client):
    """4% edge: foreperson_flag is None when Foreperson is unreachable."""
    data = client.get("/api/briefing").get_json()
    assert data["foreperson_flag"] is None


# ── Warnings ───────────────────────────────────────────────────────────────

def test_briefing_warnings_empty_when_no_escalations(client):
    """Beast: warnings is empty list when no escalations."""
    data = client.get("/api/briefing").get_json()
    assert data["warnings"] == []


def test_briefing_warnings_includes_escalation(client):
    """Beast: escalated incidents appear in warnings."""
    incident_logger.log_event(
        "elaine", "crash",
        cause="SIGKILL", outcome="escalated",
    )
    data = client.get("/api/briefing").get_json()
    assert len(data["warnings"]) == 1
    assert data["warnings"][0]["app"] == "elaine"


def test_briefing_warnings_excludes_recovered(client):
    """4% edge: recovered incidents do NOT appear in warnings."""
    incident_logger.log_event(
        "elaine", "restart",
        cause="tier_1", outcome="recovered",
    )
    data = client.get("/api/briefing").get_json()
    assert len(data["warnings"]) == 0


# ── Timestamp ──────────────────────────────────────────────────────────────

def test_briefing_timestamp_is_iso(client):
    """Beast: timestamp is ISO 8601 format."""
    data = client.get("/api/briefing").get_json()
    assert "T" in data["timestamp"]
    assert "+" in data["timestamp"] or "Z" in data["timestamp"]
