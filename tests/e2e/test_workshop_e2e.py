# Author: Mani Padisetti
"""
Playwright e2e tests for The Workshop V2.
Requires the app to be running at http://localhost:5001/workshop/
"""

import pytest
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:5001/workshop/"


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    page = browser.new_page()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    yield page
    page.close()


def test_workshop_loads_with_sidebar(page):
    """Workshop loads at /workshop/ and sidebar is visible."""
    expect(page.locator('[data-testid="sidebar-nav"]')).to_be_visible()
    expect(page.locator('[data-testid="topbar"]')).to_be_visible()


def test_click_live_filter_shows_only_live(page):
    """Clicking 'Live & Running' in sidebar shows only live items."""
    page.locator('[data-testid="sidebar-nav"]').get_by_text("Live").first.click()
    page.wait_for_timeout(500)

    cards = page.locator('[data-testid="app-card"]')
    count = cards.count()
    assert count > 0

    # Verify no planned items showing (they would be at 45% opacity)
    for i in range(count):
        opacity = cards.nth(i).evaluate("el => getComputedStyle(el).opacity")
        assert float(opacity) > 0.5, "Found a planned-opacity card in Live filter view"


def test_click_unverified_shows_unverified_only(page):
    """Clicking 'Unverified Tests' flag shows only items with unverified tests."""
    page.locator('[data-testid="sidebar-nav"]').get_by_text("Unverified").first.click()
    page.wait_for_timeout(500)

    cards = page.locator('[data-testid="app-card"]')
    count = cards.count()
    assert count > 0

    for i in range(count):
        badge = cards.nth(i).locator('[data-testid="unverified-badge"]')
        assert badge.count() > 0 or "unverified" in cards.nth(i).inner_text().lower()


def test_search_elaine_shows_card(page):
    """Searching 'ELAINE' filters to show the ELAINE card."""
    search = page.locator('[data-testid="search-input"]')
    search.fill("ELAINE")
    page.wait_for_timeout(500)

    cards = page.locator('[data-testid="app-card"]')
    found = False
    for i in range(cards.count()):
        text = cards.nth(i).inner_text()
        if "ELAINE" in text:
            found = True
            break
    assert found, "ELAINE card not found after searching"


def test_dark_light_theme_toggle(page):
    """Dark/light toggle switches the theme."""
    theme = page.locator("html").get_attribute("data-theme")
    assert theme == "dark"

    page.locator('[data-testid="theme-toggle"]').click()
    page.wait_for_timeout(300)

    theme = page.locator("html").get_attribute("data-theme")
    assert theme == "light"

    page.locator('[data-testid="theme-toggle"]').click()
    page.wait_for_timeout(300)

    theme = page.locator("html").get_attribute("data-theme")
    assert theme == "dark"
