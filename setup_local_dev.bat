@echo off
chcp 65001 > nul
REM ============================================
REM   BishulMe - Quick Setup Script
REM   First-time setup for local development
REM ============================================
echo.
echo ================================================================
echo    BishulMe - First-Time Setup
echo    This will prepare your local development environment
echo ================================================================
echo.

REM Check prerequisites
echo [1/7] Checking prerequisites...
echo.

REM Check Python
python --version > nul 2>&1
if %ERRORLEVEL% == 0 (
    echo ✅ Python installed
    python --version
) else (
    echo ❌ Python not found!
    echo    Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Node.js
node --version > nul 2>&1
if %ERRORLEVEL% == 0 (
    echo ✅ Node.js installed
    node --version
) else (
    echo ❌ Node.js not found!
    echo    Download from: https://nodejs.org/
    pause
    exit /b 1
)

REM Check PostgreSQL
netstat -an | findstr :5432 | findstr LISTENING > nul
if %ERRORLEVEL% == 0 (
    echo ✅ PostgreSQL is running on port 5432
) else (
    echo ⚠️  PostgreSQL is NOT running!
    echo    Please install and start PostgreSQL
    echo    Download: https://www.postgresql.org/download/windows/
    pause
)

REM Check Redis
netstat -an | findstr :6379 | findstr LISTENING > nul
if %ERRORLEVEL% == 0 (
    echo ✅ Redis is running on port 6379
) else (
    echo ⚠️  Redis is NOT running!
    echo    Quick start: docker run -d -p 6379:6379 redis:7-alpine
    pause
)

echo.
echo ================================================================
echo [2/7] Creating environment files...
echo ================================================================

REM Create backend .env if not exists
if not exist "backend\.env" (
    if exist "ENV_TEMPLATE_BACKEND.txt" (
        copy ENV_TEMPLATE_BACKEND.txt backend\.env > nul
        echo ✅ Created backend\.env
        echo.
        echo ⚠️  IMPORTANT: Edit backend\.env and update:
        echo    - DB_PASSWORD with your PostgreSQL password
        echo    - SECRET_KEY with a new random key
        echo.
    ) else (
        echo ❌ ENV_TEMPLATE_BACKEND.txt not found!
    )
) else (
    echo ✅ backend\.env already exists
)

REM Create frontend .env if not exists
if not exist "frontend\.env" (
    if exist "ENV_TEMPLATE_FRONTEND.txt" (
        copy ENV_TEMPLATE_FRONTEND.txt frontend\.env > nul
        echo ✅ Created frontend\.env
    )
) else (
    echo ✅ frontend\.env already exists
)

echo.
echo ================================================================
echo [3/7] Creating Python virtual environment...
echo ================================================================
if exist "backend\venv\Scripts\activate.bat" (
    echo ✅ Virtual environment already exists
) else (
    cd backend
    python -m venv venv
    if %ERRORLEVEL% == 0 (
        echo ✅ Virtual environment created
    ) else (
        echo ❌ Failed to create virtual environment
        cd ..
        pause
        exit /b 1
    )
    cd ..
)

echo.
echo ================================================================
echo [4/7] Installing Python dependencies...
echo ================================================================
cd backend
call venv\Scripts\activate
echo Upgrading pip...
python -m pip install --upgrade pip --quiet
echo Installing requirements (this may take 3-5 minutes)...
pip install -r requirements.txt --use-deprecated=legacy-resolver --quiet
if %ERRORLEVEL% == 0 (
    echo ✅ Python dependencies installed
) else (
    echo ❌ Failed to install Python dependencies
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo ================================================================
echo [5/7] Installing Node.js dependencies...
echo ================================================================
cd frontend
if exist "node_modules\" (
    echo ✅ Node modules already installed
) else (
    echo Installing npm packages (this may take 3-5 minutes)...
    call npm install --legacy-peer-deps
    if %ERRORLEVEL% == 0 (
        echo ✅ Frontend dependencies installed
    ) else (
        echo ❌ Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
)
cd ..

echo.
echo ================================================================
echo [6/7] Setting up database...
echo ================================================================
cd backend
call venv\Scripts\activate

echo Checking database connection...
python manage.py check --database default > nul 2>&1
if %ERRORLEVEL% == 0 (
    echo ✅ Database connection successful
    echo.
    echo Running migrations...
    python manage.py migrate --noinput
    if %ERRORLEVEL% == 0 (
        echo ✅ Migrations completed
    ) else (
        echo ⚠️  Migrations failed - check backend\.env database settings
    )
) else (
    echo.
    echo ❌ Cannot connect to database!
    echo.
    echo Make sure:
    echo 1. PostgreSQL is running
    echo 2. Database 'menumindai' exists
    echo    Run in psql: CREATE DATABASE menumindai;
    echo 3. backend\.env has correct DB_PASSWORD
    echo.
    pause
)
cd ..

echo.
echo ================================================================
echo [7/7] Loading initial data...
echo ================================================================
cd backend
call venv\Scripts\activate

echo.
echo Loading IML and CookLingo data...
python import_iml_cooklingo.py
if %ERRORLEVEL% == 0 (
    echo ✅ IML/CookLingo data loaded
) else (
    echo ⚠️  Failed to load IML/CookLingo data
)

echo.
echo Loading legal documents...
python manage.py load_bishulsheli_docs --force
if %ERRORLEVEL% == 0 (
    echo ✅ Legal documents loaded
) else (
    echo ⚠️  Failed to load legal documents
)

cd ..

echo.
echo ================================================================
echo    ✅ SETUP COMPLETE!
echo ================================================================
echo.
echo 📝 Next Steps:
echo.
echo 1. Create an admin user:
echo    cd backend
echo    venv\Scripts\activate
echo    python manage.py createsuperuser
echo.
echo 2. Start the application:
echo    start_fullstack_complete.bat
echo.
echo 3. Open browser:
echo    http://localhost:3000
echo.
echo 📖 For more details, see LOCAL_DEVELOPMENT_GUIDE.md
echo.
echo ================================================================
pause

