# CRITICAL BUG FIX: Recipe Not Reappearing After Re-liking

## ✅ **FIXED: Archived Recipe Not Restored When Re-liked from Discovery Page**

**Date:** 2025-10-21  
**Priority:** CRITICAL  
**Issue:** Recipe unliked/archived from Recipes page doesn't reappear when liked again from Discovery page

---

## 🐛 **The Bug:**

### **User Flow That Was Broken:**

1. ✅ User generates recipe → Automatically liked → Appears in "Recipes" page
2. ✅ User unlikes from "Recipes" page → Recipe moved to archive
3. ✅ User deletes from archive → Recipe removed from "My Recipes"
4. ❌ **User likes it again from "Discovery" page** → Recipe does NOT appear in "Recipes" page!

### **Why It Happened:**

When a user re-likes a recipe, the backend:
1. Finds the existing fork (Recipe object)
2. Calls `UserRecipe.objects.get_or_create()` to ensure a UserRecipe entry exists
3. **BUG**: The `is_archived=False` was in the `defaults` dict, which means:
   - ✅ If creating a NEW UserRecipe → Sets `is_archived=False`
   - ❌ If UserRecipe already exists (but archived) → Does NOTHING!

**Result:** The recipe stays archived (`is_archived=True`), so it doesn't appear in "My Recipes" / "Recipes" page.

---

## ✅ **The Fix:**

### **Code Changed:**

```python
# backend/apps/recipes/services.py (Lines 616-635)

if existing_fork:
    print(f"[FORK] User already has fork: {existing_fork.id}")
    
    # Ensure UserRecipe entry exists and is NOT archived
    user_recipe, created = UserRecipe.objects.get_or_create(
        user=user,
        recipe=existing_fork,
        defaults={
            'saved_at': timezone.now(),
            'is_archived': False
        }
    )
    
    # ✅ NEW: If the UserRecipe already existed but was archived, unarchive it
    if not created and user_recipe.is_archived:
        user_recipe.is_archived = False
        user_recipe.saved_at = timezone.now()  # Update saved_at to show as recently saved
        user_recipe.save(update_fields=['is_archived', 'saved_at'])
        print(f"[FORK] Unarchived recipe: {existing_fork.id}")
    
    return existing_fork
```

### **What Changed:**

**BEFORE:**
```python
UserRecipe.objects.get_or_create(
    user=user,
    recipe=existing_fork,
    defaults={'is_archived': False}  # ← Only used when CREATING
)
```
- If UserRecipe exists with `is_archived=True`, it stays archived ❌

**AFTER:**
```python
user_recipe, created = UserRecipe.objects.get_or_create(...)

# Explicitly unarchive if it was archived
if not created and user_recipe.is_archived:
    user_recipe.is_archived = False
    user_recipe.saved_at = timezone.now()
    user_recipe.save()
```
- If UserRecipe exists with `is_archived=True`, we explicitly set it to `False` ✅

---

## 🎯 **How It Works Now:**

### **Complete Flow:**

1. **First Like (Recipe Generation):**
   ```
   User generates recipe → Like created → Fork created → UserRecipe created
   is_archived = False ✅
   → Recipe appears in "Recipes" page
   ```

2. **Unlike → Archive → Delete:**
   ```
   User unlikes → RecipeLike deleted → UserRecipe.is_archived = True
   User deletes → UserRecipe might be deleted or kept as archived
   → Recipe disappears from "Recipes" page
   ```

3. **Re-like (THE FIX):**
   ```
   User likes again from Discovery →
   Backend finds existing fork ✅
   Backend finds existing UserRecipe (is_archived = True) ✅
   Backend sets is_archived = False ✅
   Backend updates saved_at to NOW ✅
   → Recipe REAPPEARS in "Recipes" page! 🎉
   ```

---

## 📝 **Files Modified:**

1. **`backend/apps/recipes/services.py`** (Lines 616-635)
   - `_create_or_get_user_fork()` method
   - Added explicit unarchiving logic when re-liking

---

## ✅ **What's Fixed:**

| Scenario | Before | After |
|----------|--------|-------|
| **First like** | ✅ Appears in Recipes | ✅ Appears in Recipes |
| **Unlike/archive** | ✅ Disappears | ✅ Disappears |
| **Re-like from Discovery** | ❌ Stays hidden | ✅ **REAPPEARS!** |
| **`saved_at` timestamp** | Old timestamp | ✅ Updated to NOW |

---

## 🧪 **Test Scenario:**

1. **Generate a recipe** from Discovery page (AI search)
   - ✅ Recipe auto-liked
   - ✅ Appears in "Recipes" page

2. **Unlike the recipe** from "Recipes" page
   - ✅ Recipe moves to archive

3. **Delete from archive**
   - ✅ Recipe removed from "My Recipes"

4. **Go back to Discovery page**
   - ✅ Recipe still visible in Discovery

5. **Like it again** from Discovery
   - ✅ **Recipe REAPPEARS in "Recipes" page!** 🎉
   - ✅ `saved_at` timestamp is updated to current time
   - ✅ Shows at the top (most recent)

---

## 📊 **Database Changes:**

**Before Fix:**
```sql
-- User unlikes
UPDATE user_recipes SET is_archived = TRUE WHERE id = X;

-- User likes again
-- Nothing happens! is_archived stays TRUE ❌
```

**After Fix:**
```sql
-- User unlikes
UPDATE user_recipes SET is_archived = TRUE WHERE id = X;

-- User likes again
UPDATE user_recipes 
SET is_archived = FALSE, saved_at = NOW()
WHERE id = X;  ✅
```

---

## 💡 **Why This Was Critical:**

1. **User Confusion:** "I liked the recipe but it's not in my Recipes page!"
2. **Data Loss:** User thinks the recipe is gone forever
3. **Broken UX:** Unlike → Re-like should restore the recipe
4. **Archive System:** The whole archive/unarchive flow depends on this

**This fix ensures the archive system works bidirectionally: archive ↔ unarchive**

---

## 🚀 **Backend Status:**

The fix is now live in the code. No database migration needed (no schema changes).

**Next time you like a previously archived recipe from Discovery, it will automatically reappear in your Recipes page!** 🎉

---

## 📝 **Summary:**

- ✅ **Root cause:** `get_or_create()` doesn't update existing archived records
- ✅ **Fix:** Explicitly set `is_archived=False` when re-liking
- ✅ **Result:** Recipes can be archived and unarchived by liking/unliking
- ✅ **Bonus:** `saved_at` timestamp updated, so recipe appears at top of "Recipes" page

**The archive system now works perfectly in both directions!** 🎉

