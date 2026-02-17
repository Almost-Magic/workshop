"""Integration tests — Workshop talks to Supervisor, ELAINE, Foreperson.

These tests run with mocked external services.  Full live integration
is verified manually during deployment.
"""

import pytest

from app import create_app
from app.services import heartbeat as heartbeat_engine
from app.services import resource_monitor


@pytest.fixture
def client():
    application = create_app(start_health_loop=False)
    application.config["TESTING"] = True
    return application.test_client()


def test_services_response_includes_heartbeat(client):
    """Integration: /api/services response includes heartbeat array."""
    resp = client.get("/api/services")
    data = resp.get_json()
    for svc in data:
        assert "heartbeat" in svc
        assert isinstance(svc["heartbeat"], list)
        assert len(svc["heartbeat"]) == 24


def test_services_response_includes_resources(client):
    """Integration: /api/services response includes resources dict."""
    resp = client.get("/api/services")
    data = resp.get_json()
    for svc in data:
        assert "resources" in svc
        assert isinstance(svc["resources"], dict)


def test_resource_monitor_graceful_degradation():
    """Integration: resource monitor returns {} when Supervisor is down."""
    resources = resource_monitor.get_resources("elaine")
    assert resources == {}


def test_heartbeat_recorded_and_retrieved():
    """Integration: heartbeat record + get cycle works end-to-end."""
    heartbeat_engine.clear_all()
    heartbeat_engine.record("test-app", True)
    hb = heartbeat_engine.get_heartbeat("test-app")
    assert len(hb) == 24
    # The most recent hour should be 1
    assert hb[-1] == 1
    heartbeat_engine.clear_all()


def test_heartbeat_all_down():
    """Integration: no records means all zeros."""
    heartbeat_engine.clear_all()
    hb = heartbeat_engine.get_heartbeat("unknown-app")
    assert all(v == 0 for v in hb)
    assert len(hb) == 24
