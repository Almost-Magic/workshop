# Author: Mani Padisetti
"""
Tests for Workshop — Central Service Registry & Launcher.
Uses httpx + pytest-asyncio. All external health pings are mocked.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from httpx import ASGITransport, AsyncClient

# Import app from parent
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, SERVICES, _ping_service  # noqa: E402


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------
class TestHealth:
    @pytest.mark.anyio
    async def test_health_returns_200(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "operational"
        assert data["service"] == "workshop"
        assert data["version"] == "2.0.0"
        assert data["total_services"] == len(SERVICES)

    @pytest.mark.anyio
    async def test_api_health_returns_200(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "operational"

    @pytest.mark.anyio
    async def test_health_has_timestamp(self, client):
        resp = await client.get("/health")
        data = resp.json()
        assert "timestamp" in data


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class TestDashboard:
    @pytest.mark.anyio
    async def test_root_returns_html(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "The Workshop" in resp.text

    @pytest.mark.anyio
    async def test_dashboard_route_returns_html(self, client):
        resp = await client.get("/dashboard")
        assert resp.status_code == 200
        assert "AMTL Launcher" in resp.text

    @pytest.mark.anyio
    async def test_dashboard_has_app_grid(self, client):
        resp = await client.get("/")
        assert "cardGrid" in resp.text

    @pytest.mark.anyio
    async def test_dashboard_has_theme_toggle(self, client):
        resp = await client.get("/")
        assert "themeToggle" in resp.text

    @pytest.mark.anyio
    async def test_dashboard_has_start_all_button(self, client):
        resp = await client.get("/")
        assert "btnStartAll" in resp.text

    @pytest.mark.anyio
    async def test_dashboard_has_view_logs_button(self, client):
        resp = await client.get("/")
        assert "btnViewLogs" in resp.text

    @pytest.mark.anyio
    async def test_dashboard_has_dark_theme_default(self, client):
        resp = await client.get("/")
        assert "#0A0E14" in resp.text

    @pytest.mark.anyio
    async def test_dashboard_has_auto_refresh(self, client):
        resp = await client.get("/")
        assert "setInterval(fetchServices, 10000)" in resp.text


# ---------------------------------------------------------------------------
# Service registry
# ---------------------------------------------------------------------------
class TestRegistry:
    def test_registry_has_14_services(self):
        assert len(SERVICES) == 14

    def test_all_services_have_required_fields(self):
        for svc in SERVICES:
            assert "name" in svc
            assert "id" in svc
            assert "port" in svc
            assert "health" in svc
            assert "description" in svc
            assert "built" in svc

    def test_elaine_is_first(self):
        assert SERVICES[0]["id"] == "elaine"
        assert SERVICES[0]["port"] == 5000

    def test_workshop_is_second(self):
        assert SERVICES[1]["id"] == "workshop"
        assert SERVICES[1]["port"] == 5001

    def test_costanza_port(self):
        costanza = next(s for s in SERVICES if s["id"] == "costanza")
        assert costanza["port"] == 5201

    def test_not_built_apps(self):
        not_built = [s for s in SERVICES if not s["built"]]
        assert len(not_built) == 4
        not_built_ids = {s["id"] for s in not_built}
        assert not_built_ids == {"atlas", "sentinel", "studio", "genie"}

    def test_built_apps(self):
        built = [s for s in SERVICES if s["built"]]
        assert len(built) == 10


# ---------------------------------------------------------------------------
# Services API
# ---------------------------------------------------------------------------
class TestServicesAPI:
    @pytest.mark.anyio
    async def test_list_services_returns_all(self, client):
        with patch("app._ping_service", new_callable=AsyncMock) as mock_ping:
            mock_ping.side_effect = lambda svc: {**svc, "status": "live" if svc["built"] else "not_built"}
            resp = await client.get("/api/services")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["services"]) == 14
            assert "summary" in data
            assert "timestamp" in data

    @pytest.mark.anyio
    async def test_service_health_known(self, client):
        with patch("app._ping_service", new_callable=AsyncMock) as mock_ping:
            mock_ping.return_value = {"id": "elaine", "status": "live"}
            resp = await client.get("/api/services/elaine/health")
            assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_service_health_unknown(self, client):
        resp = await client.get("/api/services/nonexistent/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "unknown"


# ---------------------------------------------------------------------------
# Ping service helper
# ---------------------------------------------------------------------------
class TestPingService:
    @pytest.mark.anyio
    async def test_not_built_returns_not_built(self):
        svc = {"name": "Test", "id": "test", "port": 9999, "health": "/health", "built": False}
        result = await _ping_service(svc)
        assert result["status"] == "not_built"

    @pytest.mark.anyio
    async def test_live_service(self):
        svc = {"name": "Test", "id": "test", "port": 9999, "health": "/health", "built": True}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("app.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = instance
            result = await _ping_service(svc)
            assert result["status"] == "live"

    @pytest.mark.anyio
    async def test_down_service(self):
        svc = {"name": "Test", "id": "test", "port": 9999, "health": "/health", "built": True}
        with patch("app.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.side_effect = Exception("Connection refused")
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = instance
            result = await _ping_service(svc)
            assert result["status"] == "down"


# ---------------------------------------------------------------------------
# Start All endpoint
# ---------------------------------------------------------------------------
class TestStartAll:
    @pytest.mark.anyio
    async def test_start_all_triggers(self, client):
        with patch("app.subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock(pid=12345)
            resp = await client.post("/api/start-all")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "triggered"
            assert data["pid"] == 12345

    @pytest.mark.anyio
    async def test_start_all_error(self, client):
        with patch("app.subprocess.Popen") as mock_popen:
            mock_popen.side_effect = FileNotFoundError("Not found")
            resp = await client.post("/api/start-all")
            data = resp.json()
            assert data["status"] == "error"


# ---------------------------------------------------------------------------
# Logs endpoint
# ---------------------------------------------------------------------------
class TestLogs:
    @pytest.mark.anyio
    async def test_logs_success(self, client):
        with patch("app.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="line1\nline2\nline3")
            resp = await client.get("/api/logs/elaine")
            assert resp.status_code == 200
            data = resp.json()
            assert data["service"] == "elaine"
            assert len(data["lines"]) == 3

    @pytest.mark.anyio
    async def test_logs_no_session(self, client):
        with patch("app.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            resp = await client.get("/api/logs/nonexistent")
            data = resp.json()
            assert "error" in data
