# Author: Mani Padisetti
"""
Beast Test Suite -- Workshop
Port: 5001
Path: /home/mani/workshop/
Run:  python -m pytest beast_test.py -v

Central Service Registry & Launcher for the AMTL ecosystem.
Tests health, core endpoints, edge cases, negative paths, NGINX subpath, and security.

Almost Magic Tech Lab
"""

import pytest
import httpx

BASE_URL = "http://localhost:5001"
APP_NAME = "workshop"
NGINX_URL = "http://amtl"
PREFIX = "/workshop"


# ---------------------------------------------------------------------------
# SECTION 1: HEALTH (3 tests)
# ---------------------------------------------------------------------------
class TestHealth:
    """Health endpoint tests -- verify Workshop is alive and reporting correctly."""

    def test_health_happy_path(self):
        """Happy: GET /workshop/health returns 200 with operational status."""
        r = httpx.get(f"{BASE_URL}{PREFIX}/health", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "operational"
        assert data["service"] == "workshop"

    def test_api_health(self):
        """Happy: GET /workshop/api/health returns 200 with version and uptime."""
        r = httpx.get(f"{BASE_URL}{PREFIX}/api/health", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "operational"
        assert "version" in data
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0

    def test_health_refresh(self):
        """Happy: POST /workshop/api/health/refresh triggers a refresh cycle."""
        r = httpx.post(f"{BASE_URL}{PREFIX}/api/health/refresh", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "refresh_complete"


# ---------------------------------------------------------------------------
# SECTION 2: CORE ENDPOINTS (6 tests)
# ---------------------------------------------------------------------------
class TestCoreEndpoints:
    """Core service endpoints -- services, registry, constellation, incidents, briefing."""

    def test_services_list(self):
        """Happy: GET /workshop/api/services returns a list of registered services."""
        r = httpx.get(f"{BASE_URL}{PREFIX}/api/services", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        first = data[0]
        assert "id" in first
        assert "name" in first
        assert "status" in first
        assert "group" in first

    def test_single_service(self):
        """Happy: GET /workshop/api/services/workshop returns Workshop details."""
        r = httpx.get(f"{BASE_URL}{PREFIX}/api/services/workshop", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "workshop"
        assert data["name"] is not None
        assert "port" in data
        assert "status" in data

    def test_registry(self):
        """Happy: GET /workshop/api/registry returns the full ecosystem registry."""
        r = httpx.get(f"{BASE_URL}{PREFIX}/api/registry", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        item = data[0]
        assert "id" in item
        assert "name" in item
        assert "status" in item

    def test_constellation(self):
        """Happy: GET /workshop/api/constellation returns node-graph data."""
        r = httpx.get(f"{BASE_URL}{PREFIX}/api/constellation", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)
        if len(data["nodes"]) > 0:
            node = data["nodes"][0]
            assert "id" in node
            assert "name" in node
            assert "group" in node

    def test_incidents(self):
        """Happy: GET /workshop/api/incidents returns incident list."""
        r = httpx.get(f"{BASE_URL}{PREFIX}/api/incidents", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_briefing(self):
        """Happy: GET /workshop/api/briefing returns the morning briefing."""
        r = httpx.get(f"{BASE_URL}{PREFIX}/api/briefing", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# SECTION 3: EDGE CASES (3 tests)
# ---------------------------------------------------------------------------
class TestEdgeCases:
    """Edge-case tests -- boundary conditions and unusual inputs."""

    def test_invalid_service_id(self):
        """Edge: GET /workshop/api/services/nonexistent-app-xyz returns 404."""
        r = httpx.get(
            f"{BASE_URL}{PREFIX}/api/services/nonexistent-app-xyz", timeout=10
        )
        assert r.status_code == 404
        data = r.json()
        assert "error" in data

    def test_registry_filter_empty(self):
        """Edge: GET /workshop/api/registry?status=nonexistent returns empty list."""
        r = httpx.get(
            f"{BASE_URL}{PREFIX}/api/registry?status=nonexistent_status_value",
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_help_unknown_screen(self):
        """Edge: GET /workshop/api/help/totally-unknown-screen returns 404."""
        r = httpx.get(
            f"{BASE_URL}{PREFIX}/api/help/totally-unknown-screen", timeout=10
        )
        assert r.status_code == 404
        data = r.json()
        assert "error" in data

    def test_help_known_screen(self):
        """Edge: GET /workshop/api/help/dashboard returns help content."""
        r = httpx.get(f"{BASE_URL}{PREFIX}/api/help/dashboard", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "howItWorks" in data
        assert "shortcuts" in data


# ---------------------------------------------------------------------------
# SECTION 4: NEGATIVE PATHS (3 tests)
# ---------------------------------------------------------------------------
class TestNegativePaths:
    """Negative-path tests -- missing fields, bad payloads, invalid operations."""

    def test_register_missing_name(self):
        """Negative: POST /workshop/api/apps/register without name returns 400."""
        r = httpx.post(
            f"{BASE_URL}{PREFIX}/api/apps/register",
            json={"description": "No name provided"},
            timeout=10,
        )
        assert r.status_code == 400
        data = r.json()
        assert "error" in data

    def test_command_empty_query(self):
        """Negative: POST /workshop/api/command with empty query returns 400."""
        r = httpx.post(
            f"{BASE_URL}{PREFIX}/api/command",
            json={"query": ""},
            timeout=10,
        )
        assert r.status_code == 400
        data = r.json()
        assert "error" in data

    def test_start_invalid_group(self):
        """Negative: POST /workshop/api/groups/nonexistent-group/start returns 404."""
        r = httpx.post(
            f"{BASE_URL}{PREFIX}/api/groups/nonexistent-group-xyz/start",
            timeout=10,
        )
        assert r.status_code == 404
        data = r.json()
        assert "error" in data

    def test_annotate_missing_note(self):
        """Negative: POST annotate without note field returns 400."""
        r = httpx.post(
            f"{BASE_URL}{PREFIX}/api/incidents/fake-id-999/annotate",
            json={},
            timeout=10,
        )
        assert r.status_code == 400
        data = r.json()
        assert "error" in data


# ---------------------------------------------------------------------------
# SECTION 5: NGINX SUBPATH (2 tests)
# ---------------------------------------------------------------------------
class TestNginxSubpath:
    """NGINX subpath compliance -- static assets and health at /workshop/."""

    def test_dashboard_static_refs(self):
        """Happy: GET /workshop/ dashboard HTML references /workshop/static/ not /static/."""
        r = httpx.get(f"{NGINX_URL}{PREFIX}/", timeout=10, follow_redirects=True)
        assert r.status_code == 200
        body = r.text
        # Should NOT contain bare /static/ references (without /workshop prefix)
        # But SHOULD contain /workshop/static/ if static assets are used
        if "/static/" in body:
            assert f"{PREFIX}/static/" in body, (
                "Static assets must use the /workshop/static/ subpath prefix"
            )

    def test_health_at_nginx_subpath(self):
        """Happy: GET http://amtl/workshop/health returns operational via NGINX."""
        r = httpx.get(f"{NGINX_URL}{PREFIX}/health", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "operational"


# ---------------------------------------------------------------------------
# SECTION 6: SECURITY (3 tests)
# ---------------------------------------------------------------------------
class TestSecurity:
    """Security tests -- injection, oversized payloads, command injection."""

    def test_sql_injection_service_id(self):
        """Security: SQL injection in service_id does not cause 500."""
        malicious_id = "'; DROP TABLE services; --"
        r = httpx.get(
            f"{BASE_URL}{PREFIX}/api/services/{malicious_id}", timeout=10
        )
        # Should return 404 (unknown service), NOT 500
        assert r.status_code in (404, 422), (
            f"SQL injection should not crash the server (got {r.status_code})"
        )

    def test_large_payload_register(self):
        """Security: Oversized payload on register does not crash the server."""
        huge_name = "A" * 100_000
        r = httpx.post(
            f"{BASE_URL}{PREFIX}/api/apps/register",
            json={"name": huge_name, "description": "stress test"},
            timeout=10,
        )
        # Should return a response (200, 400, or 413), NOT hang or 500
        assert r.status_code in (200, 201, 400, 413, 422), (
            f"Large payload should be handled gracefully (got {r.status_code})"
        )

    def test_command_injection_in_command(self):
        """Security: Shell metacharacters in command query do not execute."""
        r = httpx.post(
            f"{BASE_URL}{PREFIX}/api/command",
            json={"query": "; rm -rf / && cat /etc/passwd"},
            timeout=10,
        )
        # Should return a safe response, not 500 or shell output
        assert r.status_code in (200, 400), (
            f"Command injection should be handled safely (got {r.status_code})"
        )
        data = r.json()
        # Response should not contain filesystem content
        assert "/root:" not in str(data), "Response must not leak /etc/passwd content"
        assert "bin/bash" not in str(data), "Response must not leak shell paths"

    def test_xss_in_service_lookup(self):
        """Security: XSS payload in service lookup returns JSON, not HTML."""
        xss = "<img+onerror=alert(1)+src=x>"
        r = httpx.get(
            f"{BASE_URL}{PREFIX}/api/services/{xss}", timeout=10
        )
        assert r.status_code in (404, 422)
        # Critical: response must be JSON (content-type prevents browser rendering)
        content_type = r.headers.get("content-type", "")
        assert "application/json" in content_type, (
            "Error responses must be JSON to prevent XSS reflection"
        )
        data = r.json()
        assert "error" in data
