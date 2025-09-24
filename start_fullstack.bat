@echo off
echo Starting MenuMind AI - Complete Development Environment...
echo.

echo [0/4] Verifying ASGI configuration...
findstr /C:"from apps.shopping.user_consumer import UserNotificationConsumer" backend\menumine_ai\asgi.py | findstr /N "^[1-9]:" > nul
if %ERRORLEVEL% == 0 (
    echo.
    echo ================================= WARNING =================================
    echo  CRITICAL ERROR: ASGI imports are in wrong order!
    echo  Consumer imports MUST be AFTER Django initialization!
    echo  
    echo  The file backend\menumine_ai\asgi.py has consumer imports at the top.
    echo  This will cause the application to crash on startup.
    echo  
    echo  Please ensure consumer imports come AFTER get_asgi_application^(^)
    echo ========================================================================
    echo.
    echo Press any key to continue anyway, or Ctrl+C to abort and fix the file...
    pause
    echo.
)

echo [1/4] Starting Django Backend Server with ASGI/WebSocket support (Port 8000)...
start "Django Backend" cmd /k "cd backend && daphne -b 0.0.0.0 -p 8000 menumine_ai.asgi:application"

echo [2/4] Waiting 5 seconds for Django to start...
timeout /t 5 /nobreak > nul

echo [3/4] Starting React Frontend (Port 3000)...
start "React Frontend" cmd /k "cd frontend && npm start"

echo [4/4] Starting Test Page Server (Port 8001)...
start "HTTP Server" cmd /k "python -m http.server 8001"

echo Waiting 8 seconds for all servers to start...
timeout /t 8 /nobreak > nul

echo.
echo ============================================
echo    MenuMind AI - Full Stack Running!
echo ============================================
echo   Frontend (React):     http://localhost:3000
echo   Backend (Django):     http://localhost:8000  
echo   Test Dashboard:       http://localhost:8001/test_backend.html
echo   Admin Panel:          http://localhost:8000/admin/
echo ============================================
echo.

echo Opening applications in browser...
start http://localhost:3000
timeout /t 2 /nobreak > nul
start http://localhost:8001/test_backend.html

echo.
echo ============================================
echo      Server Management Options
echo ============================================
echo Press 'S' to stop all servers and exit
echo Press 'R' to restart all servers  
echo Press any other key to keep servers running and exit
echo ============================================
choice /C SR /N /M "Your choice (S/R): "

if %ERRORLEVEL% == 1 (
    echo.
    echo Stopping all servers...
    echo Stopping Django backend servers...
    taskkill /F /IM python.exe /T 2>nul
    echo Stopping Node.js frontend servers...
    taskkill /F /IM node.exe /T 2>nul
    echo Stopping Command Prompt windows...
    taskkill /F /IM cmd.exe /FI "WINDOWTITLE eq Django Backend*" 2>nul
    taskkill /F /IM cmd.exe /FI "WINDOWTITLE eq React Frontend*" 2>nul
    taskkill /F /IM cmd.exe /FI "WINDOWTITLE eq HTTP Server*" 2>nul
    echo All servers stopped.
    timeout /t 2 /nobreak > nul
    exit /b 0
)

if %ERRORLEVEL% == 2 (
    echo.
    echo Restarting all servers...
    echo Stopping existing servers...
    taskkill /F /IM python.exe /T 2>nul
    taskkill /F /IM node.exe /T 2>nul
    timeout /t 3 /nobreak > nul
    echo Restarting...
    call "%~f0"
    exit /b 0
)

echo.
echo Servers continue running in background...
echo Use 'stop_servers.bat' to stop them later.
echo.
