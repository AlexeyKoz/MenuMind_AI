# Bug Fixes: Shopping List AI Agent

## Bug #1: normalized_name Field Error ✅

### Problem
```
Cannot resolve keyword 'normalized_name' into field
```

### Fix
Changed deduplication from non-existent `normalized_name` to actual `name` field:
```python
# Before (WRONG)
normalized_name = agent._normalize_recipe_name(query)
existing_canonical = CanonicalRecipe.objects.filter(
    normalized_name=normalized_name
).first()

# After (CORRECT)
existing_canonical = CanonicalRecipe.objects.filter(
    name__icontains=query.lower()
).first()
```

---

## Bug #2: ShoppingItem Field Names Error ✅

### Problem
```
ShoppingItem() got unexpected keyword arguments: 'standard_quantity', 'added_by_color'
```

### Root Cause
Code was using incorrect field names that don't exist in the `ShoppingItem` model.

### Fix
Corrected field names:

| Wrong Field | Correct Field |
|-------------|---------------|
| `standard_quantity` | `quantity` |
| `added_by_color` | `user_color` |

**Before:**
```python
new_item = ShoppingItem.objects.create(
    shopping_list=shopping_list,
    name=ingredient_name,
    standard_quantity=Decimal(str(standard_quantity)),  # ❌ WRONG
    weight_quantity=Decimal(str(weight_quantity)),
    liquid_quantity=Decimal(str(liquid_quantity)),
    added_by=request.user,
    added_by_color=user_color,  # ❌ WRONG
    ingredient_key=ingredient_key
)
```

**After:**
```python
new_item = ShoppingItem.objects.create(
    shopping_list=shopping_list,
    name=ingredient_name,
    quantity=Decimal(str(item_quantity)),  # ✅ CORRECT
    unit=unit or 'unit',
    weight_quantity=Decimal(str(weight_quantity)),
    liquid_quantity=Decimal(str(liquid_quantity)),
    added_by=request.user,
    user_color=user_color,  # ✅ CORRECT
    ingredient_key=ingredient_key
)
```

Also fixed the update logic:
```python
# Before (WRONG)
existing_item.standard_quantity += Decimal(str(standard_quantity))

# After (CORRECT)
existing_item.quantity += Decimal(str(item_quantity))
```

---

## Files Changed
- ✅ `backend/apps/shopping/views.py` - Fixed both bugs in `ai_add_items` method

## Testing
- ✅ No linting errors
- ✅ Field names match actual model fields
- ✅ Ready for testing

## Next Steps
1. Restart backend server
2. Try adding a recipe to shopping list
3. Should work without 500 errors!

---

**Status:** ✅ Both bugs FIXED

