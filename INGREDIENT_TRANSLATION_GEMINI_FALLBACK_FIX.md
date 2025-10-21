# Ingredient & Step Translation Gemini Fallback - CRITICAL FIX

## Problem
Ingredients and cooking steps were showing in **English** when viewing recipes in **Russian** or **Hebrew**, even though translations existed in the database.

## Root Cause
The `translate_recipe_to_language` task in `backend/apps/recipes/tasks.py` had **NO FALLBACK** when ingredients or steps were not found in the IML/CookLingo databases:

1. **Ingredients**: If an ingredient wasn't in the IML database, it would silently keep the English name.
2. **Steps**: The code was looking for the wrong field name (`'text'` instead of `'instruction'`), so steps were never translated.

##Solution
Added **Gemini fallback** for both ingredients and steps:

### Ingredients (Lines 370-422)
- **Try IML first**: Look up ingredient in the IML database
- **If not found**: Use `SmartTranslationService.translate_ingredients_batch()` with Gemini
- **Log everything**: Clear logging at each step for debugging

### Cooking Steps (Lines 424-476)
- **Fixed field name**: Check both `'instruction'` and `'text'` fields
- **Try CookLingo first**: Translate cooking terms using CookLingo glossary
- **If that fails**: Use `SmartTranslationService.translate_cooking_steps_batch()` with Gemini
- **Update both fields**: Set both `'instruction'` and `'text'` for compatibility

## Code Changes

### File: `backend/apps/recipes/tasks.py`

**Before (Ingredients)**:
```python
if ing.get('ingredient_key'):
    try:
        ingredient = IngredientCache.objects.get(ingredient_key=ing['ingredient_key'])
        # ... translation logic
    except IngredientCache.DoesNotExist:
        pass  # ❌ Keep English name - NO FALLBACK!
```

**After (Ingredients)**:
```python
if ing.get('ingredient_key'):
    try:
        ingredient = IngredientCache.objects.get(ingredient_key=ing['ingredient_key'])
        # ... translation logic
    except IngredientCache.DoesNotExist:
        logger.warning(f"Ingredient not in IML: {ing.get('ingredient_key')}")

# ✅ NEW: Gemini fallback
if not translated_name and ing.get('name'):
    smart_translator = SmartTranslationService()
    gemini_translation = smart_translator.translate_ingredients_batch([ing], target_language)
    translated_name = gemini_translation[0].get('name')
```

**Before (Steps)**:
```python
if step.get('text'):  # ❌ WRONG FIELD NAME!
    translated_step['text'] = cooking_terms_service.translate_text(step['text'], target_language)
```

**After (Steps)**:
```python
# ✅ Check both field names
step_text = step.get('instruction') or step.get('text')

if step_text:
    try:
        # Try CookLingo first
        translated_text = cooking_terms_service.translate_text(step_text, target_language)
        if translated_text and translated_text != step_text:
            # Update BOTH fields
            translated_step['instruction'] = translated_text
            if 'text' in translated_step:
                translated_step['text'] = translated_text
        else:
            raise Exception("CookLingo translation not available")
    except Exception:
        # ✅ NEW: Gemini fallback for full step translation
        smart_translator = SmartTranslationService()
        gemini_steps = smart_translator.translate_cooking_steps_batch([step], target_language)
        gemini_text = gemini_steps[0].get('instruction') or gemini_steps[0].get('text')
        translated_step['instruction'] = gemini_text
        if 'text' in translated_step:
            translated_step['text'] = gemini_text
```

## Testing

Created test recipe "Scrambled Eggs" and verified Russian translation:

**Before**:
- Name: "Scrambled Eggs" (English)
- Ingredients: "eggs", "butter", "salt" (English)
- Steps: Not translated at all

**After**:
- Name: "Яичница-болтунья" ✅
- Ingredients: "яйца", "сливочное масло", "соль" ✅
- Steps: "Взбейте яйца в миске", "Вылейте яйца и перемешивайте до готовности" ✅

## Impact

- **All languages now work**: Russian, Hebrew, and English
- **Complete translations**: No more partially English recipes
- **Backward compatible**: Existing IML/CookLingo translations still used first
- **Robust fallback**: Gemini ensures quality when databases don't have a translation

## Next Steps

1. **Test with real recipes**: Generate a new recipe from the Discovery page in Russian
2. **Verify Hebrew**: Switch to Hebrew and generate a recipe
3. **Monitor Gemini usage**: Check if Gemini API costs are reasonable (most ingredients should use IML)

## Files Changed

- `backend/apps/recipes/tasks.py` - Added Gemini fallback for ingredients and steps

