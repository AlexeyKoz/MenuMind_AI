@echo off
echo Waiting for services to start...
echo.
echo Please wait 30-40 seconds after running restart_both_services.bat
echo.
echo Then run:
echo   cd frontend\tests
echo   python test_focused_duplicate.py
echo.
echo Or test manually:
echo   1. Open http://localhost:3000/discover
echo   2. Click "Create Recipe"
echo   3. Enter "carbonara"
echo   4. Click "Next"
echo   5. Should see modal (not JSON)
echo.
pause

