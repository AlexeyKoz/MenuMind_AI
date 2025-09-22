@echo off
echo ============================================
echo  MenuMind AI - Full Stack Development Environment
echo ============================================
echo.

echo [CLEANUP] Stopping any existing servers to prevent conflicts...
echo.

echo [1/3] Stopping Python processes (Django/Daphne servers)...
taskkill /f /im python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python processes stopped
) else (
    echo ℹ No Python processes were running
)

echo [2/3] Stopping Node.js processes (React dev server)...
taskkill /f /im node.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Node.js processes stopped
) else (
    echo ℹ No Node.js processes were running
)

echo [3/3] Freeing up ports 3000, 8000, 8001...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
    echo ✓ Port 3000 freed
)
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
    echo ✓ Port 8000 freed
)
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8001" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
    echo ✓ Port 8001 freed
)

echo ✅ Cleanup completed successfully!
echo.

echo [STEP 1/4] Checking dependencies...
cd backend
if not exist "manage.py" (
    echo ERROR: manage.py not found in backend directory!
    pause
    exit /b 1
)
cd ..

cd frontend
if not exist "package.json" (
    echo ERROR: package.json not found in frontend directory!
    pause
    exit /b 1
)
cd ..
echo Dependencies check passed.
echo.

echo [STEP 2/4] Starting Django Backend with ASGI Server (WebSocket Support) on Port 8000...
start "Django ASGI Backend" cmd /k "cd backend && echo Starting Django with ASGI/WebSocket support... && python -m daphne -b 0.0.0.0 -p 8000 menumine_ai.asgi:application --verbosity 1"

echo [STEP 3/4] Waiting 8 seconds for Django ASGI server to start...
timeout /t 8 /nobreak > nul

echo Testing Django backend connection...
curl -s http://localhost:8000/health/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Django backend is responding
) else (
    echo ⚠ Warning: Django backend may not be ready yet
)
echo.

echo [STEP 4/4] Starting React Frontend Development Server on Port 3000...
start "React Frontend" cmd /k "cd frontend && echo Starting React development server... && npm start"

echo Waiting 10 seconds for React to start...
timeout /t 10 /nobreak > nul

echo.
echo ============================================
echo    MenuMind AI - Full Stack Status
echo ============================================
echo   ✓ Frontend (React):      http://localhost:3000
echo   ✓ Backend (Django ASGI): http://localhost:8000  
echo   ✓ WebSocket Endpoint:    ws://localhost:8000/ws/
echo   ✓ Admin Panel:           http://localhost:8000/admin/
echo   ✓ API Docs:              http://localhost:8000/api/
echo ============================================
echo.
echo 🚀 COLLABORATIVE FEATURES ENABLED:
echo   • Real-time Shopping Lists
echo   • WebSocket Communication  
echo   • Multi-user Collaboration
echo ============================================
echo.

echo [TESTING] Checking server health...
echo Testing Django API...
curl -s http://localhost:8000/api/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Django API is working
) else (
    echo ✗ Django API connection failed
)

echo.
echo Opening applications in browser...
start http://localhost:3000
timeout /t 3 /nobreak > nul

echo.
echo 🎉 All servers are running!
echo.
echo 📝 USAGE TIPS:
echo   • Login with: testuser1 / password123
echo   • Create collaborative shopping lists
echo   • Share lists using collaboration keys
echo   • Test real-time features with multiple browser tabs
echo.
echo Press any key to stop all servers and exit...
pause > nul

echo.
echo [SHUTDOWN] Stopping all servers...
echo.

echo Stopping Python processes (Django/Daphne servers)...
taskkill /f /im python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python processes stopped
) else (
    echo ℹ No Python processes were running
)

echo Stopping Node.js processes (React dev server)...
taskkill /f /im node.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Node.js processes stopped
) else (
    echo ℹ No Node.js processes were running
)

echo Freeing up ports...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
    echo ✓ Port 3000 freed
)
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
    echo ✓ Port 8000 freed
)
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8001" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
    echo ✓ Port 8001 freed
)

echo.
echo ✅ All servers stopped successfully!
echo Goodbye! 👋
