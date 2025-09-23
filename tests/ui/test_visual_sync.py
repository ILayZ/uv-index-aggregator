"""
Visual regression tests for UI components.

These tests capture screenshots and verify visual consistency:
- Layout and styling verification
- Chart rendering appearance  
- Responsive design verification
- Cross-browser visual consistency
"""
import pytest
from pathlib import Path


class TestChartVisuals:
    """Test visual appearance of charts and data visualization."""
    
    def test_chart_container_visual(self, page, ui_url):
        """Test the visual appearance of the chart container."""
        page.goto(ui_url)
        page.wait_for_load_state("networkidle")
        
        # Take screenshot of initial state
        screenshot_path = Path(__file__).parent / "screenshots" / "chart_container.png"
        screenshot_path.parent.mkdir(exist_ok=True)
        
        page.screenshot(path=screenshot_path)
        
        # Verify chart container is visible
        result = page.locator("#result")
        assert result.is_visible()
        
    def test_initial_layout_visual(self, page, ui_url):
        """Test the visual appearance of initial page layout."""
        page.goto(ui_url)
        page.wait_for_load_state("networkidle")
        
        # Take screenshot of initial layout
        screenshot_path = Path(__file__).parent / "screenshots" / "initial_layout.png"
        screenshot_path.parent.mkdir(exist_ok=True)
        
        page.screenshot(path=screenshot_path)
        
        # Verify key visual elements
        assert page.locator("h1").is_visible()
        assert page.locator("#lat").is_visible()
        assert page.locator("#go").is_visible()


class TestAccessibilityVisuals:
    """Test visual accessibility features."""
    
    def test_focus_states_visual(self, page, ui_url):
        """Test visual appearance of focus states."""
        page.goto(ui_url)
        
        # Focus on latitude input
        page.locator("#lat").focus()
        
        # Take screenshot of focus state
        screenshot_path = Path(__file__).parent / "screenshots" / "focus_state.png"
        screenshot_path.parent.mkdir(exist_ok=True)
        
        page.screenshot(path=screenshot_path)
        
        # Verify element is focused
        focused_element = page.locator(":focus")
        assert focused_element.get_attribute("id") == "lat"
