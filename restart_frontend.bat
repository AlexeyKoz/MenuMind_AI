@echo off
echo ================================================
echo   Restarting Frontend to Apply Duplicate Fix
echo ================================================
echo.

echo [1/3] Stopping all Node processes...
taskkill /F /IM node.exe >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Node processes stopped
) else (
    echo [INFO] No Node processes found
)

echo.
echo [2/3] Waiting 2 seconds...
timeout /t 2 /nobreak >nul

echo.
echo [3/3] Starting frontend dev server...
cd /d C:\Users\al7ko\Desktop\menumine-ai\frontend

echo.
echo Starting React dev server...
echo Open http://localhost:3000 in your browser
echo.
echo ================================================
echo   After server starts, test the fix:
echo   1. Go to Discover page
echo   2. Click "Create Recipe"  
echo   3. Enter "карбонара"
echo   4. Click "Next"
echo   5. Modal should appear (not JSON!)
echo ================================================
echo.

npm start

