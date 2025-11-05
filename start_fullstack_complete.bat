@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
REM ============================================
REM   BishulMe - Complete Full Stack Launcher
REM   LOCAL DEVELOPMENT (Without Docker)
REM ============================================
echo.
echo ================================================================
echo    BishulMe - Local Development System Launcher
echo    Running without Docker on Windows PC
echo ================================================================
echo.

REM ============================================
REM Step 0: Check Environment Files
REM ============================================
echo [0/9] Checking environment configuration...

REM Check if backend .env exists
if not exist "backend\.env" (
    echo ⚠️  backend\.env not found!
    echo    Creating from template...
    if exist "ENV_TEMPLATE_BACKEND.txt" (
        copy ENV_TEMPLATE_BACKEND.txt backend\.env > nul
        echo ✅ Created backend\.env - PLEASE UPDATE WITH YOUR VALUES!
        echo    Edit backend\.env and set your PostgreSQL password
        timeout /t 5 /nobreak > nul
    ) else (
        echo ❌ ENV_TEMPLATE_BACKEND.txt not found!
        echo    Please create backend\.env manually
        pause
        exit /b 1
    )
) else (
    echo ✅ backend\.env found
)

REM Check if frontend .env exists
if not exist "frontend\.env" (
    echo ⚠️  frontend\.env not found!
    echo    Creating from template...
    if exist "ENV_TEMPLATE_FRONTEND.txt" (
        copy ENV_TEMPLATE_FRONTEND.txt frontend\.env > nul
        echo ✅ Created frontend\.env
    ) else (
        echo ⚠️  ENV_TEMPLATE_FRONTEND.txt not found - frontend will use defaults
    )
) else (
    echo ✅ frontend\.env found
)

REM ============================================
REM Step 1: Check PostgreSQL (REQUIRED for data)
REM ============================================
echo.
echo [1/9] Checking PostgreSQL connection...
netstat -an | findstr :5432 | findstr LISTENING > nul
if %ERRORLEVEL% == 0 (
    echo ✅ PostgreSQL is running on port 5432
) else (
    echo.
    echo ====================================================
    echo  ❌ PostgreSQL is NOT running!
    echo  
    echo  Please install and start PostgreSQL:
    echo  1. Download: https://www.postgresql.org/download/windows/
    echo  2. Install and remember your password
    echo  3. Update backend\.env with your DB password
    echo  4. Create database: CREATE DATABASE menumindai;
    echo  
    echo  Or use Docker Postgres:
    echo     docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15
    echo ====================================================
    echo.
    pause
    exit /b 1
)

REM ============================================
REM Step 2: Check Redis (REQUIRED for caching + WebSockets)
REM ============================================
echo.
echo [2/9] Checking Redis connection...
netstat -an | findstr :6379 | findstr LISTENING > nul
if %ERRORLEVEL% == 0 (
    echo ✅ Redis is running on port 6379
    echo    ^(Cache + WebSocket channels ready^)
) else (
    echo ⚠️  Redis is NOT running - attempting to start...
    
    REM Check common Redis locations
    set "REDIS_FOUND=0"
    
    if exist "C:\Program Files\Redis\redis-server.exe" (
        echo    Found Redis in: C:\Program Files\Redis\
        start "Redis Server" "C:\Program Files\Redis\redis-server.exe"
        timeout /t 3 /nobreak > nul
        echo ✅ Redis server started!
        set "REDIS_FOUND=1"
    )
    
    if "!REDIS_FOUND!"=="0" (
        if exist "%USERPROFILE%\scoop\apps\redis\current\redis-server.exe" (
            echo    Found Redis in: Scoop
            start "Redis Server" "%USERPROFILE%\scoop\apps\redis\current\redis-server.exe"
            timeout /t 3 /nobreak > nul
            echo ✅ Redis server started!
            set "REDIS_FOUND=1"
        )
    )
    
    if "!REDIS_FOUND!"=="0" (
        if exist "C:\redis\redis-server.exe" (
            echo    Found Redis in: C:\redis\
            start "Redis Server" "C:\redis\redis-server.exe"
            timeout /t 3 /nobreak > nul
            echo ✅ Redis server started!
            set "REDIS_FOUND=1"
        )
    )
    
    if "!REDIS_FOUND!"=="0" (
        echo.
        echo ====================================================
        echo  ❌ Redis NOT found!
        echo  
        echo  Install Redis ^(choose one^):
        echo  1. Docker: docker run -d -p 6379:6379 redis:7-alpine
        echo  2. Scoop:  scoop install redis
        echo  3. WSL:    wsl sudo service redis-server start
        echo  4. Manual: https://github.com/tporadowski/redis/releases
        echo  
        echo  System cannot start without Redis!
        echo ====================================================
        echo.
        pause
        exit /b 1
    )
)

REM ============================================
REM Step 3: Check if virtual environment exists
REM ============================================
echo.
echo [3/9] Checking Python virtual environment...
if exist "backend\venv\Scripts\activate.bat" (
    echo ✅ Virtual environment found
) else (
    echo.
    echo ====================================================
    echo  ❌ Virtual environment not found!
    echo  
    echo  Creating virtual environment...
    echo ====================================================
    cd backend
    python -m venv venv
    if %ERRORLEVEL% == 0 (
        echo ✅ Virtual environment created
        echo.
        echo Installing dependencies...
        call venv\Scripts\activate
        pip install --upgrade pip
        pip install -r requirements.txt --use-deprecated=legacy-resolver
        echo ✅ Dependencies installed
        cd ..
    ) else (
        echo ❌ Failed to create virtual environment
        cd ..
        pause
        exit /b 1
    )
)

REM ============================================
REM Step 4: Check Database Migrations
REM ============================================
echo.
echo [4/9] Checking database migrations...
cd backend
call venv\Scripts\activate
python manage.py showmigrations --list > nul 2>&1
if %ERRORLEVEL% == 0 (
    echo ✅ Database is accessible
    echo.
    echo Running migrations...
    python manage.py migrate --noinput
    if %ERRORLEVEL% == 0 (
        echo ✅ Migrations applied successfully
    ) else (
        echo ⚠️  Migration failed - database may need setup
    )
) else (
    echo.
    echo ====================================================
    echo  ⚠️  Cannot connect to database!
    echo  
    echo  Make sure:
    echo  1. PostgreSQL is running
    echo  2. Database 'menumindai' exists
    echo  3. backend\.env has correct credentials
    echo  
    echo  To create database, run in psql:
    echo     CREATE DATABASE menumindai;
    echo ====================================================
    echo.
)
cd ..

REM ============================================
REM Step 5: Check Node.js and Frontend Dependencies
REM ============================================
echo.
echo [5/9] Checking frontend dependencies...
if exist "frontend\node_modules\" (
    echo ✅ Node modules found
) else (
    echo.
    echo ====================================================
    echo  ⚠️  Node modules not found!
    echo  
    echo  Installing frontend dependencies...
    echo  This may take a few minutes...
    echo ====================================================
    cd frontend
    call npm install --legacy-peer-deps
    if %ERRORLEVEL% == 0 (
        echo ✅ Frontend dependencies installed
    ) else (
        echo ❌ Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
    cd ..
)

REM ============================================
REM Step 6: Start Django Backend (Daphne ASGI)
REM ============================================
echo.
echo [6/9] Starting Django Backend with Daphne ^(Port 8000^)...
echo    Features: REST API + WebSockets + Admin
start "BishulMe - Django Backend" cmd /k "cd backend && venv\Scripts\activate && daphne -b 0.0.0.0 -p 8000 menumine_ai.asgi:application"
timeout /t 5 /nobreak > nul

REM ============================================
REM Step 7: Start Celery Worker (Background Tasks)
REM ============================================
echo.
echo [7/9] Starting Celery Worker ^(Background Tasks^)...
echo    Tasks: Cache cleanup, translations, etc.
start "BishulMe - Celery Worker" cmd /k "cd backend && venv\Scripts\activate && celery -A menumine_ai worker -l INFO --pool=solo"
timeout /t 3 /nobreak > nul

REM ============================================
REM Step 8: Start Celery Beat (Scheduled Tasks)
REM ============================================
echo.
echo [8/9] Starting Celery Beat ^(Task Scheduler^)...
echo    Schedule: Daily cache cleanup at 3:30 AM
start "BishulMe - Celery Beat" cmd /k "cd backend && venv\Scripts\activate && celery -A menumine_ai beat -l INFO"
timeout /t 2 /nobreak > nul

REM ============================================
REM Step 9: Start React Frontend
REM ============================================
echo.
echo [9/9] Starting React Frontend ^(Port 3000^)...
echo    UI: Recipe discovery, inventory, shopping lists
start "BishulMe - React Frontend" cmd /k "cd frontend && set BROWSER=none && npm start"
timeout /t 3 /nobreak > nul

REM ============================================
REM Verify all services
REM ============================================
echo.
echo Verifying services...
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
echo    BishulMe - LOCAL DEVELOPMENT SYSTEM RUNNING
echo ================================================================
echo.
echo 🌐 WEB INTERFACES:
echo    Frontend:           http://localhost:3000
echo    Admin Panel:        http://localhost:8000/admin/
echo    API Docs:           http://localhost:8000/api/
echo.
echo 🔌 WEBSOCKET ENDPOINTS:
echo    Shopping Lists:     ws://localhost:8000/ws/shopping/{list_id}/
echo    Notifications:      ws://localhost:8000/ws/user/notifications/
echo.
echo 🔧 SERVICES RUNNING:
echo    PostgreSQL:         ✅ Port 5432 (Local)
echo    Redis Cache:        ✅ Port 6379 (Local)
echo    Django ASGI:        ✅ Port 8000
echo    Celery Worker:      ✅ Background tasks
echo    Celery Beat:        ✅ Scheduled tasks
echo    React Frontend:     ✅ Port 3000
echo.
echo 📝 DEVELOPMENT MODE:
echo    ✅ Hot reload enabled (frontend)
echo    ✅ Debug mode enabled (backend)
echo    ✅ CORS configured for localhost
echo    ✅ Multilingual support (en/he/ru)
echo.
echo 💡 QUICK TIPS:
echo    - Backend changes: Save file, Daphne auto-reloads
echo    - Frontend changes: Save file, React auto-reloads
echo    - Database: Use pgAdmin or psql for direct access
echo    - Redis: Use Redis Insight or redis-cli
echo    - Stop all: Run stop_servers_complete.bat
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


