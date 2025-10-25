# Version Control System - Testing Guide

## 🧪 Complete Testing Checklist

Let's test every component of the version control system!

---

## TEST 1: Backend Version Endpoint ✅

### Test the Version API

**URL**: http://localhost:8000/api/core/version/

**Expected Response:**
```json
{
  "version": "0.9.0",
  "app_name": "MenuMind AI",
  "author": "Alexey Kozlov",
  "license": "MIT",
  "build_date": "2025-10-25",
  "environment": "development",
  "api_version": "v1",
  "python_version": "3.13.0",
  "django_version": "4.2.7",
  "server_time": "2025-10-25T..."
}
```

### Test Commands:

```bash
# Test 1: Using curl
curl http://localhost:8000/api/core/version/

# Test 2: Using PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/api/core/version/" | Select-Object -ExpandProperty Content | ConvertFrom-Json

# Test 3: Using browser
# Open: http://localhost:8000/api/core/version/
```

**✅ Pass Criteria:**
- Returns 200 OK
- Shows version "0.9.0"
- All fields present
- No authentication required

---

## TEST 2: Health Check Endpoint ✅

**URL**: http://localhost:8000/api/core/health/

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "0.9.0",
  "timestamp": "2025-10-25T...",
  "services": {
    "database": "healthy",
    "cache": "healthy"
  }
}
```

### Test Command:
```bash
curl http://localhost:8000/api/core/health/
```

**✅ Pass Criteria:**
- Returns 200 OK
- Shows version "0.9.0"
- All services healthy

---

## TEST 3: Frontend Footer Display ✅

### Where to Check:
1. **Login Page**: http://localhost:3000/
2. **Dashboard**: http://localhost:3000/dashboard
3. **Settings Page**: http://localhost:3000/app-settings
4. **Any Page**: Footer should be visible at bottom

**Expected Display:**
```
© 2025 Alexey Kozlov. All rights reserved. | About | Settings | v0.9.0
```

**✅ Pass Criteria:**
- Footer visible on all pages
- Shows "v0.9.0" on the right side
- Copyright shows "2025"
- Links work (About, Settings)

---

## TEST 4: Settings Page Version Info ✅

### Navigation:
1. Login to the app
2. Go to Settings: http://localhost:3000/app-settings
3. Scroll to "About" section

**Expected Display:**
```
About
┌─────────────────────────────────┐
│ Application:     MenuMind AI v0.9.0 │
│ Frontend Version: v0.9.0        │
│ Backend Version:  v0.9.0        │
│ Environment:      Development   │
│ API Version:      v1            │
│ Build Date:       2025-10-25    │
│ Author:           Alexey Kozlov │
└─────────────────────────────────┘
```

**✅ Pass Criteria:**
- Shows frontend version: 0.9.0
- Shows backend version: 0.9.0 (loaded from API)
- Environment shows "development"
- No loading errors
- Build date is today

---

## TEST 5: Version Update Script ✅

### Test the Automated Updater

```bash
# Navigate to project root
cd C:\Users\al7ko\Desktop\menumine-ai

# Test dry run (will ask for confirmation, say 'n')
python scripts/update_version.py 0.9.1

# Expected output:
# ⚠️  About to update MenuMind AI to version 0.9.1
# This will modify the following files:
#   - backend/menumine_ai/__init__.py
#   - backend/menumine_ai/settings.py
#   - frontend/package.json
#   - frontend/src/config/version.ts
# 
# Continue? [y/N]: n
# ❌ Cancelled
```

**✅ Pass Criteria:**
- Script runs without errors
- Shows correct file list
- Validates version format
- Asks for confirmation
- Can be cancelled

---

## TEST 6: Invalid Version Format ✅

### Test Error Handling

```bash
# Test invalid formats
python scripts/update_version.py 1.0          # Invalid (needs MAJOR.MINOR.PATCH)
python scripts/update_version.py abc          # Invalid (not numbers)
python scripts/update_version.py              # Invalid (no version provided)

# Expected: Error message with valid format examples
```

**✅ Pass Criteria:**
- Rejects invalid formats
- Shows helpful error messages
- Provides examples

---

## TEST 7: CHANGELOG.md ✅

### Verify Changelog

```bash
# View changelog
cat CHANGELOG.md

# Or open in text editor
notepad CHANGELOG.md
```

**✅ Pass Criteria:**
- File exists in project root
- Contains version 0.9.0 section
- Follows Keep a Changelog format
- Has all categories (Added, Changed, Fixed)
- Includes migration guides

---

## TEST 8: Rate Limiting Integration ✅

### Verify Rate Limiting Still Works

**As Regular User:**
```bash
# Login as regular user (not testuser1/testuser2)
# Try to generate 6 recipes quickly (should hit per-minute limit)
```

**Expected:**
- First 5 requests succeed
- 6th request returns 429 error with friendly message

**As Exempt User (testuser1):**
```bash
# Login as testuser1
# Generate as many recipes as you want
```

**Expected:**
- All requests succeed
- No rate limiting

**✅ Pass Criteria:**
- Rate limiting still works
- Version info included in successful responses
- Both systems work together

---

## TEST 9: Cross-Origin Requests ✅

### Test from Frontend

Open browser console on http://localhost:3000 and run:

```javascript
// Test version endpoint
fetch('http://localhost:8000/api/core/version/')
  .then(r => r.json())
  .then(data => console.log('Version:', data.version));

// Should output: Version: 0.9.0
```

**✅ Pass Criteria:**
- No CORS errors
- Returns version data
- Works without authentication

---

## TEST 10: Multiple Language Support ✅

### Test Footer in Different Languages

1. **English**: Switch to English → Check footer shows "All rights reserved"
2. **Russian**: Switch to Russian → Check footer shows "Все права защищены"
3. **Hebrew**: Switch to Hebrew → Check footer shows "כל הזכויות שמורות"

**Version should stay the same** (v0.9.0) **in all languages**

**✅ Pass Criteria:**
- Footer text translates
- Version stays "v0.9.0" (not translated)
- Layout works in RTL (Hebrew)

---

## TEST 11: Mobile Responsiveness ✅

### Test on Mobile Size

1. Open browser DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Select mobile device (e.g., iPhone 12)
4. Navigate to different pages

**✅ Pass Criteria:**
- Footer remains visible
- Version number readable
- No layout breaking
- Works on all screen sizes

---

## TEST 12: Build Date Auto-Update ✅

### Verify Build Date

Check that build date updates automatically:

```typescript
// In frontend/src/config/version.ts
export const APP_BUILD_DATE = '2025-10-25';
```

```python
# In backend/menumine_ai/settings.py
APP_BUILD_DATE = date.today().isoformat()  # Auto-updates
```

**✅ Pass Criteria:**
- Frontend shows static date: "2025-10-25"
- Backend auto-updates to today's date
- Both are displayed correctly in Settings page

---

## 📊 TEST RESULTS SUMMARY

Copy this table and fill in your results:

```
┌──────────────────────────────────────┬────────┬───────────┐
│ Test                                 │ Status │ Notes     │
├──────────────────────────────────────┼────────┼───────────┤
│ 1. Backend Version Endpoint          │ [ ]    │           │
│ 2. Health Check Endpoint             │ [ ]    │           │
│ 3. Frontend Footer Display           │ [ ]    │           │
│ 4. Settings Page Version Info        │ [ ]    │           │
│ 5. Version Update Script             │ [ ]    │           │
│ 6. Invalid Version Format            │ [ ]    │           │
│ 7. CHANGELOG.md                      │ [ ]    │           │
│ 8. Rate Limiting Integration         │ [ ]    │           │
│ 9. Cross-Origin Requests             │ [ ]    │           │
│ 10. Multiple Language Support        │ [ ]    │           │
│ 11. Mobile Responsiveness            │ [ ]    │           │
│ 12. Build Date Auto-Update           │ [ ]    │           │
└──────────────────────────────────────┴────────┴───────────┘

Legend: [✅] Pass | [❌] Fail | [⚠️] Partial
```

---

## 🚀 Quick Test Script

Run all automated tests at once:

```powershell
# Save as test_version_control.ps1

Write-Host "🧪 Testing MenuMind AI Version Control System" -ForegroundColor Cyan
Write-Host "=" * 60

# Test 1: Backend Version Endpoint
Write-Host "`n📡 Test 1: Backend Version Endpoint" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/core/version/" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    if ($data.version -eq "0.9.0") {
        Write-Host "✅ PASS: Version endpoint returns 0.9.0" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL: Expected 0.9.0, got $($data.version)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ FAIL: Cannot reach endpoint - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Health Check
Write-Host "`n📡 Test 2: Health Check Endpoint" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/core/health/" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    if ($data.version -eq "0.9.0" -and $data.status -eq "healthy") {
        Write-Host "✅ PASS: Health check includes version" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL: Health check incomplete" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ FAIL: Cannot reach endpoint" -ForegroundColor Red
}

# Test 3: Version Update Script
Write-Host "`n🔧 Test 3: Version Update Script" -ForegroundColor Yellow
if (Test-Path "scripts/update_version.py") {
    Write-Host "✅ PASS: Script exists" -ForegroundColor Green
} else {
    Write-Host "❌ FAIL: Script not found" -ForegroundColor Red
}

# Test 4: CHANGELOG
Write-Host "`n📄 Test 4: CHANGELOG.md" -ForegroundColor Yellow
if (Test-Path "CHANGELOG.md") {
    $content = Get-Content "CHANGELOG.md" -Raw
    if ($content -match "0\.9\.0") {
        Write-Host "✅ PASS: CHANGELOG contains 0.9.0" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL: CHANGELOG missing 0.9.0" -ForegroundColor Red
    }
} else {
    Write-Host "❌ FAIL: CHANGELOG not found" -ForegroundColor Red
}

# Test 5: Frontend Config
Write-Host "`n📱 Test 5: Frontend Version Config" -ForegroundColor Yellow
if (Test-Path "frontend/src/config/version.ts") {
    $content = Get-Content "frontend/src/config/version.ts" -Raw
    if ($content -match "APP_VERSION = '0\.9\.0'") {
        Write-Host "✅ PASS: Frontend version is 0.9.0" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL: Frontend version mismatch" -ForegroundColor Red
    }
} else {
    Write-Host "❌ FAIL: version.ts not found" -ForegroundColor Red
}

Write-Host "`n" + ("=" * 60)
Write-Host "✅ Automated tests complete!" -ForegroundColor Cyan
Write-Host "📝 Please manually test UI components in browser" -ForegroundColor Yellow
```

**Run it:**
```powershell
cd C:\Users\al7ko\Desktop\menumine-ai
.\test_version_control.ps1
```

---

## 🎯 Expected Results

If everything works correctly:

- ✅ All API endpoints return version 0.9.0
- ✅ Footer shows v0.9.0 on all pages
- ✅ Settings page displays complete version info
- ✅ Update script validates and confirms
- ✅ CHANGELOG is complete
- ✅ Rate limiting still works
- ✅ Multi-language support works
- ✅ Mobile responsive

---

## 🐛 Troubleshooting

### Issue: Backend endpoint returns 404
**Solution**: Check that `/api/core/` is mounted in main urls.py

### Issue: Frontend shows "Loading backend info..."
**Solution**: 
1. Check CORS settings
2. Verify API URL in .env
3. Check browser console for errors

### Issue: Version script fails
**Solution**: 
1. Run from project root
2. Check Python version (3.7+)
3. Verify file paths exist

### Issue: Footer not showing
**Solution**: 
1. Check App.tsx has `<Footer />` component
2. Verify import path
3. Check for CSS conflicts

---

## ✅ Sign-Off Checklist

Before considering version control complete:

- [ ] Backend version endpoint works
- [ ] Frontend displays version correctly
- [ ] Settings page shows all version info
- [ ] Update script runs successfully
- [ ] CHANGELOG is up to date
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Git tag can be created

---

**Ready to test!** Start with Test 1 and work your way down. 🚀

