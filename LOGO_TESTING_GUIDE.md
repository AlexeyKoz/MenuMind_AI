# 🧪 Logo Management System - Testing Guide

## Overview

This guide covers all testing for the logo management system, including:
- Backend unit tests (Django)
- Frontend unit tests (Jest)
- API integration tests
- End-to-end workflow tests
- Manual testing procedures

---

## 🚀 Quick Start

### Run All Tests

```bash
# Windows
run_logo_tests.bat

# Linux/Mac
chmod +x run_logo_tests.sh
./run_logo_tests.sh
```

This will run:
1. Backend tests (Django unit tests)
2. API tests (Python E2E tests)
3. Frontend tests (Jest)

---

## 🔧 Prerequisites

### Backend Tests
```bash
# Ensure backend is running
docker-compose -f docker-compose.prod.yml up -d backend

# OR for local development
start_fullstack_complete.bat
```

### Frontend Tests
```bash
cd frontend
npm install
```

### Python E2E Tests
```bash
pip install requests colorama
```

---

## 📋 Test Coverage

### 1. Backend Tests (`backend/branding/tests.py`)

**What's Tested:**
- ✅ SiteLogo model creation and validation
- ✅ Logo uniqueness (one active per type+language)
- ✅ Multi-language support (EN, RU, HE)
- ✅ Logo API endpoints
- ✅ Filtering by language and type
- ✅ Fallback logic (specific → all → static)
- ✅ PWA manifest endpoint
- ✅ SiteSettings singleton pattern

**Run Backend Tests:**
```bash
# In Docker
docker exec menumine_backend_prod python manage.py test branding

# With verbose output
docker exec menumine_backend_prod python manage.py test branding --verbosity=2

# Specific test
docker exec menumine_backend_prod python manage.py test branding.tests.SiteLogoModelTests
```

**Expected Output:**
```
Creating test database...
.......................
----------------------------------------------------------------------
Ran 23 tests in 2.345s

OK
```

---

### 2. Frontend Tests (`frontend/src/services/logoService.test.ts`)

**What's Tested:**
- ✅ Logo fetching for all 3 languages
- ✅ Caching behavior (1 hour cache)
- ✅ Cache clearing
- ✅ Fallback on API errors
- ✅ Timeout handling
- ✅ Specific logo type fetching
- ✅ Navbar logo (desktop/mobile)
- ✅ Login page logo
- ✅ Favicon retrieval
- ✅ Dynamic favicon updates
- ✅ Language-specific logo loading

**Run Frontend Tests:**
```bash
cd frontend

# Run all tests
npm test

# Run only logo tests
npm test -- logoService.test.ts

# With coverage
npm test -- --coverage logoService.test.ts

# Watch mode
npm test -- --watch logoService.test.ts
```

**Expected Output:**
```
PASS  src/services/logoService.test.ts
  LogoService
    getLogos
      ✓ should fetch logos for English (45ms)
      ✓ should fetch logos for Russian (12ms)
      ✓ should fetch logos for Hebrew (10ms)
      ✓ should cache logos for 1 hour (8ms)
      ✓ should return empty object on API error (5ms)
    ...

Test Suites: 1 passed, 1 total
Tests:       18 passed, 18 total
```

---

### 3. End-to-End API Tests (`test_logo_system.py`)

**What's Tested:**
- ✅ API health check
- ✅ Branding endpoint accessibility
- ✅ Admin panel accessibility
- ✅ Logo retrieval for EN/RU/HE
- ✅ Navbar desktop logos (all languages)
- ✅ Navbar mobile logos (all languages)
- ✅ Login page logos (all languages)
- ✅ Favicon (all languages)
- ✅ App icon/PWA (all languages)
- ✅ Manifest endpoint (all languages)

**Run E2E Tests:**
```bash
# Standard output
python test_logo_system.py

# Verbose output
python test_logo_system.py --verbose
```

**Expected Output:**
```
======================================================================
         LOGO MANAGEMENT SYSTEM - COMPREHENSIVE TESTS
======================================================================

Testing API: http://localhost:8000
Testing Admin: http://localhost:8000/admin

======================================================================
                     SYSTEM HEALTH CHECK
======================================================================
✓ PASS API health check
       Backend is running

======================================================================
                  BRANDING API ENDPOINT
======================================================================
✓ PASS Branding API endpoint accessible
       Status: 200

======================================================================
              NAVBAR DESKTOP LOGO - ALL LANGUAGES
======================================================================
✓ PASS Navbar Desktop (EN)
       URL: http://localhost:8000/media/branding/logos/navbar...
✓ PASS Navbar Desktop (RU)
       URL: http://localhost:8000/media/branding/logos/navbar...
✓ PASS Navbar Desktop (HE)
       URL: http://localhost:8000/media/branding/logos/navbar...

... (more tests)

======================================================================
TEST SUMMARY
======================================================================

Total Tests: 32
Passed: 32
Failed: 0
Success Rate: 100.0%

======================================================================
```

---

## 🎯 Manual Testing Checklist

### Test 1: Admin Logo Upload

1. **Access Admin:**
   - Go to http://localhost:8000/admin/
   - Login with admin credentials
   - Navigate to **Site Branding → Site Logos**

2. **Upload via Quick Setup:**
   - Click **"Quick Setup"** button
   - Upload logos for all languages:
     - Navbar Desktop: EN, RU, HE
     - Navbar Mobile: EN, RU, HE
     - Login Page: EN, RU, HE
     - Favicon: All
     - App Icon: All
   - Click **"Upload All Logos"**

3. **Verify Upload:**
   - Check list shows all uploaded logos
   - Preview thumbnails visible
   - Active status = ✓ (checked)

**Expected Result:** ✅ All logos uploaded successfully

---

### Test 2: API Returns Logos

**Test English:**
```bash
curl http://localhost:8000/api/branding/logos/for_language/?lang=en | python -m json.tool
```

**Expected Response:**
```json
{
  "navbar_desktop": {
    "id": "uuid-here",
    "logo_type": "navbar_desktop",
    "language_code": "en",
    "file_url": "http://localhost:8000/media/branding/logos/navbar_desktop_en_abc123.svg",
    "alt_text": "BishulSheli",
    "is_active": true,
    "width": 200,
    "height": 50,
    "dimensions": "200x50"
  },
  "navbar_mobile": { ... },
  "login_page": { ... }
}
```

**Repeat for Russian and Hebrew:**
```bash
curl http://localhost:8000/api/branding/logos/for_language/?lang=ru | python -m json.tool
curl http://localhost:8000/api/branding/logos/for_language/?lang=he | python -m json.tool
```

**Expected Result:** ✅ All 3 languages return their respective logos

---

### Test 3: Frontend Logo Display

#### Test 3a: Login Page Logo

1. Open http://localhost/login
2. Check language selector shows current language
3. Verify logo matches the language:
   - **English:** English logo displayed
   - **Russian:** Russian/English logo displayed
   - **Hebrew:** Hebrew logo displayed

**Steps:**
- Switch to English → Verify English login logo
- Switch to Russian → Verify Russian login logo
- Switch to Hebrew → Verify Hebrew login logo

**Expected Result:** ✅ Logo changes based on selected language

---

#### Test 3b: Navbar Desktop Logo

1. Login to the application
2. View navigation bar on **desktop** (browser width > 768px)
3. Verify horizontal logo displayed
4. Switch languages (EN → RU → HE)
5. Verify logo updates for each language

**Expected Result:** ✅ Navbar logo changes per language

---

#### Test 3c: Navbar Mobile Logo

1. Open browser DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Select mobile device (iPhone, Android)
4. Verify compact/square logo displayed
5. Switch languages
6. Verify mobile logo updates

**Expected Result:** ✅ Mobile logo changes per language

---

#### Test 3d: Favicon (Browser Tab Icon)

1. Look at browser tab
2. Verify favicon displays correctly
3. Switch languages
4. Check if favicon updates (may require page refresh)

**Expected Result:** ✅ Favicon visible in browser tab

---

### Test 4: Language Switching

**Test Scenario:**
1. Start on English
2. Switch to Russian
3. Switch to Hebrew
4. Switch back to English

**What to Check:**
- ✅ Navbar logo changes
- ✅ Mobile logo changes (on mobile view)
- ✅ Login page logo changes
- ✅ No JavaScript errors in console
- ✅ Smooth transition (no flickering)

---

### Test 5: Fallback Logic

**Scenario:** Delete Russian logos, keep only English and Hebrew

**Steps:**
1. In admin, deactivate all Russian logos
2. Switch to Russian language on frontend
3. Verify it falls back to "all" language or static logos

**Expected Result:** ✅ App still displays logos (fallback works)

---

### Test 6: Cache Behavior

**Steps:**
1. Open browser DevTools → Network tab
2. Load page (logos fetched from API)
3. Refresh page within 1 hour
4. Check Network tab: API not called again (cached)
5. Wait 1 hour OR clear cache via `logoService.clearCache()`
6. Refresh: API called again

**Expected Result:** ✅ Caching reduces API calls

---

### Test 7: Admin Quick Setup

1. Go to **Site Logos** in admin
2. Click **"Quick Setup"**
3. Verify form has 5 sections:
   - Navbar Desktop (EN/RU/HE)
   - Navbar Mobile (EN/RU/HE)
   - Login Page (EN/RU/HE)
   - Favicon (EN/RU/HE)
   - App Icon (EN/RU/HE)
4. Upload multiple logos at once
5. Click **"Upload All Logos"**
6. Verify success message
7. Check logos appear in list

**Expected Result:** ✅ Bulk upload works correctly

---

### Test 8: Individual Logo Edit

1. Click on any logo in the list
2. Verify large preview displays
3. Change image file
4. Change alt text
5. Toggle active status
6. Save
7. Verify changes reflected in API

**Expected Result:** ✅ Individual edits work

---

## 🐛 Troubleshooting

### Backend Tests Fail

**Problem:** `django.db.utils.OperationalError: no such table: site_logos`

**Solution:**
```bash
docker exec menumine_backend_prod python manage.py migrate branding
```

---

### Frontend Tests Fail

**Problem:** `Cannot find module 'logoService'`

**Solution:**
```bash
cd frontend
npm install
```

---

### E2E Tests Show "Backend not running"

**Problem:** API not accessible

**Solution:**
```bash
# Start backend
docker-compose -f docker-compose.prod.yml up -d backend

# OR
start_fullstack_complete.bat
```

---

### Logos Not Showing in Tests

**Problem:** API returns empty objects

**Solution:**
1. Upload logos via admin: http://localhost:8000/admin/
2. Use Quick Setup to upload all logos
3. Ensure logos are marked as "Active"

---

### Cache Issues

**Problem:** Old logos showing after update

**Solution:**
```javascript
// In browser console
logoService.clearCache();
location.reload();
```

**Or clear backend cache:**
```bash
docker exec menumine_backend_prod python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

---

## 📊 Test Results Interpretation

### All Tests Pass (100%)
✅ **System is production-ready!**
- All features working
- All languages supported
- API stable
- Frontend integration complete

### 80-99% Pass
⚠️ **Minor issues detected**
- Check failed tests
- May be missing some logos
- Non-critical functionality affected

### Below 80% Pass
❌ **Critical issues**
- Backend may not be running
- Migrations not applied
- No logos uploaded
- API endpoint misconfigured

---

## 🎯 Testing Workflow

### After Initial Setup
```bash
1. deploy_logo_system.bat        # Deploy system
2. Upload logos via admin        # Add content
3. run_logo_tests.bat           # Run all tests
4. Check test results           # Verify success
```

### After Making Changes
```bash
1. Make code changes
2. docker-compose -f docker-compose.prod.yml restart backend
3. run_logo_tests.bat
4. Manual testing (if needed)
```

### Before Production Deployment
```bash
1. run_logo_tests.bat           # All tests must pass
2. Manual testing checklist     # Verify UI/UX
3. Performance testing          # Check load times
4. Deploy to production
```

---

## 📝 Test Documentation

Each test file includes inline documentation:

- **`backend/branding/tests.py`**: Django test docstrings
- **`frontend/src/services/logoService.test.ts`**: Jest test descriptions
- **`test_logo_system.py`**: Python docstrings and comments

---

## 🚀 Continuous Integration

### GitHub Actions Example

```yaml
name: Logo System Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Start Docker Containers
        run: docker-compose -f docker-compose.prod.yml up -d
      
      - name: Run Backend Tests
        run: docker exec menumine_backend_prod python manage.py test branding
      
      - name: Run API Tests
        run: |
          pip install requests colorama
          python test_logo_system.py
      
      - name: Run Frontend Tests
        run: |
          cd frontend
          npm install
          npm test -- logoService.test.ts
```

---

## 📚 Additional Resources

- **Django Testing**: https://docs.djangoproject.com/en/4.2/topics/testing/
- **Jest Documentation**: https://jestjs.io/docs/getting-started
- **Requests Library**: https://requests.readthedocs.io/

---

**Happy Testing!** 🧪✅

