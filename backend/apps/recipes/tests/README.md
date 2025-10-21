# Testing Suite for Recipe Translation

This directory contains automated tests for verifying recipe generation and translation functionality.

## Tests

### 1. Backend Test: Recipe Translation (`test_recipe_translation.py`)

Tests that recipes are properly generated and translated to all supported languages (English, Russian, Hebrew).

**What it tests:**
- Recipe generation from user query
- Canonical recipe stored in English
- Immediate translation to user's preferred language (Russian)
- Background translation queued for other languages (Hebrew)
- Ingredient translation
- Cooking steps translation
- Language switching returns correct translations

**Run the test:**
```bash
cd backend
python -m pytest apps/recipes/tests/test_recipe_translation.py -v -s
```

**Expected output:**
```
🧪 TEST: Recipe Generation + Translation
✅ Recipe created: <name>
✅ Canonical has X ingredients
✅ Canonical has Y steps
✅ Russian translation exists and is completed
✅ Hebrew translation queued (background task)
✅ ALL TESTS PASSED!
```

---

### 2. Frontend Test: Language Switching (`test_language_switching.py`)

Selenium test that verifies language switching on the Discover page with visual screenshots.

**What it tests:**
- Login functionality
- Navigate to Discover page
- Generate recipe using AI agent
- Open recipe detail
- Switch between languages (Russian → English → Hebrew → Russian)
- Verify content changes in each language
- Take screenshots at each step

**Prerequisites:**
```bash
# Install Selenium
pip install selenium

# Install Chrome WebDriver
# Windows: Download from https://chromedriver.chromium.org/
# Or use: pip install webdriver-manager
```

**Run the test:**
```bash
cd frontend/tests
python test_language_switching.py
```

**Before running:**
1. Start backend: `cd backend && python manage.py runserver`
2. Start frontend: `cd frontend && npm run dev`
3. Ensure test user exists:
   ```bash
   cd backend
   python manage.py shell
   >>> from django.contrib.auth import get_user_model
   >>> User = get_user_model()
   >>> User.objects.create_user(username='testuser', email='test@example.com', password='testpass123', preferred_language='ru')
   ```

**Expected output:**
```
🧪 FRONTEND TEST: Language Switching on Discover Page
✅ Logged in successfully
✅ On Discover page
✅ Recipe generated
✅ Recipe opened
✅ Switched to ru
✅ Switched to en
✅ Switched to he
📊 TEST RESULTS
✅ PASS: English and Russian steps are different
✅ PASS: Russian step contains Cyrillic characters
✅ PASS: Hebrew step contains Hebrew characters
📁 Screenshots saved to: test_screenshots/
```

**Screenshots:**
All screenshots are saved to `test_screenshots/` with timestamps:
- `01_logged_in.png` - After login
- `02_discover_page.png` - Discover page
- `03_recipe_generated.png` - Recipe generated
- `04_recipe_opened_initial.png` - Recipe detail opened
- `05_language_ru.png` - Russian translation
- `05_language_en.png` - English version
- `05_language_he.png` - Hebrew translation

---

## Quick Run All Tests

```bash
# Backend test
cd backend
python -m pytest apps/recipes/tests/test_recipe_translation.py -v -s

# Frontend test (in a separate terminal)
cd frontend/tests
python test_language_switching.py
```

---

## Troubleshooting

### Backend Test Fails

1. **No translation found**: 
   - Check that Gemini API key is configured
   - Check backend logs for translation errors
   - Verify IML and CookLingo databases are synced

2. **Recipe generation fails**:
   - Check that Groq/Gemini API keys are configured
   - Check internet connection for recipe search
   - Check backend logs for errors

### Frontend Test Fails

1. **Login fails**:
   - Verify test user exists with correct password
   - Check that backend is running on port 8000
   - Check that frontend is running on port 5173

2. **Language switching doesn't work**:
   - Check browser console for errors
   - Verify language selector element exists
   - Check network tab for API calls

3. **ChromeDriver issues**:
   - Download matching ChromeDriver version
   - Use `webdriver-manager` for automatic management
   - Check Chrome browser version

---

## CI/CD Integration

To run these tests in CI/CD:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          python -m pytest apps/recipes/tests/test_recipe_translation.py -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install Selenium
        run: pip install selenium webdriver-manager
      - name: Start backend
        run: |
          cd backend
          python manage.py runserver &
      - name: Start frontend
        run: |
          cd frontend
          npm install
          npm run dev &
      - name: Run Selenium tests
        run: |
          cd frontend/tests
          python test_language_switching.py
```

