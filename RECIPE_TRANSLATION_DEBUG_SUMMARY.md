# Recipe Translation Issue - Debug Summary

## 🎯 **THE PROBLEM**

**Symptoms:**
- Cooking steps remain in English when interface is switched to Russian/Hebrew
- Ingredients translate correctly ✅
- Steps do NOT translate ❌

**User Experience:**
- Generate recipe "борщ" in Russian interface
- Steps show in English: "Heat a skillet over medium heat..."
- Expected: "Разогрейте сковороду на среднем огне..."

---

## 🔍 **ROOT CAUSE IDENTIFIED**

### **Issue 1: Translation Strategy**

**OLD APPROACH (Word-by-Word Replacement):**
```
"Sift flour into a bowl" → "Sift мука into a отделить bowl" ❌
```

The `CookingTermsTranslationService` was doing word-by-word replacement, not full sentence translation.

**SOLUTION IMPLEMENTED:**
Created `SmartTranslationService.translate_cooking_steps_batch()` that:
1. Builds glossary from CookLingo database
2. Uses Gemini to translate FULL sentences with glossary context
3. Result: "Просейте муку в миску" ✅

**Files Modified:**
- `backend/apps/core/smart_translator.py` - Added `translate_cooking_steps_batch()` method
- `backend/apps/recipes/services.py` - Updated to use new translation method

---

### **Issue 2: Translation Not Returned to Frontend**

**LOGS SHOW:**
```
[GEMINI] Successfully translated 19 cooking steps  ✅
[TRANSLATION] Translation completed               ✅
BUT... steps still English in frontend            ❌
```

**The Problem:**
In `backend/apps/recipes/views.py`, the code checks for translation immediately after recipe creation, but there's a race condition - the translation might not be marked as `completed` yet.

**SOLUTION IMPLEMENTED:**
Added wait loop in `views.py` (`find_recipe` method) that:
1. Waits up to 2 seconds for translation to complete
2. Logs what's being retrieved
3. Returns translated content to frontend

**Debug Logging Added:**
```python
print(f"[TRANSLATION_CHECK] Looking for {user_language} translation")
print(f"[TRANSLATION] First translated step: {translated_text[:80]}...")
```

---

## 📝 **TESTS CREATED**

### **1. Backend Test**
**File:** `backend/apps/recipes/tests/test_recipe_translation.py`

**What it tests:**
- Recipe generation from query
- Canonical recipe stored in English
- Immediate translation to Russian
- Background translation to Hebrew
- Ingredient translation
- **Cooking steps translation** (the bug we're fixing!)
- Language switching

**Run with:**
```bash
cd backend
python -m pytest apps/recipes/tests/test_recipe_translation.py -v -s
```

**Note:** Currently blocked by Django migration conflicts (`duplicate column name: deletion_warning_sent_at`). This is a separate database schema issue.

---

### **2. Simple Test Script**
**File:** `test_recipe_simple.py`

**What it does:**
- Creates test user
- Generates recipe for "pelmeni"
- Checks if Russian translation exists and is completed
- Verifies steps contain Cyrillic characters

**Run with:**
```bash
python test_recipe_simple.py
```

**Current Issue:** Async context error in `CookingTermsTranslationService.__init__()` - it queries the database synchronously from an async context.

---

### **3. Frontend Selenium Test**
**File:** `frontend/tests/test_language_switching.py`

**What it tests:**
- Login
- Navigate to Discover page
- Generate recipe using AI
- Open recipe detail
- Switch languages: RU → EN → HE → RU
- Take screenshots at each step
- Verify content changes

**Run with:**
```bash
cd frontend/tests
python test_language_switching.py
```

**Prerequisites:**
- Backend running on port 8000
- Frontend running on port 5173
- Test user created
- Chrome WebDriver installed

---

## 🚀 **HOW TO TEST MANUALLY (Right Now)**

### **Option 1: Simple Manual Test**

1. **Start backend** (if not running):
   ```bash
   cd backend
   python manage.py runserver
   ```

2. **Generate a new recipe** in Russian:
   - Go to Discover page
   - Search for "борщ" or "пельмени"
   - Open the recipe

3. **Check backend console** for these logs:
   ```
   [SMART_TRANSLATE] Translating 19 cooking steps to ru
   [SMART_TRANSLATE] Built glossary with X cooking terms
   [GEMINI] Successfully translated 19 cooking steps
   [TRANSLATION_CHECK] Looking for ru translation
   [TRANSLATION] First translated step: <should be in Russian>
   ```

4. **Check frontend**:
   - Do you see Cyrillic in cooking steps?
   - Switch to English - do steps change?
   - Switch back to Russian - do steps change back?

---

### **Option 2: Quick Database Check**

Run this in Django shell:
```bash
cd backend
python manage.py shell
```

```python
from apps.recipes.models import CanonicalRecipe, RecipeTranslation

# Get last recipe
recipe = CanonicalRecipe.objects.latest('created_at')
print(f"Recipe: {recipe.name}")
print(f"English step 1: {recipe.base_steps[0].get('instruction')[:80]}")

# Check Russian translation
ru_trans = RecipeTranslation.objects.filter(
    canonical_recipe=recipe,
    language='ru',
    status='completed'
).first()

if ru_trans:
    print(f"Russian step 1: {ru_trans.base_steps[0].get('instruction')[:80]}")
else:
    print("NO RUSSIAN TRANSLATION FOUND!")
```

---

## 🔧 **REMAINING ISSUES TO FIX**

### **1. Database Migration Conflict**
```
django.db.utils.OperationalError: duplicate column name: deletion_warning_sent_at
```

**Fix:** Need to check and merge conflicting migrations in `apps/shopping/migrations/`.

---

### **2. Async Context in CookingTermsTranslationService**
```
django.core.exceptions.SynchronousOnlyOperation: You cannot call this from an async context
```

**Location:** `backend/apps/core/cooking_terms_service.py:31`

**Fix:** Move database query out of `__init__()` or use `sync_to_async`.

---

### **3. Frontend Not Refetching on Language Change**

**Location:** `frontend/src/pages/CanonicalRecipesPage.tsx`

**Current behavior:**
- `useEffect` watches `i18n.language` and refetches recipe
- BUT: Translation might not be ready yet

**Fix:** Add loading state and retry logic.

---

##📊 **WHAT WE KNOW FOR SURE**

✅ **Translation is happening** - Gemini logs show successful translation  
✅ **Translation is being saved** - Database query shows completed translation  
❌ **Translation is NOT being returned** - Frontend receives English steps  

**The bug is in the data flow between:**
1. `RecipeAgentService` (generates + translates) →
2. `views.py:find_recipe()` (retrieves translation) →
3. Frontend (displays data)

**Most likely issue:** The translation is saved but the response to frontend contains the English version from `canonical_recipe` instead of the Russian version from `ru_translation`.

---

## 🎯 **NEXT STEPS**

### **Immediate (to fix the bug):**

1. **Add more debug logging** in `views.py` to see EXACTLY what's being returned:
   ```python
   print(f"[RESPONSE] Returning base_steps: {canonical_recipe['base_steps'][0]}")
   ```

2. **Check if translation is being overridden** somewhere after it's set.

3. **Verify frontend is using the correct field** - check if it's reading `base_steps` or `steps`.

### **Long-term (for reliability):**

1. Fix database migrations
2. Fix async context issue in CookingTermsTranslationService
3. Add retry logic in frontend for incomplete translations
4. Add E2E tests to CI/CD pipeline

---

## 📁 **FILES CREATED/MODIFIED**

### **Created:**
- `backend/apps/core/smart_translator.py` - Smart translation service
- `backend/apps/recipes/tests/test_recipe_translation.py` - Backend test
- `backend/apps/recipes/tests/README.md` - Test documentation
- `frontend/tests/test_language_switching.py` - Frontend Selenium test
- `test_recipe_simple.py` - Simple test script
- `backend/pytest.ini` - Pytest configuration
- `RECIPE_TRANSLATION_DEBUG_SUMMARY.md` - This file

### **Modified:**
- `backend/apps/recipes/services.py` - Updated translation logic
- `backend/apps/recipes/views.py` - Added translation retrieval with wait loop
- `backend/apps/core/cooking_terms_service.py` - (needs async fix)

---

## 🤔 **QUESTIONS FOR USER**

1. **When you generate a recipe now, what do you see in backend console?**
   - Look for: `[TRANSLATION] First translated step: ...`
   
2. **Can you open browser DevTools Network tab and check the API response?**
   - Look for: `/api/recipes/recipes/find_recipe/`
   - Check if `base_steps` contains Cyrillic or English

3. **If you refresh the page after generating a recipe, do the steps translate?**
   - This would confirm translation exists but isn't being returned initially

---

**Last Updated:** 2025-10-21 01:20 AM  
**Status:** Tests created, waiting to run due to async/migration issues  
**Priority:** HIGH - User has been testing manually for 4 hours

