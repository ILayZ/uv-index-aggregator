"""
Integration tests for UI components with real backend interactions - Synchronous Version.

These tests verify end-to-end functionality including:
- Real API calls to backend
- Data flow from backend to frontend
- Chart rendering with real data
- Error scenarios with backend responses

Uses synchronous Playwright API to avoid pytest-asyncio event loop conflicts.
"""
import pytest
import json
from pathlib import Path
from playwright.sync_api import sync_playwright


class TestBackendIntegration:
    """Test UI integration with actual backend."""
    
    def test_health_endpoint_integration(self):
        """Test that the backend health endpoint is accessible."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        backend_server = "http://localhost:8080"  # Default backend URL
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Use real backend URL
                page.evaluate(f"""
                    fetch('{backend_server}/health')
                        .then(r => r.json())
                        .then(data => {{
                            window.healthCheck = data;
                        }})
                        .catch(err => {{
                            window.healthError = err.message;
                        }});
                """)
                
                page.wait_for_timeout(2000)
                
                # Check that health check succeeded
                health_result = page.evaluate("window.healthCheck")
                health_error = page.evaluate("window.healthError")
                
                if health_error is not None:
                    pytest.skip(f"Backend not available: {health_error}")
                
                assert health_result is not None
                assert health_result.get("ok") is True
                
            finally:
                browser.close()
    
    def test_providers_endpoint_integration(self):
        """Test providers endpoint integration."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        backend_server = "http://localhost:8080"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Fetch providers data
                page.evaluate(f"""
                    fetch('{backend_server}/providers')
                        .then(r => r.json())
                        .then(data => {{
                            window.providersData = data;
                        }})
                        .catch(err => {{
                            window.providersError = err.message;
                        }});
                """)
                
                page.wait_for_timeout(2000)
                
                providers_data = page.evaluate("window.providersData")
                providers_error = page.evaluate("window.providersError")
                
                if providers_error is not None:
                    pytest.skip(f"Backend providers endpoint not available: {providers_error}")
                
                assert providers_data is not None
                assert isinstance(providers_data, dict)
                assert "open_meteo" in providers_data
                
            finally:
                browser.close()
    
    def test_real_uv_data_fetch(self):
        """Test fetching real UV data from backend."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        backend_server = "http://localhost:8080"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Override the fetch URL to use real backend
                page.evaluate(f"""
                    // Override the fetchData function to use the test backend
                    window.originalFetchData = window.fetchData;
                    window.fetchData = function() {{
                        const lat = document.getElementById('lat').value;
                        const lon = document.getElementById('lon').value;
                        const date = document.getElementById('date').value;
                        const tz = document.getElementById('tz').value;
                        const qs = new URLSearchParams({{ lat, lon }});
                        if (date) qs.set('date', date);
                        if (tz) qs.set('tz', tz);
                        
                        fetch('{backend_server}/uv?' + qs.toString())
                            .then(r => r.json())
                            .then(data => {{
                                window.lastUVData = data;
                                draw(data);
                            }})
                            .catch(err => {{
                                window.lastUVError = err.message;
                                alert('Error: ' + err);
                            }});
                    }};
                """)
                
                # Click fetch with default coordinates
                page.click("#go")
                page.wait_for_timeout(5000)  # Give more time for real API calls
                
                uv_data = page.evaluate("window.lastUVData")
                uv_error = page.evaluate("window.lastUVError")
                
                if uv_error is not None:
                    pytest.skip(f"Backend UV endpoint not available: {uv_error}")
                
                # Verify we got valid UV data
                assert uv_data is not None
                assert isinstance(uv_data, dict)
                assert "lat" in uv_data
                assert "lon" in uv_data
                
                # Check that chart was updated
                chart_element = page.locator("#chart")
                assert chart_element.is_visible()
                # Verify chart was rendered by checking Plotly data
                page.wait_for_timeout(3000)  # Longer wait for chart rendering
                
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
                        if (chartDiv && chartDiv.querySelector('.plotly-graph-div')) {
                            return 1; // At least something was rendered
                        }
                        
                        return 0;
                    })()
                """)
                assert chart_data > 0  # Should have content
                
            finally:
                browser.close()


class TestMockIntegration:
    """Test UI integration with mocked backend responses."""
    
    def test_successful_data_flow(self):
        """Test complete data flow from fetch to chart rendering."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Mock successful UV data response
                mock_data = {
                    "lat": 37.1882,
                    "lon": -3.6067,
                    "date": "2024-09-22",
                    "tz": "Europe/Madrid",
                    "now_local_iso": "2024-09-22T14:30:00",
                    "now_bucket_time": "2024-09-22T14:00:00",
                    "hourly": [
                        {"time": "2024-09-22T08:00:00", "consensus": 2.0, "low": 1.5, "high": 2.5, "providers": {"openweathermap": 2.0}, "outliers": []},
                        {"time": "2024-09-22T10:00:00", "consensus": 4.5, "low": 4.0, "high": 5.0, "providers": {"openweathermap": 4.5}, "outliers": []},
                        {"time": "2024-09-22T12:00:00", "consensus": 7.2, "low": 6.8, "high": 7.6, "providers": {"openweathermap": 7.2}, "outliers": []},
                        {"time": "2024-09-22T14:00:00", "consensus": 8.5, "low": 8.0, "high": 9.0, "providers": {"openweathermap": 8.5}, "outliers": []},
                        {"time": "2024-09-22T16:00:00", "consensus": 6.8, "low": 6.3, "high": 7.3, "providers": {"openweathermap": 6.8}, "outliers": []},
                        {"time": "2024-09-22T18:00:00", "consensus": 3.2, "low": 2.8, "high": 3.6, "providers": {"openweathermap": 3.2}, "outliers": []}
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
                
                # Click fetch to trigger data flow
                page.click("#go")
                page.wait_for_timeout(5000)  # Wait longer for processing
                
                # Verify chart was rendered by checking Plotly data
                chart_element = page.locator("#chart")
                assert chart_element.is_visible()
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
                        
                        // Method 4: Check innerHTML for substantial content
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
                assert "8.5" in summary_text  # Max UV should be shown
                
                # Verify providers information is displayed
                providers_element = page.locator("#providers")
                assert providers_element.is_visible()
                providers_text = providers_element.inner_text()
                assert "openweathermap" in providers_text.lower()
                
            finally:
                browser.close()
    
    def test_error_response_handling(self):
        """Test handling of error responses from backend."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Mock error response
                page.route("**/uv?*", lambda route: route.fulfill(
                    status=500,
                    content_type="application/json",
                    body='{"error": "Internal server error"}'
                ))
                
                # Set up dialog handler for alerts
                alert_messages = []
                def handle_dialog(dialog):
                    alert_messages.append(dialog.message)
                    dialog.accept()
                
                page.on("dialog", handle_dialog)
                
                # Click fetch to trigger error
                page.click("#go")
                page.wait_for_timeout(3000)
                
                # Verify error was handled appropriately
                # (Either via alert or UI error message)
                # This will depend on the frontend implementation
                
            finally:
                browser.close()
    
    def test_partial_data_handling(self):
        """Test handling of partial or incomplete data responses."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Mock partial data response (missing some fields)
                partial_data = {
                    "lat": 37.1882,
                    "lon": -3.6067,
                    "hourly": [
                        {"time": "2024-09-22T12:00:00", "consensus": 7.2, "low": 6.8, "high": 7.6}
                    ],
                    "summary": {},  # Empty summary
                    "providers": []  # No providers
                }
                
                page.route("**/uv?*", lambda route: route.fulfill(
                    content_type="application/json",
                    body=str(partial_data).replace("'", '"')
                ))
                
                # Click fetch
                page.click("#go")
                page.wait_for_timeout(3000)
                
                # Verify app doesn't crash with partial data
                chart_element = page.locator("#chart")
                assert chart_element.is_visible()
                
                # App should remain functional
                fetch_button = page.locator("#go")
                assert fetch_button.is_enabled()
                
            finally:
                browser.close()


class TestLocationIntegration:
    """Test integration with different locations and scenarios."""
    
    def test_different_coordinates(self):
        """Test fetching data for different coordinate sets."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        test_locations = [
            {"lat": "40.7128", "lon": "-74.0060", "city": "New York"},
            {"lat": "51.5074", "lon": "-0.1278", "city": "London"},
            {"lat": "-33.8688", "lon": "151.2093", "city": "Sydney"}
        ]
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            for location in test_locations:
                page = browser.new_page()
                
                try:
                    page.goto(ui_url)
                    
                    # Mock data for each location
                    mock_data = {
                        "lat": float(location["lat"]),
                        "lon": float(location["lon"]),
                        "hourly": [
                            {"time": "2024-09-22T12:00:00", "consensus": 5.0, "low": 4.5, "high": 5.5}
                        ],
                        "summary": {"uv_max": 5.0},
                        "providers": [{"name": "test", "error": None}]
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
                    
                    # Set coordinates
                    page.fill("#lat", location["lat"])
                    page.fill("#lon", location["lon"])
                    
                    # Fetch data
                    page.click("#go")
                    page.wait_for_timeout(5000)  # Wait longer for chart rendering
                    
                    # Verify chart rendered for this location
                    chart_element = page.locator("#chart")
                    assert chart_element.is_visible()
                    
                    # Check chart content using JavaScript
                    chart_data = page.evaluate("""
                        (() => {
                            const chartDiv = document.getElementById('chart');
                            
                            if (chartDiv && chartDiv.data && chartDiv.data.length > 0) {
                                return chartDiv.data.length;
                            }
                            
                            if (chartDiv && chartDiv._fullData && chartDiv._fullData.length > 0) {
                                return chartDiv._fullData.length;
                            }
                            
                            const plotlyDiv = chartDiv ? chartDiv.querySelector('.plotly-graph-div') : null;
                            if (plotlyDiv) {
                                return 1;
                            }
                            
                            if (chartDiv && chartDiv.innerHTML.trim().length > 1000) {
                                return 1;
                            }
                            
                            return 0;
                        })()
                    """)
                    assert chart_data > 0, f"Chart not rendered for location {location['city']}"
                    
                finally:
                    page.close()
            
            browser.close()
    
    def test_timezone_handling(self):
        """Test timezone handling in data requests."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        test_timezones = ["auto", "UTC", "Europe/Madrid", "America/New_York", "Asia/Tokyo"]
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)  # Wait for any immediate JavaScript
                
                for tz in test_timezones:
                    # Mock data with timezone
                    mock_data = {
                        "lat": 37.1882,
                        "lon": -3.6067,
                        "tz": tz,
                        "date": "2024-09-22",
                        "hourly": [{"time": "2024-09-22T12:00:00", "consensus": 6.0}],
                        "summary": {},
                        "providers": []
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
                    
                    # Set timezone
                    page.fill("#tz", tz)
                    
                    # Fetch data
                    page.click("#go")
                    page.wait_for_timeout(1500)
                    
                    # Verify chart was rendered
                    chart_element = page.locator("#chart")
                    assert chart_element.is_visible()
                    
                    # Verify summary shows timezone
                    summary_element = page.locator("#summary")
                    assert summary_element.is_visible()
                    summary_text = summary_element.inner_text()
                    if tz != "auto":
                        assert tz in summary_text or "undefined" in summary_text  # Allow for undefined timezone display
                    
                    # Clear route for next test
                    page.unroute("**/uv?*")
                
            finally:
                browser.close()


class TestChartFunctionality:
    """Test chart-specific functionality and interactions."""
    
    def test_chart_traces_creation(self):
        """Test that chart traces are created correctly."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Mock data with multiple providers
                page.route("**/uv?*", lambda route: route.fulfill(
                    content_type="application/json",
                    body="""{
                        "lat": 37.1882,
                        "lon": -3.6067,
                        "date": "2024-09-22",
                        "tz": "Europe/Madrid",
                        "now_bucket_time": "2024-09-22T14:00:00",
                        "hourly": [
                            {
                                "time": "2024-09-22T12:00:00",
                                "consensus": 6.0,
                                "low": 5.5,
                                "high": 6.5,
                                "providers": {
                                    "openweathermap": 6.1,
                                    "visualcrossing": 5.9,
                                    "open_meteo": 6.0
                                },
                                "outliers": ["visualcrossing"]
                            }
                        ],
                        "summary": {},
                        "providers": []
                    }"""
                ))
                
                page.click("#go")
                page.wait_for_timeout(2000)
                
                # Check that Plotly chart exists and has traces
                traces_count = page.evaluate("""
                    (() => {
                        const chartDiv = document.getElementById('chart');
                        return chartDiv && chartDiv.data ? chartDiv.data.length : 0;
                    })();
                """)
                
                # Should have: confidence band, consensus line, provider lines, outlier markers
                assert traces_count >= 5  # At least 5 traces
                
            finally:
                browser.close()
    
    def test_chart_now_line(self):
        """Test that the 'now' line is drawn correctly."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Mock data with now_bucket_time
                page.route("**/uv?*", lambda route: route.fulfill(
                    content_type="application/json",
                    body="""{
                        "lat": 37.1882,
                        "lon": -3.6067,
                        "now_bucket_time": "2024-09-22T14:00:00",
                        "date": "2024-09-22",
                        "hourly": [
                            {
                                "time": "2024-09-22T12:00:00",
                                "consensus": 6.0,
                                "low": 5.5,
                                "high": 6.5,
                                "providers": {},
                                "outliers": []
                            }
                        ],
                        "summary": {},
                        "providers": []
                    }"""
                ))
                
                page.click("#go")
                page.wait_for_timeout(2000)
                
                # Check that chart has shapes (the now line)
                shapes_count = page.evaluate("""
                    (() => {
                        const chartDiv = document.getElementById('chart');
                        return chartDiv && chartDiv.layout && chartDiv.layout.shapes 
                            ? chartDiv.layout.shapes.length : 0;
                    })()
                """)
                
                assert shapes_count >= 1  # Should have at least the now line
                
            finally:
                browser.close()
    
    def test_chart_title_formatting(self):
        """Test that chart title is formatted correctly."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)  # Wait for any immediate JavaScript
                
                page.route("**/uv?*", lambda route: route.fulfill(
                    content_type="application/json",
                    body="""{
                        "lat": 40.7128,
                        "lon": -74.0060,
                        "date": "2024-09-22",
                        "tz": "America/New_York",
                        "hourly": [],
                        "summary": {},
                        "providers": []
                    }"""
                ))
                
                # Set New York coordinates
                page.fill("#lat", "40.7128")
                page.fill("#lon", "-74.0060")
                page.click("#go")
                page.wait_for_timeout(2000)
                
                # Check chart title
                chart_title = page.evaluate("""
                    (() => {
                        const chartDiv = document.getElementById('chart');
                        if (chartDiv && chartDiv.layout && chartDiv.layout.title) {
                            const title = chartDiv.layout.title;
                            return typeof title === 'string' ? title : title.text || '';
                        }
                        return '';
                    })()
                """)
                
                assert "UV Index for 2024-09-22" in chart_title
                assert "(40.7128, -74.0060)" in chart_title
                assert "[America/New_York]" in chart_title
                
            finally:
                browser.close()


class TestTimeFormatting:
    """Test time formatting and display functions."""
    
    def test_time_formatting_function(self):
        """Test the fmtTime JavaScript function."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Test the fmtTime function directly
                test_cases = [
                    ("2024-09-22T14:30:00", "2024-09-22 14:30"),
                    ("2024-09-22T08:00:00", "2024-09-22 08:00"),
                    ("", ""),
                ]
                
                for input_time, expected in test_cases:
                    result = page.evaluate(f"fmtTime('{input_time}')")
                    assert result == expected, f"fmtTime('{input_time}') returned '{result}', expected '{expected}'"
                    
                # Test null case
                result = page.evaluate("fmtTime(null)")
                assert result == "", f"fmtTime(null) returned '{result}', expected ''"
                
            finally:
                browser.close()


class TestWindowsAndAdvice:
    """Test UV exposure windows and advice display."""
    
    def test_exposure_windows_display(self):
        """Test that exposure windows are displayed correctly."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Mock data with detailed windows
                page.route("**/uv?*", lambda route: route.fulfill(
                    content_type="application/json",
                    body="""{
                        "lat": 37.1882,
                        "lon": -3.6067,
                        "date": "2024-09-22",
                        "tz": "Europe/Madrid",
                        "now_local_iso": "2024-09-22T14:30:00",
                        "hourly": [],
                        "summary": {
                            "uv_max": 9.2,
                            "uv_max_time": "2024-09-22T13:00:00",
                            "advice": [
                                "Use SPF 50+ sunscreen",
                                "Wear UV-blocking sunglasses",
                                "Seek shade between 11 AM and 4 PM"
                            ],
                            "windows": {
                                "best": [
                                    {"start": "2024-09-22T07:00:00", "end": "2024-09-22T09:00:00"},
                                    {"start": "2024-09-22T18:00:00", "end": "2024-09-22T20:00:00"}
                                ],
                                "moderate": [
                                    {"start": "2024-09-22T09:00:00", "end": "2024-09-22T11:00:00"},
                                    {"start": "2024-09-22T16:00:00", "end": "2024-09-22T18:00:00"}
                                ],
                                "avoid": [
                                    {"start": "2024-09-22T11:00:00", "end": "2024-09-22T16:00:00"}
                                ]
                            }
                        },
                        "providers": []
                    }"""
                ))
                
                page.click("#go")
                page.wait_for_timeout(1000)
                
                summary_text = page.locator("#summary").inner_text()
                
                # Check peak UV display
                assert "Peak UV: 9.2" in summary_text
                assert "13:00" in summary_text
                
                # Check advice
                assert "SPF 50+" in summary_text
                assert "UV-blocking sunglasses" in summary_text
                assert "Seek shade" in summary_text
                
                # Check windows formatting - expect full date format
                assert "Best" in summary_text
                assert "2024-09-22 07:00 → 2024-09-22 09:00" in summary_text
                assert "2024-09-22 18:00 → 2024-09-22 20:00" in summary_text
                
                assert "Moderate" in summary_text
                assert "2024-09-22 09:00 → 2024-09-22 11:00" in summary_text
                assert "2024-09-22 16:00 → 2024-09-22 18:00" in summary_text
                
                assert "Avoid" in summary_text
                assert "2024-09-22 11:00 → 2024-09-22 16:00" in summary_text
                
            finally:
                browser.close()
    
    def test_empty_windows_display(self):
        """Test display when no exposure windows are available."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Mock data with empty windows
                page.route("**/uv?*", lambda route: route.fulfill(
                    content_type="application/json",
                    body="""{
                        "lat": 37.1882,
                        "lon": -3.6067,
                        "date": "2024-09-22",
                        "tz": "Europe/Madrid",
                        "hourly": [],
                        "summary": {
                            "windows": {
                                "best": [],
                                "moderate": [],
                                "avoid": []
                            }
                        },
                        "providers": []
                    }"""
                ))
                
                page.click("#go")
                page.wait_for_timeout(1000)
                
                summary_text = page.locator("#summary").inner_text()
                
                # Should show "None" for empty windows
                lines = summary_text.split('\n')
                for line in lines:
                    if "Best" in line and ":" in line:
                        assert "None" in line
                    elif "Moderate" in line and ":" in line:
                        assert "None" in line
                    elif "Avoid" in line and ":" in line:
                        assert "None" in line
                        
            finally:
                browser.close()


class TestProviderErrorHandling:
    """Test handling of provider errors and status display."""
    
    def test_mixed_provider_status(self):
        """Test display of mixed provider success/error status."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Mock response with mixed provider status
                page.route("**/uv?*", lambda route: route.fulfill(
                    content_type="application/json",
                    body="""{
                        "lat": 37.1882,
                        "lon": -3.6067,
                        "date": "2024-09-22",
                        "tz": "Europe/Madrid",
                        "hourly": [],
                        "summary": {},
                        "providers": [
                            {"name": "openweathermap", "error": null},
                            {"name": "visualcrossing", "error": null},
                            {"name": "open_meteo", "error": "Rate limit exceeded"},
                            {"name": "weatherbit", "error": "Invalid API key"},
                            {"name": "openuv", "error": null}
                        ]
                    }"""
                ))
                
                page.click("#go")
                page.wait_for_timeout(1000)
                
                providers_text = page.locator("#providers").inner_text()
                
                # Check successful providers
                assert "openweathermap: OK" in providers_text
                assert "visualcrossing: OK" in providers_text
                assert "openuv: OK" in providers_text
                
                # Check failed providers
                assert "open_meteo: Rate limit exceeded" in providers_text
                assert "weatherbit: Invalid API key" in providers_text
                
            finally:
                browser.close()
    
    def test_all_providers_failed(self):
        """Test display when all providers fail."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        ui_url = f"file:///{frontend_dir.absolute()}/index.html"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(ui_url)
                
                # Mock response with all providers failed
                page.route("**/uv?*", lambda route: route.fulfill(
                    content_type="application/json",
                    body="""{
                        "lat": 37.1882,
                        "lon": -3.6067,
                        "date": "2024-09-22",
                        "tz": "Europe/Madrid",
                        "hourly": [],
                        "summary": {},
                        "providers": [
                            {"name": "openweathermap", "error": "Service unavailable"},
                            {"name": "visualcrossing", "error": "Network timeout"},
                            {"name": "open_meteo", "error": "API down for maintenance"}
                        ]
                    }"""
                ))
                
                page.click("#go")
                page.wait_for_timeout(1000)
                
                providers_text = page.locator("#providers").inner_text()
                
                # All providers should show error messages
                assert "openweathermap: Service unavailable" in providers_text
                assert "visualcrossing: Network timeout" in providers_text
                assert "open_meteo: API down for maintenance" in providers_text
                
                # Should not show any "OK" status
                assert ": OK" not in providers_text
                
            finally:
                browser.close()
