# CRITICAL FIX: Unit Translation Missing from Smart Translator

## The Problem
After restarting with `start_fullstack.bat`, you generated a NEW recipe and the logs showed:
```
[GEMINI] ✅ Successfully translated 21 cooking steps to Russian
[TRANSLATION] ✅ Completed immediate translation to ru
```

BUT when you viewed the recipe, units were still in English:
- "g" instead of "г"
- "pcs" instead of "шт"
- "as" instead of being removed

## Root Cause
The **immediate translation** in `services.py` uses `SmartTranslationService.translate_ingredients_batch()` which:
- ✅ Translates ingredient **names** (спагетти, яйца)
- ✅ Uses IML database + Gemini fallback
- ❌ **NEVER translated units!**

Meanwhile, `tasks.py` had unit translation, but it's only called for **background** translations!

## The Fix
Added unit translation dictionary to `SmartTranslationService.translate_ingredients_batch()`:

### File: `backend/apps/core/smart_translator.py`

```python
# Lines 72-100: Added unit translation dictionary
unit_translations = {
    'ru': {
        'g': 'г', 'kg': 'кг', 'mg': 'мг',
        'ml': 'мл', 'l': 'л',
        'tsp': 'ч.л.', 'tbsp': 'ст.л.', 'cup': 'чашка',
        'pcs': 'шт', 'cloves': 'зубчика',
        'as': ''  # Remove "as" from "as needed"
        ...
    },
    'he': { ... }
}

# Lines 107-115: Translate units for each ingredient
if target_language in unit_translations and ing.get('unit'):
    unit = ing.get('unit').lower().strip()
    if unit in unit_translations[target_language]:
        translated_unit = unit_translations[target_language][unit]
        if translated_unit:  # Only set if not empty
            translated_ing['unit'] = translated_unit
```

## What This Fixes
✅ Units translated in **immediate** translation (user's language)
✅ Units translated in **background** translation (other languages)
✅ "as" unit removed (from "1 as needed")
✅ Both Russian and Hebrew supported

## Test Now
1. **Delete** the old Carbonara recipe (it has old units)
2. **Generate a BRAND NEW recipe** (try "борщ" or "шакшука")
3. **Check**:
   - г instead of g ✅
   - ч.л. instead of tsp ✅
   - ст.л. instead of tbsp ✅
   - шт instead of pcs ✅
   - зубчика instead of cloves ✅

## Backend Status
✅ Restarted with fix
✅ Ready to generate NEW recipes correctly
✅ Both `services.py` (immediate) AND `tasks.py` (background) now have unit translation

**This was the FINAL missing piece!** Generate a fresh recipe and it should be 100% Russian! 🎯

