# CRITICAL BUG FIXED: Division by Zero Crash

## What Happened
Looking at your logs:
```
[ENRICH] Processing 0 ingredients...
[PREPARE_STEPS] Starting with 0 steps
[TRANSLATION] ⚠️ Immediate translation failed: division by zero
```

**The AI failed to extract ANY data** from the website, then the translation code crashed when trying to calculate statistics!

## Root Causes

### 1. Division by Zero (FIXED)
**File:** `backend/apps/core/smart_translator.py` line 196

**Before:**
```python
f"Savings: {((... + ...) / len(ingredients) * 100):.1f}%"
```

When `len(ingredients) == 0`, this crashed!

**After:**
```python
if len(ingredients) > 0:
    savings_pct = ((... + ...) / len(ingredients) * 100)
    logger.info(f"Savings: {savings_pct:.1f}% from databases/cache")
else:
    logger.info(f"Savings: N/A (no ingredients to translate)")
```

### 2. No Error Handling for Empty Recipes (FIXED)
**File:** `backend/apps/recipes/services.py` line 783-790

Added check before translation:
```python
if not canonical.base_ingredients and not canonical.base_steps:
    logger.warning("Recipe has no ingredients or steps - marking translation as failed")
    translation.status = 'failed'
    translation.save()
```

This prevents trying to translate empty recipes and shows a clear error.

## The REAL Problem

The AI extracted **ZERO ingredients and ZERO steps** from the website!

This is why you see:
- "Ингредиенты не указаны" (Ingredients not specified)
- "Инструкции не указаны" (Instructions not specified)

The website either:
1. Had no recipe content
2. Had content in a format the AI couldn't parse
3. Blocked the scraper (403 error)

## What's Fixed

✅ No more crashes when recipe has no content
✅ Clear error message instead of crash
✅ Translation marked as 'failed' instead of 'in_progress'
✅ Better logging to understand what went wrong

## What to Do Next

**You need to search for recipes from BETTER websites!**

Try these search queries that have better success rates:
- "борщ" (Borscht - very common recipe)
- "шакшука" (Shakshuka - simple, well-documented)
- "пельмени" (Dumplings)

The AI will try multiple websites and pick the best one. If the first 5 websites all fail or have no content, it will show this error.

## Backend Status
✅ Restarted with fixes
✅ Won't crash on empty recipes
✅ Better error messages
✅ Ready to try again

**Please try generating a recipe with a COMMON dish name that's likely to have good recipe websites!**

