@echo off
REM BishulMe - Open WSL2 Development Environment
REM This script opens WSL2 and starts the development environment

echo.
echo ═══════════════════════════════════════════════════════════════
echo   🚀 Opening BishulMe Development (WSL2)
echo ═══════════════════════════════════════════════════════════════
echo.

REM Check if WSL2 is installed
wsl --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ WSL2 is not installed!
    echo.
    echo Please install WSL2 first:
    echo    1. Open PowerShell as Administrator
    echo    2. Run: wsl --install
    echo    3. Restart your computer
    echo.
    pause
    exit /b 1
)

echo ✅ WSL2 is installed
echo.

REM Check if Docker Desktop is running
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Docker Desktop is not running!
    echo.
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo ✅ Docker Desktop is running
echo.

REM Determine project path in WSL2
echo Checking project location...
echo.

REM Option 1: Check if project is in WSL2 home
wsl -e bash -c "test -d ~/MenuMind_AI && echo 'WSL_HOME' || echo 'NOT_FOUND'" > temp_check.txt
set /p LOCATION=<temp_check.txt
del temp_check.txt

if "%LOCATION%"=="WSL_HOME" (
    echo ✅ Found project in WSL2 home directory
    echo    Path: ~/MenuMind_AI
    echo.
    echo Opening WSL2 terminal and starting development...
    echo.
    wsl -d Ubuntu-22.04 -e bash -c "cd ~/MenuMind_AI && chmod +x start_dev_wsl.sh && ./start_dev_wsl.sh && bash"
) else (
    echo ℹ️  Project not in WSL2 home
    echo    Using Windows path: /mnt/c/Users/al7ko/Desktop/after-deploy/MenuMind_AI
    echo.
    echo 💡 TIP: For better performance, copy project to WSL2:
    echo    wsl
    echo    cp -r /mnt/c/Users/al7ko/Desktop/after-deploy/MenuMind_AI ~/MenuMind_AI
    echo.
    echo Opening WSL2 terminal and starting development...
    echo.
    wsl -d Ubuntu-22.04 -e bash -c "cd /mnt/c/Users/al7ko/Desktop/after-deploy/MenuMind_AI && chmod +x start_dev_wsl.sh && ./start_dev_wsl.sh && bash"
)

REM If WSL2 terminal closes, show this message
echo.
echo WSL2 terminal closed.
echo.
echo To reopen: Double-click open_wsl_dev.bat
echo.
pause


