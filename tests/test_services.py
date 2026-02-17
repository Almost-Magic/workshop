"""Beast + Edge-case tests for service API endpoints.

Tests cover:
  - GET /api/services (full list)
  - GET /api/services/<id> (single)
  - POST /api/services/<id>/start
  - POST /api/services/<id>/stop
  - POST /api/services/<id>/restart
  - POST /api/groups/<group>/start
  - POST /api/groups/<group>/stop
  - POST /api/command
  - Edge cases: 404s, 409s, ghost operations
"""

import json

import pytest

from app import create_app


@pytest.fixture
def client():
    application = create_app(start_health_loop=False)
    application.config["TESTING"] = True
    return application.test_client()


# ── GET /api/services ──────────────────────────────────────────────────────

def test_services_returns_list(client):
    """Beast: /api/services returns a JSON array."""
    resp = client.get("/api/services")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_services_count_is_24(client):
    """Beast: exactly 24 services in registry."""
    data = client.get("/api/services").get_json()
    assert len(data) == 24


def test_services_contains_elaine(client):
    """Beast: ELAINE is in the service list."""
    data = client.get("/api/services").get_json()
    ids = [s["id"] for s in data]
    assert "elaine" in ids


def test_services_contains_ghost_apps(client):
    """Beast: ghost apps are present in the list."""
    data = client.get("/api/services").get_json()
    ghosts = [s for s in data if s.get("ghost")]
    assert len(ghosts) == 4


def test_services_have_required_fields(client):
    """Beast: every service has the required API fields."""
    data = client.get("/api/services").get_json()
    required = {"id", "name", "group", "port", "status", "health", "ghost"}
    for svc in data:
        for field in required:
            assert field in svc, f"{svc['id']} missing field: {field}"


def test_services_port_5002_is_learning_assistant(client):
    """Beast: port 5002 belongs to Learning Assistant (DEC-006)."""
    data = client.get("/api/services").get_json()
    svc_5002 = [s for s in data if s["port"] == 5002]
    assert len(svc_5002) == 1
    assert svc_5002[0]["id"] == "learning-assistant"


def test_services_port_5009_is_identity_atlas(client):
    """Beast: port 5009 belongs to Identity Atlas (DEC-006)."""
    data = client.get("/api/services").get_json()
    svc_5009 = [s for s in data if s["port"] == 5009]
    assert len(svc_5009) == 1
    assert svc_5009[0]["id"] == "identity-atlas"


def test_services_no_duplicate_ports(client):
    """Beast: no two services share the same primary port."""
    data = client.get("/api/services").get_json()
    ports = [s["port"] for s in data]
    assert len(ports) == len(set(ports))


# ── GET /api/services/<id> ─────────────────────────────────────────────────

def test_get_single_service(client):
    """Beast: fetch a single service by ID."""
    resp = client.get("/api/services/workshop")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["id"] == "workshop"
    assert data["port"] == 5003


def test_get_unknown_service_404(client):
    """4% edge: unknown service returns 404."""
    resp = client.get("/api/services/nonexistent")
    assert resp.status_code == 404


# ── POST /api/services/<id>/start ──────────────────────────────────────────

def test_start_unknown_service_404(client):
    """4% edge: starting a non-existent service returns 404."""
    resp = client.post("/api/services/nonexistent/start")
    assert resp.status_code == 404


def test_start_ghost_service_400(client):
    """4% edge: starting a ghost app returns 400."""
    resp = client.post("/api/services/sophia/start")
    assert resp.status_code == 400


def test_start_service_returns_starting(client):
    """Beast: starting a stopped service returns 'starting'."""
    resp = client.post("/api/services/elaine/start")
    data = resp.get_json()
    assert data["status"] == "starting"


def test_start_already_running_409(client):
    """4% edge: starting an already-running service returns 409."""
    # Start it first
    client.post("/api/services/elaine/start")
    # Simulate "running" state
    with client.application.app_context():
        mgr = client.application.config["SERVICE_MANAGER"]
        mgr._services["elaine"]["status"] = "running"
    resp = client.post("/api/services/elaine/start")
    assert resp.status_code == 409


# ── POST /api/services/<id>/stop ───────────────────────────────────────────

def test_stop_unknown_service_404(client):
    """4% edge: stopping a non-existent service returns 404."""
    resp = client.post("/api/services/nonexistent/stop")
    assert resp.status_code == 404


def test_stop_ghost_service_400(client):
    """4% edge: stopping a ghost app returns 400."""
    resp = client.post("/api/services/sophia/stop")
    assert resp.status_code == 400


def test_stop_already_stopped_409(client):
    """4% edge: stopping an already-stopped service returns 409."""
    resp = client.post("/api/services/elaine/stop")
    assert resp.status_code == 409


# ── POST /api/services/<id>/restart ────────────────────────────────────────

def test_restart_unknown_404(client):
    """4% edge: restarting a non-existent service returns 404."""
    resp = client.post("/api/services/nonexistent/restart")
    assert resp.status_code == 404


def test_restart_ghost_400(client):
    """4% edge: restarting a ghost app returns 400."""
    resp = client.post("/api/services/sophia/restart")
    assert resp.status_code == 400


def test_restart_returns_restarting(client):
    """Beast: restarting returns 'restarting' status."""
    resp = client.post("/api/services/elaine/restart")
    data = resp.get_json()
    assert data["status"] == "restarting"


# ── POST /api/groups/<group>/start ─────────────────────────────────────────

def test_start_core_group(client):
    """Beast: starting 'core' group returns results for core services."""
    resp = client.post("/api/groups/core/start")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "elaine" in data or "workshop" in data


def test_start_nonexistent_group_404(client):
    """4% edge: starting a non-existent group returns 404."""
    resp = client.post("/api/groups/nonexistent/start")
    assert resp.status_code == 404


# ── POST /api/groups/<group>/stop ──────────────────────────────────────────

def test_stop_nonexistent_group_404(client):
    """4% edge: stopping a non-existent group returns 404."""
    resp = client.post("/api/groups/nonexistent/stop")
    assert resp.status_code == 404


# ── POST /api/command ──────────────────────────────────────────────────────

def test_command_fuzzy_match_writer(client):
    """Beast: 'writer' fuzzy-matches CK Writer."""
    resp = client.post(
        "/api/command",
        data=json.dumps({"query": "writer"}),
        content_type="application/json",
    )
    data = resp.get_json()
    assert data["action"] == "open"
    assert data["target"] == "ck-writer"


def test_command_match_by_port(client):
    """Beast: '5004' matches CK Writer."""
    resp = client.post(
        "/api/command",
        data=json.dumps({"query": "5004"}),
        content_type="application/json",
    )
    data = resp.get_json()
    assert data["target"] == "ck-writer"


def test_command_start_all(client):
    """Beast: 'start all' returns the start_all action."""
    resp = client.post(
        "/api/command",
        data=json.dumps({"query": "start all"}),
        content_type="application/json",
    )
    data = resp.get_json()
    assert data["action"] == "start_all"


def test_command_empty_query_400(client):
    """4% edge: empty query returns 400."""
    resp = client.post(
        "/api/command",
        data=json.dumps({"query": ""}),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_command_no_match(client):
    """4% edge: nonsense query returns no matches."""
    resp = client.post(
        "/api/command",
        data=json.dumps({"query": "zzzzzzzzzzz"}),
        content_type="application/json",
    )
    data = resp.get_json()
    assert data["action"] == "none"


def test_command_ambiguous_match(client):
    """Beast: ambiguous query returns disambiguate with multiple matches."""
    resp = client.post(
        "/api/command",
        data=json.dumps({"query": "ck"}),
        content_type="application/json",
    )
    data = resp.get_json()
    # "ck" matches ck-writer and costanza (CK Swiss Army Knife) at minimum
    assert data["action"] == "disambiguate"
    assert len(data["matches"]) >= 2


# ── GET / (browser fallback) ──────────────────────────────────────────────

def test_dashboard_returns_html(client):
    """Smoke: browser fallback returns HTML."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"The Workshop" in resp.data


def test_dashboard_shows_all_groups(client):
    """Beast: dashboard HTML contains all service groups."""
    resp = client.get("/")
    html = resp.data.decode()
    assert "Core" in html
    assert "Intelligence" in html
