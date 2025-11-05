@echo off
REM ============================================
REM Logo Management System - Test Runner
REM ============================================

echo.
echo ========================================
echo  LOGO SYSTEM - COMPREHENSIVE TESTS
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install required Python packages
echo [1/5] Installing test dependencies...
pip install requests colorama --quiet

REM Check if backend is running
echo.
echo [2/5] Checking if backend is running...
curl -s http://localhost:8000/health/ >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Backend is not running at http://localhost:8000
    echo Please start the backend first using:
    echo   docker-compose -f docker-compose.prod.yml up -d
    echo   OR
    echo   start_fullstack_complete.bat
    echo.
    pause
    exit /b 1
)

REM Run backend tests
echo.
echo [3/5] Running backend tests...
docker exec menumine_backend_prod python manage.py test branding --verbosity=2
if %errorlevel% neq 0 (
    echo WARNING: Backend tests failed or container not running
    echo Continuing with API tests...
)

REM Run API/E2E tests
echo.
echo [4/5] Running end-to-end API tests...
python test_logo_system.py --verbose

REM Run frontend tests (if Jest is available)
echo.
echo [5/5] Running frontend tests...
cd frontend
if exist "node_modules\.bin\jest.cmd" (
    npm test -- logoService.test.ts --passWithNoTests
    cd ..
) else (
    echo INFO: Jest not found, skipping frontend tests
    echo To run frontend tests: cd frontend && npm test
    cd ..
)

echo.
echo ========================================
echo  ALL TESTS COMPLETE
echo ========================================
echo.
echo Next steps:
echo   1. Review test results above
echo   2. If tests failed, check:
echo      - Backend is running
echo      - Logos are uploaded via admin
echo      - Database migrations applied
echo   3. Run specific tests:
echo      - Backend: docker exec menumine_backend_prod python manage.py test branding
echo      - API: python test_logo_system.py
echo      - Frontend: cd frontend ^&^& npm test
echo.

pause

