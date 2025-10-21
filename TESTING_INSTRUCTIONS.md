# CRITICAL: TESTING THE TRANSLATION FIX

## The Problem with Your Current "Карбонара" Recipe

The recipe you're looking at was generated and translated **BEFORE my fix**. It has:
- ❌ No cooking steps (AI extraction failed from the website)
- ❌ 51 duplicate ingredients (garbage data)
- ❌ Units not translated (old bug)

**You CANNOT test with this recipe!** It's broken data.

## What I Fixed

1. **Gemini Fallback**: If ingredient/step not in database, use Gemini
2. **Field Name Bug**: Steps use `'instruction'` not `'text'`
3. **Unit Translation**: Added translation dictionary for units (g -> г, cloves -> зубчика, etc.)

## HOW TO TEST (Step-by-Step)

### 1. Delete the broken Carbonara recipe
- Go to Discovery page
- Unlike/delete the current Carbonara recipe
- OR: Just generate a different recipe

### 2. Generate a FRESH recipe
On the Discovery page, in Russian interface, search for:
- **"борщ"** (Borscht - very popular Russian soup)
- OR **"оливье"** (Olivier salad - another popular recipe)
- OR **"пельмени"** (Dumplings)

### 3. What to check in the NEW recipe:
✓ Recipe name in Russian
✓ Ingredient names in Russian (яйца, мука, соль, etc.)
✓ Units in Russian (г instead of g, ч.л. instead of tsp, зубчика instead of cloves)
✓ Cooking steps in Russian with proper instructions

### 4. Expected Results

**GOOD RECIPE:**
```
Название: Борщ
Ингредиенты:
1. 500 г свекла
2. 300 г капуста
3. 2 зубчика чеснок
4. 1 ч.л. соль

Инструкции:
1. Нарежьте свеклу кубиками
2. Варите бульон 30 минут
3. Добавьте овощи и специи
```

**BAD RECIPE (like your current one):**
```
Ingredients:
1. 200 g (No recipe provided)
2. 1 as needed eggs

Steps:
1. Given that there are no steps provided in the original text...
```

## If It STILL Fails

1. **Share the backend console output** - I need to see the logs
2. **Share a screenshot** of the new recipe
3. **Tell me the exact search query** you used

## Backend is Ready

I've restarted the backend with all fixes:
- ✅ Gemini fallback for ingredients
- ✅ Gemini fallback for steps
- ✅ Unit translation dictionary
- ✅ Fixed field name bug (`instruction` vs `text`)

**The old broken recipe cannot be fixed. You MUST generate a NEW one to test!**

