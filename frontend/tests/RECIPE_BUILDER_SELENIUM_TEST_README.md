# Recipe Builder Manual Creation - Selenium Test

## 🎯 Purpose
Test the Recipe Builder manual recipe creation flow with duplicate detection functionality.

## 🧪 Tests Included

### 1. `test_manual_recipe_creation_unique_name`
- Creates a recipe with a unique name
- Verifies all 5 steps complete successfully
- Checks that NO duplicate modal appears

### 2. `test_manual_recipe_creation_duplicate_detection`
- Attempts to create a recipe with an existing name
- Verifies duplicate modal appears in Step 1
- Tests "Create Personal Fork" option
- Verifies progression to Step 2 after selection

### 3. `test_manual_recipe_creation_duplicate_fuzzy_match`
- Tests AI/fuzzy duplicate detection
- Tries variations like "Pasta Carbonara" vs "Spaghetti Carbonara"
- Verifies semantic similarity detection

## 📋 Prerequisites

1. **Install Selenium:**
```bash
pip install selenium pytest
```

2. **Install Chrome WebDriver:**
```bash
# Windows (using chocolatey)
choco install chromedriver

# Or download from: https://chromedriver.chromium.org/
```

3. **Backend Running:**
```bash
cd backend
python manage.py runserver
```

4. **Frontend Running:**
```bash
cd frontend
npm start
```

5. **Test User:**
- Username: `testuser`
- Password: `testpassword`

Create test user if needed:
```bash
cd backend
python manage.py createsuperuser
```

## 🚀 Run Tests

### Run All Tests:
```bash
cd frontend/tests
pytest test_recipe_builder_manual_creation.py -v -s
```

### Run Specific Test:
```bash
# Test unique recipe creation
pytest test_recipe_builder_manual_creation.py::TestRecipeBuilderManualCreation::test_manual_recipe_creation_unique_name -v -s

# Test duplicate detection
pytest test_recipe_builder_manual_creation.py::TestRecipeBuilderManualCreation::test_manual_recipe_creation_duplicate_detection -v -s

# Test fuzzy matching
pytest test_recipe_builder_manual_creation.py::TestRecipeBuilderManualCreation::test_manual_recipe_creation_duplicate_fuzzy_match -v -s
```

## 📊 Expected Output

### Successful Test:
```
🧪 TEST: Manual Recipe Creation - Unique Name
✅ Logged in as testuser
✅ Opened Recipe Builder

📝 Step 1: Basic Info
   ✅ Entered recipe name: Test Recipe 1734567890
   ✅ Entered cuisine: Italian
   ✅ Selected difficulty: Beginner
   ✅ Clicked Next
   ✅ No duplicate detected (as expected)

🥕 Step 2: Ingredients
   ✅ Added ingredient 1: flour
   ✅ Added ingredient 2: eggs
   ✅ Added ingredient 3: milk
   ✅ Clicked Next

👨‍🍳 Step 3: Cooking Steps
   ✅ Entered cooking steps
   ✅ Clicked Next

👀 Step 4: Review & Edit
   ✅ Recipe data displayed for review
   ✅ Clicked Confirm & Continue

🎉 Step 5: Finalize
   ✅ Clicked Create Recipe
   ✅ Recipe created successfully!

✅ TEST PASSED: Unique recipe created successfully
```

### Duplicate Detection Test:
```
🧪 TEST: Manual Recipe Creation - Duplicate Detection
✅ Logged in as testuser
   📌 Found existing recipe: 'Spaghetti Carbonara'
✅ Opened Recipe Builder

📝 Step 1: Enter duplicate recipe name
   ✅ Entered existing recipe name: Spaghetti Carbonara
   ✅ Clicked Next

⚠️  Verifying duplicate detection...
   ✅ Duplicate modal appeared!
   ✅ All 3 options present:
      1. View Existing Recipe
      2. Create Personal Fork
      3. Create New Public Version
   ✅ Clicked 'Create Personal Fork'
   ✅ Proceeded to Step 2 after fork selection

✅ TEST PASSED: Duplicate detection working correctly!
```

## 🐛 Troubleshooting

### Test Fails with "No such element"
- Check if frontend is running on `http://localhost:3000`
- Check if backend is running on `http://localhost:8000`
- Verify test user exists and credentials are correct

### Duplicate Modal Not Appearing
- Check backend logs for duplicate detection
- Verify at least one recipe exists in Discovery page
- Check console for error messages

### Test Hangs
- Increase wait times in test
- Check browser console for JavaScript errors
- Verify WebDriver version matches Chrome version

## 📝 Notes

- Tests use Chrome browser by default
- Browser window stays open on failure for debugging
- All tests are independent and can run in any order
- Tests create unique recipe names using timestamps

## 🔧 Customize

Edit the test file to customize:
- Login credentials (line 22-23)
- Frontend URL (line 27)
- Wait times (various `time.sleep()` calls)
- Test data (ingredients, steps, etc.)

