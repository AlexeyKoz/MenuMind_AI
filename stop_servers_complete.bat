@echo off
REM ============================================
REM   MenuMind AI - Stop All Services
REM   Sprint 7 Complete
REM ============================================
echo.
echo ════════════════════════════════════════════════════════════════
echo    MenuMind AI - Stopping All Services
echo ════════════════════════════════════════════════════════════════
echo.

echo [1/6] Stopping Celery Beat ^(Scheduler^)...
taskkill /F /FI "WINDOWTITLE eq MenuMind - Celery Beat*" /T 2>nul
if %ERRORLEVEL% == 0 (
    echo ✅ Celery Beat stopped
) else (
    echo ⚠️  Celery Beat not found
)

echo.
echo [2/6] Stopping Celery Worker ^(Background Tasks^)...
taskkill /F /FI "WINDOWTITLE eq MenuMind - Celery Worker*" /T 2>nul
if %ERRORLEVEL% == 0 (
    echo ✅ Celery Worker stopped
) else (
    echo ⚠️  Celery Worker not found
)

echo.
echo [3/6] Stopping Django Backend...
taskkill /F /FI "WINDOWTITLE eq MenuMind - Django Backend*" /T 2>nul
if %ERRORLEVEL% == 0 (
    echo ✅ Django Backend stopped
) else (
    echo ⚠️  Django Backend not found
)

echo.
echo [4/6] Stopping React Frontend...
taskkill /F /FI "WINDOWTITLE eq MenuMind - React Frontend*" /T 2>nul
if %ERRORLEVEL% == 0 (
    echo ✅ React Frontend stopped
) else (
    echo ⚠️  React Frontend not found
)

echo.
echo [5/6] Stopping Test Server...
taskkill /F /FI "WINDOWTITLE eq MenuMind - Test Server*" /T 2>nul
if %ERRORLEVEL% == 0 (
    echo ✅ Test Server stopped
) else (
    echo ⚠️  Test Server not found
)

echo.
echo [6/6] Cleaning up any remaining processes...
REM Kill any orphaned processes
taskkill /F /IM celery.exe /T 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *MenuMind*" /T 2>nul
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *MenuMind*" /T 2>nul

echo.
echo ════════════════════════════════════════════════════════════════
echo    All MenuMind AI services stopped ✅
echo ════════════════════════════════════════════════════════════════
echo.
echo Note: Redis server is still running ^(shared resource^)
echo       Stop it manually if needed: taskkill /IM redis-server.exe
echo.

timeout /t 3 /nobreak > nul

