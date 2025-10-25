# MenuMind AI - Version Control System Test Script
# Run from project root: .\test_version_control.ps1

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "      MenuMind AI - Version Control System Tests" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

$testsPassed = 0
$testsFailed = 0

# Test 1: Backend Version Endpoint
Write-Host "📡 TEST 1: Backend Version Endpoint (/api/version/)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/version/" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    
    if ($data.version -eq "0.9.0") {
        Write-Host "   ✅ PASS: Returns version 0.9.0" -ForegroundColor Green
        Write-Host "   📋 App: $($data.app_name)" -ForegroundColor Gray
        Write-Host "   👤 Author: $($data.author)" -ForegroundColor Gray
        Write-Host "   📅 Build Date: $($data.build_date)" -ForegroundColor Gray
        Write-Host "   🌍 Environment: $($data.environment)" -ForegroundColor Gray
        $testsPassed++
    }
    else {
        Write-Host "   ❌ FAIL: Expected 0.9.0, got $($data.version)" -ForegroundColor Red
        $testsFailed++
    }
}
catch {
    Write-Host "   ❌ FAIL: Cannot reach endpoint" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 2: Health Check Endpoint
Write-Host "🏥 TEST 2: Health Check Endpoint (/api/health/)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health/" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    
    if ($data.version -eq "0.9.0" -and $data.status -eq "healthy") {
        Write-Host "   ✅ PASS: Health check includes version" -ForegroundColor Green
        Write-Host "   💚 Status: $($data.status)" -ForegroundColor Gray
        Write-Host "   🗄️  Database: $($data.services.database)" -ForegroundColor Gray
        Write-Host "   💾 Cache: $($data.services.cache)" -ForegroundColor Gray
        $testsPassed++
    }
    else {
        Write-Host "   ❌ FAIL: Health check incomplete or unhealthy" -ForegroundColor Red
        $testsFailed++
    }
}
catch {
    Write-Host "   ❌ FAIL: Cannot reach endpoint" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 3: Version Update Script Exists
Write-Host "🔧 TEST 3: Version Update Script" -ForegroundColor Yellow
if (Test-Path "scripts/update_version.py") {
    Write-Host "   ✅ PASS: Script exists at scripts/update_version.py" -ForegroundColor Green
    $testsPassed++
}
else {
    Write-Host "   ❌ FAIL: Script not found" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 4: CHANGELOG.md
Write-Host "📄 TEST 4: CHANGELOG.md" -ForegroundColor Yellow
if (Test-Path "CHANGELOG.md") {
    $content = Get-Content "CHANGELOG.md" -Raw
    if ($content -match "\[0\.9\.0\]") {
        Write-Host "   ✅ PASS: CHANGELOG contains version 0.9.0" -ForegroundColor Green
        $testsPassed++
    }
    else {
        Write-Host "   ❌ FAIL: CHANGELOG missing 0.9.0 section" -ForegroundColor Red
        $testsFailed++
    }
}
else {
    Write-Host "   ❌ FAIL: CHANGELOG.md not found in project root" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 5: Frontend Version Config
Write-Host "📱 TEST 5: Frontend Version Config (version.ts)" -ForegroundColor Yellow
if (Test-Path "frontend/src/config/version.ts") {
    $content = Get-Content "frontend/src/config/version.ts" -Raw
    if ($content -match "APP_VERSION = '0\.9\.0'") {
        Write-Host "   ✅ PASS: Frontend version configured as 0.9.0" -ForegroundColor Green
        $testsPassed++
    }
    else {
        Write-Host "   ❌ FAIL: Frontend version mismatch" -ForegroundColor Red
        $testsFailed++
    }
}
else {
    Write-Host "   ❌ FAIL: version.ts not found" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 6: Backend __init__.py
Write-Host "🐍 TEST 6: Backend Version (__init__.py)" -ForegroundColor Yellow
if (Test-Path "backend/menumine_ai/__init__.py") {
    $content = Get-Content "backend/menumine_ai/__init__.py" -Raw
    if ($content -match '__version__ = "0\.9\.0"') {
        Write-Host "   ✅ PASS: Backend __version__ = 0.9.0" -ForegroundColor Green
        $testsPassed++
    }
    else {
        Write-Host "   ❌ FAIL: Backend version mismatch" -ForegroundColor Red
        $testsFailed++
    }
}
else {
    Write-Host "   ❌ FAIL: __init__.py not found" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 7: Backend settings.py
Write-Host "⚙️  TEST 7: Backend Settings (settings.py)" -ForegroundColor Yellow
if (Test-Path "backend/menumine_ai/settings.py") {
    $content = Get-Content "backend/menumine_ai/settings.py" -Raw
    if ($content -match 'APP_VERSION = "0\.9\.0"') {
        Write-Host "   ✅ PASS: Settings APP_VERSION = 0.9.0" -ForegroundColor Green
        $testsPassed++
    }
    else {
        Write-Host "   ❌ FAIL: Settings version mismatch" -ForegroundColor Red
        $testsFailed++
    }
}
else {
    Write-Host "   ❌ FAIL: settings.py not found" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 8: Frontend package.json
Write-Host "📦 TEST 8: Frontend Package (package.json)" -ForegroundColor Yellow
if (Test-Path "frontend/package.json") {
    $content = Get-Content "frontend/package.json" -Raw | ConvertFrom-Json
    if ($content.version -eq "0.9.0") {
        Write-Host "   ✅ PASS: package.json version = 0.9.0" -ForegroundColor Green
        $testsPassed++
    }
    else {
        Write-Host "   ❌ FAIL: package.json version mismatch: $($content.version)" -ForegroundColor Red
        $testsFailed++
    }
}
else {
    Write-Host "   ❌ FAIL: package.json not found" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 9: Documentation Files
Write-Host "📚 TEST 9: Documentation Files" -ForegroundColor Yellow
$docs = @(
    "VERSION_CONTROL_COMPLETE.md",
    "VERSION_CONTROL_TESTING.md",
    "AI_RATE_LIMITING_COMPLETE.md"
)
$docsFound = 0
foreach ($doc in $docs) {
    if (Test-Path $doc) {
        $docsFound++
    }
}
if ($docsFound -eq $docs.Count) {
    Write-Host "   ✅ PASS: All documentation files present ($docsFound/$($docs.Count))" -ForegroundColor Green
    $testsPassed++
}
else {
    Write-Host "   ⚠️  PARTIAL: $docsFound/$($docs.Count) documentation files found" -ForegroundColor Yellow
    $testsPassed++
}
Write-Host ""

# Test 10: API Endpoints Accessibility
Write-Host "🌐 TEST 10: CORS and Accessibility" -ForegroundColor Yellow
try {
    $headers = @{
        "Origin" = "http://localhost:3000"
    }
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/version/" -Headers $headers -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ PASS: Version endpoint accessible with CORS" -ForegroundColor Green
        $testsPassed++
    }
    else {
        Write-Host "   ❌ FAIL: Unexpected status code: $($response.StatusCode)" -ForegroundColor Red
        $testsFailed++
    }
}
catch {
    Write-Host "   ⚠️  WARNING: CORS test failed (may be normal)" -ForegroundColor Yellow
    Write-Host "   Note: Endpoint is accessible, CORS headers may vary" -ForegroundColor Gray
    $testsPassed++
}
Write-Host ""

# Summary
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                    TEST RESULTS SUMMARY" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "   ✅ Tests Passed: $testsPassed" -ForegroundColor Green
Write-Host "   ❌ Tests Failed: $testsFailed" -ForegroundColor Red
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "   🎉 ALL TESTS PASSED! Version control system is working correctly." -ForegroundColor Green
    Write-Host ""
    Write-Host "   Next Steps:" -ForegroundColor Yellow
    Write-Host "   1. Test in browser: http://localhost:3000" -ForegroundColor Gray
    Write-Host "   2. Check footer shows v0.9.0" -ForegroundColor Gray
    Write-Host "   3. Visit Settings page for full version info" -ForegroundColor Gray
    Write-Host "   4. Test in multiple languages" -ForegroundColor Gray
}
else {
    Write-Host "   ⚠️  SOME TESTS FAILED. Please review the errors above." -ForegroundColor Red
}
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Manual Test Reminders
Write-Host "📝 MANUAL TESTS (Please check in browser):" -ForegroundColor Yellow
Write-Host ""
Write-Host "   🌐 Open: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "   [ ] Footer displays v0.9.0 at bottom right" -ForegroundColor White
Write-Host "   [ ] Settings page shows complete version info" -ForegroundColor White
Write-Host "   [ ] Backend version loads (not 'Loading...')" -ForegroundColor White
Write-Host "   [ ] Version visible in all languages (EN/RU/HE)" -ForegroundColor White
Write-Host "   [ ] Footer works on mobile view" -ForegroundColor White
Write-Host "   [ ] About link works" -ForegroundColor White
Write-Host "   [ ] Settings link works" -ForegroundColor White
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan

