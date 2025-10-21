# Selenium E2E Test Instructions

## What This Test Does

1. **Logs in** to the application as testuser1
2. **Switches to Russian** language
3. **Navigates to Discovery page**
4. **Generates a new recipe** using AI search (шакшука/Shakshuka)
5. **Opens recipe details**
6. **Verifies**:
   - ✅ Recipe name is in Russian (Cyrillic characters)
   - ✅ Ingredients are in Russian (at least 3/5)
   - ✅ Units are translated (г, мл, ч.л., зубчика, etc.)
   - ✅ Cooking steps are in Russian (at least 2/3)

## Requirements

```bash
pip install selenium
```

You also need Chrome browser and ChromeDriver installed.

## Running the Test

### Option 1: With visible browser (recommended for first run)
```bash
cd backend
python test_translation_selenium.py
```

### Option 2: Headless mode (faster, no UI)
Edit line 22 in the script, uncomment:
```python
chrome_options.add_argument('--headless')
```

Then run:
```bash
cd backend
python test_translation_selenium.py
```

## What You'll See

The test will:
1. Open Chrome browser
2. Login automatically
3. Switch to Russian
4. Search for "шакшука"
5. Wait for generation (30-60 seconds)
6. Open the recipe
7. Check all translations
8. Print detailed results
9. Save screenshots at each step
10. Close browser after 5 seconds

## Expected Output

```
================================================================================
SELENIUM E2E TEST: Recipe Translation
================================================================================

1. Logging in...
   ✓ Logged in successfully

2. Switching to Russian...
   ✓ Switched to Russian

3. Navigating to Discovery page...
   ✓ On Discovery page

4. Generating recipe: шакшука...
   ⏳ Waiting for recipe generation (may take 30-60 seconds)...
   ✓ Recipe generated successfully

5. Opening recipe details...
   ✓ Recipe details opened

6. Verifying translation...
   
   Recipe Name: Шакшука
   ✓ Recipe name is in Russian
   
   Found ingredients section
   
   Checking 5 ingredients:
      1. 400 г помидоры
      2. 4 шт яйца
      3. 2 зубчика чеснок
      4. 1 ч.л. соль
      5. 2 ст.л. масло оливковое
   ✓ Ingredients are in Russian (5/5)
   ✓ Units are translated (5/5)
   
   Found cooking steps section
   
   Checking 3 steps:
      1. Нарежьте помидоры кубиками и обжарьте с чесноком
      2. Добавьте специи и тушите 10 минут
      3. Сделайте углубления и разбейте яйца
   ✓ Cooking steps are in Russian (3/3)

================================================================================
TEST RESULTS
================================================================================

✅ Recipe Name Translation
✅ Ingredient Names Translation
✅ Unit Translation
✅ Cooking Steps Translation

================================================================================
✅ ALL TESTS PASSED!
================================================================================
```

## Screenshots

The test saves screenshots at each step:
- `test_screenshot_recipe_generated_*.png` - Recipe list after generation
- `test_screenshot_recipe_details_*.png` - Recipe details view
- `test_screenshot_error_*.png` - If error occurs

## Troubleshooting

### Issue: ChromeDriver not found
```bash
# Windows (using Chocolatey)
choco install chromedriver

# Or download manually from:
# https://chromedriver.chromium.org/
```

### Issue: Language not switching
- The test tries to find the language switcher automatically
- If it fails, manually switch to Russian before running the test
- Or modify the script to match your specific UI elements

### Issue: Recipe generation timeout
- Increase timeout on line 92: `EC.presence_of_element_located(...), 90)`
- Change 90 to 120 or higher

### Issue: Elements not found
- The test uses generic XPath selectors
- You may need to adjust selectors based on your specific HTML structure
- Check the saved screenshots to see what the page looks like

## Customization

Edit these variables at the top of the script:

```python
FRONTEND_URL = "http://localhost:3000"  # Your frontend URL
TEST_USERNAME = "testuser1"              # Your test username
TEST_PASSWORD = "testpass123"            # Your test password
RECIPE_SEARCH = "шакшука"                # Recipe to search for
```

## What to Check If Test Fails

1. **Backend logs** - Check for errors during recipe generation
2. **Screenshots** - See what the page actually looked like
3. **Browser console** - Open DevTools and check for JS errors
4. **Network tab** - Verify API calls are succeeding

This test will give us a **definitive answer** about whether the translation system works end-to-end!

