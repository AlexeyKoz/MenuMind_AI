# Complete Backend Restart and Test Script

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  COMPLETE BACKEND RESTART & TEST" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Kill all Python processes
Write-Host "[1/5] Stopping all Python processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*menumine-ai*"} | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Host "   ✓ Python processes stopped`n" -ForegroundColor Green

# Step 2: Clear Python cache
Write-Host "[2/5] Clearing Python cache..." -ForegroundColor Yellow
Set-Location C:\Users\al7ko\Desktop\menumine-ai\backend
Remove-Item -Recurse -Force apps\users\__pycache__ -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force apps\__pycache__ -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force __pycache__ -ErrorAction SilentlyContinue
Write-Host "   ✓ Cache cleared`n" -ForegroundColor Green

# Step 3: Start backend in background
Write-Host "[3/5] Starting backend..." -ForegroundColor Yellow
$backend = Start-Process -FilePath "python" -ArgumentList "manage.py", "runserver" -PassThru -NoNewWindow -RedirectStandardOutput "backend_output.log" -RedirectStandardError "backend_error.log"
Write-Host "   ✓ Backend starting (PID: $($backend.Id))`n" -ForegroundColor Green

# Step 4: Wait for backend to be ready
Write-Host "[4/5] Waiting for backend to be ready..." -ForegroundColor Yellow
$maxWait = 30
$waited = 0
$ready = $false

while ($waited -lt $maxWait) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
    $waited++
    Write-Host "   Waiting... ($waited/$maxWait seconds)" -NoNewline -ForegroundColor Gray
    Write-Host "`r" -NoNewline
}

if ($ready) {
    Write-Host "   ✓ Backend is ready!              `n" -ForegroundColor Green
} else {
    Write-Host "   ✗ Backend failed to start`n" -ForegroundColor Red
    Write-Host "Check logs:" -ForegroundColor Yellow
    Write-Host "   backend_output.log"
    Write-Host "   backend_error.log"
    exit 1
}

# Step 5: Run tests
Write-Host "[5/5] Running automated tests...`n" -ForegroundColor Yellow
python test_email_verification_complete.py

# Cleanup
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Backend is still running (PID: $($backend.Id))" -ForegroundColor Cyan
Write-Host "To stop it: Stop-Process -Id $($backend.Id)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

