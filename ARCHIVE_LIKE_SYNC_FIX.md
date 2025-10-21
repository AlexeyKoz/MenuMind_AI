# AUTOMATIC LIKE/UNLIKE SYNC: Archive System Integration

## ✅ **FIXED: Like Status Now Syncs with Archive Actions**

**Date:** 2025-10-21  
**Priority:** HIGH  
**Issue:** When archiving a recipe, the like/heart on Discovery page remained filled

---

## 🐛 **The Problem:**

### **User Flow That Was Broken:**

1. ✅ User likes recipe from Discovery page → Heart filled, recipe saved to "Recipes" page
2. ✅ User archives recipe from "Recipes" page → Recipe moved to archive
3. ❌ **Heart on Discovery page still filled!** → User thinks recipe is still liked
4. ❌ If user clicks heart again → Creates confusion (is it liked or not?)

**Why This Was Bad:**
- **UI Inconsistency:** Heart showed "liked" but recipe was archived
- **User Confusion:** "I archived it, why is it still liked?"
- **Broken UX:** Archive and like status should be synchronized

---

## ✅ **The Fix:**

### **1. Archive → Automatically Unlike**

When a user archives a recipe, the like is now automatically removed:

```python
# backend/apps/recipes/views.py (Lines 410-422)

@action(detail=True, methods=['delete'])
def unsave_recipe(self, request, pk=None):
    """Archive recipe (soft delete) from user's collection"""
    # ... archive the recipe ...
    
    # ✅ NEW: Automatically remove like from canonical recipe when archiving
    if recipe.canonical_recipe:
        try:
            like = RecipeLike.objects.get(
                user=request.user,
                canonical_recipe=recipe.canonical_recipe
            )
            like.delete()
            print(f"[ARCHIVE] Removed like from canonical recipe: {recipe.canonical_recipe.id}")
        except RecipeLike.DoesNotExist:
            # No like exists, that's fine
            pass
```

### **2. Restore → Automatically Re-like**

When a user restores a recipe from archive, the like is automatically recreated:

```python
# backend/apps/recipes/views.py (Lines 450-458)

@action(detail=True, methods=['post'])
def restore_recipe(self, request, pk=None):
    """Restore archived recipe to user's collection"""
    # ... restore the recipe ...
    
    # ✅ NEW: Automatically re-like the canonical recipe when restoring
    if recipe.canonical_recipe:
        like, created = RecipeLike.objects.get_or_create(
            user=request.user,
            canonical_recipe=recipe.canonical_recipe
        )
        if created:
            print(f"[RESTORE] Re-liked canonical recipe: {recipe.canonical_recipe.id}")
```

---

## 🎯 **How It Works Now:**

### **Complete Flow:**

1. **Like from Discovery:**
   ```
   User clicks heart on Discovery page
   → RecipeLike created ✅
   → Recipe fork created ✅
   → UserRecipe created (is_archived=False) ✅
   → Heart filled on Discovery page ✅
   → Recipe appears in "Recipes" page ✅
   ```

2. **Archive from Recipes Page:**
   ```
   User clicks "Archive" on Recipes page
   → UserRecipe.is_archived = True ✅
   → ✅ NEW: RecipeLike deleted automatically
   → Heart unfilled on Discovery page ✅
   → Recipe moves to Archive ✅
   ```

3. **Restore from Archive:**
   ```
   User clicks "Restore" on Archive page
   → UserRecipe.is_archived = False ✅
   → ✅ NEW: RecipeLike recreated automatically
   → Heart filled on Discovery page ✅
   → Recipe reappears in "Recipes" page ✅
   ```

4. **Like Again from Discovery (After Archive):**
   ```
   User clicks heart on Discovery page (after archiving)
   → RecipeLike created ✅
   → Existing fork found ✅
   → UserRecipe.is_archived = False ✅ (from previous fix)
   → Heart filled on Discovery page ✅
   → Recipe reappears in "Recipes" page ✅
   ```

---

## 📝 **Files Modified:**

1. **`backend/apps/recipes/views.py`** (Lines 410-422)
   - `unsave_recipe()` method
   - Added automatic like removal when archiving

2. **`backend/apps/recipes/views.py`** (Lines 450-458)
   - `restore_recipe()` method
   - Added automatic like restoration when restoring from archive

---

## ✅ **What's Fixed:**

| Action | Before | After |
|--------|--------|-------|
| **Archive recipe** | Heart stays filled on Discovery ❌ | ✅ Heart unfilled automatically |
| **Restore recipe** | Need to manually re-like ❌ | ✅ Heart filled automatically |
| **Like after archive** | ✅ Works (from previous fix) | ✅ Still works |
| **UI consistency** | Heart and archive status out of sync ❌ | ✅ Always synchronized |

---

## 🧪 **Test Scenarios:**

### **Scenario 1: Archive → Heart Unfills**

1. **Generate recipe** from Discovery → Heart filled ✅
2. **Go to Recipes page** → Recipe visible ✅
3. **Click "Archive"** → Recipe moves to archive ✅
4. **Go back to Discovery page** → ✅ **Heart is now unfilled!** 🎉

### **Scenario 2: Restore → Heart Refills**

1. **Go to Archive page** → See archived recipe ✅
2. **Click "Restore"** → Recipe moves back to Recipes ✅
3. **Go to Discovery page** → ✅ **Heart is filled again!** 🎉

### **Scenario 3: Archive → Permanent Delete → Re-like**

1. **Archive recipe** → Heart unfilled ✅
2. **Permanently delete from archive** → Recipe removed ✅
3. **Go to Discovery page** → Heart still unfilled ✅
4. **Click heart** → Recipe re-saved, heart filled ✅
5. **Go to Recipes page** → ✅ **Recipe reappears!** 🎉

---

## 🔄 **State Synchronization:**

This fix ensures perfect synchronization between:

| State | Recipes Page | Archive Page | Discovery Heart | RecipeLike DB |
|-------|--------------|--------------|-----------------|---------------|
| **Active** | ✅ Visible | ❌ Not visible | ✅ Filled | ✅ Exists |
| **Archived** | ❌ Not visible | ✅ Visible | ❌ **Unfilled** | ❌ **Deleted** |
| **Restored** | ✅ Visible | ❌ Not visible | ✅ **Filled** | ✅ **Recreated** |
| **Deleted** | ❌ Not visible | ❌ Not visible | ❌ Unfilled | ❌ Deleted |

---

## 💡 **Why This Is Important:**

1. **UI Consistency:** Heart icon always reflects actual saved status
2. **User Clarity:** No confusion about whether a recipe is liked/saved
3. **Better UX:** Archive/restore automatically manages likes
4. **Data Integrity:** RecipeLike and UserRecipe states are synchronized

**Users no longer need to manually unlike/re-like when archiving/restoring!**

---

## 📊 **Backend Logs:**

When archiving:
```
[ARCHIVE] Removed like from canonical recipe: abc123...
```

When restoring:
```
[RESTORE] Re-liked canonical recipe: abc123...
```

---

## 🚀 **Impact:**

- ✅ **Archive** → Automatically unlikes
- ✅ **Restore** → Automatically re-likes
- ✅ **Perfect synchronization** between archive status and like status
- ✅ **No manual unliking needed** when archiving
- ✅ **Better user experience** across Discovery, Recipes, and Archive pages

**The archive system is now fully integrated with the like system!** 🎉

---

## 📝 **Summary:**

- ✅ **Root cause:** Archive didn't remove likes, restore didn't recreate them
- ✅ **Fix:** Added automatic like management to archive/restore actions
- ✅ **Result:** Heart icon on Discovery page always reflects actual saved status
- ✅ **Bonus:** Users don't need to think about likes when archiving/restoring

**Archive and like systems are now perfectly synchronized!** 🎉

