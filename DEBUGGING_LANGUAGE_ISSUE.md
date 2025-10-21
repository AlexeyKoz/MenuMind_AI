# 🔧 Debugging Language Switching Issue

## 📋 **Checklist to Debug**

### **Step 1: Check Frontend Console**

Open the browser console (F12) and look for these messages when you switch language:

**Expected logs:**
```
🌍 Language changed to he, refetching recipe abc-123...
✅ Recipe refetched with he translation
   Ingredients preview: [{amount: "2", unit: "tbsp", name: "שמן"}, ...]
```

**If you DON'T see these logs:**
- Frontend is not detecting language change
- Issue: `i18n.language` not updating
- Solution: Hard refresh (Ctrl+F5)

**If you see:**
```
⚠️ No recipe selected, skipping language change refetch
```
- Recipe is not in `selectedRecipe` state
- Issue: Recipe modal might be using different state
- Solution: Check if recipe is in modal vs main view

---

### **Step 2: Check Backend Console**

Look at Django console for these messages:

**Expected logs:**
```
[RETRIEVE] Recipe abc-123 requested by user in language: he
[RETRIEVE] ⚠️ No he translation found for recipe abc-123
[RETRIEVE] 🔄 Creating he translation NOW for recipe abc-123
   [IML] Translated: flour → קמח
   [IML] Translated: eggs → ביצים
[RETRIEVE] ✅ Translation completed! Returning he version
```

**If you see:**
```
[RETRIEVE] Recipe abc-123 requested by user in language: en
```
- User's `preferred_language` is still 'en'
- Issue: Language switcher not updating backend
- Solution: Check if API call is working

---

### **Step 3: Manually Check User's Language**

Run this in Django shell:

```bash
cd backend
python manage.py shell

from apps.users.models import User

# Get your user
user = User.objects.get(username='YOUR_USERNAME')
print(f"User's preferred_language: {user.preferred_language}")

# If it says 'en', manually update:
user.preferred_language = 'he'
user.save()
print("✅ Updated to Hebrew")
```

---

### **Step 4: Manually Create Translation**

If translation doesn't exist, create it manually:

```bash
cd backend
python manage.py shell

from apps.recipes.models import CanonicalRecipe, RecipeTranslation
from apps.core.models import IngredientCache
from apps.core.cooking_terms_service import CookingTermsTranslationService
from django.utils import timezone

# Get the Shakshuka recipe (or any recipe by name)
recipe = CanonicalRecipe.objects.filter(name__icontains='shakshuka').first()
print(f"Found recipe: {recipe.name} ({recipe.id})")

# Check if Hebrew translation exists
translation = RecipeTranslation.objects.filter(
    canonical_recipe=recipe,
    language='he'
).first()

if translation:
    print(f"✅ Translation exists: {translation.status}")
    if translation.status == 'completed':
        print(f"   Ingredients: {len(translation.base_ingredients)}")
        print(f"   Steps: {len(translation.base_steps)}")
        print(f"   First ingredient: {translation.base_ingredients[0]}")
else:
    print("❌ No Hebrew translation found - creating now...")
    
    # Create translation record
    translation = RecipeTranslation.objects.create(
        canonical_recipe=recipe,
        language='he',
        status='in_progress'
    )
    
    # Initialize cooking terms service
    cooking_terms_service = CookingTermsTranslationService()
    
    # Translate ingredients
    translated_ingredients = []
    for ing in recipe.base_ingredients:
        translated_ing = ing.copy()
        
        if ing.get('ingredient_key'):
            try:
                ingredient_obj = IngredientCache.objects.get(
                    ingredient_key=ing['ingredient_key'])
                translations_dict = {}
                for trans in ingredient_obj.translations.all():
                    translations_dict[trans.language] = trans.name
                
                if 'he' in translations_dict:
                    translated_ing['name'] = translations_dict['he']
                    print(f"   Translated: {ing['name']} → {translated_ing['name']}")
            except IngredientCache.DoesNotExist:
                pass
        
        translated_ingredients.append(translated_ing)
    
    # Translate steps
    translated_steps = []
    for step in recipe.base_steps:
        translated_step = step.copy()
        
        if step.get('text'):
            original_text = step['text']
            translated_step['text'] = cooking_terms_service.translate_text(
                original_text,
                'he'
            )
            print(f"   Step: {original_text[:40]}...")
            print(f"      → {translated_step['text'][:40]}...")
        
        translated_steps.append(translated_step)
    
    # Save translation
    translation.name = recipe.name
    translation.description = recipe.description
    translation.base_ingredients = translated_ingredients
    translation.base_steps = translated_steps
    translation.status = 'completed'
    translation.completed_at = timezone.now()
    translation.save()
    
    print(f"\n✅ Translation created!")
    print(f"   Ingredients: {len(translated_ingredients)}")
    print(f"   Steps: {len(translated_steps)}")
```

---

### **Step 5: Test API Directly**

Use curl or Postman to test the API:

```bash
# Get your auth token from browser (F12 → Application → Local Storage)
# Look for 'token' or 'access_token'

# Test getting recipe
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:8000/api/recipes/canonical/RECIPE_ID/

# Check response - should have base_ingredients and base_steps
```

---

### **Step 6: Force Frontend Refresh**

If all else fails, add a manual refresh button:

1. Open browser console (F12)
2. Type:
   ```javascript
   // Get current recipe ID from the page
   const recipeId = 'YOUR_RECIPE_ID';
   
   // Fetch with current language
   fetch(`http://localhost:8000/api/recipes/canonical/${recipeId}/`, {
     headers: {
       'Authorization': 'Bearer ' + localStorage.getItem('token')
     }
   })
   .then(r => r.json())
   .then(data => {
     console.log('Recipe data:', data);
     console.log('First ingredient:', data.base_ingredients[0]);
   });
   ```

---

## 🐛 **Common Issues**

### **Issue 1: Frontend not refetching**

**Symptoms:**
- No console logs when switching language
- Recipe doesn't update

**Causes:**
- `i18n.language` not changing
- `useEffect` not triggering
- Hard-coded English content

**Fix:**
1. Hard refresh (Ctrl+F5)
2. Clear browser cache
3. Check if LanguageSwitcher is actually changing `i18n.language`

---

### **Issue 2: Backend not creating translation**

**Symptoms:**
- Backend logs show "Returning English version"
- No translation errors in console

**Causes:**
- IML database empty
- CookLingo database empty
- Translation logic error

**Fix:**
```bash
# Check database counts
python manage.py shell

from apps.core.models import IngredientCache, CookingTermCache

print(f"IML ingredients: {IngredientCache.objects.count()}")
print(f"CookLingo terms: {CookingTermCache.objects.count()}")

# If 0, sync databases
exit()

python manage.py sync_iml_to_postgres
python manage.py sync_cooklingo_to_postgres
```

---

### **Issue 3: User's language not updating**

**Symptoms:**
- Backend always receives language='en'
- Switching language doesn't persist

**Causes:**
- API call failing
- User model not saving

**Fix:**
```bash
# Manually set user language
python manage.py shell

from apps.users.models import User

user = User.objects.get(username='YOUR_USERNAME')
user.preferred_language = 'he'
user.save()

print(f"✅ Set language to: {user.preferred_language}")
```

---

## 🚀 **Quick Fix Steps**

**If nothing is working, do this:**

1. **Set language in database:**
   ```bash
   python manage.py shell
   from apps.users.models import User
   user = User.objects.first()  # Or get by username
   user.preferred_language = 'he'
   user.save()
   ```

2. **Manually create translation** (use script in Step 4)

3. **Hard refresh frontend** (Ctrl+F5)

4. **Open recipe** → Should be in Hebrew

---

## 📝 **What to Report**

If still not working, provide:

1. **Frontend console logs** (copy all messages)
2. **Backend console logs** (copy from Django terminal)
3. **User's language**: Run `User.objects.get(username='YOUR_USERNAME').preferred_language`
4. **Translation exists**: Run `RecipeTranslation.objects.filter(canonical_recipe__name__icontains='shakshuka', language='he').exists()`
5. **Database counts**: IML and CookLingo counts

---

**Try Step 3 first** (manually check user's language) - this is most likely the issue!

