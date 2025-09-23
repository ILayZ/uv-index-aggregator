"""
Utilities for UI testing - Synchronous Version.

Common functions and helpers for UI tests using synchronous Playwright API.
"""
import json
from typing import Dict, Any, Optional
from pathlib import Path
from playwright.sync_api import sync_playwright


class UVTestDataBuilder:
    """Builder class for creating test data."""
    
    def __init__(self):
        self.data = {
            "lat": 37.1882,
            "lon": -3.6067,
            "date": "2024-09-22",
            "tz": "Europe/Madrid",
            "hourly": [],
            "summary": {},
            "providers": []
        }
    
    def with_coordinates(self, lat: float, lon: float) -> "UVTestDataBuilder":
        """Set coordinates."""
        self.data["lat"] = lat
        self.data["lon"] = lon
        return self
    
    def with_timezone(self, tz: str) -> "UVTestDataBuilder":
        """Set timezone."""
        self.data["tz"] = tz
        return self
    
    def with_hourly_data(self, hours: int = 24, base_uv: float = 5.0) -> "UVTestDataBuilder":
        """Add hourly UV data."""
        hourly = []
        for i in range(hours):
            hour = f"{i:02d}"
            uv_value = max(0, base_uv + (i - 12) * 0.5)  # Peak at noon
            hourly.append({
                "time": f"2024-09-22T{hour}:00:00",
                "consensus": round(uv_value, 1),
                "low": round(uv_value - 0.3, 1),
                "high": round(uv_value + 0.3, 1),
                "providers": {"openweathermap": round(uv_value, 1)},
                "outliers": []
            })
        self.data["hourly"] = hourly
        return self
    
    def with_summary(self, max_uv: Optional[float] = None) -> "UVTestDataBuilder":
        """Add summary data."""
        if max_uv is None and self.data["hourly"]:
            max_uv = max(h["consensus"] for h in self.data["hourly"])
            max_time = next(h["time"] for h in self.data["hourly"] if h["consensus"] == max_uv)
        else:
            if max_uv is None:
                max_uv = 8.5
            max_time = "2024-09-22T13:00:00"
        
        advice = []
        # max_uv is guaranteed to be a float at this point
        assert max_uv is not None
        if max_uv > 8:
            advice = ["Use SPF 50+ sunscreen", "Seek shade during peak hours"]
        elif max_uv > 5:
            advice = ["Use SPF 30+ sunscreen", "Wear protective clothing"]
        else:
            advice = ["Use SPF 15+ sunscreen"]
        
        self.data["summary"] = {
            "uv_max": max_uv,
            "uv_max_time": max_time,
            "advice": advice,
            "windows": {
                "best": [{"start": "2024-09-22T07:00:00", "end": "2024-09-22T09:00:00"}],
                "moderate": [{"start": "2024-09-22T09:00:00", "end": "2024-09-22T11:00:00"}],
                "avoid": [{"start": "2024-09-22T11:00:00", "end": "2024-09-22T16:00:00"}]
            }
        }
        return self
    
    def with_providers(self, *provider_specs) -> "UVTestDataBuilder":
        """Add provider data."""
        providers = []
        for spec in provider_specs:
            if isinstance(spec, str):
                providers.append({"name": spec, "error": None})
            elif isinstance(spec, dict):
                providers.append(spec)
        self.data["providers"] = providers
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the test data."""
        return self.data.copy()


class UITestHelper:
    """Helper class for common UI testing operations using sync Playwright."""
    
    @staticmethod
    def get_frontend_url() -> str:
        """Get the frontend URL for testing."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        return f"file:///{frontend_dir.absolute()}/index.html"
    
    @staticmethod
    def create_mock_uv_data(
        lat: float = 37.1882,
        lon: float = -3.6067,
        max_uv: float = 8.5,
        hours: int = 8
    ) -> Dict[str, Any]:
        """Create mock UV data for testing."""
        return (UVTestDataBuilder()
                .with_coordinates(lat, lon)
                .with_hourly_data(hours, max_uv)
                .with_summary(max_uv)
                .with_providers("openweathermap", "visualcrossing")
                .build())
    
    @staticmethod
    def setup_mock_api_response(page, data: Dict[str, Any]):
        """Set up mock API response for testing."""
        json_data = json.dumps(data)
        page.route("**/uv?*", lambda route: route.fulfill(
            content_type="application/json",
            body=json_data
        ))
    
    @staticmethod
    def fill_form_coordinates(page, lat: str, lon: str, date: str = "", tz: str = ""):
        """Fill form with coordinates and optional date/timezone."""
        page.fill("#lat", lat)
        page.fill("#lon", lon)
        if date:
            page.fill("#date", date)
        if tz:
            page.fill("#tz", tz)
    
    @staticmethod
    def wait_for_chart_render(page, timeout: int = 3000):
        """Wait for chart to render completely."""
        page.wait_for_timeout(timeout)
        
        # Verify chart has content
        chart_element = page.locator("#chart")
        assert chart_element.is_visible()
        
        chart_html = chart_element.inner_html()
        assert len(chart_html) > 100  # Should have substantial content
        
        return chart_element
    
    @staticmethod
    def get_summary_text(page) -> str:
        """Get summary section text."""
        summary_element = page.locator("#summary")
        assert summary_element.is_visible()
        return summary_element.inner_text()
    
    @staticmethod
    def get_providers_text(page) -> str:
        """Get providers section text."""
        providers_element = page.locator("#providers")
        assert providers_element.is_visible()
        return providers_element.inner_text()
    
    @staticmethod
    def verify_default_form_values(page):
        """Verify form has expected default values."""
        lat_value = page.locator("#lat").input_value()
        lon_value = page.locator("#lon").input_value()
        tz_value = page.locator("#tz").input_value()
        date_value = page.locator("#date").input_value()
        
        assert lat_value == "37.1882", f"Expected lat 37.1882, got {lat_value}"
        assert lon_value == "-3.6067", f"Expected lon -3.6067, got {lon_value}"
        assert tz_value == "auto", f"Expected timezone 'auto', got {tz_value}"
        assert date_value == "", f"Expected empty date, got {date_value}"
    
    @staticmethod
    def take_screenshot(page, name: str) -> Path:
        """Take a screenshot and save it."""
        screenshot_path = Path(__file__).parent / "screenshots" / f"{name}.png"
        screenshot_path.parent.mkdir(exist_ok=True)
        page.screenshot(path=screenshot_path)
        return screenshot_path


class TestLocationHelper:
    """Helper for testing different locations."""
    
    LOCATIONS = {
        "granada": {"lat": "37.1882", "lon": "-3.6067", "tz": "Europe/Madrid"},
        "new_york": {"lat": "40.7128", "lon": "-74.0060", "tz": "America/New_York"},
        "london": {"lat": "51.5074", "lon": "-0.1278", "tz": "Europe/London"},
        "sydney": {"lat": "-33.8688", "lon": "151.2093", "tz": "Australia/Sydney"},
        "tokyo": {"lat": "35.6762", "lon": "139.6503", "tz": "Asia/Tokyo"}
    }
    
    @classmethod
    def get_location(cls, name: str) -> Dict[str, str]:
        """Get location data by name."""
        return cls.LOCATIONS[name]
    
    @classmethod
    def run_for_all_locations(cls, test_func):
        """Run a test function for all predefined locations."""
        results = {}
        for name, location in cls.LOCATIONS.items():
            try:
                test_func(location, name)
                results[name] = "PASSED"
            except Exception as e:
                results[name] = f"FAILED: {e}"
        return results


class MockAPIServer:
    """Helper for mocking API responses in tests."""
    
    @staticmethod
    def create_error_response(status: int = 500, message: str = "Internal server error"):
        """Create an error response."""
        return {
            "status": status,
            "content_type": "application/json",
            "body": json.dumps({"error": message})
        }
    
    @staticmethod
    def create_empty_response():
        """Create an empty data response."""
        return {
            "status": 200,
            "content_type": "application/json",
            "body": json.dumps({
                "lat": 37.1882,
                "lon": -3.6067,
                "hourly": [],
                "summary": {},
                "providers": []
            })
        }
    
    @staticmethod
    def create_partial_response():
        """Create a partial data response."""
        return {
            "status": 200,
            "content_type": "application/json",
            "body": json.dumps({
                "lat": 37.1882,
                "lon": -3.6067,
                "hourly": [
                    {"time": "2024-09-22T12:00:00", "consensus": 5.0}
                ],
                "summary": {},
                "providers": []
            })
        }


def run_ui_test_with_browser(test_func, headless: bool = True, **kwargs):
    """
    Run a UI test function with a browser instance.
    
    Args:
        test_func: Function that takes (page, ui_url) as arguments
        headless: Whether to run browser in headless mode
        **kwargs: Additional arguments passed to test_func
    """
    ui_url = UITestHelper.get_frontend_url()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        
        try:
            result = test_func(page, ui_url, **kwargs)
            return result
        finally:
            browser.close()


def create_test_data_with_errors():
    """Create test data that includes provider errors."""
    return {
        "lat": 37.1882,
        "lon": -3.6067,
        "hourly": [
            {"time": "2024-09-22T12:00:00", "consensus": 6.0, "low": 5.5, "high": 6.5}
        ],
        "summary": {
            "uv_max": 6.0,
            "uv_max_time": "2024-09-22T12:00:00",
            "advice": ["Use SPF 30+ sunscreen"]
        },
        "providers": [
            {"name": "openweathermap", "error": None},
            {"name": "visualcrossing", "error": "API key invalid"},
            {"name": "weatherbit", "error": "Rate limit exceeded"}
        ]
    }
    def json(self) -> str:
        """Build as JSON string."""
        return json.dumps(self.build())


# Common test data sets
GRANADA_COORDS = {"lat": 37.1882, "lon": -3.6067}
NYC_COORDS = {"lat": 40.7128, "lon": -74.0060}
LONDON_COORDS = {"lat": 51.5074, "lon": -0.1278}
SYDNEY_COORDS = {"lat": -33.8688, "lon": 151.2093}

# Common test scenarios
def create_high_uv_scenario() -> UVTestDataBuilder:
    """Create test data for high UV scenario."""
    return (UVTestDataBuilder()
            .with_hourly_data(hours=12, base_uv=8.0)
            .with_summary(max_uv=10.5)
            .with_providers("openweathermap", "visualcrossing"))

def create_error_scenario() -> UVTestDataBuilder:
    """Create test data with provider errors."""
    return (UVTestDataBuilder()
            .with_providers(
                {"name": "openweathermap", "error": "API rate limit exceeded"},
                {"name": "visualcrossing", "error": "Network timeout"},
                {"name": "open_meteo", "error": None}
            ))

def create_minimal_scenario() -> UVTestDataBuilder:
    """Create minimal test data."""
    return (UVTestDataBuilder()
            .with_hourly_data(hours=6, base_uv=3.0)
            .with_providers("openweathermap"))
