@echo off
echo ============================================
echo  MenuMind AI - Server Cleanup
echo ============================================
echo.

echo Stopping all development servers...
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

echo.
echo ✅ All servers stopped successfully!
echo.
echo 💡 TIP: Use 'start_fullstack.bat' for automatic cleanup + startup!
echo    It now includes all this cleanup functionality built-in.
echo.
pause
