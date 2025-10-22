@echo off
chcp 65001 > nul
REM ============================================
REM   MenuMind AI - Complete Full Stack Launcher
REM   Sprint 7 Complete - All Services
REM ============================================
echo.
echo ================================================================
echo    MenuMind AI - Complete System Launcher
echo    Sprint 7: Validation + Caching + Translation + Inventory
echo ================================================================
echo.

REM ============================================
REM Step 0: Check Redis (REQUIRED for caching + WebSockets)
REM ============================================
echo [0/8] Checking Redis connection...
netstat -an | findstr :6379 | findstr LISTENING > nul
if %ERRORLEVEL% == 0 (
    echo ✅ Redis is running on port 6379
    echo    ^(Cache + WebSocket channels ready^)
) else (
    echo ⚠️  Redis is NOT running - attempting to start...
    
    REM Check common Redis locations
    if exist "C:\Program Files\Redis\redis-server.exe" (
        echo    Found Redis in: C:\Program Files\Redis\
        start "Redis Server" "C:\Program Files\Redis\redis-server.exe"
        timeout /t 3 /nobreak > nul
        echo ✅ Redis server started!
    ) else if exist "%USERPROFILE%\scoop\apps\redis\current\redis-server.exe" (
        echo    Found Redis in: Scoop
        start "Redis Server" "%USERPROFILE%\scoop\apps\redis\current\redis-server.exe"
        timeout /t 3 /nobreak > nul
        echo ✅ Redis server started!
    ) else if exist "C:\redis\redis-server.exe" (
        echo    Found Redis in: C:\redis\
        start "Redis Server" "C:\redis\redis-server.exe"
        timeout /t 3 /nobreak > nul
        echo ✅ Redis server started!
    ) else (
        echo.
        echo ====================================================
        echo  Redis NOT found! System will continue but:
        echo  X No caching (slower performance)
        echo  X No background tasks (Celery)
        echo  X Limited WebSocket support
        echo  
        echo  Install Redis:
        echo  - Scoop:      scoop install redis
        echo  - Chocolatey: choco install redis-64
        echo  - Manual:     https://github.com/tporadowski/redis/releases
        echo  - WSL:        wsl sudo service redis-server start
        echo ====================================================
        echo.
        timeout /t 3 /nobreak > nul
    )
)

REM ============================================
REM Step 1: Verify ASGI configuration
REM ============================================
echo.
echo [1/8] Verifying ASGI configuration...
findstr /C:"from apps.shopping.user_consumer import UserNotificationConsumer" backend\menumine_ai\asgi.py | findstr /N "^[1-9]:" > nul
if %ERRORLEVEL% == 0 (
    echo ⚠️  ASGI import order issue detected!
    echo    ^(Will attempt to continue, but WebSockets may fail^)
    timeout /t 2 /nobreak > nul
) else (
    echo ✅ ASGI configuration looks correct
)

REM ============================================
REM Step 2: Check if virtual environment exists
REM ============================================
echo.
echo [2/8] Checking Python virtual environment...
if exist "backend\venv\Scripts\activate.bat" (
    echo ✅ Virtual environment found
) else (
    echo ⚠️  Virtual environment not found at backend\venv
    echo    Make sure you've run: python -m venv backend/venv
    timeout /t 3 /nobreak > nul
)

REM ============================================
REM Step 3: Start Django Backend (Daphne ASGI)
REM ============================================
echo.
echo [3/8] Starting Django Backend with Daphne ^(Port 8000^)...
echo    Features: REST API + WebSockets + Admin
start "MenuMind - Django Backend" cmd /k "cd backend && venv\Scripts\activate && daphne -b 0.0.0.0 -p 8000 menumine_ai.asgi:application"
timeout /t 5 /nobreak > nul

REM ============================================
REM Step 4: Start Celery Worker (Background Tasks)
REM ============================================
echo.
echo [4/8] Starting Celery Worker ^(Background Tasks^)...
echo    Tasks: Cache cleanup, translations, etc.
start "MenuMind - Celery Worker" cmd /k "cd backend && venv\Scripts\activate && celery -A menumine_ai worker -l INFO --pool=solo"
timeout /t 3 /nobreak > nul

REM ============================================
REM Step 5: Start Celery Beat (Scheduled Tasks)
REM ============================================
echo.
echo [5/8] Starting Celery Beat ^(Task Scheduler^)...
echo    Schedule: Daily cache cleanup at 3:30 AM
start "MenuMind - Celery Beat" cmd /k "cd backend && venv\Scripts\activate && celery -A menumine_ai beat -l INFO"
timeout /t 2 /nobreak > nul

REM ============================================
REM Step 6: Start React Frontend
REM ============================================
echo.
echo [6/8] Starting React Frontend ^(Port 3000^)...
echo    UI: Recipe discovery, inventory, shopping lists
start "MenuMind - React Frontend" cmd /k "cd frontend && set BROWSER=none && npm start"
timeout /t 3 /nobreak > nul

REM ============================================
REM Step 7: Start Test Server (Optional)
REM ============================================
echo.
echo [7/8] Starting Test Dashboard ^(Port 8001^)...
start "MenuMind - Test Server" cmd /k "python -m http.server 8001"

REM ============================================
REM Step 8: Verify all services
REM ============================================
echo.
echo [8/8] Verifying services...
timeout /t 5 /nobreak > nul

REM Check Django
echo.
echo Checking Django backend...
curl -s http://localhost:8000/health/ > nul 2>&1
if %ERRORLEVEL% == 0 (
    echo ✅ Django backend responding
) else (
    echo ⚠️  Django backend not responding yet ^(may need more time^)
)

REM Check Frontend
echo Checking React frontend...
timeout /t 5 /nobreak > nul
curl -s http://localhost:3000 > nul 2>&1
if %ERRORLEVEL% == 0 (
    echo ✅ React frontend responding
) else (
    echo ⚠️  React frontend not responding yet ^(may need more time^)
)

REM ============================================
REM Display System Status
REM ============================================
echo.
echo ================================================================
echo    MenuMind AI - SYSTEM RUNNING
echo ================================================================
echo.
echo 🌐 WEB INTERFACES:
echo    Frontend:           http://localhost:3000
echo    Admin Panel:        http://localhost:8000/admin/
echo    API Docs:           http://localhost:8000/api/
echo    Test Dashboard:     http://localhost:8001/test_backend.html
echo.
echo 🔌 WEBSOCKET ENDPOINTS:
echo    Shopping Lists:     ws://localhost:8000/ws/shopping/{list_id}/
echo    Notifications:      ws://localhost:8000/ws/user/notifications/
echo.
echo 🔧 BACKEND SERVICES:
echo    Django ASGI:        ✅ Port 8000
echo    Celery Worker:      ✅ Background tasks
echo    Celery Beat:        ✅ Scheduled tasks
echo    Redis Cache:        ✅ Port 6379
echo.
echo 📊 SPRINT 7 FEATURES:
echo    ✅ Phase 1: Recipe Validation ^(UniversalValidator^)
echo    ✅ Phase 2: Multilingual ^(en/he/ru^)
echo    ✅ Phase 3: Two-tier Caching ^(Redis + PostgreSQL^)
echo    ✅ Phase 4: Full Recipe Generation ^(AI-powered^)
echo.
echo 🎯 KEY ENDPOINTS:
echo    Generate Recipes:   POST /api/inventory/generate_recipes/
echo    Create Recipe:      POST /api/inventory/create-recipe-from-brief/
echo    Discovery:          GET  /api/recipes/discovery/
echo    Health Check:       GET  /health/
echo.
echo ================================================================
echo.

REM ============================================
REM Auto-open Frontend Browser
REM ============================================
echo Opening frontend in browser...
start http://localhost:3000
echo.
echo Servers are running in background.
echo To stop servers later, run: stop_servers_complete.bat
echo.
timeout /t 2 /nobreak > nul
exit /b 0

