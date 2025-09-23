@echo off
REM Test runner script for Windows

set PYTHON_EXE=c:/Users/A63192530/PycharmProjects/uv-index-aggregator/.venv/Scripts/python.exe

if "%1"=="install" (
    echo Installing test dependencies...
    %PYTHON_EXE% -m pip install -r requirements-test.txt
    %PYTHON_EXE% -m playwright install chromium
    echo Test dependencies installed!
    goto end
)

if "%1"=="demo" (
    echo Running UI test demo...
    %PYTHON_EXE% demo_ui_tests.py
    goto end
)

if "%1"=="ui" (
    echo Running UI tests...
    %PYTHON_EXE% simple_ui_tests.py
    goto end
)

if "%1"=="unit" (
    echo Running unit tests...
    %PYTHON_EXE% -m pytest tests/ -k "not ui" -v
    goto end
)

if "%1"=="all" (
    echo Running all tests...
    %PYTHON_EXE% -m pytest tests/ -v
    goto end
)

if "%1"=="coverage" (
    echo Running tests with coverage...
    %PYTHON_EXE% -m pytest tests/ --cov=backend --cov-report=html --cov-report=term-missing -v
    echo Coverage report generated in htmlcov/
    goto end
)

if "%1"=="help" (
    goto help
)

if "%1"=="" (
    goto help
)

echo Unknown command: %1
goto help

:help
echo.
echo UV Index Aggregator Test Runner
echo ================================
echo.
echo Available commands:
echo   install    - Install test dependencies and Playwright browsers
echo   demo       - Run interactive UI test demo
echo   ui         - Run UI tests only  
echo   unit       - Run unit tests only
echo   all        - Run all tests
echo   coverage   - Run tests with coverage report
echo   help       - Show this help message
echo.
echo Examples:
echo   test.bat install
echo   test.bat demo
echo   test.bat ui
echo   test.bat coverage
echo.

:end
