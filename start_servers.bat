@echo off
echo Starting MenuMind AI Development Servers...
echo.

echo Starting Django Backend Server (Port 8000)...
start "Django Backend" cmd /k "cd backend && python manage.py runserver 0.0.0.0:8000"

echo Waiting 5 seconds for Django to start...
timeout /t 5 /nobreak > nul

echo Starting HTTP Server for Test Page (Port 8001)...
start "HTTP Server" cmd /k "python -m http.server 8001"

echo Waiting 3 seconds for HTTP server to start...
timeout /t 3 /nobreak > nul

echo.
echo ============================================
echo   MenuMind AI Servers Started!
echo ============================================
echo   Backend (Django):  http://localhost:8000
echo   Test Page:         http://localhost:8001/test_backend.html
echo   Original Test:     http://localhost:8001/test_api.html
echo ============================================
echo.

echo Opening test page in browser...
start http://localhost:8001/test_backend.html

echo.
echo Press any key to exit...
pause > nul
