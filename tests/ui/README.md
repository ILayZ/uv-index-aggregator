# UI Tests for UV Index Aggregator

This directory contains comprehensive UI tests for the UV Index Aggregator frontend application using Playwright.

## Overview

The UI test suite covers:
- **Basic UI functionality** - Page loading, element presence, form interactions
- **Data fetching and rendering** - Chart creation, API integration, error handling  
- **Visual regression testing** - Layout consistency, responsive design
- **Accessibility testing** - Keyboard navigation, semantic HTML
- **Performance testing** - Load times, chart rendering performance
- **Cross-browser compatibility** - Chromium, Firefox, WebKit

## Test Structure

```
tests/ui/
├── conftest.py              # Test configuration and fixtures
├── test_frontend.py         # Core UI functionality tests
├── test_integration.py      # Backend integration tests
├── test_visual.py          # Visual regression tests
├── test_utils.py           # Test utilities and helpers
└── screenshots/            # Generated screenshots for visual tests
```

## Test Categories

### Basic UI Tests (`test_frontend.py`)
- **TestUIBasics**: Page loading, element presence, default values
- **TestFormInteractions**: Input validation, form behavior
- **TestDataFetching**: API calls, chart rendering, data display
- **TestErrorHandling**: Network errors, API errors, invalid responses
- **TestResponsiveDesign**: Mobile/tablet viewports
- **TestAccessibility**: Keyboard navigation, ARIA labels
- **TestPerformance**: Load times, rendering performance

### Integration Tests (`test_integration.py`)
- **TestBackendIntegration**: Real API calls to backend services
- **TestChartFunctionality**: Chart traces, legends, axes
- **TestTimeFormatting**: Time display functions
- **TestWindowsAndAdvice**: UV exposure windows, safety advice
- **TestProviderErrorHandling**: Provider status display

### Visual Tests (`test_visual.py`)
- **TestVisualRegression**: Screenshot comparison, layout verification
- **TestCrossBrowserVisual**: Cross-browser consistency
- **TestChartVisuals**: Chart appearance, legend formatting

## Installation

1. Install test dependencies:
```bash
pip install playwright pytest-playwright pytest-asyncio pytest-html pytest-cov
```

2. Install Playwright browsers:
```bash
playwright install
```

## Running Tests

### Using the test runner script:
```bash
# Run all UI tests
python run_ui_tests.py --type ui

# Run with specific browser
python run_ui_tests.py --browser firefox --headed

# Run integration tests only
python run_ui_tests.py --type integration

# Run with coverage and HTML report
python run_ui_tests.py --coverage --html-report
```

### Using pytest directly:
```bash
# All UI tests
pytest tests/ui/ --browser chromium

# Specific test file
pytest tests/ui/test_frontend.py -v

# Headed mode (show browser)
pytest tests/ui/ --headed

# Generate HTML report
pytest tests/ui/ --html=report.html --self-contained-html
```

## Test Configuration

Configuration is managed through `pyproject.toml`:
- Default browser: Chromium
- Headless mode: True
- Screenshots on failure: Yes
- Video recording: On failure only
- Timeout: 30 seconds

## Fixtures

### Core Fixtures (`conftest.py`)
- `backend_server`: Starts backend server for integration tests
- `ui_url`: Frontend file URL
- `test_coordinates`: Default test coordinates (Granada, Spain)

### Test Utilities (`test_utils.py`)
- `TestDataBuilder`: Builder pattern for creating test data
- `UITestHelpers`: Common UI interaction helpers
- Pre-defined test scenarios and coordinate sets

## Writing New Tests

### Basic Test Structure
```python
async def test_my_feature(page: Page, ui_url: str):
    await page.goto(ui_url)
    
    # Test interactions
    await page.click("#my-button")
    
    # Assertions
    await expect(page.locator("#result")).to_be_visible()
```

### Using Test Utilities
```python
from tests.ui.test_utils import TestDataBuilder, UITestHelpers

async def test_with_mock_data(page: Page, ui_url: str):
    # Build test data
    data = (TestDataBuilder()
            .with_coordinates(40.7128, -74.0060)
            .with_hourly_data(hours=12)
            .with_summary()
            .build())
    
    # Mock API response
    await UITestHelpers.mock_api_response(page, "/uv*", data)
    
    # Test functionality
    await UITestHelpers.fill_coordinates(page, 40.7128, -74.0060)
    await UITestHelpers.trigger_fetch(page)
    await UITestHelpers.wait_for_chart_render(page)
```

### Visual Regression Tests
```python
async def test_visual_consistency(page: Page, ui_url: str):
    await page.goto(ui_url)
    
    # Setup state
    await page.fill("#lat", "37.1882")
    
    # Take screenshot
    await page.screenshot(path="screenshots/my_test.png")
    
    # Compare with baseline (manual process)
```

## Continuous Integration

The UI tests run automatically on:
- Push to main/develop branches
- Pull requests to main
- Multiple browsers (Chromium, Firefox, WebKit)

CI workflow includes:
- Backend server startup
- Playwright browser installation
- Test execution with coverage
- Artifact upload (reports, screenshots)
- Lighthouse performance audits

## Debugging Tests

### Local Debugging
```bash
# Run in headed mode to see browser
pytest tests/ui/test_frontend.py::test_name --headed

# Enable verbose output
pytest tests/ui/ -v -s

# Run single test with debug
pytest tests/ui/test_frontend.py::test_name --pdb
```

### Debug Screenshots
Screenshots are automatically taken on test failures and saved to `tests/ui/screenshots/`.

### Common Issues
1. **Backend not available**: Ensure backend server is running on port 8080
2. **Timing issues**: Increase wait times for slow chart rendering
3. **Element not found**: Check selectors match HTML structure
4. **Browser crashes**: Update Playwright browsers

## Performance Considerations

- Tests run in parallel by default
- Use `page.route()` for mocking to avoid real API calls
- Screenshots and videos only captured on failures
- Lighthouse audits run separately to avoid interference

## Best Practices

1. **Use data-testid attributes** for stable selectors
2. **Mock external dependencies** to avoid flaky tests
3. **Test user workflows** rather than implementation details
4. **Keep tests independent** - each test should set up its own state
5. **Use meaningful assertions** that reflect user expectations
6. **Organize tests by feature** rather than by type of assertion

## Future Enhancements

- [ ] Add visual diff comparison tools
- [ ] Implement page object model pattern
- [ ] Add mobile device simulation tests
- [ ] Integrate with accessibility testing tools
- [ ] Add database state verification for integration tests
