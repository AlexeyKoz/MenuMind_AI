# 🧪 Discovery Agent - Testing Checklist

## ✅ Critical Improvements Made

### 1. **Immediate Translation**
- Recipes now translate to user's language **immediately** during generation
- No more English flash, no need to refresh

### 2. **Aggressive Junk Filtering**
- "1 as needed" entries removed
- AI commentary removed ("After analyzing...", "I found...")
- Website fluff removed ("visit my blog", "subscribe")

### 3. **Language Switching**
- When you change site language, recipes fetch the correct translation
- Translations are cached in database (fast retrieval)

---

## 🧪 Test Scenarios

### **Test 1: Generate Recipe in Russian** 🇷🇺

**Steps:**
1. Open menumine-ai frontend
2. Switch to Russian (top right: "ru Русский")
3. Go to "Обзор" (Discovery) page
4. Search: **"шоколадный торт"** (chocolate cake)
5. Wait 5-10 seconds

**Expected Results:**
- ✅ Recipe appears with Russian name
- ✅ All ingredients in Russian (мука, яйца, сахар, etc.)
- ✅ All steps in Russian (using CookLingo terms)
- ✅ NO "1 as needed" entries
- ✅ NO junk text like "After analyzing..."
- ✅ Steps are actual cooking instructions (10-20 steps)

**Backend Logs to Check:**
```
[TRANSLATION] ⚡ Translating IMMEDIATELY to ru (user's language)
[TRANSLATION] ✅ User language translation completed: created
[TRANSLATION] ✅ Using ru translation for response
```

---

### **Test 2: Switch to Hebrew** 🇮🇱

**Steps:**
1. After Test 1, switch to Hebrew (top right: "he עברית")
2. Stay on same recipe OR search again
3. Recipe should now be in Hebrew

**Expected Results:**
- ✅ Same recipe, now in Hebrew
- ✅ All ingredients in Hebrew
- ✅ All steps in Hebrew
- ✅ Fast loading (translation cached)

**Backend Logs to Check:**
```
[TRANSLATION] ✅ Using he translation for response
```

---

### **Test 3: Complex Recipe (Napoleon Cake)** 🍰

**Steps:**
1. Switch to Russian
2. Go to Discovery page
3. Search: **"торт наполеон"** (Napoleon cake)
4. Wait for generation

**Expected Results:**
- ✅ At least 15-20 steps (Napoleon is complex!)
- ✅ All steps are cooking actions (not website fluff)
- ✅ Ingredients include: мука, масло, яйца, сметана, etc.
- ✅ NO "1 as needed" garbage

**Special Check:**
- Napoleon cake should have steps for:
  1. Making dough
  2. Rolling thin layers
  3. Baking each layer
  4. Making cream
  5. Assembling layers
  6. Chilling
- If you only see 3-4 steps, the AI is still summarizing (report this!)

---

### **Test 4: English Recipe (Control)** 🇺🇸

**Steps:**
1. Switch to English (top right: "en English")
2. Go to Discovery page
3. Search: **"beef wellington"**
4. Wait for generation

**Expected Results:**
- ✅ Recipe appears in English
- ✅ NO immediate translation (user language is English)
- ✅ Background translations queued for Russian + Hebrew
- ✅ Clean ingredients (no junk)
- ✅ Complete steps (Beef Wellington is complex, 15+ steps)

**Backend Logs to Check:**
```
[TRANSLATION] ✅ Queued background translations for: ['ru', 'he']
```

---

### **Test 5: Check Specific Ingredients** 🥕

**Search for recipes with these ingredients and verify translations:**

| English | Russian | Hebrew |
|---------|---------|--------|
| flour | мука | קמח |
| eggs | яйца | ביצים |
| milk | молоко | חלב |
| butter | сливочное масло | חמאה |
| sugar | сахар | סוכר |
| salt | соль | מלח |
| water | вода | מים |

**Steps:**
1. Generate a cake recipe in Russian
2. Check that ingredients match the table above
3. Switch to Hebrew, check again

---

## 🐛 Known Issues to Watch For

### **Issue 1: "1 as needed" Still Appears**
**If this happens:**
1. Check backend logs for AI response
2. Look for: `[AI] ✅ Cleaned response, starts with INGREDIENTS`
3. If not found, the AI prompt is not being followed
4. Report the exact query that caused it

### **Issue 2: Recipe in Wrong Language**
**If recipe appears in English when you're on Russian:**
1. Check backend logs for: `[TRANSLATION] ⚡ Translating IMMEDIATELY`
2. If not found, user language detection failed
3. Check user profile settings (preferred_language field)

### **Issue 3: Incomplete Steps**
**If recipe only has 3-5 steps for a complex dish:**
1. Check backend logs for: `[RCIP] Recipe has X ingredients and Y steps`
2. If Y < 10 for complex recipes, AI is summarizing
3. Report the recipe name and URL the AI scraped from

### **Issue 4: Translation Missing**
**If switching language shows English instead of translation:**
1. Check backend logs for: `[TRANSLATION] ⚠️ No completed translation found`
2. Check database: `RecipeTranslation` table, look for `status` field
3. If status is 'failed', check error logs

---

## 📊 Performance Benchmarks

### **Expected Timings:**

| Action | Time | Status |
|--------|------|--------|
| Generate recipe (Russian user) | 5-10 sec | ✅ Includes immediate translation |
| Generate recipe (English user) | 3-7 sec | ✅ No translation needed |
| Switch language (cached) | < 1 sec | ✅ Fetches from database |
| Background translation | 10-30 sec | ⏳ Happens async |

### **What's Normal:**
- First recipe generation: 5-10 seconds (scraping + AI + translation)
- Cached recipe retrieval: < 1 second
- Language switching: < 1 second (if translation exists)

### **What's Too Slow:**
- Generation > 15 seconds → Web scraping issue or AI timeout
- Language switch > 3 seconds → Database query issue

---

## 🔍 Debug Commands

### **Check if translation exists:**
```bash
# Open Django shell
cd backend
python manage.py shell

# Check translations for a recipe
from apps.recipes.models import CanonicalRecipe, RecipeTranslation

recipe = CanonicalRecipe.objects.latest('created_at')
print(f"Recipe: {recipe.name}")

translations = RecipeTranslation.objects.filter(canonical_recipe=recipe)
for t in translations:
    print(f"  - {t.language}: {t.status}")
```

### **Check IML sync status:**
```bash
cd backend
python manage.py shell

from apps.core.models import IngredientCache, CookingTermCache

print(f"IML Ingredients: {IngredientCache.objects.count()}")
print(f"CookLingo Terms: {CookingTermCache.objects.count()}")
```

### **View backend logs:**
Watch the Django console for:
- `[TRANSLATION]` - Translation status
- `[AI]` - AI extraction results
- `[IML]` - Ingredient enrichment
- `[RCIP]` - Recipe conversion

---

## ✅ Success Criteria

**All tests pass if:**

- ✅ Recipes generate in user's selected language
- ✅ NO "1 as needed" or junk text in ingredients
- ✅ NO website commentary in steps
- ✅ Language switching works instantly
- ✅ Complex recipes have 10+ steps
- ✅ Ingredients translate correctly (IML)
- ✅ Cooking terms translate correctly (CookLingo)

**If ANY test fails:**
1. Check backend logs
2. Note exact query and language
3. Report with screenshots + logs

---

## 🚀 Ready to Test!

Start with **Test 1** (Russian chocolate cake) - this is the most important one!

If that works, the system is functioning correctly. 🎉

