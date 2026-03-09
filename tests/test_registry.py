"""Beast tests for Workshop V2 Registry API and UI elements.

Tests cover:
  - GET /workshop/api/registry (full list + filters)
  - GET /workshop/api/health/all
  - POST /workshop/api/apps/register
  - UI element data-testid presence
  - NGINX subpath compliance
  - Registry data integrity
"""

import json
import os
import shutil

import pytest

from app import create_app


@pytest.fixture
def client():
    application = create_app(start_health_loop=False)
    application.config["TESTING"] = True
    return application.test_client()


@pytest.fixture(autouse=True)
def protect_registry():
    """Back up registry.json before each test and restore after."""
    src = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                       "data", "registry.json")
    bak = src + ".bak"
    shutil.copy2(src, bak)
    yield
    shutil.copy2(bak, src)
    os.remove(bak)


# === Registry API Tests ===

def test_api_registry_returns_200(client):
    """GET /workshop/api/registry returns 200."""
    resp = client.get("/workshop/api/registry")
    assert resp.status_code == 200


def test_api_registry_returns_55_items(client):
    """GET /workshop/api/registry returns exactly 55 items."""
    resp = client.get("/workshop/api/registry")
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 55


def test_api_registry_filter_status_live(client):
    """GET /workshop/api/registry?status=live returns only live items."""
    resp = client.get("/workshop/api/registry?status=live")
    data = resp.get_json()
    assert all(item["status"] == "live" for item in data)
    assert len(data) > 0


def test_api_registry_filter_status_building(client):
    """GET /workshop/api/registry?status=building returns only building items."""
    resp = client.get("/workshop/api/registry?status=building")
    data = resp.get_json()
    assert all(item["status"] == "building" for item in data)


def test_api_registry_filter_status_planned(client):
    """GET /workshop/api/registry?status=planned returns only planned items."""
    resp = client.get("/workshop/api/registry?status=planned")
    data = resp.get_json()
    assert all(item["status"] == "planned" for item in data)


def test_api_registry_filter_cat_internal(client):
    """GET /workshop/api/registry?cat=internal returns only internal items."""
    resp = client.get("/workshop/api/registry?cat=internal")
    data = resp.get_json()
    assert all(item["category"] == "internal" for item in data)
    assert len(data) == 26


def test_api_registry_filter_cat_opensource(client):
    """GET /workshop/api/registry?cat=opensource returns only open-source items."""
    resp = client.get("/workshop/api/registry?cat=opensource")
    data = resp.get_json()
    assert all(item["category"] == "opensource" for item in data)
    assert len(data) == 7


def test_api_registry_filter_cat_commercial(client):
    """GET /workshop/api/registry?cat=commercial returns only commercial items."""
    resp = client.get("/workshop/api/registry?cat=commercial")
    data = resp.get_json()
    assert all(item["category"] == "commercial" for item in data)
    assert len(data) == 4


def test_api_registry_filter_cat_consulting(client):
    """GET /workshop/api/registry?cat=consulting returns only consulting items."""
    resp = client.get("/workshop/api/registry?cat=consulting")
    data = resp.get_json()
    assert all(item["category"] == "consulting" for item in data)
    assert len(data) == 4


def test_api_registry_filter_cat_content(client):
    """GET /workshop/api/registry?cat=content returns only content items."""
    resp = client.get("/workshop/api/registry?cat=content")
    data = resp.get_json()
    assert all(item["category"] == "content" for item in data)
    assert len(data) == 6


def test_api_registry_filter_cat_infra(client):
    """GET /workshop/api/registry?cat=infra returns only infra items."""
    resp = client.get("/workshop/api/registry?cat=infra")
    data = resp.get_json()
    assert all(item["category"] == "infra" for item in data)
    assert len(data) == 8


def test_api_registry_combined_filter(client):
    """GET /workshop/api/registry?status=live&cat=internal returns live internal items."""
    resp = client.get("/workshop/api/registry?status=live&cat=internal")
    data = resp.get_json()
    assert all(
        item["status"] == "live" and item["category"] == "internal"
        for item in data
    )
    assert len(data) > 0


def test_api_registry_item_shape(client):
    """Each registry item has all required fields."""
    resp = client.get("/workshop/api/registry")
    data = resp.get_json()
    required_fields = [
        "id", "name", "emoji", "port", "description",
        "category", "status", "tests", "tests_verified", "has_spec",
    ]
    for item in data:
        for field in required_fields:
            assert field in item, (
                f"Missing field '{field}' in item '{item.get('name', 'unknown')}'"
            )


def test_api_registry_valid_statuses(client):
    """All items have a valid status value."""
    resp = client.get("/workshop/api/registry")
    data = resp.get_json()
    valid_statuses = {"live", "building", "planned"}
    for item in data:
        assert item["status"] in valid_statuses, (
            f"Invalid status '{item['status']}' for '{item['name']}'"
        )


def test_api_registry_valid_categories(client):
    """All items have a valid category value."""
    resp = client.get("/workshop/api/registry")
    data = resp.get_json()
    valid_cats = {"internal", "opensource", "commercial", "consulting", "content", "infra"}
    for item in data:
        assert item["category"] in valid_cats, (
            f"Invalid category '{item['category']}' for '{item['name']}'"
        )


# === Register App Tests ===

def test_api_register_app_success(client):
    """POST /workshop/api/apps/register creates a new entry."""
    resp = client.post(
        "/workshop/api/apps/register",
        json={
            "name": "Test Registration App",
            "port": "9999",
            "category": "internal",
            "status": "planned",
        },
        content_type="application/json",
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["item"]["name"] == "Test Registration App"


def test_api_register_app_missing_name(client):
    """POST /workshop/api/apps/register without name returns 400."""
    resp = client.post(
        "/workshop/api/apps/register",
        json={"port": "9999"},
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_api_register_app_duplicate(client):
    """POST /workshop/api/apps/register with existing name returns 200."""
    resp = client.post(
        "/workshop/api/apps/register",
        json={"name": "ELAINE"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert "already registered" in resp.get_json()["message"]


# === Health All Tests ===

def test_api_health_all_returns_200(client):
    """GET /workshop/api/health/all returns 200."""
    resp = client.get("/workshop/api/health/all")
    assert resp.status_code == 200


def test_api_health_all_returns_dict(client):
    """GET /workshop/api/health/all returns a dictionary."""
    resp = client.get("/workshop/api/health/all")
    data = resp.get_json()
    assert isinstance(data, dict)


# === UI Tests ===

def test_ui_sidebar_nav_renders(client):
    """Main page contains sidebar nav element."""
    resp = client.get("/workshop/")
    assert b'data-testid="sidebar-nav"' in resp.data


def test_ui_filter_chips_render(client):
    """Main page contains filter chips."""
    resp = client.get("/workshop/")
    assert b'data-testid="filter-chips"' in resp.data


def test_ui_app_cards_render(client):
    """Main page contains app card elements."""
    resp = client.get("/workshop/")
    assert b'data-testid="app-card"' in resp.data


def test_ui_search_input_renders(client):
    """Main page contains search input."""
    resp = client.get("/workshop/")
    assert b'data-testid="search-input"' in resp.data


def test_ui_theme_toggle_renders(client):
    """Main page contains theme toggle button."""
    resp = client.get("/workshop/")
    assert b'data-testid="theme-toggle"' in resp.data


def test_ui_topbar_renders(client):
    """Main page contains topbar element."""
    resp = client.get("/workshop/")
    assert b'data-testid="topbar"' in resp.data


def test_ui_unverified_badge_present(client):
    """Main page shows unverified badge for items with unverified tests."""
    resp = client.get("/workshop/")
    assert b'data-testid="unverified-badge"' in resp.data or b"unverified" in resp.data.lower()


# === NGINX Subpath Tests ===

def test_static_refs_use_workshop_prefix(client):
    """All static references use /workshop/static/ prefix."""
    import re
    resp = client.get("/workshop/")
    html = resp.data.decode("utf-8")
    static_refs = re.findall(r'(?:href|src)="(/[^"]*static[^"]*)"', html)
    for ref in static_refs:
        assert ref.startswith("/workshop/static/"), (
            f"Static ref '{ref}' does not use /workshop/static/ prefix"
        )


def test_api_fetch_urls_use_workshop_prefix(client):
    """All JavaScript fetch calls use /workshop/api/ prefix."""
    import re
    resp = client.get("/workshop/")
    html = resp.data.decode("utf-8")
    fetch_calls = re.findall(r"fetch\(['\"]([^'\"]+)['\"]", html)
    for url in fetch_calls:
        if "/api/" in url:
            assert url.startswith("/workshop/api/"), (
                f"Fetch URL '{url}' does not use /workshop/api/ prefix"
            )


# === Registry Data Integrity ===

def test_elaine_in_registry(client):
    """ELAINE exists in the registry with correct data."""
    resp = client.get("/workshop/api/registry")
    data = resp.get_json()
    elaine = [i for i in data if i["name"] == "ELAINE"]
    assert len(elaine) == 1
    assert elaine[0]["port"] == "5000"
    assert elaine[0]["status"] == "live"
    assert elaine[0]["tests"] == "783"


def test_workshop_in_registry(client):
    """The Workshop itself exists in the registry."""
    resp = client.get("/workshop/api/registry")
    data = resp.get_json()
    workshop = [i for i in data if i["name"] == "The Workshop"]
    assert len(workshop) == 1
    assert workshop[0]["status"] == "live"


def test_status_counts_correct(client):
    """Registry has correct counts per status."""
    resp = client.get("/workshop/api/registry")
    data = resp.get_json()
    live = [i for i in data if i["status"] == "live"]
    building = [i for i in data if i["status"] == "building"]
    planned = [i for i in data if i["status"] == "planned"]
    assert len(live) + len(building) + len(planned) == 55


def test_workshop_health_shortcut(client):
    """GET /workshop/health returns 200."""
    resp = client.get("/workshop/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "operational"


def test_root_redirects_to_workshop(client):
    """GET / redirects to /workshop/."""
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/workshop/" in resp.headers.get("Location", "")
