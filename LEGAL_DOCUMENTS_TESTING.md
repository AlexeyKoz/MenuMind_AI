# Legal Documents System - Testing Guide

## ⚠️ CURRENT STATUS

The legal documents system is **code-complete** but needs database connection configuration.

**Error:** `[Errno 11001] getaddrinfo failed` - DNS/hostname resolution issue

---

## 🔧 QUICK FIX - Database Connection

### Check `backend/.env` file and ensure:

```ini
# Database
DB_HOST=localhost    # ← Make sure this is "localhost" not a hostname
DB_PORT=5432
DB_NAME=menumindai
DB_USER=postgres
DB_PASSWORD=MenuMind2025!SecureDB
```

If `DB_HOST` is set to a hostname like `db` or `postgresql`, change it to `localhost`.

---

## 📋 COMPLETE TESTING CHECKLIST

### ✅ Phase 1: Load Documents

Once database is connected, run:

```bash
python backend\manage.py load_bishulsheli_docs --path "legal_documents" --force
```

**Expected Output:**
```
======================================================================
Loading BishulSheli Legal Documents (EN, RU, HE)
======================================================================
Created: Terms of Service (EN) v2.0 - XXXX chars, XXX words
Created: Privacy Policy (EN) v2.0 - XXXX chars, XXX words
Created: Cookie Policy (EN) v2.0 - XXXX chars, XXX words
Created: Copyright Notice (EN) v2.0 - XXXX chars, XXX words
Created: RCIP License (EN) v2.0 - XXXX chars, XXX words
Created: Условия использования (RU) v2.0 - XXXX chars, XXX words
Created: Политика конфиденциальности (RU) v2.0 - XXXX chars, XXX words
Created: Политика cookies (RU) v2.0 - XXXX chars, XXX words
Created: Авторские права (RU) v2.0 - XXXX chars, XXX words
Created: Лицензия RCIP (RU) v2.0 - XXXX chars, XXX words
Created: תנאי שימוש (HE) v2.0 - XXXX chars, XXX words
Created: מדיניות פרטיות (HE) v2.0 - XXXX chars, XXX words
Created: מדיניות עוגיות (HE) v2.0 - XXXX chars, XXX words
Created: זכויות יוצרים (HE) v2.0 - XXXX chars, XXX words
Created: רישיון RCIP (HE) v2.0 - XXXX chars, XXX words
======================================================================
Loaded: 15 | Skipped: 0 | Errors: 0
======================================================================

Total legal documents in database: 15
  - English: 5
  - Russian: 5
  - Hebrew: 5

✅ All BishulSheli documents loaded successfully!
```

---

### ✅ Phase 2: Test API Endpoints

#### Test 1: Terms of Service (English)
```bash
curl http://localhost:8000/api/legal/terms/?lang=en
```

**Expected:** JSON with English terms document

#### Test 2: Privacy Policy (Russian)
```bash
curl http://localhost:8000/api/legal/privacy/?lang=ru
```

**Expected:** JSON with Russian privacy policy

#### Test 3: Cookie Policy (Hebrew)
```bash
curl http://localhost:8000/api/legal/cookies/?lang=he
```

**Expected:** JSON with Hebrew cookie policy

#### Test 4: All Document Types
```bash
# English
curl http://localhost:8000/api/legal/terms/?lang=en
curl http://localhost:8000/api/legal/privacy/?lang=en
curl http://localhost:8000/api/legal/cookies/?lang=en
curl http://localhost:8000/api/legal/copyright/?lang=en
curl http://localhost:8000/api/legal/rcip/?lang=en

# Russian
curl http://localhost:8000/api/legal/terms/?lang=ru
curl http://localhost:8000/api/legal/privacy/?lang=ru
curl http://localhost:8000/api/legal/cookies/?lang=ru
curl http://localhost:8000/api/legal/copyright/?lang=ru
curl http://localhost:8000/api/legal/rcip/?lang=ru

# Hebrew
curl http://localhost:8000/api/legal/terms/?lang=he
curl http://localhost:8000/api/legal/privacy/?lang=he
curl http://localhost:8000/api/legal/cookies/?lang=he
curl http://localhost:8000/api/legal/copyright/?lang=he
curl http://localhost:8000/api/legal/rcip/?lang=he
```

---

### ✅ Phase 3: Test Django Admin

#### 1. **Access Admin Panel**
Navigate to: `http://localhost:8000/admin/legal/legaldocument/`

#### 2. **Check List View**
Verify you see:
- ✅ 15 documents total
- ✅ 5 English (EN)
- ✅ 5 Russian (RU)
- ✅ 5 Hebrew (HE)
- ✅ All marked as "Active"
- ✅ Language code column visible
- ✅ Word count showing

#### 3. **Test File Upload**
1. Click **"Upload Document"** button
2. Fill form:
   - Document Type: `Terms of Service`
   - Language: `English`
   - Version: `2.1`
   - Effective Date: Today
   - Upload File: Any `.md` file
   - Check "Set as Active"
3. Click "Upload"
4. **Expected:** Success message, document appears in list

#### 4. **Test Direct Edit**
1. Click any document
2. Try **both methods:**
   - **Method A:** Upload a new .md file
   - **Method B:** Edit content textarea directly
3. Save
4. **Expected:** Changes saved successfully

---

### ✅ Phase 4: Test Frontend Integration

#### 1. **Check Documents Load**
1. Open http://localhost in browser
2. Open Developer Console (F12)
3. Go to "Network" tab
4. Navigate to Settings > Legal Documents
5. Click on any document link

**Expected Network Requests:**
```
GET /api/legal/terms/?lang=en
Status: 200 OK
Response: JSON with document content
```

#### 2. **Test Language Switching**
1. Change language to Russian
2. Open any legal document
3. **Expected:** Document appears in Russian

**Network Request:**
```
GET /api/legal/terms/?lang=ru
Status: 200 OK
Response: JSON with Russian content
```

#### 3. **Test All Languages**
- Switch to EN → Check all 5 documents
- Switch to RU → Check all 5 documents
- Switch to HE → Check all 5 documents

---

### ✅ Phase 5: Test Google Button Centering

#### Test Scenario 1: Fresh Page Load
1. Open http://localhost
2. Logout if logged in
3. **Check:** Google button is centered

#### Test Scenario 2: Recognized User
1. Login with Google once
2. Logout
3. Return to login page
4. **Check:** Google button stays centered (may show user info)

#### Test Scenario 3: Language Switch
1. On login page, switch languages (EN → RU → HE)
2. **Check:** Button stays centered in all languages

#### Test Scenario 4: Mobile View
1. Open Developer Tools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Test various screen sizes
4. **Check:** Button stays centered on all sizes

---

## 🎯 SUCCESS CRITERIA

### ✅ Legal Documents System
- [ ] All 15 documents loaded successfully
- [ ] API returns correct documents for each language
- [ ] Admin panel shows all documents
- [ ] File upload works from admin
- [ ] Direct editing works in admin
- [ ] Frontend displays documents correctly
- [ ] Language switching works properly

### ✅ Google Button
- [ ] Button centered on fresh page load
- [ ] Button centered with recognized user
- [ ] Button centered on language switch
- [ ] Button centered on mobile view
- [ ] Button centered on tablet view
- [ ] Button centered on desktop view

---

## 🐛 TROUBLESHOOTING

### Problem: Database connection failed
**Solution:**
1. Check PostgreSQL is running: `Get-Process postgres`
2. Update `backend/.env` with `DB_HOST=localhost`
3. Restart Django

### Problem: Documents not loading in frontend
**Solution:**
1. Check API response in browser console
2. Verify documents exist in database
3. Check language code matches (en/ru/he)

### Problem: Admin upload fails
**Solution:**
1. Check file is `.md` format
2. Check file size < 5MB
3. Check file encoding is UTF-8

### Problem: Google button not centered
**Solution:**
1. Clear browser cache (Ctrl+Shift+R)
2. Check `frontend/src/components/GoogleSignInButton.tsx` has latest changes
3. Rebuild frontend if necessary

---

## 📊 AUTOMATED TEST SCRIPT

Create `test_legal_docs.bat`:

```batch
@echo off
echo ========================================
echo Testing Legal Documents System
echo ========================================

echo.
echo [1/5] Testing API Endpoints...
curl -s http://localhost:8000/api/legal/terms/?lang=en | findstr "content" > nul && echo ✓ EN Terms OK || echo ✗ EN Terms FAILED
curl -s http://localhost:8000/api/legal/terms/?lang=ru | findstr "content" > nul && echo ✓ RU Terms OK || echo ✗ RU Terms FAILED
curl -s http://localhost:8000/api/legal/terms/?lang=he | findstr "content" > nul && echo ✓ HE Terms OK || echo ✗ HE Terms FAILED

echo.
echo [2/5] Testing Document Count...
python backend\manage.py shell -c "from legal.models import LegalDocument; print(f'Total: {LegalDocument.objects.count()}')"

echo.
echo [3/5] Testing Active Documents...
python backend\manage.py shell -c "from legal.models import LegalDocument; print(f'Active: {LegalDocument.objects.filter(is_active=True).count()}')"

echo.
echo [4/5] Testing Language Distribution...
python backend\manage.py shell -c "from legal.models import LegalDocument; print(f'EN: {LegalDocument.objects.filter(language_code=\"en\").count()}'); print(f'RU: {LegalDocument.objects.filter(language_code=\"ru\").count()}'); print(f'HE: {LegalDocument.objects.filter(language_code=\"he\").count()}')"

echo.
echo [5/5] Testing Frontend...
curl -s http://localhost | findstr "bishul" > nul && echo ✓ Frontend OK || echo ✗ Frontend FAILED

echo.
echo ========================================
echo Testing Complete!
echo ========================================
```

Run: `.\test_legal_docs.bat`

---

## 🎉 COMPLETION

When all tests pass:
1. ✅ Legal documents loaded
2. ✅ API endpoints working
3. ✅ Admin interface functional
4. ✅ Frontend integration complete
5. ✅ Google button properly centered

**Your BishulMe app is ready for production!** 🚀

