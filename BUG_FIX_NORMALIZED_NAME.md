# Bug Fix: normalized_name Error

## Problem
The shopping list AI agent was failing with:
```
Cannot resolve keyword 'normalized_name' into field
```

## Root Cause
The code was trying to query `CanonicalRecipe` by `normalized_name`, which doesn't exist in the model. The deduplication logic was incorrect.

## Solution
Changed from:
```python
normalized_name = agent._normalize_recipe_name(query)
existing_canonical = CanonicalRecipe.objects.filter(
    normalized_name=normalized_name
).first()
```

To:
```python
existing_canonical = CanonicalRecipe.objects.filter(
    name__icontains=query.lower()
).first()
```

## Why This Works
- Uses `name__icontains` for case-insensitive partial matching
- Matches against the actual `name` field which exists in the model
- Simple and effective for finding similar recipes
- The full `recipe_hash` deduplication still happens in the background task

## Files Changed
- `backend/apps/shopping/views.py` - Fixed deduplication check in `ai_add_items` method

## Status
✅ Fixed - Ready to test

