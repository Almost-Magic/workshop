# Author: Mani Padisetti
"""Proof Tests — Workshop Playwright.

Browser-based verification against the live server on port 5001.
Requires: pip install pytest-playwright && playwright install chromium
"""

import pytest
from playwright.sync_api import sync_playwright


BASE_URL = "http://localhost:5001"


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture
def page(browser):
    pg = browser.new_page()
    pg.goto(BASE_URL, wait_until="networkidle")
    yield pg
    pg.close()


class TestPageLoad:
    """PROOF: Dashboard loads in a real browser."""

    def test_page_loads(self, page):
        """Page returns a non-empty document."""
        assert page.title() or page.content()

    def test_workshop_text_visible(self, page):
        """'Workshop' text appears on the page."""
        assert page.locator("text=Workshop").first.is_visible()


class TestSidebar:
    """PROOF: Sidebar is present and styled."""

    def test_sidebar_exists(self, page):
        """Sidebar element with class 'sidebar' exists."""
        sidebar = page.locator(".sidebar")
        assert sidebar.count() > 0
        assert sidebar.first.is_visible()


class TestThemeToggle:
    """PROOF: Theme toggle button exists."""

    def test_theme_toggle_exists(self, page):
        """A theme toggle button is present in the page."""
        # Look for the toggle button by id, class, or known icon text
        toggle = page.locator("#themeToggle, .theme-toggle, button:has-text('☿'), button:has-text('☉')")
        assert toggle.count() > 0


class TestServiceCards:
    """PROOF: At least one service card is rendered."""

    def test_service_card_visible(self, page):
        """At least one .card element is visible."""
        cards = page.locator(".card")
        assert cards.count() > 0
        assert cards.first.is_visible()


class TestStatusBar:
    """PROOF: Status bar exists at the bottom."""

    def test_status_bar_exists(self, page):
        """Status bar element is present."""
        bar = page.locator(".status-bar")
        assert bar.count() > 0
        assert bar.first.is_visible()
