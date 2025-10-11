@echo off
echo ============================================
echo  MenuMind AI - Server Cleanup
echo ============================================
echo.

echo Stopping all development servers...
echo.

echo [1/5] Stopping Python processes (Django/Daphne servers)...
taskkill /f /im python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python processes stopped (Django)
) else (
    echo ℹ No Python processes were running
)

echo [2/5] Stopping Node.js processes (React dev server)...
taskkill /f /im node.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Node.js processes stopped
) else (
    echo ℹ No Node.js processes were running
)

echo [3/5] Stopping Redis server...
taskkill /f /im redis-server.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Redis server stopped
) else (
    echo ℹ Redis was not running or managed externally
)

echo [4/5] Freeing up ports 3000, 8000, 8001, 6379...
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
for /f "tokens=5" %%a in ('netstat -aon ^| find ":6379" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
    echo ✓ Port 6379 (Redis) freed
)

echo [5/5] Cleanup complete!
echo.
echo ✅ All servers stopped successfully!
echo.
echo 💡 TIP: Use 'start_fullstack.bat' for automatic cleanup + startup!
echo    It now includes all this cleanup functionality built-in.
echo.
pause
