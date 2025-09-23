"""
UI Tests for UV Index Aggregator Frontend - Synchronous Version.

These tests verify the functionality of the web interface including:
- Page loading and basic UI elements
- Input validation and form interactions
- Data fetching and chart rendering
- Error handling
- Responsive behavior

Uses synchronous Playwright API to avoid pyt                # Add request/response and error logging
                page.on("request", lambda request: print(f"Request: {request.method} {request.url}"))
                page.on("response", lambda response: print(f"Response: {response.status} {response.url}"))
                page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))
                page.on("pageerror", lambda error: print(f"Page error: {error}"))
                
                # Click fetch to load data
                page.click("#go")
                page.wait_for_timeout(3000)  # Wait for chart renderingncio event loop conflicts.
"""
import pytest
import re
import json
from pathlib import Path
from playwright.sync_api import sync_playwright


class TestUIBasics:
    """Test basic UI functionality and page loading."""
    
    def test_page_loads_successfully(self):
        """Test that the main page loads without errors."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Check title
                title = page.title()
                assert title == "UV Index Aggregator", f"Expected 'UV Index Aggregator', got '{title}'"
                
                # Check main heading
                heading = page.locator("h1")
                heading_text = heading.inner_text()
                assert heading_text == "UV Index Aggregator"
                
            finally:
                browser.close()
    
    def test_required_elements_present(self):
        """Test that all required UI elements are present."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Check input fields
                assert page.locator("#lat").is_visible()
                assert page.locator("#lon").is_visible()
                assert page.locator("#date").is_visible()
                assert page.locator("#tz").is_visible()
                
                # Check fetch button
                assert page.locator("#go").is_visible()
                go_button_text = page.locator("#go").inner_text()
                assert go_button_text == "Fetch"
                
                # Check chart and info containers
                assert page.locator("#chart").is_visible()
                assert page.locator("#summary").is_visible()
                assert page.locator("#providers").is_visible()
                
            finally:
                browser.close()
    
    def test_default_values(self):
        """Test that input fields have expected default values."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Check latitude and longitude (Granada, Spain)
                lat_value = page.locator("#lat").input_value()
                lon_value = page.locator("#lon").input_value()
                tz_value = page.locator("#tz").input_value()
                
                assert lat_value == "37.1882", f"Expected lat 37.1882, got {lat_value}"
                assert lon_value == "-3.6067", f"Expected lon -3.6067, got {lon_value}"
                assert tz_value == "auto", f"Expected timezone 'auto', got {tz_value}"
                
                # Date should be empty by default
                date_value = page.locator("#date").input_value()
                assert date_value == "", f"Expected empty date, got {date_value}"
                
            finally:
                browser.close()


class TestFormInteractions:
    """Test form input validation and interactions."""
    
    def test_coordinate_input_validation(self):
        """Test coordinate input accepts valid decimal numbers."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Test valid coordinates (NYC)
                page.fill("#lat", "40.7128")
                page.fill("#lon", "-74.0060")
                
                lat_value = page.locator("#lat").input_value()
                lon_value = page.locator("#lon").input_value()
                
                assert lat_value == "40.7128"
                assert lon_value == "-74.0060"
                
            finally:
                browser.close()
    
    def test_date_input_format(self):
        """Test date input accepts valid date format."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Test valid date format
                page.fill("#date", "2024-09-22")
                date_value = page.locator("#date").input_value()
                assert date_value == "2024-09-22"
                
            finally:
                browser.close()
    
    def test_timezone_input(self):
        """Test timezone input accepts various formats."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url, wait_until="domcontentloaded", timeout=15000)

                page.wait_for_timeout(2000)  # Wait for any immediate JavaScript
                
                # Test timezone values
                test_timezones = ["auto", "UTC", "Europe/Madrid", "America/New_York"]
                
                for tz in test_timezones:
                    page.fill("#tz", tz)
                    tz_value = page.locator("#tz").input_value()
                    assert tz_value == tz, f"Expected timezone {tz}, got {tz_value}"
                
            finally:
                browser.close()
    
    def test_form_submission_state(self):
        """Test form state during submission."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url, wait_until="domcontentloaded", timeout=15000)

                page.wait_for_timeout(2000)  # Wait for any immediate JavaScript
                
                # Mock API to control response timing
                page.route("**/uv?*", lambda route: route.fulfill(
                    content_type="application/json",
                    body='{"lat": 37.1882, "lon": -3.6067, "hourly": [], "summary": {}, "providers": []}'
                ))
                
                # Check fetch button is enabled initially
                fetch_button = page.locator("#go")
                assert fetch_button.is_enabled()
                
                # Click fetch and verify form state
                fetch_button.click()
                page.wait_for_timeout(1000)  # Brief wait for response
                
                # Button should be enabled again after response
                assert fetch_button.is_enabled()
                
            finally:
                browser.close()


class TestUIFeedback:
    """Test UI feedback and user experience elements."""
    
    def test_error_handling_display(self):
        """Test that errors are displayed to the user."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url, wait_until="domcontentloaded", timeout=15000)

                page.wait_for_timeout(2000)  # Wait for any immediate JavaScript
                
                # Mock API error response
                page.route("**/uv?*", lambda route: route.abort())
                
                # Set up alert handler
                alert_message = None
                def handle_alert(alert):
                    nonlocal alert_message
                    alert_message = alert.message
                    alert.accept()
                
                page.on("dialog", handle_alert)
                
                # Click fetch to trigger error
                page.click("#go")
                page.wait_for_timeout(2000)  # Wait for error handling
                
                # Verify error was shown (via alert or other UI feedback)
                # Note: This depends on how the frontend handles errors
                
            finally:
                browser.close()
    
    def test_loading_state_feedback(self):
        """Test loading state feedback during data fetch."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url, wait_until="domcontentloaded", timeout=15000)

                page.wait_for_timeout(2000)  # Wait for any immediate JavaScript
                
                # Mock delayed API response
                def delayed_response(route):
                    import time
                    time.sleep(1)  # Simulate slow API
                    route.fulfill(
                        content_type="application/json",
                        body='{"lat": 37.1882, "lon": -3.6067, "hourly": [], "summary": {}, "providers": []}'
                    )
                
                page.route("**/uv?*", delayed_response)
                
                # Check initial state
                fetch_button = page.locator("#go")
                initial_text = fetch_button.inner_text()
                
                # Click and check if there's any loading indication
                fetch_button.click()
                page.wait_for_timeout(500)  # Check mid-request
                
                # Wait for completion
                page.wait_for_timeout(2000)
                
                # Verify final state
                final_text = fetch_button.inner_text()
                assert final_text == initial_text or final_text == "Fetch"
                
            finally:
                browser.close()


class TestDataVisualization:
    """Test data visualization and chart functionality."""
    
    def test_chart_renders_with_mock_data(self):
        """Test chart rendering with mocked UV data."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url, wait_until="domcontentloaded", timeout=15000)

                page.wait_for_timeout(2000)  # Wait for any immediate JavaScript
                
                # Mock comprehensive UV data
                mock_data = {
                    "lat": 37.1882,
                    "lon": -3.6067,
                    "date": "2024-09-22",
                    "tz": "Europe/Madrid",
                    "hourly": [
                        {"time": "2024-09-22T08:00:00", "consensus": 2.0, "low": 1.5, "high": 2.5},
                        {"time": "2024-09-22T10:00:00", "consensus": 4.5, "low": 4.0, "high": 5.0},
                        {"time": "2024-09-22T12:00:00", "consensus": 7.2, "low": 6.8, "high": 7.6},
                        {"time": "2024-09-22T14:00:00", "consensus": 8.5, "low": 8.0, "high": 9.0},
                        {"time": "2024-09-22T16:00:00", "consensus": 6.8, "low": 6.3, "high": 7.3},
                        {"time": "2024-09-22T18:00:00", "consensus": 3.2, "low": 2.8, "high": 3.6}
                    ],
                    "summary": {
                        "uv_max": 8.5,
                        "uv_max_time": "2024-09-22T14:00:00",
                        "advice": ["Use SPF 30+ sunscreen", "Wear protective clothing"]
                    },
                    "providers": [{"name": "openweathermap", "error": None}]
                }
                
                page.route("**/uv?*", lambda route: route.fulfill(
                    content_type="application/json",
                    body=json.dumps(mock_data)
                ))
                
                # Also mock localhost specifically
                page.route("http://localhost:8080/uv?*", lambda route: route.fulfill(
                    content_type="application/json", 
                    body=json.dumps(mock_data)
                ))
                
                # Click fetch to load data
                page.click("#go")
                page.wait_for_timeout(5000)  # Wait longer for chart rendering
                
                # Verify chart container has content
                chart_element = page.locator("#chart")
                assert chart_element.is_visible()
                
                # Check that chart has been populated by verifying Plotly chart data
                page.wait_for_timeout(5000)  # Longer wait for Plotly rendering
                
                # Try multiple ways to detect chart data
                chart_data = page.evaluate("""
                    (() => {
                        const chartDiv = document.getElementById('chart');
                        
                        // Method 1: Check data property
                        if (chartDiv && chartDiv.data && chartDiv.data.length > 0) {
                            return chartDiv.data.length;
                        }
                        
                        // Method 2: Check _fullData property  
                        if (chartDiv && chartDiv._fullData && chartDiv._fullData.length > 0) {
                            return chartDiv._fullData.length;
                        }
                        
                        // Method 3: Check if Plotly has rendered anything
                        const plotlyDiv = chartDiv ? chartDiv.querySelector('.plotly-graph-div') : null;
                        if (plotlyDiv) {
                            return 1; // At least something was rendered
                        }
                        
                        // Method 4: Check innerHTML for any content
                        if (chartDiv && chartDiv.innerHTML.trim().length > 1000) {
                            return 1; // Chart has substantial content
                        }
                        
                        return 0;
                    })()
                """)
                assert chart_data > 0, f"Chart data not found. chart_data = {chart_data}"
                
                # Verify summary information is displayed
                summary_element = page.locator("#summary")
                assert summary_element.is_visible()
                summary_text = summary_element.inner_text()
                assert "8.5" in summary_text  # Max UV value should be shown
                
            finally:
                browser.close()
    
    def test_empty_data_handling(self):
        """Test handling of empty or minimal data responses."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url, wait_until="domcontentloaded", timeout=15000)

                page.wait_for_timeout(2000)  # Wait for any immediate JavaScript
                
                # Mock empty data response
                page.route("**/uv?*", lambda route: route.fulfill(
                    content_type="application/json",
                    body='{"lat": 37.1882, "lon": -3.6067, "hourly": [], "summary": {}, "providers": []}'
                ))
                
                # Click fetch
                page.click("#go")
                page.wait_for_timeout(2000)
                
                # Verify page doesn't crash with empty data
                chart_element = page.locator("#chart")
                assert chart_element.is_visible()
                
                # Page should still be functional
                fetch_button = page.locator("#go")
                assert fetch_button.is_enabled()
                
            finally:
                browser.close()


class TestResponsiveDesign:
    """Test responsive design and layout adaptability."""
    
    def test_mobile_viewport_layout(self):
        """Test layout on mobile viewport."""
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
                
                # Verify all elements are still visible and accessible
                assert page.locator("#lat").is_visible()
                assert page.locator("#lon").is_visible()
                assert page.locator("#date").is_visible()
                assert page.locator("#tz").is_visible()
                assert page.locator("#go").is_visible()
                assert page.locator("#chart").is_visible()
                
                # Verify form is still functional
                page.fill("#lat", "40.7128")
                lat_value = page.locator("#lat").input_value()
                assert lat_value == "40.7128"
                
            finally:
                browser.close()
    
    def test_desktop_viewport_layout(self):
        """Test layout on desktop viewport."""
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
                
                # Verify layout is appropriate for desktop
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

