"""Beast Tests — Workshop FastAPI v2.0.

Unit/integration tests using httpx AsyncClient against the ASGI app.
No live server required.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app import app, SERVICES


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Health ────────────────────────────────────────────────────────────────

class TestHealth:
    """Beast: /health returns operational status."""

    @pytest.mark.anyio
    async def test_health_returns_200(self, client):
        r = await client.get("/health")
        assert r.status_code == 200

    @pytest.mark.anyio
    async def test_health_status_operational(self, client):
        data = (await client.get("/health")).json()
        assert data["status"] == "operational"

    @pytest.mark.anyio
    async def test_health_service_name(self, client):
        data = (await client.get("/health")).json()
        assert data["service"] == "workshop"


# ── Dashboard ─────────────────────────────────────────────────────────────

class TestDashboard:
    """Beast: GET / serves the Workshop dashboard."""

    @pytest.mark.anyio
    async def test_dashboard_returns_200(self, client):
        r = await client.get("/")
        assert r.status_code == 200

    @pytest.mark.anyio
    async def test_dashboard_contains_workshop(self, client):
        r = await client.get("/")
        assert "Workshop" in r.text


# ── Services API ──────────────────────────────────────────────────────────

class TestServicesAPI:
    """Beast: /api/services returns the service registry."""

    @pytest.mark.anyio
    async def test_services_returns_200(self, client):
        r = await client.get("/api/services")
        assert r.status_code == 200

    @pytest.mark.anyio
    async def test_services_returns_list(self, client):
        data = (await client.get("/api/services")).json()
        services = data["services"] if isinstance(data, dict) else data
        assert isinstance(services, list)
        assert len(services) >= 1

    @pytest.mark.anyio
    async def test_service_object_fields(self, client):
        data = (await client.get("/api/services")).json()
        services = data["services"] if isinstance(data, dict) else data
        required = {"id", "name", "port", "emoji", "group", "url"}
        for svc in services:
            missing = required - set(svc.keys())
            assert not missing, f"Service {svc.get('name', '?')} missing fields: {missing}"


# ── Single Service Health ─────────────────────────────────────────────────

class TestServiceHealth:
    """Beast: /api/services/{id}/health for individual services."""

    @pytest.mark.anyio
    async def test_known_service_health(self, client):
        """Health check for 'workshop' itself should return something."""
        r = await client.get("/api/services/workshop/health")
        assert r.status_code == 200

    @pytest.mark.anyio
    async def test_unknown_service_returns_error(self, client):
        """Unknown service ID returns non-healthy response."""
        r = await client.get("/api/services/nonexistent_xyz/health")
        if r.status_code == 200:
            data = r.json()
            assert data.get("status") != "healthy", "Unknown service should not be healthy"
        else:
            assert r.status_code in (404, 422)


# ── Logs ──────────────────────────────────────────────────────────────────

class TestLogs:
    """Beast: /api/logs/{id} returns log output."""

    @pytest.mark.anyio
    async def test_logs_known_service(self, client):
        r = await client.get("/api/logs/workshop")
        # Should return 200 even if no tmux session exists
        assert r.status_code == 200

    @pytest.mark.anyio
    async def test_logs_unknown_service(self, client):
        r = await client.get("/api/logs/nonexistent_xyz")
        assert r.status_code in (200, 404)
