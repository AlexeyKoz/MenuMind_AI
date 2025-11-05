@echo off
REM ============================================
REM Logo Management System - Deploy Script
REM ============================================

echo.
echo ========================================
echo  DEPLOYING LOGO MANAGEMENT SYSTEM
echo ========================================
echo.

REM Step 1: Stop containers
echo [1/6] Stopping containers...
docker-compose -f docker-compose.prod.yml down
if %errorlevel% neq 0 (
    echo ERROR: Failed to stop containers
    pause
    exit /b 1
)

REM Step 2: Rebuild containers
echo.
echo [2/6] Rebuilding containers (this may take a few minutes)...
docker-compose -f docker-compose.prod.yml up -d --build
if %errorlevel% neq 0 (
    echo ERROR: Failed to rebuild containers
    pause
    exit /b 1
)

REM Step 3: Wait for backend to be ready
echo.
echo [3/6] Waiting for backend to be ready...
timeout /t 10 /nobreak >nul

REM Step 4: Create migrations
echo.
echo [4/6] Creating migrations for branding app...
docker exec menumine_backend_prod python manage.py makemigrations branding
if %errorlevel% neq 0 (
    echo WARNING: Migrations might already exist or there was an error
)

REM Step 5: Apply migrations
echo.
echo [5/6] Applying migrations...
docker exec menumine_backend_prod python manage.py migrate branding
if %errorlevel% neq 0 (
    echo ERROR: Failed to apply migrations
    pause
    exit /b 1
)

REM Step 6: Create media directory
echo.
echo [6/6] Setting up media directory...
docker exec menumine_backend_prod mkdir -p /app/media/branding/logos
docker exec menumine_backend_prod chmod -R 755 /app/media

echo.
echo ========================================
echo  DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo Next Steps:
echo   1. Access admin: http://localhost:8000/admin/
echo   2. Navigate to "Site Logos"
echo   3. Click "Quick Setup" to upload logos
echo.
echo Test API:
echo   curl http://localhost:8000/api/branding/logos/for_language/?lang=en
echo.

REM Open browser to admin
echo Opening admin panel...
start http://localhost:8000/admin/

pause

