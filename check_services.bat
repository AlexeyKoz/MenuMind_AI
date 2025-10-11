@echo off
echo ============================================
echo  MenuMind AI - Service Status Check
echo ============================================
echo.

echo Checking service status...
echo.

REM Check Redis
echo [1/4] Redis Server (Port 6379) - Optional
netstat -an | findstr :6379 | findstr LISTENING > nul
if %ERRORLEVEL% == 0 (
    echo     ✅ RUNNING on port 6379
) else (
    echo     ❌ NOT RUNNING
    echo        Start with: start_fullstack.bat
)
echo.

REM Check Django/Daphne
echo [2/4] Django Backend - Daphne ASGI Server (Port 8000)
netstat -an | findstr :8000 | findstr LISTENING > nul
if %ERRORLEVEL% == 0 (
    echo     ✅ RUNNING on port 8000
    echo        Try: curl http://localhost:8000/health/
) else (
    echo     ❌ NOT RUNNING
    echo        Start with: start_fullstack.bat
)
echo.

REM Check React Frontend
echo [3/4] React Frontend (Port 3000)
netstat -an | findstr :3000 | findstr LISTENING > nul
if %ERRORLEVEL% == 0 (
    echo     ✅ RUNNING on port 3000
    echo        Open: http://localhost:3000
) else (
    echo     ❌ NOT RUNNING
    echo        Start with: start_fullstack.bat
)
echo.

REM Check Test Server
echo [4/4] Test HTTP Server (Port 8001)
netstat -an | findstr :8001 | findstr LISTENING > nul
if %ERRORLEVEL% == 0 (
    echo     ✅ RUNNING on port 8001
    echo        Open: http://localhost:8001/test_backend.html
) else (
    echo     ⚠️  NOT RUNNING (optional service)
)
echo.

echo ============================================
echo  Quick Actions
echo ============================================
echo.
echo To START all services:    start_fullstack.bat
echo To STOP all services:     stop_servers.bat
echo To CHECK logs:            Look at the CMD windows
echo.
echo ============================================
pause

