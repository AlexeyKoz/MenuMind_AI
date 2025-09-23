@echo off
echo Starting MenuMind AI - Complete Development Environment...
echo.

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
echo Press any key to exit...
pause > nul
