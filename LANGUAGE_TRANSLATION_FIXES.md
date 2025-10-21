# ✅ FIXED: Language Translation Issues

## Two Bugs Fixed

### 🐛 Bug #1: Search in Russian → Recipe Generated in Russian
**Even when interface was in English!**

### 🐛 Bug #2: Switching Back to English Shows Russian
**English → Russian works ✅, but Russian → English shows Russian ❌**

---

## Root Causes

### Bug #1: Gemini Missing "Always English" Instruction

**Problem:**
- Groq had system message: "Always output in English - we will translate later" ✅
- Gemini (primary AI) had NO such instruction ❌
- Result: Gemini extracted recipe in source language (Russian site → Russian recipe)

**Code Location:** `backend/apps/recipes/services.py` line 1447

```python
# BEFORE (Gemini):
prompt = f"""Extract the complete recipe from this webpage. Get ALL ingredients...
# ❌ No language instruction!

# BEFORE (Groq fallback):
"content": "...Always output in English - we will translate later."
# ✅ Has instruction, but only used as fallback!
```

**Fix Applied:**
```python
# AFTER (Gemini):
prompt = f"""You are a professional recipe extraction expert...

IMPORTANT: Always output in ENGLISH - we will translate to other languages later.

Recipe Name: {recipe_name}
...
INGREDIENTS - FORMAT STRICTLY AS:
...
- OUTPUT IN ENGLISH (translate if source is in another language)

COOKING STEPS - FORMAT STRICTLY AS:
...
- OUTPUT IN ENGLISH (translate if source is in another language)
```

---

### Bug #2: `translate_recipe_name()` Skips English Translation

**Problem:**
```python
# backend/apps/core/smart_translator.py line 582
def translate_recipe_name(self, name: str, target_language: str) -> str:
    """
    Args:
        name: Recipe name in English  ← WRONG ASSUMPTION!
    """
    if target_language == 'en':
        return name  ← Just returns original Russian name!
```

**The Issue:**
- Function assumes `name` is always in English
- Reality: If recipe extracted in Russian, `name` is in Russian
- When user switches to English, code returns Russian name unchanged

**Fix Applied:**
```python
# AFTER:
def translate_recipe_name(self, name: str, target_language: str) -> str:
    """
    Args:
        name: Recipe name (in any language)  ← FIXED!
        target_language: Target language code (en, ru, he)  ← Now includes 'en'!
    """
    # REMOVED this early return:
    # if target_language == 'en':
    #     return name
    
    # Now ALWAYS translates using Gemini:
    prompt = f"""Translate this recipe name to {target_lang_name}.
    Return ONLY the translated name, nothing else.
    
    Recipe name: {name}  ← Can be Russian, Hebrew, or English!
    
    Translation in {target_lang_name}:"""
```

---

## How It Works Now

### Scenario 1: Generate Recipe (Interface in English)

**BEFORE:**
1. User searches "карбонара" while interface is English
2. Brave finds Russian recipe sites
3. Gemini extracts in Russian → recipe name: "Карбонара" ❌
4. User sees Russian recipe even though interface is English ❌

**AFTER:**
1. User searches "карбонара" while interface is English
2. Brave finds Russian recipe sites
3. Gemini extracts in English (as instructed) → recipe name: "Carbonara" ✅
4. User sees English recipe ✅
5. Background translations to Russian/Hebrew created ✅

---

### Scenario 2: Language Switching

**BEFORE:**
1. User has recipe "Карбонара" (generated in Russian)
2. User switches to English
3. `translate_recipe_name("Карбонара", "en")` called
4. Function returns "Карбонара" unchanged (skipped translation) ❌
5. User still sees "Карбонара" in English interface ❌

**AFTER:**
1. User has recipe "Карбонара" (if somehow still in Russian)
2. User switches to English
3. `translate_recipe_name("Карбонара", "en")` called
4. Gemini translates "Карбонара" → "Carbonara" ✅
5. User sees "Carbonara" in English interface ✅

---

## Expected Logs

### Recipe Generation (Interface in English):
```
[SEARCH+SCRAPE] ✅ Got 2 recipes via Brave+Firecrawl
[GEMINI] ✅ Received response: X characters
[RCIP] Recipe name: 'Carbonara'  ← ENGLISH now!
[ENRICH] User language: en
[TRANSLATION] ✅ Completed immediate translation to en
[TRANSLATION] ✅ Queued background translations for: ['ru', 'he']
```

### Language Switching (Russian → English):
```
[LIST] User language: en (from query param: en)
[LIST] Translating 1 recipe names to en
[LIST] ⚠️ No translation in DB for Карбонара, using Gemini fallback...
[SMART_TRANSLATE] Translating recipe name to English
[LIST] ✅ GEMINI: Карбонара -> Carbonara
```

---

## Files Changed

### 1. `backend/apps/recipes/services.py`
**Lines 1447-1495:** Added "Always output in ENGLISH" to Gemini extraction prompt

**Changes:**
- Added system instruction at top of prompt
- Added "OUTPUT IN ENGLISH" to both ingredients and steps sections
- Ensures Gemini translates non-English sources to English

### 2. `backend/apps/core/smart_translator.py`
**Lines 571-600:** Removed early return for English translation

**Changes:**
- Removed `if target_language == 'en': return name`
- Updated docstring to clarify name can be in any language
- Now always uses Gemini to translate, even to English

---

## Testing

**Backend restarted!** ✅

### Test 1: Generate Recipe in English Interface
1. **Set interface to English** (en)
2. **Search:** "карбонара" or "шоколадный торт"
3. **Expected:**
   - Recipe name in English: "Carbonara", "Chocolate Cake" ✅
   - Ingredients in English ✅
   - Steps in English ✅

### Test 2: Language Switching
1. **Generate recipe in any language**
2. **Switch to Russian** → Should translate to Russian ✅
3. **Switch to Hebrew** → Should translate to Hebrew ✅
4. **Switch to English** → Should translate to English ✅ (FIXED!)

### Test 3: Old Recipes (Already in Russian)
1. **Old recipe with Russian name**
2. **Switch to English**
3. **Expected:**
   - Name translates via Gemini fallback ✅
   - Ingredients/steps translate via Gemini fallback ✅

---

## Status

✅ **Bug #1 fixed** - Gemini now extracts in English
✅ **Bug #2 fixed** - English translation now works
✅ **Backend restarted**
✅ **Ready to test**

---

## Try Now!

1. **Generate a new recipe** (search "карбонара" while interface is English)
   - Should see English recipe ✅

2. **Switch languages:**
   - English → Russian → Hebrew → English
   - All should work now! ✅

---

**Both language issues fixed!** 🎊

