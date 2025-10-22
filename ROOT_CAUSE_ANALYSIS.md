# ROOT CAUSE ANALYSIS - Translation Bugs

## Investigation Date: 2025-10-22
## Recipe: Philadelphia Roll

## THE REAL PROBLEM

### 1. ENGLISH-FIRST GENERATION
**Root Cause:** The system generates recipes in ENGLISH first, then attempts to "translate" them to Russian.

**Evidence:**
- Recipe `source_type: ai_generated` 
- Created ~2 hours ago  
- Base recipe is in English (seen in the screenshot - English instructions)
- Translation layer applied afterwards

**Why This Causes Mixed Language:**
- The translation service (CookingTermsTranslationService) only translates specific cooking terms
- It does NOT translate full sentences
- Result: English verbs + Russian nouns = "Place приготовленный rice"

### 2. IMPERIAL UNITS (oz, cup) When User Wants Metric
**Root Cause:** AI generates recipes without checking user's unit preference

**Evidence:**
- User preference: kg, liter (metric)
- Recipe shows: oz, cup (imperial)
- Unit translation happens at DISPLAY time, not GENERATION time

**Why This Is Wrong:**
- Should generate "100g" not "4oz" when user prefers metric
- Translation of "oz" → "унция" is correct, but we shouldn't use oz at all!

## WHY MY "FIXES" DIDN'T WORK

### Failed Fix #1: Enhanced Translation Prompts
- Added strong "ONLY RUSSIAN" prompts to Recipe Builder
- Problem: These recipes aren't from Recipe Builder! They're from inventory generator
- The inventory generator still generates in English first

### Failed Fix #2: Unit Translation
- Created unit_utils.py to translate "as" → "шт"
- Problem: Doesn't run at generation time, only at display time
- Also doesn't address imperial vs metric issue

### Failed Fix #3: Gemini Translation in Builder
- Changed Recipe Builder to use full AI translation
- Problem: User is using INVENTORY GENERATOR, not Recipe Builder
- Wrong code path!

## THE ACTUAL FIX NEEDED

###  FIX INVENTORY GENERATOR

**Location:** `backend/apps/shopping/full_recipe_generator.py`

**Current Flow:**
1. AI generates recipe in English
2. Save to database
3. Translation service tries to translate
4. Results in mixed language

**Required Flow:**
1. Check user's preferred language
2. Generate recipe DIRECTLY in that language
3. Check user's unit preference (metric/imperial)
4. Generate with correct units from the start
5. NO translation layer needed!

**Code Changes Needed:**
```python
# In full_recipe_generator.py _build_full_recipe_prompt()

# ADD user_preferences parameter:
def _build_full_recipe_prompt(self, brief: Dict, language: str, user_preferences: Dict) -> str:
    
    # Get user's unit system
    unit_system = user_preferences.get('unit_system', 'metric')  # metric or imperial
    
    # Build language-specific prompt
    if language == 'ru':
        unit_instruction = "Используйте МЕТРИЧЕСКУЮ систему: граммы (г), килограммы (кг), миллилитры (мл), литры (л). НЕ ИСПОЛЬЗУЙТЕ унции, чашки, или другие имперские единицы."
        
        prompt = f\"\"\"Вы профессиональный шеф-повар. 
        
        КРИТИЧЕСКИ ВАЖНО:
        1. ВСЕ инструкции ТОЛЬКО на русском языке
        2. {unit_instruction}
        3. НЕТ английских слов вообще
        
        [... rest of Russian prompt ...]
        \"\"\"
```

### FIX #2: Validate Before Saving

Add validation that REJECTS recipes with mixed language:

```python
def _validate_language_purity(text: str, expected_language: str) -> bool:
    if expected_language == 'ru':
        # Check for English words (3+ Latin letters)
        import re
        english_words = re.findall(r'\\b[A-Za-z]{3,}\\b', text)
        if english_words:
            print(f"REJECTED: Found English words: {english_words}")
            return False
    return True
```

### FIX #3: Pass User Preferences to AI

**In:** `backend/apps/shopping/inventory_views.py` → `create_recipe_from_brief()`

```python
# Get user preferences
user_preferences = {
    'unit_system': 'metric' if request.user.weight_unit == 'kg' else 'imperial',
    'language': language
}

# Pass to generator
rcip_recipe = full_recipe_generator.generate_full_recipe(
    brief, 
    language,
    user_preferences=user_preferences  # NEW!
)
```

## SUMMARY

**Why bugs keep happening:**
1. Fixing wrong code (Recipe Builder instead of Inventory Generator)
2. Fixing at wrong layer (translation instead of generation)
3. Not passing user preferences to AI
4. No validation to reject bad output

**What needs to happen:**
1. Generate recipes DIRECTLY in target language
2. Use user's preferred unit system from the start
3. Validate output before saving
4. Stop trying to "translate" - just generate correctly!

## TEST PLAN

To verify fix works:
1. Set user preference to Russian + Metric
2. Generate NEW recipe from inventory
3. Check: ALL text is Russian (no English)
4. Check: ALL units are metric (g, kg, ml, l - no oz, cup)
5. If PASS: Fix works!
6. If FAIL: Log what went wrong and fix that specific issue

---

Generated: 2025-10-22
Status: DIAGNOSIS COMPLETE - READY TO IMPLEMENT REAL FIX

