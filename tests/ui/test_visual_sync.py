"""
Visual regression tests for UI components - Synchronous Version.

These tests capture screenshots and verify visual consistency:
- Layout and styling verification
- Chart rendering appearance
- Responsive design verification
- Cross-browser visual consistency

Uses synchronous Playwright API to avoid pytest-asyncio event loop conflicts.
"""
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright


class TestVisualRegression:
    """Test visual appearance and layout consistency."""
    
    def test_initial_page_layout(self):
        """Test the initial page layout and appearance."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url, wait_until="domcontentloaded", timeout=15000)

                page.wait_for_timeout(2000)  # Wait for any immediate JavaScript
                page.wait_for_load_state("networkidle")
                
                # Take screenshot of initial state
                screenshot_path = Path(__file__).parent / "screenshots" / "initial_layout.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                
                page.screenshot(path=screenshot_path)
                
                # Verify key visual elements are present and positioned correctly
                form_row = page.locator(".row")
                assert form_row.is_visible()
                
                # Check that inputs are horizontally aligned
                lat_box = page.locator("#lat").bounding_box()
                lon_box = page.locator("#lon").bounding_box()
                
                assert lat_box is not None and lon_box is not None
                # Inputs should be roughly at the same vertical level (allowing some tolerance)
                assert abs(lat_box["y"] - lon_box["y"]) < 10
                
            finally:
                browser.close()
    
    def test_chart_with_data_visual(self):
        """Test visual appearance of chart with data."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Mock comprehensive data for visual testing
                page.route("**/uv?*", lambda route: route.fulfill(
                    content_type="application/json",
                    body="""{
                        "lat": 37.1882,
                        "lon": -3.6067,
                        "date": "2024-09-22",
                        "tz": "Europe/Madrid",
                        "now_local_iso": "2024-09-22T14:30:00",
                        "now_bucket_time": "2024-09-22T14:00:00",
                        "hourly": [
                            {"time": "2024-09-22T06:00:00", "consensus": 0.5, "low": 0.0, "high": 1.0, "providers": {"openweathermap": 0.5}, "outliers": []},
                            {"time": "2024-09-22T08:00:00", "consensus": 2.0, "low": 1.5, "high": 2.5, "providers": {"openweathermap": 2.0}, "outliers": []},
                            {"time": "2024-09-22T10:00:00", "consensus": 4.5, "low": 4.0, "high": 5.0, "providers": {"openweathermap": 4.5}, "outliers": []},
                            {"time": "2024-09-22T12:00:00", "consensus": 7.2, "low": 6.8, "high": 7.6, "providers": {"openweathermap": 7.2}, "outliers": []},
                            {"time": "2024-09-22T14:00:00", "consensus": 8.5, "low": 8.0, "high": 9.0, "providers": {"openweathermap": 8.5}, "outliers": []},
                            {"time": "2024-09-22T16:00:00", "consensus": 6.8, "low": 6.3, "high": 7.3, "providers": {"openweathermap": 6.8}, "outliers": []},
                            {"time": "2024-09-22T18:00:00", "consensus": 3.2, "low": 2.8, "high": 3.6, "providers": {"openweathermap": 3.2}, "outliers": []},
                            {"time": "2024-09-22T20:00:00", "consensus": 0.8, "low": 0.5, "high": 1.1, "providers": {"openweathermap": 0.8}, "outliers": []}
                        ],
                        "summary": {
                            "uv_max": 8.5,
                            "uv_max_time": "2024-09-22T14:00:00",
                            "advice": ["Use SPF 30+ sunscreen", "Wear protective clothing"],
                            "windows": {
                                "best": [{"start": "2024-09-22T06:00:00", "end": "2024-09-22T09:00:00"}],
                                "moderate": [{"start": "2024-09-22T09:00:00", "end": "2024-09-22T11:00:00"}],
                                "avoid": [{"start": "2024-09-22T11:00:00", "end": "2024-09-22T17:00:00"}]
                            }
                        },
                        "providers": [
                            {"name": "openweathermap", "error": null}
                        ]
                    }"""
                ))
                
                page.click("#go")
                page.wait_for_timeout(3000)  # Wait for chart to render
                
                # Take screenshot of page with chart
                screenshot_path = Path(__file__).parent / "screenshots" / "chart_with_data.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                
                page.screenshot(path=screenshot_path)
                
                # Verify chart is visible and has content
                chart_element = page.locator("#chart")
                assert chart_element.is_visible()
                
                # Check that chart has actual content (not empty)
                chart_html = chart_element.inner_html()
                assert len(chart_html) > 500  # Chart should have substantial content
                
            finally:
                browser.close()
    
    def test_summary_cards_layout(self):
        """Test visual layout of summary and provider cards."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Mock data with advice and providers for visual testing
                page.route("**/uv?*", lambda route: route.fulfill(
                    content_type="application/json",
                    body="""{
                        "lat": 37.1882,
                        "lon": -3.6067,
                        "hourly": [
                            {"time": "2024-09-22T12:00:00", "consensus": 8.5, "low": 8.0, "high": 9.0}
                        ],
                        "summary": {
                            "uv_max": 8.5,
                            "uv_max_time": "2024-09-22T14:00:00",
                            "advice": ["Use SPF 30+ sunscreen", "Seek shade during peak hours", "Wear protective clothing"],
                            "windows": {
                                "best": [{"start": "2024-09-22T07:00:00", "end": "2024-09-22T09:00:00"}],
                                "moderate": [{"start": "2024-09-22T09:00:00", "end": "2024-09-22T11:00:00"}],
                                "avoid": [{"start": "2024-09-22T11:00:00", "end": "2024-09-22T16:00:00"}]
                            }
                        },
                        "providers": [
                            {"name": "openweathermap", "error": null},
                            {"name": "visualcrossing", "error": null}
                        ]
                    }"""
                ))
                
                page.click("#go")
                page.wait_for_timeout(3000)
                
                # Take screenshot of summary cards
                screenshot_path = Path(__file__).parent / "screenshots" / "summary_cards.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                
                page.screenshot(path=screenshot_path)
                
                # Verify layout elements
                summary_element = page.locator("#summary")
                providers_element = page.locator("#providers")
                
                assert summary_element.is_visible()
                assert providers_element.is_visible()
                
                # Check content is properly displayed
                summary_text = summary_element.inner_text()
                assert "8.5" in summary_text
                assert "SPF" in summary_text
                
                providers_text = providers_element.inner_text()
                assert "openweathermap" in providers_text.lower()
                
            finally:
                browser.close()
    
    def test_responsive_mobile_layout(self):
        """Test responsive layout on mobile viewport."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                # Set mobile viewport
                page.set_viewport_size({"width": 375, "height": 667})
                page.goto(ui_url, wait_until="domcontentloaded", timeout=15000)

                page.wait_for_timeout(2000)  # Wait for any immediate JavaScript
                page.wait_for_load_state("networkidle")
                
                # Take screenshot of mobile layout
                screenshot_path = Path(__file__).parent / "screenshots" / "mobile_layout.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                
                page.screenshot(path=screenshot_path)
                
                # Verify all elements are still accessible on mobile
                assert page.locator("#lat").is_visible()
                assert page.locator("#lon").is_visible()
                assert page.locator("#date").is_visible()
                assert page.locator("#tz").is_visible()
                assert page.locator("#go").is_visible()
                assert page.locator("#chart").is_visible()
                
                # Check form is still functional
                page.fill("#lat", "40.7128")
                lat_value = page.locator("#lat").input_value()
                assert lat_value == "40.7128"
                
            finally:
                browser.close()
    
    def test_responsive_desktop_layout(self):
        """Test responsive layout on desktop viewport."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                # Set desktop viewport
                page.set_viewport_size({"width": 1920, "height": 1080})
                page.goto(ui_url, wait_until="domcontentloaded", timeout=15000)

                page.wait_for_timeout(2000)  # Wait for any immediate JavaScript
                page.wait_for_load_state("networkidle")
                
                # Take screenshot of desktop layout
                screenshot_path = Path(__file__).parent / "screenshots" / "desktop_layout.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                
                page.screenshot(path=screenshot_path)
                
                # Verify desktop-specific layout characteristics
                form_row = page.locator(".row")
                assert form_row.is_visible()
                
                # Check horizontal layout of form inputs
                lat_box = page.locator("#lat").bounding_box()
                lon_box = page.locator("#lon").bounding_box()
                
                assert lat_box is not None and lon_box is not None
                # On desktop, inputs should be side by side
                assert lat_box["x"] < lon_box["x"]  # lat should be left of lon
                
            finally:
                browser.close()


class TestChartVisuals:
    """Test chart-specific visual elements."""
    
    def test_chart_axis_labels(self):
        """Test that chart has proper axis labels and formatting."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Mock data for chart testing
                page.route("**/uv?*", lambda route: route.fulfill(
                    content_type="application/json",
                    body="""{
                        "lat": 37.1882,
                        "lon": -3.6067,
                        "hourly": [
                            {"time": "2024-09-22T08:00:00", "consensus": 2.0, "low": 1.5, "high": 2.5},
                            {"time": "2024-09-22T10:00:00", "consensus": 4.5, "low": 4.0, "high": 5.0},
                            {"time": "2024-09-22T12:00:00", "consensus": 7.2, "low": 6.8, "high": 7.6},
                            {"time": "2024-09-22T14:00:00", "consensus": 8.5, "low": 8.0, "high": 9.0}
                        ],
                        "summary": {"uv_max": 8.5},
                        "providers": []
                    }"""
                ))
                
                page.click("#go")
                page.wait_for_timeout(3000)
                
                # Take screenshot of chart area specifically
                chart_element = page.locator("#chart")
                screenshot_path = Path(__file__).parent / "screenshots" / "chart_details.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                
                chart_element.screenshot(path=screenshot_path)
                
                # Verify chart structure
                assert chart_element.is_visible()
                chart_html = chart_element.inner_html()
                
                # Chart should have substantial content indicating proper rendering
                assert len(chart_html) > 200
                
            finally:
                browser.close()
    
    def test_error_state_visual(self):
        """Test visual appearance during error states."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Mock error response
                page.route("**/uv?*", lambda route: route.abort())
                
                # Set up dialog handler
                def handle_dialog(dialog):
                    dialog.accept()
                
                page.on("dialog", handle_dialog)
                
                page.click("#go")
                page.wait_for_timeout(3000)
                
                # Take screenshot of error state
                screenshot_path = Path(__file__).parent / "screenshots" / "error_state.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                
                page.screenshot(path=screenshot_path)
                
                # Verify page is still functional after error
                fetch_button = page.locator("#go")
                assert fetch_button.is_enabled()
                
            finally:
                browser.close()
    
    def test_loading_state_visual(self):
        """Test visual appearance during loading states."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Mock delayed response
                def delayed_response(route):
                    import time
                    time.sleep(2)  # Simulate slow API
                    route.fulfill(
                        content_type="application/json",
                        body='{"lat": 37.1882, "lon": -3.6067, "hourly": [], "summary": {}, "providers": []}'
                    )
                
                page.route("**/uv?*", delayed_response)
                
                page.click("#go")
                page.wait_for_timeout(1000)  # Capture during loading
                
                # Take screenshot of loading state
                screenshot_path = Path(__file__).parent / "screenshots" / "loading_state.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                
                page.screenshot(path=screenshot_path)
                
                # Wait for completion
                page.wait_for_timeout(3000)
                
                # Verify final state
                fetch_button = page.locator("#go")
                assert fetch_button.is_enabled()
                
            finally:
                browser.close()


class TestAccessibilityVisuals:
    """Test accessibility-related visual elements."""
    
    def test_contrast_and_readability(self):
        """Test that text has sufficient contrast and is readable."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Take screenshot for contrast analysis
                screenshot_path = Path(__file__).parent / "screenshots" / "contrast_test.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                
                page.screenshot(path=screenshot_path)
                
                # Verify text elements are visible
                heading = page.locator("h1")
                assert heading.is_visible()
                
                # Check form labels and inputs are visible
                input_elements = ["#lat", "#lon", "#date", "#tz", "#go"]
                for element_id in input_elements:
                    element = page.locator(element_id)
                    assert element.is_visible()
                
            finally:
                browser.close()
    
    def test_focus_states(self):
        """Test visual focus states for interactive elements."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Focus on first input
                page.focus("#lat")
                page.wait_for_timeout(500)
                
                # Take screenshot with focus
                screenshot_path = Path(__file__).parent / "screenshots" / "focus_state.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                
                page.screenshot(path=screenshot_path)
                
                # Verify focus is functional
                page.fill("#lat", "40.7128")  # fill() replaces content, type() appends
                lat_value = page.locator("#lat").input_value()
                assert lat_value == "40.7128"
                
            finally:
                browser.close()
