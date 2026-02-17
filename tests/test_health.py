"""Smoke + Beast tests for the Workshop health endpoint."""

from app import create_app


def test_health_returns_200():
    """Smoke: /api/health returns HTTP 200."""
    application = create_app()
    client = application.test_client()
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_health_contains_required_fields():
    """Beast: response includes all required fields."""
    application = create_app()
    client = application.test_client()
    data = client.get("/api/health").get_json()
    for field in ("status", "uptime_seconds", "version",
                  "services_running", "services_total"):
        assert field in data, f"Missing field: {field}"


def test_health_status_is_operational():
    """Beast: status field is 'operational'."""
    application = create_app()
    client = application.test_client()
    data = client.get("/api/health").get_json()
    assert data["status"] == "operational"


def test_health_version():
    """Beast: version matches config."""
    application = create_app()
    client = application.test_client()
    data = client.get("/api/health").get_json()
    assert data["version"] == "1.0.0"


def test_health_refresh():
    """Smoke: POST /api/health/refresh returns 200."""
    application = create_app()
    client = application.test_client()
    resp = client.post("/api/health/refresh")
    assert resp.status_code == 200
