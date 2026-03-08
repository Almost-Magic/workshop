"""Tests for the Context-Aware Help API (Phase 7).

Covers:
  - All 4 screen IDs return 200
  - Unknown screen returns 404
  - Response includes required fields
  - firstVisitTooltip present on all screens
  - Keyboard shortcuts present
  - Related screens cross-reference correctly
"""

import pytest

from app import create_app


@pytest.fixture()
def client():
    application = create_app(start_health_loop=False)
    application.config["TESTING"] = True
    with application.test_client() as c:
        yield c


SCREENS = ["dashboard", "service-manager", "constellation", "incidents"]


class TestHelpEndpoint:
    """GET /api/help/<screen_id>."""

    @pytest.mark.parametrize("screen_id", SCREENS)
    def test_returns_200(self, client, screen_id):
        resp = client.get(f"/api/help/{screen_id}")
        assert resp.status_code == 200

    def test_unknown_screen_404(self, client):
        resp = client.get("/api/help/nonexistent")
        assert resp.status_code == 404
        assert "error" in resp.get_json()

    @pytest.mark.parametrize("screen_id", SCREENS)
    def test_has_how_it_works(self, client, screen_id):
        data = client.get(f"/api/help/{screen_id}").get_json()
        assert "howItWorks" in data
        assert len(data["howItWorks"]) > 0

    @pytest.mark.parametrize("screen_id", SCREENS)
    def test_has_quick_actions(self, client, screen_id):
        data = client.get(f"/api/help/{screen_id}").get_json()
        assert "quickActions" in data
        assert isinstance(data["quickActions"], list)
        assert len(data["quickActions"]) >= 1

    @pytest.mark.parametrize("screen_id", SCREENS)
    def test_has_first_visit_tooltip(self, client, screen_id):
        data = client.get(f"/api/help/{screen_id}").get_json()
        assert "firstVisitTooltip" in data
        assert len(data["firstVisitTooltip"]) > 0

    @pytest.mark.parametrize("screen_id", SCREENS)
    def test_has_shortcuts(self, client, screen_id):
        data = client.get(f"/api/help/{screen_id}").get_json()
        assert "shortcuts" in data
        assert isinstance(data["shortcuts"], list)

    @pytest.mark.parametrize("screen_id", SCREENS)
    def test_has_related_screens(self, client, screen_id):
        data = client.get(f"/api/help/{screen_id}").get_json()
        assert "relatedScreens" in data
        assert isinstance(data["relatedScreens"], list)

    def test_dashboard_shortcuts_include_space(self, client):
        data = client.get("/api/help/dashboard").get_json()
        keys = [s["key"] for s in data["shortcuts"]]
        assert "Space" in keys

    def test_dashboard_related_screens(self, client):
        data = client.get("/api/help/dashboard").get_json()
        assert "constellation" in data["relatedScreens"]

    @pytest.mark.parametrize("screen_id", SCREENS)
    def test_has_tips(self, client, screen_id):
        data = client.get(f"/api/help/{screen_id}").get_json()
        assert "tips" in data
        assert isinstance(data["tips"], list)
