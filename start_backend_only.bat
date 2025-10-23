@echo off
REM ============================================================
REM MenuMine AI - Backend Only Startup Script
REM ============================================================
REM This script starts ONLY the backend Django server
REM Use this when you only need to work on backend APIs
REM ============================================================

echo ============================================================
echo    MenuMine AI - Starting Backend Server
echo ============================================================
echo.

REM Change to backend directory
cd backend

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run the full setup first or create venv manually.
    echo.
    pause
    exit /b 1
)

echo [1/3] Activating Python virtual environment...
call venv\Scripts\activate.bat

echo [2/3] Checking environment variables...
if not exist ".env" (
    echo [WARNING] .env file not found! Please create one with your API keys.
    echo.
)

echo [3/3] Starting Django development server...
echo.
echo ============================================================
echo    Backend Server Starting on http://localhost:8000
echo ============================================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start Django server
python manage.py runserver

REM If server stops, pause to see any error messages
echo.
echo Backend server stopped.
pause

