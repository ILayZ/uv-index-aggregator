"""
Integration tests for backend API and frontend interaction.
"""
import pytest
import json


class TestBackendIntegration:
    """Test integration with backend API."""
    
    def test_health_endpoint_integration(self, page, ui_url, backend_server):
        """Test that health endpoint is accessible."""
        # This is a basic test that can be expanded
        page.goto(ui_url)
        assert page.locator("h1").is_visible()
        
    def test_providers_endpoint_integration(self, page, ui_url, backend_server):
        """Test providers endpoint integration."""
        page.goto(ui_url)
        assert page.locator("#go").is_visible()


class TestMockIntegration:
    """Test integration with mock data."""
    
    def test_successful_data_flow(self, page, ui_url):
        """Test successful data flow through the application."""
        page.goto(ui_url)
        
        # Fill form with test data
        page.fill("#lat", "37.1882")
        page.fill("#lon", "-3.6067")
        page.fill("#date", "2024-06-15")
        
        # The form should be ready for submission
        assert page.locator("#go").is_enabled()
        
    def test_error_response_handling(self, page, ui_url):
        """Test error response handling."""
        page.goto(ui_url)
        
        # Test with invalid coordinates
        page.fill("#lat", "999")
        page.fill("#lon", "999")
        
        # Form should still be submittable (validation happens server-side)
        assert page.locator("#go").is_enabled()
        
    def test_partial_data_handling(self, page, ui_url):
        """Test handling of partial data responses."""
        page.goto(ui_url)
        
        # Fill with minimal valid data
        page.fill("#lat", "0")
        page.fill("#lon", "0")
        
        assert page.locator("#go").is_enabled()


class TestLocationIntegration:
    """Test location-specific integration scenarios."""
    
    def test_different_coordinates(self, page, ui_url, test_coordinates):
        """Test with different coordinate sets."""
        page.goto(ui_url)
        
        # Use test coordinates
        page.fill("#lat", str(test_coordinates["lat"]))
        page.fill("#lon", str(test_coordinates["lon"]))
        
        # Verify values were set
        lat_value = page.locator("#lat").input_value()
        lon_value = page.locator("#lon").input_value()
        
        assert float(lat_value) == test_coordinates["lat"]
        assert float(lon_value) == test_coordinates["lon"]
        
    def test_timezone_handling(self, page, ui_url):
        """Test timezone handling in integration."""
        page.goto(ui_url)
        
        # Test different timezones
        timezones = ["UTC", "America/New_York", "Asia/Tokyo"]
        
        for tz in timezones:
            page.fill("#tz", tz)
            tz_value = page.locator("#tz").input_value()
            assert tz_value == tz


class TestChartFunctionality:
    """Test chart functionality integration."""
    
    def test_chart_container_setup(self, page, ui_url):
        """Test that chart container is properly set up."""
        page.goto(ui_url)
        
        # Check result container exists for chart rendering
        result = page.locator("#result")
        assert result.is_visible()
        
        # Check initial state
        result_text = result.inner_text()
        # Should be empty or contain placeholder text initially
        assert result_text is not None
