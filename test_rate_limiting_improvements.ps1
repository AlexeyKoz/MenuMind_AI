# MenuMind AI - Rate Limiting Improvements Test Script
# Tests:
# 1. HTTP Headers on successful requests
# 2. User rate limit status endpoint
# 3. Admin metrics dashboard endpoint

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   Rate Limiting Improvements Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"
$testResults = @()

# Test credentials
$testuser1 = @{
    username = "testuser1"
    password = "TestPassword123!"
}

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers,
        [object]$Body
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    
    try {
        $params = @{
            Uri         = $Url
            Method      = $Method
            Headers     = $Headers
            ContentType = "application/json"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json)
        }
        
        $response = Invoke-WebRequest @params -ErrorAction Stop
        
        Write-Host "  Success: Status $($response.StatusCode)" -ForegroundColor Green
        
        # Parse response
        $data = $response.Content | ConvertFrom-Json
        
        # Check for rate limit headers
        $rateLimitHeaders = @(
            'X-RateLimit-Limit-Minute',
            'X-RateLimit-Remaining-Minute',
            'X-RateLimit-Reset-Minute',
            'X-RateLimit-Limit-Daily',
            'X-RateLimit-Remaining-Daily',
            'X-RateLimit-Reset-Daily'
        )
        
        $headersFound = @()
        foreach ($header in $rateLimitHeaders) {
            $headerValue = $response.Headers[$header]
            if ($headerValue) {
                $headersFound += "${header}: ${headerValue}"
            }
        }
        
        if ($headersFound.Count -gt 0) {
            Write-Host "  Rate Limit Headers Found:" -ForegroundColor Green
            foreach ($h in $headersFound) {
                Write-Host "    - $h" -ForegroundColor Gray
            }
        }
        
        return @{
            Success = $true
            Status  = $response.StatusCode
            Data    = $data
            Headers = $response.Headers
        }
        
    }
    catch {
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        return @{
            Success = $false
            Error   = $_.Exception.Message
        }
    }
}

# Get auth token
Write-Host "`n1. Getting authentication token..." -ForegroundColor Cyan
try {
    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/users/auth/login/" -Method Post `
        -Body (@{
            username = $testuser1.username
            password = $testuser1.password
        } | ConvertTo-Json) -ContentType "application/json"

    if ($loginResponse.access) {
        $token = $loginResponse.access
        Write-Host "  Logged in as $($testuser1.username)" -ForegroundColor Green
    }
    else {
        Write-Host "  Failed to login" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "  Error logging in: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$authHeaders = @{
    "Authorization" = "Bearer $token"
}

# Test 1: Check HTTP Headers on Recipe Generation
Write-Host "`n2. Testing HTTP Headers on Recipe Generation..." -ForegroundColor Cyan
$result1 = Test-Endpoint -Name "Recipe Generation with Headers" `
    -Method "POST" `
    -Url "$baseUrl/api/ai_agents/generate_recipes/" `
    -Headers $authHeaders `
    -Body @{
    max_recipes = 1
    cuisine     = "Italian"
}

if ($result1.Success -and $result1.Headers['X-RateLimit-Limit-Daily']) {
    Write-Host "  TEST PASSED: HTTP headers working!" -ForegroundColor Green
    $testResults += "PASS: HTTP Headers"
}
else {
    Write-Host "  TEST FAILED: No rate limit headers found" -ForegroundColor Red
    $testResults += "FAIL: HTTP Headers"
}

# Test 2: User Rate Limit Status Endpoint
Write-Host "`n3. Testing User Rate Limit Status Endpoint..." -ForegroundColor Cyan
$result2 = Test-Endpoint -Name "Rate Limit Status" `
    -Method "GET" `
    -Url "$baseUrl/api/ai/rate-limit-status/" `
    -Headers $authHeaders

if ($result2.Success -and $result2.Data.limits) {
    Write-Host "  TEST PASSED: Status endpoint working!" -ForegroundColor Green
    Write-Host "`n  Status Details:" -ForegroundColor Gray
    Write-Host "    User: $($result2.Data.user)" -ForegroundColor Gray
    Write-Host "    Plan: $($result2.Data.plan)" -ForegroundColor Gray
    Write-Host "    Limit Per Minute: $($result2.Data.limits.per_minute)" -ForegroundColor Gray
    Write-Host "    Limit Per Day: $($result2.Data.limits.per_day)" -ForegroundColor Gray
    Write-Host "    Used Today: $($result2.Data.usage.today)" -ForegroundColor Gray
    Write-Host "    Remaining Today: $($result2.Data.remaining.daily)" -ForegroundColor Gray
    $testResults += "PASS: Status Endpoint"
}
else {
    Write-Host "  TEST FAILED: Status endpoint not working" -ForegroundColor Red
    $testResults += "FAIL: Status Endpoint"
}

# Test 3: Admin Metrics Dashboard
Write-Host "`n4. Testing Admin Metrics Dashboard..." -ForegroundColor Cyan

$result3 = Test-Endpoint -Name "Admin Metrics" `
    -Method "GET" `
    -Url "$baseUrl/api/ai/admin/metrics/" `
    -Headers $authHeaders

if ($result3.Success -and $result3.Data.overview) {
    Write-Host "  TEST PASSED: Admin metrics working!" -ForegroundColor Green
    Write-Host "`n  Metrics Overview:" -ForegroundColor Gray
    Write-Host "    Total Requests Today: $($result3.Data.overview.total_requests_today)" -ForegroundColor Gray
    Write-Host "    Total Requests (24h): $($result3.Data.overview.total_requests_last_24h)" -ForegroundColor Gray
    Write-Host "    Unique Users Today: $($result3.Data.overview.unique_users_today)" -ForegroundColor Gray
    Write-Host "    Total Recipes Generated Today: $($result3.Data.overview.total_recipes_generated_today)" -ForegroundColor Gray
    
    if ($result3.Data.top_users) {
        Write-Host "`n  Top Users (24h):" -ForegroundColor Gray
        $count = 0
        foreach ($user in $result3.Data.top_users) {
            $count++
            Write-Host "    $count. $($user.user__username): $($user.requests) requests, $($user.recipes) recipes" -ForegroundColor Gray
            if ($count -ge 5) { break }
        }
    }
    
    $testResults += "PASS: Admin Metrics"
}
elseif ($result3.Error -match "403|Admin access required") {
    Write-Host "  TEST SKIPPED: User is not admin" -ForegroundColor Yellow
    Write-Host "    Note: To test admin metrics, make testuser1 a staff user in Django admin" -ForegroundColor Yellow
    $testResults += "SKIP: Admin Metrics (not admin)"
}
else {
    Write-Host "  TEST FAILED: Admin metrics not working" -ForegroundColor Red
    $testResults += "FAIL: Admin Metrics"
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   Test Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

foreach ($result in $testResults) {
    if ($result -match "^PASS") {
        Write-Host "  $result" -ForegroundColor Green
    }
    elseif ($result -match "^SKIP") {
        Write-Host "  $result" -ForegroundColor Yellow
    }
    else {
        Write-Host "  $result" -ForegroundColor Red
    }
}

$passCount = ($testResults | Where-Object { $_ -match "^PASS" }).Count
$totalCount = $testResults.Count

Write-Host "`n  Result: $passCount/$totalCount tests passed" -ForegroundColor Cyan

# Additional test: Show headers format example
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   HTTP Headers Example" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($result1.Headers) {
    Write-Host "Example headers sent with recipe generation response:" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  X-RateLimit-Limit-Minute: $($result1.Headers['X-RateLimit-Limit-Minute'])" -ForegroundColor Gray
    Write-Host "  X-RateLimit-Remaining-Minute: $($result1.Headers['X-RateLimit-Remaining-Minute'])" -ForegroundColor Gray
    Write-Host "  X-RateLimit-Reset-Minute: $($result1.Headers['X-RateLimit-Reset-Minute'])" -ForegroundColor Gray
    Write-Host "  X-RateLimit-Limit-Daily: $($result1.Headers['X-RateLimit-Limit-Daily'])" -ForegroundColor Gray
    Write-Host "  X-RateLimit-Remaining-Daily: $($result1.Headers['X-RateLimit-Remaining-Daily'])" -ForegroundColor Gray
    Write-Host "  X-RateLimit-Reset-Daily: $($result1.Headers['X-RateLimit-Reset-Daily'])" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Frontend can use these headers to:" -ForegroundColor Yellow
    Write-Host "  - Display usage quota to users" -ForegroundColor Gray
    Write-Host "  - Show countdown timers" -ForegroundColor Gray
    Write-Host "  - Disable buttons when limit reached" -ForegroundColor Gray
    Write-Host "  - Calculate optimal request timing" -ForegroundColor Gray
}

Write-Host "`n========================================`n" -ForegroundColor Cyan
