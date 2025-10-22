# TRANSLATION BUG - ROOT CAUSE INVESTIGATION

## Problems (Occurring Repeatedly)
1. **Russian instructions contain English words** - "Place cooked рис", "Mix полностью", "Add 1 cup of рис"
2. **Units show imperial (oz, унция) when user preference is metric (kg, liter)**

## Investigation Steps

### Step 1: Check Recipe Source
- Where was this recipe generated?
- When was it generated?
- Which AI model was used?
- Was it from inventory generator or recipe builder?

### Step 2: Check Translation Flow
- Is translation happening at generation time or retrieval time?
- Are translations being cached?
- Is the AI generating in Russian or English first, then translating?

### Step 3: Check Unit System
- Where is user's unit preference being read?
- Is it being passed to the AI during generation?
- Are units being converted or just translated?

## Hypothesis

### Hypothesis 1: AI Generates in English, Translation Fails
**Theory:** The AI generates recipes in English first, then attempts to translate. The translation service only translates cooking terms, not full sentences, leaving English words mixed in.

**Evidence:**
- Instructions show pattern: "English verb + Russian noun" (Place рис, Mix полностью)
- This is exactly what happens when word-by-word translation fails

**If True:** Need to generate recipes directly in target language, not translate after

### Hypothesis 2: Cached Old Recipes
**Theory:** These recipes were generated before fixes were applied, and are being served from cache.

**Evidence:**
- Same recipe showing same issues despite multiple "fixes"

**If True:** Need to invalidate cache and regenerate

### Hypothesis 3: Wrong Translation Service Being Used
**Theory:** Multiple translation systems exist (CookingTermsTranslationService, SmartTranslationService, Gemini direct). The wrong one is being used at the wrong time.

**Evidence:**
- CookingTermsTranslationService only translates specific cooking terms
- This would leave non-cooking-term English words untranslated

**If True:** Need to use full AI translation (Gemini/Groq) for ALL text, not just cooking terms

### Hypothesis 4: Units Not Respecting User Preferences
**Theory:** AI generation doesn't check user's unit preference (metric vs imperial) before generating recipe.

**Evidence:**
- Recipe shows "oz" when user prefers "kg"
- AI was probably given prompts without user preference context

**If True:** Need to pass user's unit preference to AI at generation time

## Next Actions
1. Add comprehensive logging to trace recipe generation flow
2. Check database to see when this recipe was created
3. Verify which translation service is actually being called
4. Check if user preferences are being passed to AI
5. Create test that PROVES the fix works before claiming it's fixed

## REAL FIX CHECKLIST
- [ ] Log every step of recipe generation
- [ ] Pass user unit preference to AI
- [ ] Generate recipes DIRECTLY in target language (not translate after)
- [ ] Verify translation quality before saving
- [ ] Add validation that rejects mixed-language output
- [ ] Test with NEW recipe generation (not old cached recipes)

