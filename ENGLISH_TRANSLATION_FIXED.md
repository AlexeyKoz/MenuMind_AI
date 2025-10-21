# ✅ FIXED: Recipe Names Not Translating to English

## Problem

When switching to English, recipe names stayed in their original language:
- ❌ "карбонара" (should be "Carbonara")
- ❌ "Шоколадный торт" (should be "Chocolate Cake")

## Root Cause

In `backend/apps/recipes/views.py`, line 1115:

```python
# OLD CODE (WRONG):
if user_language != 'en':
    # Only translate if NOT English
    # This means: English language gets skipped!
```

**The bug:** Code assumed English was the "base" language and never needed translation. But if a recipe was generated in Russian or Hebrew, it stayed in that language when viewing in English.

## Fix Applied

**Changed:**
```python
# OLD:
if user_language != 'en':
    # Translate names
    
# NEW:
# Always check for translations (removed the if statement)
# Translate recipe names to user's language (always check for translations)
```

Now the system:
1. ✅ Always looks for translation in the requested language
2. ✅ Uses database translation if available
3. ✅ Falls back to Gemini if not in database
4. ✅ Works for ALL languages (en, ru, he)

---

## How It Works Now

### Scenario: Russian Recipe, English User

```
Recipe: "карбонара" (generated in Russian)
User switches to English
  ↓
[LIST] User language: en
[LIST] Translating 2 recipe names to en
  ↓
Check RecipeTranslation database for 'en'
  ↓
If found in DB:
  [LIST] ✅ DB: карбонара -> Carbonara
  
If NOT in DB:
  [LIST] ⚠️ No translation in DB, using Gemini fallback
  [LIST] ✅ GEMINI: карбонара -> Carbonara
```

---

## Testing

**Backend has auto-reloaded with the fix!**

### Test Steps:

1. **Switch to English** in your app
2. **Refresh** the Discover page
3. **See recipe names in English:**
   - "карбонара" → "Carbonara" ✅
   - "Шоколадный торт" → "Chocolate Cake" ✅

### What You'll See in Logs:

```
[LIST] User language: en (from query param: en)
[LIST] Translating 2 recipe names to en
[LIST] ⚠️ No translation in DB for карбонара, using Gemini fallback...
[LIST] ✅ GEMINI: карбонара -> Carbonara
[LIST] ⚠️ No translation in DB for Шоколадный торт, using Gemini fallback...
[LIST] ✅ GEMINI: Шоколадный торт -> Chocolate Cake
```

---

## Files Modified

- **`backend/apps/recipes/views.py`**
  - Removed `if user_language != 'en':` check
  - Now translates to ALL languages including English

---

## Why This Happened

The original logic assumed:
- English = default language
- All recipes start in English
- Only translate FROM English to other languages

But in reality:
- Recipes can be generated in ANY language (based on user's preference)
- A Russian user generates recipes in Russian
- An English user needs those Russian recipes translated to English

**Fix:** Treat ALL languages equally - always check for translations!

---

## Status

✅ **Fixed and auto-reloaded**

**Action:** Switch to English and refresh - names should now translate!

If they don't translate immediately, it's because:
1. No English translation in database yet (Gemini will create it on-the-fly)
2. Gemini fallback will translate and display correctly

---

**Result: Recipe names now translate to ALL languages including English!** 🎉

