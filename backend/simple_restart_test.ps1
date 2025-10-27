Write-Host "`nComplete Backend Restart and Test`n" -ForegroundColor Cyan

Write-Host "[1/4] Stopping Python processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*menumine-ai*"} | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Host "Done`n" -ForegroundColor Green

Write-Host "[2/4] Clearing cache..." -ForegroundColor Yellow
Set-Location C:\Users\al7ko\Desktop\menumine-ai\backend
Remove-Item -Recurse -Force apps\users\__pycache__ -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force apps\__pycache__ -ErrorAction SilentlyContinue
Write-Host "Done`n" -ForegroundColor Green

Write-Host "[3/4] Starting backend..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "manage.py", "runserver" -WorkingDirectory "C:\Users\al7ko\Desktop\menumine-ai\backend"
Start-Sleep -Seconds 10
Write-Host "Done`n" -ForegroundColor Green

Write-Host "[4/4] Running tests..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
python test_email_verification_complete.py

Write-Host "`nDone!`n" -ForegroundColor Cyan

