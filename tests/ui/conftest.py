"""
Pytest configuration for UI tests.
"""
import pytest
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright


@pytest.fixture
def ui_url():
    """Return the frontend URL."""
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    return f"file:///{frontend_dir.absolute()}/index.html"


@pytest.fixture
def test_coordinates():
    """Test coordinates for Granada, Spain."""
    return {
        "lat": 37.1882,
        "lon": -3.6067,
        "city": "Granada, Spain"
    }


@pytest.fixture
def backend_server():
    """Provide backend server URL for integration tests."""
    return "http://localhost:8080"


@pytest.fixture
async def page():
    """Provide a Playwright page for async tests."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        yield page
        await browser.close()
