@echo off
echo ================================================
echo   COMPLETE FIX - Restarting Backend + Frontend
echo ================================================
echo.

echo [1/5] Stopping all Node processes...
taskkill /F /IM node.exe >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Frontend stopped
) else (
    echo [INFO] Frontend not running
)

echo.
echo [2/5] Stopping Django backend...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *manage.py runserver*" >nul 2>&1
echo [OK] Backend stopped

echo.
echo [3/5] Waiting 2 seconds...
timeout /t 2 /nobreak >nul

echo.
echo [4/5] Starting Django backend...
cd /d C:\Users\al7ko\Desktop\menumine-ai\backend
start cmd /k "title Backend - Django && python manage.py runserver"
timeout /t 3 /nobreak >nul
echo [OK] Backend starting on http://127.0.0.1:8000

echo.
echo [5/5] Starting React frontend...
cd /d C:\Users\al7ko\Desktop\menumine-ai\frontend
start cmd /k "title Frontend - React && npm start"
echo [OK] Frontend starting on http://localhost:3000

echo.
echo ================================================
echo   ✅ BOTH SERVICES RESTARTED
echo ================================================
echo.
echo FIXES APPLIED:
echo   1. Backend: Disabled AI rate limiting (builder.py)
echo   2. Frontend: Fixed duplicate modal display
echo.
echo WAIT 30 seconds for services to start, then test:
echo   1. Go to http://localhost:3000/discover
echo   2. Click "Create Recipe"
echo   3. Enter "карбонара"
echo   4. Click "Next"
echo   5. ✅ Should see modal (NOT JSON!)
echo.
echo ================================================
pause

