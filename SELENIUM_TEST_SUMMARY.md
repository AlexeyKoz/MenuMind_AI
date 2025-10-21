# Selenium Test Summary

## ✅ Setup Complete

- ✅ Selenium installed
- ✅ ChromeDriver available
- ✅ Test script ready: `test_translation_selenium.py`

## Running the Test

### Automated Test (Full E2E)
```bash
cd backend
python test_translation_selenium.py
```

This will:
1. Open Chrome browser automatically
2. Login as testuser1
3. Switch to Russian
4. Navigate to Discovery
5. Search for "шакшука" (Shakshuka)
6. Wait for generation (30-60 seconds)
7. Open recipe details
8. Verify all translations
9. Print detailed results
10. Save screenshots
11. Close browser after 5 seconds

### Manual Testing (If automated fails)

1. **Start your frontend** (http://localhost:3000)
2. **Login** as testuser1
3. **Switch to Russian** language
4. **Go to Discovery page**
5. **Search for a simple recipe** in the AI search box:
   - Try: "шакшука" (Shakshuka)
   - Or: "борщ" (Borscht)
   - Or: "оливье" (Olivier salad)
6. **Click "Найти рецепт"** (Find Recipe)
7. **Wait 30-60 seconds** for generation
8. **Click on the recipe card** to open details
9. **Check the recipe**:

#### What to Check:
- [ ] Recipe name in Russian (Cyrillic characters)
- [ ] Ingredient names in Russian
- [ ] Units in Russian:
  - g → г
  - tsp → ч.л.
  - tbsp → ст.л.
  - cloves → зубчика
  - pcs → шт
- [ ] Cooking steps in Russian (no English error messages)

#### Good Example:
```
Шакшука

Ингредиенты:
• 400 г помидоры
• 4 шт яйца
• 2 зубчика чеснок
• 1 ч.л. соль

Инструкции:
1. Нарежьте помидоры кубиками
2. Обжарьте с чесноком 5 минут
3. Разбейте яйца и готовьте до готовности
```

#### Bad Example (Old Bug):
```
Carbonara

Ingredients:
• 200 g (No recipe provided)
• 2 cloves garlic

Instructions:
1. Given that there are no steps provided in the original text, I cannot provide any translations.
```

## Expected Test Results

If all fixes are working:

```
================================================================================
TEST RESULTS
================================================================================

OK Recipe Name Translation
OK Ingredient Names Translation
OK Unit Translation
OK Cooking Steps Translation

================================================================================
OK ALL TESTS PASSED!
================================================================================
```

## Screenshots

The test saves screenshots to `backend/`:
- `test_screenshot_recipe_generated_*.png`
- `test_screenshot_recipe_details_*.png`
- `test_screenshot_error_*.png` (if error)

## What This Proves

✅ **Ingredients**: Translated using IML + Gemini fallback
✅ **Units**: Translated using dictionary (g → г, etc.)
✅ **Steps**: Translated using CookLingo + Gemini fallback
✅ **Complete Flow**: Recipe generated → Translated → Displayed correctly

## If Test Fails

1. Check backend console for errors
2. Look at the saved screenshots
3. Try generating the recipe manually to see the actual output
4. Share:
   - Test output
   - Screenshots
   - Backend console logs
   - Recipe name you searched for

## Important Notes

⚠️ **Do NOT test with old recipes!** Old recipes (like the Carbonara you showed earlier) were generated with the OLD buggy code. They have broken data and cannot be fixed. You **MUST** generate a **NEW** recipe to see the fixes.

⚠️ **Backend must be running!** The test requires the backend API to be available at http://localhost:8000

⚠️ **Frontend must be running!** The test requires the frontend UI to be available at http://localhost:3000

