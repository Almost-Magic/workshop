"""Beast + Edge-case tests for the Incident Logger and API.

Covers:
  - IncidentLogger: log_event, get_incidents, annotate, clear_all
  - GET /api/incidents
  - POST /api/incidents/{id}/annotate
  - Edge cases: empty DB, non-existent ID, filter by app
"""

import json

import pytest

from app import create_app
from app.services import incident_logger


@pytest.fixture(autouse=True)
def clean_incidents():
    """Ensure a clean incident DB for every test."""
    incident_logger.clear_all()
    yield
    incident_logger.clear_all()


@pytest.fixture
def client():
    application = create_app(start_health_loop=False)
    application.config["TESTING"] = True
    return application.test_client()


# ── IncidentLogger Unit Tests ──────────────────────────────────────────────

def test_log_event_returns_incident():
    """Beast: log_event returns a dict with all fields."""
    inc = incident_logger.log_event("elaine", "start")
    assert inc["id"].startswith("INC-")
    assert inc["app_id"] == "elaine"
    assert inc["event"] == "start"


def test_log_event_increments_id():
    """Beast: IDs increment sequentially."""
    inc1 = incident_logger.log_event("elaine", "start")
    inc2 = incident_logger.log_event("elaine", "stop")
    num1 = int(inc1["id"].split("-")[1])
    num2 = int(inc2["id"].split("-")[1])
    assert num2 == num1 + 1


def test_get_incidents_returns_list():
    """Beast: get_incidents returns a list."""
    incident_logger.log_event("elaine", "start")
    incidents = incident_logger.get_incidents()
    assert isinstance(incidents, list)
    assert len(incidents) == 1


def test_get_incidents_newest_first():
    """Beast: incidents are returned newest-first."""
    incident_logger.log_event("elaine", "start")
    incident_logger.log_event("elaine", "stop")
    incidents = incident_logger.get_incidents()
    assert incidents[0]["event"] == "stop"


def test_get_incidents_filter_by_app():
    """Beast: filter by app_id works."""
    incident_logger.log_event("elaine", "start")
    incident_logger.log_event("supervisor", "start")
    incidents = incident_logger.get_incidents(app_id="elaine")
    assert len(incidents) == 1
    assert incidents[0]["app_id"] == "elaine"


def test_get_incidents_limit():
    """Beast: limit parameter caps results."""
    for i in range(10):
        incident_logger.log_event("elaine", "start")
    incidents = incident_logger.get_incidents(limit=3)
    assert len(incidents) == 3


def test_get_incidents_empty_db():
    """4% edge: empty database returns empty list."""
    incidents = incident_logger.get_incidents()
    assert incidents == []


def test_annotate_success():
    """Beast: annotating an incident updates the note."""
    inc = incident_logger.log_event("elaine", "crash")
    result = incident_logger.annotate(inc["id"], "Investigated: port conflict.")
    assert result is True
    incidents = incident_logger.get_incidents()
    assert incidents[0]["annotation"] == "Investigated: port conflict."


def test_annotate_nonexistent_id():
    """4% edge: annotating a non-existent ID returns False."""
    result = incident_logger.annotate("INC-9999", "note")
    assert result is False


def test_log_event_with_all_fields():
    """Beast: all optional fields are stored."""
    incident_logger.log_event(
        "elaine", "crash",
        cause="SIGKILL", details="OOM killer",
        outcome="escalated",
    )
    incidents = incident_logger.get_incidents()
    assert incidents[0]["cause"] == "SIGKILL"
    assert incidents[0]["details"] == "OOM killer"
    assert incidents[0]["outcome"] == "escalated"


# ── API Tests ──────────────────────────────────────────────────────────────

def test_api_incidents_empty(client):
    """4% edge: /api/incidents returns empty list when no incidents."""
    resp = client.get("/api/incidents")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_api_incidents_returns_data(client):
    """Beast: /api/incidents returns logged incidents."""
    incident_logger.log_event("elaine", "start")
    resp = client.get("/api/incidents")
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["app_id"] == "elaine"


def test_api_incidents_filter_by_app(client):
    """Beast: ?app=elaine filters correctly."""
    incident_logger.log_event("elaine", "start")
    incident_logger.log_event("supervisor", "start")
    resp = client.get("/api/incidents?app=elaine")
    data = resp.get_json()
    assert len(data) == 1


def test_api_incidents_limit(client):
    """Beast: ?limit=2 caps results."""
    for _ in range(5):
        incident_logger.log_event("elaine", "start")
    resp = client.get("/api/incidents?limit=2")
    data = resp.get_json()
    assert len(data) == 2


def test_api_annotate_success(client):
    """Beast: annotating via API works."""
    inc = incident_logger.log_event("elaine", "crash")
    resp = client.post(
        f"/api/incidents/{inc['id']}/annotate",
        data=json.dumps({"note": "Fixed port conflict."}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "annotated"


def test_api_annotate_empty_note_400(client):
    """4% edge: empty note returns 400."""
    inc = incident_logger.log_event("elaine", "crash")
    resp = client.post(
        f"/api/incidents/{inc['id']}/annotate",
        data=json.dumps({"note": ""}),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_api_annotate_nonexistent_404(client):
    """4% edge: annotating a non-existent incident returns 404."""
    resp = client.post(
        "/api/incidents/INC-9999/annotate",
        data=json.dumps({"note": "test"}),
        content_type="application/json",
    )
    assert resp.status_code == 404
