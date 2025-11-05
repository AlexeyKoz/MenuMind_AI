@echo off
REM MenuMind AI - Docker Development Helper Script
REM Quick commands for working with Docker in development mode

echo.
echo ====================================
echo   MenuMind AI - Docker Manager
echo ====================================
echo.

if "%1"=="" goto menu
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="build" goto build
if "%1"=="status" goto status
if "%1"=="shell" goto shell
if "%1"=="db" goto db
if "%1"=="clean" goto clean
if "%1"=="help" goto help

:menu
echo Choose an option:
echo.
echo [1] Start all services (dev mode)
echo [2] Stop all services
echo [3] Restart all services
echo [4] View logs
echo [5] Rebuild containers
echo [6] Check status
echo [7] Access backend shell
echo [8] Access database
echo [9] Clean up Docker
echo [0] Exit
echo.
set /p choice="Enter your choice: "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto build
if "%choice%"=="6" goto status
if "%choice%"=="7" goto shell
if "%choice%"=="8" goto db
if "%choice%"=="9" goto clean
if "%choice%"=="0" exit
goto menu

:start
echo.
echo [*] Starting all services in development mode...
echo.
docker compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start services!
    exit /b 1
)
echo.
echo [SUCCESS] All services started!
echo.
echo Services available at:
echo - Frontend:  http://localhost:3000
echo - Backend:   http://localhost:8000
echo - Admin:     http://localhost:8000/admin
echo - Database:  localhost:5432
echo - Redis:     localhost:6379
echo.
echo Run: docker compose logs -f
echo To view real-time logs
echo.
if "%1"=="" pause
exit /b 0

:stop
echo.
echo [*] Stopping all services...
echo.
docker compose down
if %errorlevel% neq 0 (
    echo [ERROR] Failed to stop services!
    exit /b 1
)
echo.
echo [SUCCESS] All services stopped!
echo.
if "%1"=="" pause
exit /b 0

:restart
echo.
echo [*] Restarting all services...
echo.
docker compose restart
if %errorlevel% neq 0 (
    echo [ERROR] Failed to restart services!
    exit /b 1
)
echo.
echo [SUCCESS] All services restarted!
echo.
if "%1"=="" pause
exit /b 0

:logs
echo.
echo [*] Showing logs (Ctrl+C to exit)...
echo.
docker compose logs -f --tail=100
if "%1"=="" pause
exit /b 0

:build
echo.
echo [*] Rebuilding all containers...
echo.
docker compose down
docker compose build --no-cache
docker compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to rebuild!
    exit /b 1
)
echo.
echo [SUCCESS] All containers rebuilt and started!
echo.
if "%1"=="" pause
exit /b 0

:status
echo.
echo [*] Checking service status...
echo.
docker compose ps
echo.
echo Docker resources:
docker stats --no-stream
echo.
if "%1"=="" pause
exit /b 0

:shell
echo.
echo [*] Accessing backend shell...
echo [*] Type 'exit' to return
echo.
docker compose exec backend bash
if "%1"=="" pause
exit /b 0

:db
echo.
echo [*] Accessing PostgreSQL database...
echo [*] Type '\q' to exit
echo.
docker compose exec db psql -U postgres -d menumine_ai
if "%1"=="" pause
exit /b 0

:clean
echo.
echo [WARNING] This will remove all stopped containers, unused networks, and dangling images!
echo.
set /p confirm="Are you sure? (y/n): "
if /i not "%confirm%"=="y" (
    echo Cancelled.
    if "%1"=="" pause
    exit /b 0
)
echo.
echo [*] Cleaning up Docker...
echo.
docker system prune -f
echo.
echo [SUCCESS] Docker cleanup complete!
echo.
if "%1"=="" pause
exit /b 0

:help
echo.
echo Usage: docker-dev.bat [command]
echo.
echo Commands:
echo   start     - Start all services
echo   stop      - Stop all services
echo   restart   - Restart all services
echo   logs      - View logs
echo   build     - Rebuild containers
echo   status    - Check service status
echo   shell     - Access backend shell
echo   db        - Access database
echo   clean     - Clean up Docker
echo   help      - Show this help
echo.
echo No command runs interactive menu.
echo.
if "%1"=="" pause
exit /b 0


