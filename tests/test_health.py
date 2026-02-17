"""Smoke + Beast tests for the Workshop health endpoint.

Phase 0 regression tests plus new Phase 1 tests.
"""

import pytest

from app import create_app


@pytest.fixture
def client():
    application = create_app(start_health_loop=False)
    application.config["TESTING"] = True
    return application.test_client()


# ── Smoke ──────────────────────────────────────────────────────────────────

def test_health_returns_200(client):
    """Smoke: /api/health returns HTTP 200."""
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_health_refresh_returns_200(client):
    """Smoke: POST /api/health/refresh returns 200."""
    resp = client.post("/api/health/refresh")
    assert resp.status_code == 200


# ── Beast ──────────────────────────────────────────────────────────────────

def test_health_contains_required_fields(client):
    """Beast: response includes all required fields."""
    data = client.get("/api/health").get_json()
    for field in ("status", "uptime_seconds", "version",
                  "services_running", "services_total"):
        assert field in data, f"Missing field: {field}"


def test_health_status_is_operational(client):
    """Beast: status field is 'operational'."""
    data = client.get("/api/health").get_json()
    assert data["status"] == "operational"


def test_health_version(client):
    """Beast: version is 1.0.0."""
    data = client.get("/api/health").get_json()
    assert data["version"] == "1.0.0"


def test_health_services_total_is_24(client):
    """Beast: total services matches registry (24)."""
    data = client.get("/api/health").get_json()
    assert data["services_total"] == 24


def test_health_uptime_is_numeric(client):
    """Beast: uptime_seconds is a positive number."""
    data = client.get("/api/health").get_json()
    assert isinstance(data["uptime_seconds"], (int, float))
    assert data["uptime_seconds"] >= 0
