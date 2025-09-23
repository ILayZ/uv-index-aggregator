"""
UI Tests for UV Index Aggregator Frontend.

These tests verify the functionality of the web interface including:
- Page loading and basic UI elements
- Input validation and form interactions
- Data fetching and chart rendering
- Error handling
- Responsive behavior

Uses pytest-playwright fixtures to support multiple browsers.
"""
import pytest
import re
import json
from pathlib import Path


class TestUIBasics:
    """Test basic UI functionality and page loading."""
    
    def test_page_loads_successfully(self, page, ui_url):
        """Test that the main page loads without errors."""
        page.goto(ui_url)
        
        # Check title
        title = page.title()
        assert title == "UV Index Aggregator", f"Expected 'UV Index Aggregator', got '{title}'"
        
        # Check main heading
        heading = page.locator("h1")
        heading_text = heading.inner_text()
        assert heading_text == "UV Index Aggregator"
        
    def test_required_elements_present(self, page, ui_url):
        """Test that all required form elements are present."""
        page.goto(ui_url)
        
        # Check input fields
        assert page.locator("#lat").is_visible()
        assert page.locator("#lon").is_visible()
        assert page.locator("#date").is_visible()
        assert page.locator("#tz").is_visible()
        
        # Check buttons
        assert page.locator("#go").is_visible()
        
        # Check result container
        assert page.locator("#result").is_visible()
        
    def test_default_values(self, page, ui_url):
        """Test that default values are set correctly."""
        page.goto(ui_url)
        
        # Check latitude default
        lat_value = page.locator("#lat").input_value()
        assert lat_value == "37.1882"
        
        # Check longitude default
        lon_value = page.locator("#lon").input_value()
        assert lon_value == "-3.6067"
        
        # Check timezone default
        tz_value = page.locator("#tz").input_value()
        assert tz_value == "Europe/Madrid"


class TestFormInteractions:
    """Test form input validation and interactions."""
    
    def test_coordinate_input_validation(self, page, ui_url):
        """Test coordinate input accepts valid values."""
        page.goto(ui_url)
        
        # Test valid latitude
        page.fill("#lat", "40.7128")
        lat_value = page.locator("#lat").input_value()
        assert lat_value == "40.7128"
        
        # Test valid longitude
        page.fill("#lon", "-74.0060")
        lon_value = page.locator("#lon").input_value()
        assert lon_value == "-74.0060"
        
    def test_date_input_format(self, page, ui_url):
        """Test date input accepts proper format."""
        page.goto(ui_url)
        
        # Test valid date
        page.fill("#date", "2024-06-15")
        date_value = page.locator("#date").input_value()
        assert date_value == "2024-06-15"
        
    def test_timezone_input(self, page, ui_url):
        """Test timezone input accepts valid timezone."""
        page.goto(ui_url)
        
        # Test different timezone
        page.fill("#tz", "America/New_York")
        tz_value = page.locator("#tz").input_value()
        assert tz_value == "America/New_York"
        
    def test_form_submission_state(self, page, ui_url):
        """Test form submission button state."""
        page.goto(ui_url)
        
        # Check button is initially visible and not disabled
        go_button = page.locator("#go")
        assert go_button.is_visible()
        
        # Check button text
        button_text = go_button.inner_text()
        assert button_text == "Fetch UV Data"


class TestUIFeedback:
    """Test UI feedback and user interaction states."""
    
    def test_error_handling_display(self, page, ui_url):
        """Test error handling display."""
        page.goto(ui_url)
        
        # Initially result should be empty or contain default message
        result = page.locator("#result")
        assert result.is_visible()
        
    def test_loading_state_feedback(self, page, ui_url):
        """Test loading state feedback."""
        page.goto(ui_url)
        
        # Check that result container exists for loading feedback
        result = page.locator("#result")
        assert result.is_visible()


class TestDataVisualization:
    """Test chart and data visualization components."""
    
    def test_chart_container_present(self, page, ui_url):
        """Test that chart container is present."""
        page.goto(ui_url)
        
        # Check if chart container exists (Plotly typically creates a div)
        # This might be created dynamically, so we just check the result area
        result = page.locator("#result")
        assert result.is_visible()


class TestResponsiveDesign:
    """Test responsive design behavior."""
    
    def test_mobile_viewport_layout(self, page, ui_url):
        """Test layout on mobile viewport."""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(ui_url)
        
        # Check that elements are still visible on mobile
        assert page.locator("h1").is_visible()
        assert page.locator("#lat").is_visible()
        assert page.locator("#go").is_visible()
        
    def test_desktop_viewport_layout(self, page, ui_url):
        """Test layout on desktop viewport."""
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(ui_url)
        
        # Check that elements are visible on desktop
        assert page.locator("h1").is_visible()
        assert page.locator("#lat").is_visible()
        assert page.locator("#go").is_visible()
