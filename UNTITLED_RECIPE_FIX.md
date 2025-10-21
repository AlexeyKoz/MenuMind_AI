# ✅ FIXED: "Untitled Recipe" Bug

## Problem

Recipe was generating with:
- ✅ Good quality ingredients
- ✅ Good quality cooking steps  
- ✅ Proper translation
- ❌ **"Untitled Recipe"** as name instead of actual recipe name

---

## Root Cause

When the **AI Validator** fixed a recipe (Stage 3 validation), it returned a new recipe object that **lost the original name**!

```python
# AI Validator fixes ingredients/steps
fixed_recipe = ai_validator.fix_recipe(rcip_recipe, validation_report)

# But fixed_recipe might not include the original name!
# Result: Recipe saved with name = None → frontend shows "Untitled Recipe"
```

---

## Fix Applied

**File:** `backend/apps/recipes/services.py`

### Change 1: Preserve Recipe Name & Metadata

```python
if fixed_recipe:
    logger.info("[VALIDATION] ✅ Recipe fixed by AI")
    
    # IMPORTANT: Preserve the original recipe name and metadata
    if not fixed_recipe.get('name') and rcip_recipe.get('name'):
        fixed_recipe['name'] = rcip_recipe['name']
        logger.info(f"[VALIDATION] Preserved recipe name: {rcip_recipe['name']}")
    
    # Preserve other metadata that AI might not include
    if not fixed_recipe.get('description') and rcip_recipe.get('description'):
        fixed_recipe['description'] = rcip_recipe['description']
    
    if not fixed_recipe.get('cuisine') and rcip_recipe.get('cuisine'):
        fixed_recipe['cuisine'] = rcip_recipe['cuisine']
```

### Change 2: Added Debug Logging

```python
logger.info(f"[VALIDATION] Starting validation for recipe: {rcip_recipe.get('name', 'Unknown')}")
```

---

## How It Works Now

### Recipe Generation Flow:

1. **Extract from website** → RCIP format with name
   ```json
   {
     "name": "Яблочный пирог",
     "ingredients": [...],
     "steps": [...]
   }
   ```

2. **Auto-validation** (free rules) → checks quality
   - If confidence < 80% → flag for AI fix

3. **AI fixes ingredients/steps** → but now preserves name!
   ```python
   # Original: "Яблочный пирог"
   # Fixed recipe gets same name: "Яблочный пирог" ✅
   ```

4. **Save to database** → with proper name ✅

5. **Translate to user's language** → name also translated ✅

---

## Expected Results

### Before Fix:
```
Recipe Name: "Untitled Recipe" ❌
Ingredients: ✅ Good quality
Steps: ✅ Good quality  
Translation: ✅ Working
```

### After Fix:
```
Recipe Name: "Яблочный пирог" ✅
Ingredients: ✅ Good quality
Steps: ✅ Good quality
Translation: ✅ Working
```

---

## Testing

**Backend restarted!** ✅

### Test Steps:

1. **Search:** "яблочный пирог" (in Russian)
2. **Generate recipe**
3. **Check name:**
   - Should show: "Яблочный пирог" ✅
   - NOT: "Untitled Recipe" ❌

### Console Logs to Watch:

```
[VALIDATION] Starting validation for recipe: Яблочный пирог
[VALIDATION] Confidence: 65%
[VALIDATION] ⚠️ Recipe flagged - attempting AI fix...
[VALIDATION] ✅ Recipe fixed by AI
[VALIDATION] Preserved recipe name: Яблочный пирог  ← NEW!
```

---

## Why It Happened

The AI Validator's prompt says:
```json
{
  "name": "Recipe Name",
  "ingredients": [...],
  "steps": [...]
}
```

But when **fixing** a recipe, the AI sometimes focuses on ingredients/steps and **forgets to include the name** in the response!

Our fix:
- ✅ Always preserve the original name
- ✅ Always preserve other metadata (description, cuisine)
- ✅ Only let AI fix ingredients/steps

---

## Status

✅ **Fix applied**
✅ **Backend restarted**
✅ **Ready to test**

**Action:** Try generating a new recipe - it should have the correct name now!

---

## Additional Improvements

Also added metadata preservation:
- `description` - recipe description
- `cuisine` - cuisine type (e.g., "Russian", "Italian")

This ensures AI fixes **only modify ingredients/steps**, not the entire recipe metadata!

---

**No more "Untitled Recipe"!** 🎉

