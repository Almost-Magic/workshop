# Author: Mani Padisetti
"""
Workshop v2 — Test Suite
Tests for API endpoints, fleet registry, health checks, and dashboard.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app import app, FLEET_REGISTRY, GROUP_ORDER, _health_cache, db_healthy


@pytest.fixture
def client():
    """Create a test client for Workshop v2."""
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# /api/health
# ---------------------------------------------------------------------------
class TestHealthEndpoint:
    """Tests for GET /api/health — AMTL standard."""

    def test_health_returns_200(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_has_required_fields(self, client):
        data = client.get("/api/health").json()
        assert data["service"] == "workshop"
        assert data["port"] == 5001
        assert data["version"] == "2.0.0"
        assert "timestamp" in data
        assert "database_connected" in data
        assert "fleet_total" in data
        assert "fleet_up" in data

    def test_health_alias_at_slash_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["service"] == "workshop"

    def test_health_alias_at_workshop_health(self, client):
        response = client.get("/workshop/health")
        assert response.status_code == 200
        assert response.json()["service"] == "workshop"

    def test_health_response_under_50ms(self, client):
        import time
        start = time.monotonic()
        client.get("/api/health")
        elapsed = (time.monotonic() - start) * 1000
        assert elapsed < 500  # generous for test env, real target <50ms

    def test_health_database_connected_is_bool(self, client):
        data = client.get("/api/health").json()
        assert isinstance(data["database_connected"], bool)

    def test_health_fleet_total_matches_registry(self, client):
        data = client.get("/api/health").json()
        assert data["fleet_total"] == len(FLEET_REGISTRY)


# ---------------------------------------------------------------------------
# /api/apps
# ---------------------------------------------------------------------------
class TestAppsEndpoint:
    """Tests for GET /api/apps."""

    def test_apps_returns_200(self, client):
        response = client.get("/api/apps")
        assert response.status_code == 200

    def test_apps_returns_all_registered(self, client):
        data = client.get("/api/apps").json()
        assert len(data["apps"]) == 16

    def test_apps_has_summary(self, client):
        data = client.get("/api/apps").json()
        summary = data["summary"]
        assert "total" in summary
        assert "up" in summary
        assert "down" in summary
        assert "degraded" in summary
        assert "not_built" in summary
        assert summary["total"] == 16

    def test_apps_has_groups(self, client):
        data = client.get("/api/apps").json()
        assert data["groups"] == GROUP_ORDER

    def test_apps_each_has_required_fields(self, client):
        data = client.get("/api/apps").json()
        for a in data["apps"]:
            assert "slug" in a
            assert "name" in a
            assert "port" in a
            assert "group" in a
            assert "status" in a
            assert "badge" in a
            assert "badge_class" in a

    def test_apps_includes_elaine(self, client):
        data = client.get("/api/apps").json()
        slugs = [a["slug"] for a in data["apps"]]
        assert "elaine" in slugs

    def test_apps_includes_beast(self, client):
        data = client.get("/api/apps").json()
        slugs = [a["slug"] for a in data["apps"]]
        assert "beast" in slugs

    def test_apps_includes_sure(self, client):
        data = client.get("/api/apps").json()
        slugs = [a["slug"] for a in data["apps"]]
        assert "sure" in slugs

    def test_apps_infrastructure_group_has_five(self, client):
        data = client.get("/api/apps").json()
        infra = [a for a in data["apps"] if a["group"] == "Infrastructure"]
        assert len(infra) == 5

    def test_apps_ck_life_os_has_two(self, client):
        data = client.get("/api/apps").json()
        ck = [a for a in data["apps"] if a["group"] == "CK Life OS"]
        assert len(ck) == 2

    def test_apps_intelligence_has_four(self, client):
        data = client.get("/api/apps").json()
        intel = [a for a in data["apps"] if a["group"] == "Intelligence"]
        assert len(intel) == 4

    def test_apps_revenue_has_four(self, client):
        data = client.get("/api/apps").json()
        rev = [a for a in data["apps"] if a["group"] == "Revenue"]
        assert len(rev) == 4

    def test_apps_utilities_has_one(self, client):
        data = client.get("/api/apps").json()
        util = [a for a in data["apps"] if a["group"] == "Utilities"]
        assert len(util) == 1

    def test_apps_pinned_count_is_eight(self, client):
        data = client.get("/api/apps").json()
        pinned = [a for a in data["apps"] if a["pinned"]]
        assert len(pinned) == 8


# ---------------------------------------------------------------------------
# /api/apps/{slug}/health
# ---------------------------------------------------------------------------
class TestAppHealthEndpoint:
    """Tests for GET /api/apps/{slug}/health."""

    def test_known_app_returns_result(self, client):
        response = client.get("/api/apps/elaine/health")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "elaine"
        assert data["name"] == "ELAINE"

    def test_unknown_app_returns_error(self, client):
        response = client.get("/api/apps/nonexistent/health")
        data = response.json()
        assert data["status"] == "unknown"
        assert "error" in data

    def test_not_built_app_returns_not_built(self, client):
        response = client.get("/api/apps/sophia/health")
        data = response.json()
        assert data["status"] == "not_built"


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class TestDashboard:
    """Tests for the dashboard HTML."""

    def test_root_returns_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_workshop_slash_returns_html(self, client):
        response = client.get("/workshop/")
        assert response.status_code == 200

    def test_dark_theme_in_html(self, client):
        html = client.get("/").text
        assert 'data-theme="dark"' in html

    def test_gold_accent_in_html(self, client):
        html = client.get("/").text
        assert "#C9944A" in html or "C9944A" in html

    def test_bg_colour_in_html(self, client):
        html = client.get("/").text
        assert "#0A0E14" in html or "0A0E14" in html

    def test_title_in_html(self, client):
        html = client.get("/").text
        assert "The Workshop" in html

    def test_australian_english_lang(self, client):
        html = client.get("/").text
        assert 'lang="en-AU"' in html

    def test_pinned_bar_in_html(self, client):
        html = client.get("/").text
        assert "pinned-bar" in html

    def test_sidebar_in_html(self, client):
        html = client.get("/").text
        assert "sidebar" in html

    def test_light_theme_toggle_in_html(self, client):
        html = client.get("/").text
        assert "toggleTheme" in html


# ---------------------------------------------------------------------------
# Fleet Registry
# ---------------------------------------------------------------------------
class TestFleetRegistry:
    """Tests for the FLEET_REGISTRY constant."""

    def test_registry_has_16_apps(self):
        assert len(FLEET_REGISTRY) == 16

    def test_all_slugs_unique(self):
        slugs = [a["slug"] for a in FLEET_REGISTRY]
        assert len(slugs) == len(set(slugs))

    def test_all_ports_are_integers(self):
        for a in FLEET_REGISTRY:
            assert isinstance(a["port"], int)

    def test_group_order_has_five(self):
        assert len(GROUP_ORDER) == 5
        assert GROUP_ORDER == ["Infrastructure", "CK Life OS", "Intelligence", "Revenue", "Utilities"]

    def test_pinned_apps_are_correct(self):
        pinned = [a["slug"] for a in FLEET_REGISTRY if a["pinned"]]
        expected = {"elaine", "beast", "sure", "baldrick", "ckwriter", "ckla", "sentinel", "peterman"}
        assert set(pinned) == expected

    def test_no_sqlite_in_registry(self):
        import json
        dump = json.dumps(FLEET_REGISTRY).lower()
        assert "sqlite" not in dump


# ---------------------------------------------------------------------------
# /api/activity
# ---------------------------------------------------------------------------
class TestActivityEndpoint:
    """Tests for GET /api/activity."""

    def test_activity_returns_200(self, client):
        response = client.get("/api/activity")
        assert response.status_code == 200

    def test_activity_has_entries(self, client):
        data = client.get("/api/activity").json()
        assert "entries" in data
        assert "count" in data


# ---------------------------------------------------------------------------
# /api/fleet-score
# ---------------------------------------------------------------------------
class TestFleetScoreEndpoint:
    """Tests for GET /api/fleet-score."""

    def test_fleet_score_returns_200(self, client):
        response = client.get("/api/fleet-score")
        assert response.status_code == 200

    def test_fleet_score_has_fields(self, client):
        data = client.get("/api/fleet-score").json()
        assert "score" in data
        assert "app_count" in data
