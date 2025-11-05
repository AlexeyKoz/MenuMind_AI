@echo off
REM ============================================
REM   Add Mailjet Credentials to backend/.env
REM ============================================
echo.
echo ================================================================
echo    Adding Mailjet Configuration to backend\.env
echo ================================================================
echo.

REM Check if .env exists
if not exist "backend\.env" (
    echo Creating backend\.env from template...
    copy ENV_TEMPLATE_BACKEND.txt backend\.env > nul
)

echo Adding/Updating Mailjet credentials...

REM Create temporary file with updated content
powershell -Command "$envPath = 'backend\.env'; $content = Get-Content $envPath -Raw; if ($content -notmatch 'MAILJET_API_KEY=') { Add-Content $envPath \"`nMAILJET_API_KEY=7fddcffd9c674043d468c076f6b3f399\" } else { $content = $content -replace 'MAILJET_API_KEY=.*', 'MAILJET_API_KEY=7fddcffd9c674043d468c076f6b3f399'; Set-Content $envPath $content -NoNewline }; $content = Get-Content $envPath -Raw; if ($content -notmatch 'MAILJET_SECRET_KEY=') { Add-Content $envPath \"`nMAILJET_SECRET_KEY=63cad8b87cd6be051280f3fa1e5c3c41\" } else { $content = $content -replace 'MAILJET_SECRET_KEY=.*', 'MAILJET_SECRET_KEY=63cad8b87cd6be051280f3fa1e5c3c41'; Set-Content $envPath $content -NoNewline }; $content = Get-Content $envPath -Raw; if ($content -notmatch 'MAILJET_SENDER_EMAIL=') { Add-Content $envPath \"`nMAILJET_SENDER_EMAIL=support@bishul.me\" } else { $content = $content -replace 'MAILJET_SENDER_EMAIL=.*', 'MAILJET_SENDER_EMAIL=support@bishul.me'; Set-Content $envPath $content -NoNewline }; $content = Get-Content $envPath -Raw; if ($content -notmatch 'MAILJET_SENDER_NAME=') { Add-Content $envPath \"`nMAILJET_SENDER_NAME=BishulSheli\" } else { $content = $content -replace 'MAILJET_SENDER_NAME=.*', 'MAILJET_SENDER_NAME=BishulSheli'; Set-Content $envPath $content -NoNewline }; $content = Get-Content $envPath -Raw; if ($content -notmatch 'MAILJET_TEMPLATE_VERIFY_EN=') { Add-Content $envPath \"`nMAILJET_TEMPLATE_VERIFY_EN=7459709\" } else { $content = $content -replace 'MAILJET_TEMPLATE_VERIFY_EN=.*', 'MAILJET_TEMPLATE_VERIFY_EN=7459709'; Set-Content $envPath $content -NoNewline }; $content = Get-Content $envPath -Raw; if ($content -notmatch 'MAILJET_TEMPLATE_VERIFY_RU=') { Add-Content $envPath \"`nMAILJET_TEMPLATE_VERIFY_RU=7459713\" } else { $content = $content -replace 'MAILJET_TEMPLATE_VERIFY_RU=.*', 'MAILJET_TEMPLATE_VERIFY_RU=7459713'; Set-Content $envPath $content -NoNewline }; $content = Get-Content $envPath -Raw; if ($content -notmatch 'MAILJET_TEMPLATE_VERIFY_HE=') { Add-Content $envPath \"`nMAILJET_TEMPLATE_VERIFY_HE=7459704\" } else { $content = $content -replace 'MAILJET_TEMPLATE_VERIFY_HE=.*', 'MAILJET_TEMPLATE_VERIFY_HE=7459704'; Set-Content $envPath $content -NoNewline }"

echo.
echo ================================================================
echo    ✅ Mailjet Configuration Added!
echo ================================================================
echo.
echo Added to backend\.env:
echo   - MAILJET_API_KEY=7fddcffd9c674043d468c076f6b3f399
echo   - MAILJET_SECRET_KEY=63cad8b87cd6be051280f3fa1e5c3c41
echo   - MAILJET_SENDER_EMAIL=support@bishul.me
echo   - MAILJET_SENDER_NAME=BishulSheli
echo   - MAILJET_TEMPLATE_VERIFY_EN=7459709
echo   - MAILJET_TEMPLATE_VERIFY_RU=7459713
echo   - MAILJET_TEMPLATE_VERIFY_HE=7459704
echo.
echo 🧪 Test emails with:
echo    cd backend
echo    python manage.py test_verification_email your@email.com --all-languages
echo.
pause

