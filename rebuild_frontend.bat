@echo off
REM ============================================================
REM MenuMine AI - Force Frontend Rebuild
REM ============================================================
REM Use this when frontend changes are not appearing
REM This will clear all caches and force a fresh build
REM ============================================================

echo ============================================================
echo    Force Rebuilding Frontend...
echo ============================================================
echo.

cd frontend

echo [1/4] Stopping any running frontend processes...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq npm*" 2>nul

echo [2/4] Clearing build cache...
if exist "build" (
    echo     - Removing build folder...
    rmdir /s /q build
)

if exist "node_modules\.cache" (
    echo     - Removing node_modules cache...
    rmdir /s /q node_modules\.cache
)

echo [3/4] Clearing browser cache files...
if exist ".eslintcache" (
    del /f /q .eslintcache
)

echo [4/4] Starting fresh development server...
echo.
echo ============================================================
echo    Frontend will start on http://localhost:3000
echo ============================================================
echo.
echo Press Ctrl+C to stop the server
echo.
echo IMPORTANT: After frontend starts, do a HARD REFRESH in your browser:
echo    - Windows/Linux: Ctrl + Shift + R
echo    - Mac: Cmd + Shift + R
echo.

npm start

pause

