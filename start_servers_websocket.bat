@echo off
echo ===================================
echo Starting MenuMine AI with WebSocket Support
echo ===================================
echo.

REM Start backend with Daphne (ASGI server for WebSocket support)
echo [1/2] Starting Django Backend with Daphne (WebSocket enabled)...
start "Django Backend (Daphne)" cmd /k "cd backend && daphne -b 0.0.0.0 -p 8000 menumine_ai.asgi:application"
timeout /t 3 /nobreak >nul

REM Start frontend
echo [2/2] Starting React Frontend...
start "React Frontend" cmd /k "cd frontend && npm start"
timeout /t 2 /nobreak >nul

echo.
echo ===================================
echo ✅ All servers started!
echo ===================================
echo Backend (with WebSocket): http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo WebSocket endpoints:
echo - Shopping List: ws://localhost:8000/ws/shopping/{list_id}/
echo - User Notifications: ws://localhost:8000/ws/user/notifications/
echo.
echo Press any key to exit (servers will keep running)...
pause >nul

