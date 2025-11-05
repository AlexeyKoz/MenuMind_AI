@echo off
REM MenuMind AI - Docker Production Helper Script
REM Quick commands for working with Docker in production mode

echo.
echo ====================================
echo  MenuMind AI - Production Manager
echo ====================================
echo.

if "%1"=="" goto menu
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="build" goto build
if "%1"=="status" goto status
if "%1"=="backup" goto backup
if "%1"=="help" goto help

:menu
echo Choose an option:
echo.
echo [1] Start production stack
echo [2] Stop production stack
echo [3] Restart services
echo [4] View logs
echo [5] Rebuild containers
echo [6] Check status
echo [7] Backup database
echo [8] View service health
echo [0] Exit
echo.
set /p choice="Enter your choice: "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto build
if "%choice%"=="6" goto status
if "%choice%"=="7" goto backup
if "%choice%"=="8" goto health
if "%choice%"=="0" exit
goto menu

:start
echo.
echo [*] Starting production stack...
echo.
docker compose -f docker-compose.prod.yml up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start production stack!
    exit /b 1
)
echo.
echo [SUCCESS] Production stack started!
echo.
echo Services:
docker compose -f docker-compose.prod.yml ps
echo.
if "%1"=="" pause
exit /b 0

:stop
echo.
echo [WARNING] This will stop all production services!
echo.
set /p confirm="Are you sure? (y/n): "
if /i not "%confirm%"=="y" (
    echo Cancelled.
    if "%1"=="" pause
    exit /b 0
)
echo.
echo [*] Stopping production stack...
echo.
docker compose -f docker-compose.prod.yml down
if %errorlevel% neq 0 (
    echo [ERROR] Failed to stop production stack!
    exit /b 1
)
echo.
echo [SUCCESS] Production stack stopped!
echo.
if "%1"=="" pause
exit /b 0

:restart
echo.
echo [*] Restarting production services...
echo.
docker compose -f docker-compose.prod.yml restart
if %errorlevel% neq 0 (
    echo [ERROR] Failed to restart services!
    exit /b 1
)
echo.
echo [SUCCESS] Services restarted!
echo.
if "%1"=="" pause
exit /b 0

:logs
echo.
echo [*] Production logs (Ctrl+C to exit)...
echo.
docker compose -f docker-compose.prod.yml logs -f --tail=100
if "%1"=="" pause
exit /b 0

:build
echo.
echo [*] Rebuilding production containers...
echo.
docker compose -f docker-compose.prod.yml build --no-cache
if %errorlevel% neq 0 (
    echo [ERROR] Failed to rebuild!
    exit /b 1
)
echo.
echo [SUCCESS] Production containers rebuilt!
echo.
echo To deploy: docker-prod.bat start
echo.
if "%1"=="" pause
exit /b 0

:status
echo.
echo [*] Production service status...
echo.
docker compose -f docker-compose.prod.yml ps
echo.
echo Docker resources:
docker stats --no-stream
echo.
if "%1"=="" pause
exit /b 0

:backup
echo.
echo [*] Backing up database...
echo.
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "datestamp=%dt:~0,8%_%dt:~8,6%"
set "backupfile=backup_%datestamp%.sql"
echo.
echo Backup file: %backupfile%
echo.
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U postgres menumine_ai > %backupfile%
if %errorlevel% neq 0 (
    echo [ERROR] Backup failed!
    exit /b 1
)
echo.
echo [SUCCESS] Database backed up to: %backupfile%
echo.
if "%1"=="" pause
exit /b 0

:health
echo.
echo [*] Checking service health...
echo.
for %%s in (backend celery celery-beat daphne frontend) do (
    echo Checking %%s...
    docker inspect menumine_%%s_prod --format="Status: {{.State.Status}} | Health: {{.State.Health.Status}}" 2>nul
    if %errorlevel% neq 0 (
        echo %%s: NOT RUNNING
    )
    echo.
)
if "%1"=="" pause
exit /b 0

:help
echo.
echo Usage: docker-prod.bat [command]
echo.
echo Commands:
echo   start     - Start production stack
echo   stop      - Stop production stack
echo   restart   - Restart services
echo   logs      - View logs
echo   build     - Rebuild containers
echo   status    - Check service status
echo   backup    - Backup database
echo   help      - Show this help
echo.
echo No command runs interactive menu.
echo.
if "%1"=="" pause
exit /b 0


