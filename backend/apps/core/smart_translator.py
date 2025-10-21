"""
Smart Translation Service - Uses databases FIRST, Gemini as fallback
Maximizes use of IML (ingredients) and CookLingo (cooking terms) databases
"""
import logging
import re
from typing import Dict, List, Optional
from django.conf import settings
from django.core.cache import cache
from apps.core.models import IngredientCache, IngredientTranslation, CookingTermCache, CookingTermTranslation

logger = logging.getLogger(__name__)


class SmartTranslationService:
    """
    Smart translation that prioritizes database lookups over AI:
    1. Try exact match in IML/CookLingo databases
    2. Try fuzzy match in databases
    3. Check cache for previous AI translations
    4. Use Gemini only as last resort
    """

    def __init__(self):
        self.gemini_client = None
        try:
            import google.generativeai as genai
            api_key = getattr(settings, 'GEMINI_API_KEY', None)
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_client = genai.GenerativeModel(
                    'gemini-2.0-flash-exp')
                logger.info(
                    "[SMART_TRANSLATE] Initialized with Gemini Flash 2.5 fallback")
            else:
                logger.warning(
                    "[SMART_TRANSLATE] No Gemini API key - database-only mode")
        except Exception as e:
            logger.error(f"[SMART_TRANSLATE] Gemini init failed: {e}")

    def translate_ingredients_batch(
        self,
        ingredients: List[Dict],
        target_language: str
    ) -> List[Dict]:
        """
        Translate ingredients using databases first, Gemini as fallback

        Process:
        1. Check IML database for each ingredient
        2. Try fuzzy matching for close matches
        3. Check cache for previous AI translations
        4. Batch remaining unknown ingredients to Gemini
        """
        if target_language == 'en':
            return ingredients

        logger.info(
            f"[SMART_TRANSLATE] Translating {len(ingredients)} ingredients to {target_language}")

        translated_ingredients = []
        unknown_ingredients = []  # Will be sent to Gemini
        unknown_indices = []

        stats = {
            'iml_exact': 0,
            'iml_fuzzy': 0,
            'cache_hit': 0,
            'gemini_needed': 0
        }

        # Unit translation dictionary (same as in tasks.py)
        unit_translations = {
            'ru': {
                'g': 'г', 'kg': 'кг', 'mg': 'мг',
                'ml': 'мл', 'l': 'л',
                'tsp': 'ч.л.', 'tbsp': 'ст.л.', 'cup': 'чашка', 'cups': 'чашки',
                'oz': 'унция', 'lb': 'фунт',
                'pcs': 'шт', 'piece': 'шт', 'pieces': 'шт',
                'cloves': 'зубчика', 'clove': 'зубчик',
                'slice': 'ломтик', 'slices': 'ломтики',
                'pinch': 'щепотка',
                'large': 'крупный', 'medium': 'средний', 'small': 'маленький',
                'egg': 'яйцо', 'eggs': 'яйца',
                'as': '',  # Remove "as" from "as needed"
                'needed': '',  # Remove "needed"
                'taste': '',  # Remove "to taste"
                'optional': '',  # Remove "optional"
                'quantity': '',  # Remove "quantity"
                'amount': ''  # Remove "amount"
            },
            'he': {
                'g': 'גרם', 'kg': 'ק"ג', 'mg': 'מ"ג',
                'ml': 'מ"ל', 'l': 'ליטר',
                'tsp': 'כפית', 'tbsp': 'כף', 'cup': 'כוס', 'cups': 'כוסות',
                'oz': 'אונקיה', 'lb': 'ליבר',
                'pcs': 'יח', 'piece': 'יח', 'pieces': 'יח',
                'cloves': 'שיני', 'clove': 'שן',
                'slice': 'פרוסה', 'slices': 'פרוסות',
                'pinch': 'קמצוץ',
                'large': 'גדול', 'medium': 'בינוני', 'small': 'קטן',
                'egg': 'ביצה', 'eggs': 'ביצים',
                'as': '',  # Remove "as" from "as needed"
                'needed': '',
                'taste': '',
                'optional': '',
                'quantity': '',
                'amount': ''
            }
        }

        for idx, ing in enumerate(ingredients):
            translated_ing = ing.copy()
            ing_name = ing.get('name', '').strip()
            ingredient_key = ing.get('ingredient_key')

            # Translate unit if available
            if target_language in unit_translations and ing.get('unit'):
                unit = ing.get('unit').lower().strip()
                if unit in unit_translations[target_language]:
                    translated_unit = unit_translations[target_language][unit]
                    # Set the translated unit (even if empty - to remove invalid units)
                    if translated_unit == '':
                        translated_ing['unit'] = ''
                        logger.info(
                            f"   [UNIT REMOVED] Invalid unit '{ing.get('unit')}' removed from {ing_name}")
                    else:
                        translated_ing['unit'] = translated_unit
                        logger.debug(
                            f"   [UNIT] {ing.get('unit')} → {translated_unit}")
                else:
                    # Check if it's an invalid/nonsensical unit (like "servings", "ingredients", "recipes")
                    invalid_units = ['servings', 'serving', 'ingredients',
                                     'ingredient', 'recipes', 'recipe', 'items', 'item']
                    if unit in invalid_units:
                        # This is likely a parsing error - the AI extracted the wrong thing
                        # We should ideally re-extract, but for now, just translate it
                        logger.warning(
                            f"   [UNIT WARNING] Invalid unit '{unit}' detected for ingredient '{ing_name}'")
                        # Translate the invalid unit word
                        if target_language == 'ru':
                            unit_word_translations = {
                                'servings': 'порций', 'serving': 'порция',
                                'ingredients': 'ингредиентов', 'ingredient': 'ингредиент',
                                'recipes': 'рецептов', 'recipe': 'рецепт',
                                'items': 'предметов', 'item': 'предмет'
                            }
                            if unit in unit_word_translations:
                                translated_ing['unit'] = unit_word_translations[unit]

            # Skip empty names
            if not ing_name:
                translated_ingredients.append(translated_ing)
                continue

            # Strategy 1: Check if it's a real IML key (not synthetic)
            if ingredient_key and not ingredient_key.startswith('synthetic_'):
                try:
                    ingredient_obj = IngredientCache.objects.get(
                        ingredient_key=ingredient_key)
                    translation = ingredient_obj.translations.filter(
                        language=target_language).first()
                    if translation:
                        translated_ing['name'] = translation.name
                        stats['iml_exact'] += 1
                        logger.debug(
                            f"   [IML EXACT] {ing_name} → {translation.name}")
                        translated_ingredients.append(translated_ing)
                        continue
                except IngredientCache.DoesNotExist:
                    pass

            # Strategy 2: Try fuzzy match in IML by name (for synthetic keys)
            if ingredient_key and ingredient_key.startswith('synthetic_'):
                fuzzy_result = self._fuzzy_match_ingredient(
                    ing_name, target_language)
                if fuzzy_result:
                    translated_ing['name'] = fuzzy_result
                    stats['iml_fuzzy'] += 1
                    logger.debug(f"   [IML FUZZY] {ing_name} → {fuzzy_result}")
                    translated_ingredients.append(translated_ing)
                    continue

            # Strategy 3: Check cache for previous AI translation
            cache_key = f"ingredient_translate_{ing_name.lower()}_{target_language}"
            cached_translation = cache.get(cache_key)
            if cached_translation:
                translated_ing['name'] = cached_translation
                stats['cache_hit'] += 1
                logger.debug(f"   [CACHE] {ing_name} → {cached_translation}")
                translated_ingredients.append(translated_ing)
                continue

            # Strategy 4: Add to unknown list for Gemini batch translation
            unknown_ingredients.append(ing_name)
            unknown_indices.append(idx)
            translated_ingredients.append(translated_ing)  # Placeholder

        # Batch translate unknowns with Gemini (if any)
        if unknown_ingredients:
            stats['gemini_needed'] = len(unknown_ingredients)
            logger.info(
                f"[SMART_TRANSLATE] Need Gemini for {len(unknown_ingredients)} ingredients")

            gemini_translations = self._translate_with_gemini(
                unknown_ingredients, target_language)

            if gemini_translations:
                for i, translated_name in enumerate(gemini_translations):
                    idx = unknown_indices[i]
                    translated_ingredients[idx]['name'] = translated_name

                    # Cache for future use
                    orig_name = unknown_ingredients[i]
                    cache_key = f"ingredient_translate_{orig_name.lower()}_{target_language}"
                    cache.set(cache_key, translated_name,
                              timeout=60*60*24*30)  # 30 days

                    logger.debug(
                        f"   [GEMINI] {orig_name} → {translated_name}")

        # Log statistics
        logger.info(f"[SMART_TRANSLATE] Translation stats:")
        logger.info(f"   IML exact matches: {stats['iml_exact']}")
        logger.info(f"   IML fuzzy matches: {stats['iml_fuzzy']}")
        logger.info(f"   Cache hits: {stats['cache_hit']}")
        logger.info(f"   Gemini calls: {stats['gemini_needed']}")

        # Calculate savings percentage (avoid division by zero)
        if len(ingredients) > 0:
            savings_pct = ((stats['iml_exact'] + stats['iml_fuzzy'] +
                           stats['cache_hit']) / len(ingredients) * 100)
            logger.info(f"   Savings: {savings_pct:.1f}% from databases/cache")
        else:
            logger.info(f"   Savings: N/A (no ingredients to translate)")

        return translated_ingredients

    def _fuzzy_match_ingredient(self, name: str, target_language: str, threshold: float = 0.75) -> Optional[str]:
        """Try to fuzzy match ingredient name in IML database"""
        from difflib import SequenceMatcher

        name_lower = name.lower()
        name_normalized = re.sub(r'[^a-z0-9\s]', '', name_lower)

        # Get candidates from database (limit for performance)
        candidates = IngredientTranslation.objects.filter(
            language='en'
        ).select_related('ingredient')[:500]

        best_match = None
        best_score = threshold

        for candidate in candidates:
            candidate_name = candidate.name.lower()
            candidate_normalized = re.sub(r'[^a-z0-9\s]', '', candidate_name)

            # Calculate similarity
            score = SequenceMatcher(
                None, name_normalized, candidate_normalized).ratio()

            if score > best_score:
                # Found a good match, get translation
                translation = candidate.ingredient.translations.filter(
                    language=target_language
                ).first()

                if translation:
                    best_match = translation.name
                    best_score = score

        return best_match

    def _translate_with_gemini(
        self,
        ingredient_names: List[str],
        target_language: str
    ) -> List[str]:
        """Translate ingredient names using Gemini (last resort)"""
        if not self.gemini_client:
            logger.warning(
                "[SMART_TRANSLATE] No Gemini client, returning originals")
            return ingredient_names

        language_names = {
            'ru': 'Russian',
            'he': 'Hebrew',
            'en': 'English'
        }

        target_lang_name = language_names.get(target_language, target_language)

        prompt = f"""Translate these cooking ingredient names to {target_lang_name}.
Return ONLY the translations, one per line, in the exact same order.
Do NOT add numbers, bullets, explanations, or extra text.

Ingredients:
{chr(10).join(f'- {name}' for name in ingredient_names)}

Translations in {target_lang_name}:"""

        try:
            response = self.gemini_client.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 500,
                }
            )

            # Parse response
            translations = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                # Remove bullets, numbers, dashes
                line = line.lstrip('- •*0123456789. ')
                if line:
                    translations.append(line)

            if len(translations) == len(ingredient_names):
                logger.info(
                    f"[GEMINI] Successfully translated {len(translations)} ingredients")
                return translations
            else:
                logger.warning(
                    f"[GEMINI] Count mismatch: {len(translations)} != {len(ingredient_names)}")
                return ingredient_names  # Return originals if mismatch

        except Exception as e:
            logger.error(f"[GEMINI] Translation error: {e}")
            return ingredient_names  # Return originals on error

    def translate_cooking_steps_batch(
        self,
        steps: List[Dict],
        target_language: str,
        cooking_terms_service=None
    ) -> List[Dict]:
        """
        Translate cooking steps using Gemini with CookLingo as glossary

        Process:
        1. Extract all step texts
        2. Build a glossary of cooking terms from CookLingo database
        3. Send to Gemini for full translation with glossary context
        4. Return translated steps
        """
        if target_language == 'en':
            return steps

        logger.info(
            f"[SMART_TRANSLATE] Translating {len(steps)} cooking steps to {target_language}")

        # Extract step texts and their field names
        step_texts = []
        # Track which field has the text ('instruction' or 'text')
        step_fields = []

        for step in steps:
            step_text = step.get('instruction') or step.get('text')
            if step_text:
                step_texts.append(step_text)
                # Remember which field we got the text from
                if 'instruction' in step:
                    step_fields.append('instruction')
                else:
                    step_fields.append('text')
            else:
                step_texts.append('')
                step_fields.append('text')  # Default

        if not step_texts or all(not t for t in step_texts):
            logger.warning("[SMART_TRANSLATE] No step texts to translate")
            return steps

        # Build cooking terms glossary from CookLingo
        glossary = self._build_cooking_glossary(step_texts, target_language)

        # Translate with Gemini
        translated_texts = self._translate_steps_with_gemini(
            step_texts, target_language, glossary)

        # Update steps with translations
        translated_steps = []
        for idx, step in enumerate(steps):
            translated_step = step.copy()
            if idx < len(translated_texts) and translated_texts[idx]:
                field_name = step_fields[idx]
                translated_step[field_name] = translated_texts[idx]

                # Update both fields to ensure compatibility
                if field_name == 'instruction' and 'text' in translated_step:
                    translated_step['text'] = translated_texts[idx]
                elif field_name == 'text' and 'instruction' in translated_step:
                    translated_step['instruction'] = translated_texts[idx]

            translated_steps.append(translated_step)

        return translated_steps

    def _build_cooking_glossary(self, step_texts: List[str], target_language: str) -> Dict[str, str]:
        """Build a glossary of cooking terms found in the steps"""
        glossary = {}

        # Get all cooking terms from database
        all_text = ' '.join(step_texts).lower()

        # Query CookLingo for terms that appear in the text
        from apps.core.models import CookingTermCache

        cooking_terms = CookingTermCache.objects.prefetch_related(
            'translations').all()

        terms_found = 0
        terms_translated = 0

        for term_obj in cooking_terms:
            english_term = term_obj.term_english.lower()

            # Check if term appears in any step (whole word match)
            pattern = r'\b' + re.escape(english_term) + r'\b'
            if re.search(pattern, all_text, re.IGNORECASE):
                terms_found += 1
                # Get translation
                translation = term_obj.translations.filter(
                    language_code=target_language
                ).first()

                if translation:
                    glossary[term_obj.term_english] = translation.translation
                    terms_translated += 1
                    if terms_translated <= 5:  # Log first 5 terms
                        logger.debug(
                            f"   [GLOSSARY] {term_obj.term_english} → {translation.translation}")

        logger.info(
            f"[SMART_TRANSLATE] Built glossary with {len(glossary)} cooking terms (found {terms_found} terms, {terms_translated} had translations)")

        # FALLBACK STRATEGY: If no terms were translated, warn but continue
        # Gemini will translate without glossary (still high quality)
        if terms_translated == 0:
            logger.warning(
                f"[SMART_TRANSLATE] ⚠️ No cooking term translations found in database for {target_language}")
            logger.warning(
                f"[SMART_TRANSLATE] 🔄 FALLBACK: Will use Gemini for full translation without glossary")

        return glossary

    def _translate_steps_with_gemini(
        self,
        step_texts: List[str],
        target_language: str,
        glossary: Dict[str, str]
    ) -> List[str]:
        """Translate cooking steps using Gemini with glossary context"""
        if not self.gemini_client:
            logger.warning(
                "[SMART_TRANSLATE] No Gemini client, returning originals")
            return step_texts

        language_names = {
            'ru': 'Russian',
            'he': 'Hebrew',
            'en': 'English'
        }

        target_lang_name = language_names.get(target_language, target_language)

        # Build glossary section for prompt
        glossary_text = ""
        if glossary:
            glossary_items = [f"{en} = {translated}" for en,
                              translated in glossary.items()]
            glossary_text = f"""
COOKING TERMS GLOSSARY (use these exact translations when possible):
{chr(10).join(glossary_items)}
"""
            logger.info(f"[GEMINI] Using glossary with {len(glossary)} terms")
        else:
            logger.info(f"[GEMINI] No glossary - translating directly")

        # Build prompt with numbered steps
        steps_text = '\n'.join(f"{i+1}. {text}" for i,
                               text in enumerate(step_texts) if text)

        prompt = f"""You are a professional cooking translator. Translate these cooking instructions to {target_lang_name}.

IMPORTANT RULES:
- Translate EVERY step completely and accurately
- Return ONLY the translations, numbered 1., 2., 3., etc.
- Do NOT skip any steps
- Do NOT add explanations, commentary, or extra text
- Maintain the same order as the original
- Keep cooking measurements and times as-is
{glossary_text}
Instructions to translate:
{steps_text}

Translations in {target_lang_name}:"""

        try:
            response = self.gemini_client.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 3000,
                }
            )

            # Parse response
            translations = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                # Remove step numbers (1., 2., etc.)
                line = re.sub(r'^\d+\.\s*', '', line)
                if line:
                    translations.append(line)

            expected_count = len([t for t in step_texts if t])

            if len(translations) == expected_count:
                logger.info(
                    f"[GEMINI] ✅ Successfully translated {len(translations)} cooking steps to {target_lang_name}")

                # QUALITY CHECK: Verify translations are not in English
                # Check first translated step for target language characters
                if translations and target_language != 'en':
                    first_trans = translations[0].lower()

                    # Check for target language characters
                    if target_language == 'ru':
                        has_target_chars = any(
                            '\u0400' <= char <= '\u04FF' for char in first_trans)
                    elif target_language == 'he':
                        has_target_chars = any(
                            '\u0590' <= char <= '\u05FF' for char in first_trans)
                    else:
                        has_target_chars = True  # Skip check for other languages

                    if not has_target_chars:
                        # Check if it's mostly English
                        is_english = sum(1 for c in first_trans if 'a' <= c <= 'z') > len(
                            first_trans) * 0.5
                        if is_english:
                            logger.warning(
                                f"[GEMINI] ⚠️ Translation appears to be in English, not {target_lang_name}")
                            logger.warning(
                                f"[GEMINI] First step: {translations[0][:100]}")
                            logger.warning(
                                f"[GEMINI] 🔄 This may indicate Gemini fallback or translation issue")
                    else:
                        logger.info(
                            f"[GEMINI] ✅ Quality check passed - contains {target_lang_name} characters")

                return translations
            else:
                logger.error(
                    f"[GEMINI] ❌ Step count mismatch: got {len(translations)} translations but expected {expected_count}")
                logger.error(
                    f"[GEMINI] Returning original English steps as fallback")
                return step_texts

        except Exception as e:
            logger.error(f"[GEMINI] ❌ Translation error: {e}")
            import traceback
            traceback.print_exc()
            logger.error(
                f"[GEMINI] Returning original English steps as fallback")
            return step_texts  # Return originals on error

    def translate_recipe_name(self, name: str, target_language: str) -> str:
        """
        Translate recipe name to target language using Gemini

        Args:
            name: Recipe name (in any language)
            target_language: Target language code (en, ru, he)

        Returns:
            Translated recipe name
        """
        if not self.gemini_client:
            logger.warning(
                "[SMART_TRANSLATE] No Gemini client for name translation")
            return name

        language_names = {
            'ru': 'Russian',
            'he': 'Hebrew',
            'en': 'English'
        }

        target_lang_name = language_names.get(target_language, target_language)

        prompt = f"""Translate this recipe name to {target_lang_name}.
Return ONLY the translated name, nothing else.

Recipe name: {name}

Translation in {target_lang_name}:"""

        try:
            response = self.gemini_client.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 50,
                }
            )

            translated = response.text.strip()

            # Remove any quotes or extra formatting
            translated = translated.strip('"\'')

            if translated and len(translated) > 0:
                logger.info(
                    f"[SMART_TRANSLATE] Translated recipe name: {name} -> {translated}")
                return translated
            else:
                logger.warning(
                    f"[SMART_TRANSLATE] Empty translation for name: {name}")
                return name

        except Exception as e:
            logger.error(f"[SMART_TRANSLATE] Failed to translate name: {e}")
            return name
