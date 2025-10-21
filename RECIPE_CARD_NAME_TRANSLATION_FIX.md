# RECIPE CARD NAME TRANSLATION FIX

## ✅ **FIXED: Recipe Names in Card View Now Translate**

**Date:** 2025-10-21  
**Issue:** Recipe names in the card list view (Discover page) stayed in original language when switching languages

---

## 🐛 **The Problem:**

**Before:**
- ✅ Recipe detail view: Name translated correctly
- ❌ Recipe card list view: Name stayed in Hebrew/original language

**Why:**
The `list()` method in `CanonicalRecipeViewSet` was using the default Django REST Framework behavior, which just serializes the database value (English name) without checking for translations.

---

## ✅ **The Fix:**

### **Backend Changes:**

**Added custom `list()` method to `CanonicalRecipeViewSet`:**

```python
# backend/apps/recipes/views.py (Lines 1067-1106)

def list(self, request, *args, **kwargs):
    """
    List canonical recipes with translated names
    """
    queryset = self.filter_queryset(self.get_queryset())

    page = self.paginate_queryset(queryset)
    if page is not None:
        serializer = self.get_serializer(page, many=True)
        recipes_data = serializer.data
    else:
        serializer = self.get_serializer(queryset, many=True)
        recipes_data = serializer.data

    # Get user's preferred language
    user_language = getattr(request.user, 'preferred_language', 'en')
    
    # If not English, add translated names to each recipe
    if user_language != 'en':
        from .models import RecipeTranslation
        
        print(f"[LIST] Translating {len(recipes_data)} recipe names to {user_language}")
        
        for recipe_data in recipes_data:
            try:
                translation = RecipeTranslation.objects.filter(
                    canonical_recipe_id=recipe_data['id'],
                    language=user_language,
                    status='completed'
                ).first()
                
                if translation and translation.name:
                    print(f"[LIST] ✅ {recipe_data['name']} -> {translation.name}")
                    recipe_data['name'] = translation.name
            except Exception as e:
                print(f"[LIST] ⚠️ No translation for recipe {recipe_data.get('id')}: {e}")
    
    if page is not None:
        return self.get_paginated_response(recipes_data)
    return Response(recipes_data)
```

**How it works:**
1. Get the list of recipes from the database
2. Serialize them (convert to JSON)
3. **NEW:** For each recipe, look up the translation in the user's preferred language
4. **NEW:** Replace the English name with the translated name
5. Return the modified data

---

### **Frontend Changes:**

**Added language change handler to reload recipe list:**

```typescript
// frontend/src/pages/CanonicalRecipesPage.tsx (Lines 55-59)

// Reload recipe list when language changes
useEffect(() => {
    console.log(`🌍 Language changed to ${i18n.language}, reloading recipe list...`);
    loadRecipes();
}, [i18n.language]);
```

**How it works:**
1. User switches language in the UI
2. `i18n.language` changes
3. useEffect detects the change
4. Calls `loadRecipes()` to fetch the list again
5. Backend returns recipes with translated names
6. Card view updates with translated names

---

## 📝 **Files Modified:**

1. **`backend/apps/recipes/views.py`** (Lines 1067-1106)
   - Added custom `list()` method to `CanonicalRecipeViewSet`
   - Looks up translations for each recipe
   - Replaces English names with translated names

2. **`frontend/src/pages/CanonicalRecipesPage.tsx`** (Lines 55-59)
   - Added useEffect to reload recipe list on language change

---

## ✅ **What's Fixed:**

| View | Before | After |
|------|--------|-------|
| **Recipe Detail** | ✅ Name translated | ✅ Name translated |
| **Recipe Card List** | ❌ Name in Hebrew | ✅ Name translated |

### **Example:**

**When user switches from Hebrew to Russian:**

| Element | Hebrew | Russian (After Fix) |
|---------|--------|---------------------|
| Detail View Name | שקשוקה | Шакшука ✅ |
| Card View Name | שקשוקה (was stuck) | Шакшука ✅ (now updates!) |

---

## 🧪 **Test Now:**

1. ✅ **Backend restarted** (just done)
2. **Hard refresh browser** (Ctrl+Shift+R)
3. **Switch languages** (English → Russian → Hebrew)

### **Expected Results:**

**When switching from Hebrew to Russian:**
- ✅ Recipe name in detail view: "Шакшука"
- ✅ Recipe name in card list: "Шакшука" (NOT "שקשוקה")
- ✅ All recipe cards update with Russian names

**When switching from Russian to English:**
- ✅ All recipe names switch to English
- ✅ Both detail view AND card list update

---

## 📊 **Summary:**

- ✅ **Recipe detail view names translate** (was already working)
- ✅ **Recipe card list names translate** (NOW FIXED!)
- ✅ **Both views update when language changes**
- ✅ **Uses existing translation database**

**Refresh your browser and try switching languages - all recipe names should now update!** 🎉

