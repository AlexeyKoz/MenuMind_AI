@echo off
echo ============================================
echo  Restarting React Frontend Only
echo ============================================
echo.

echo [1/3] Stopping React frontend...
taskkill /f /im node.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo     ✓ React processes stopped
) else (
    echo     ℹ No React processes were running
)

echo.
echo [2/3] Waiting 2 seconds...
timeout /t 2 /nobreak > nul

echo.
echo [3/3] Starting React Frontend (Port 3000)...
start "React Frontend" cmd /k "cd frontend && set BROWSER=none && npm start"

echo.
echo ✅ React frontend restarted!
echo    Open: http://localhost:3000
echo.
echo    Press CTRL+C in the React window to stop it later
echo.
pause

