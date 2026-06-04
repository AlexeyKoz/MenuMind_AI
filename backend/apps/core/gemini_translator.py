"""
Gemini Flash 2.5 - On-the-fly ingredient translator
Handles translation of ingredients that don't exist in IML database
"""
import logging
from typing import Dict, List
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class GeminiIngredientTranslator:
    """Translates ingredient names using Gemini Flash 2.5"""

    def __init__(self):
        self.gemini_client = None
        try:
            import google.generativeai as genai
            api_key = getattr(settings, 'GEMINI_API_KEY', None)
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_client = genai.GenerativeModel(
                    'gemini-2.5-flash-lite')
                logger.info("[GEMINI] Initialized Gemini Flash 2.5")
            else:
                logger.warning("[GEMINI] No API key found")
        except ImportError:
            logger.error("[GEMINI] google-generativeai not installed")
        except Exception as e:
            logger.error(f"[GEMINI] Initialization failed: {e}")

    def batch_translate_ingredients(
        self,
        ingredients: List[Dict],
        target_language: str
    ) -> List[Dict]:
        """
        Translate a batch of ingredients to target language
        Only translates ingredients with synthetic keys (not in IML)

        Args:
            ingredients: List of ingredients with 'ingredient_key' and 'name'
            target_language: Target language code (ru, he)

        Returns:
            List of ingredients with translated names
        """
        if not self.gemini_client or target_language == 'en':
            return ingredients

        # Filter synthetic ingredients (not in IML database)
        synthetic_ingredients = [
            ing for ing in ingredients
            if ing.get('ingredient_key', '').startswith('synthetic_')
        ]

        if not synthetic_ingredients:
            logger.info("[GEMINI] No synthetic ingredients to translate")
            return ingredients

        logger.info(
            f"[GEMINI] Translating {len(synthetic_ingredients)} synthetic ingredients to {target_language}")

        # Check cache first
        cache_key = self._get_cache_key(synthetic_ingredients, target_language)
        cached_translations = cache.get(cache_key)
        if cached_translations:
            logger.info("[GEMINI] Using cached translations")
            return self._merge_translations(ingredients, cached_translations)

        # Prepare ingredient list for Gemini
        ingredient_names = [ing['name'] for ing in synthetic_ingredients]

        # Translate using Gemini
        translations = self._translate_with_gemini(
            ingredient_names, target_language)

        if translations:
            # Update ingredient names
            translated_ingredients = ingredients.copy()
            synthetic_idx = 0
            for i, ing in enumerate(translated_ingredients):
                if ing.get('ingredient_key', '').startswith('synthetic_'):
                    if synthetic_idx < len(translations):
                        translated_ingredients[i] = ing.copy()
                        translated_ingredients[i]['name'] = translations[synthetic_idx]
                        logger.info(
                            f"[GEMINI] Translated: {ing['name']} → {translations[synthetic_idx]}")
                        synthetic_idx += 1

            # Cache translations
            cache.set(cache_key, translations, timeout=60*60*24)  # 24 hours

            return translated_ingredients

        logger.warning("[GEMINI] Translation failed, returning original")
        return ingredients

    def _translate_with_gemini(
        self,
        ingredient_names: List[str],
        target_language: str
    ) -> List[str]:
        """Translate ingredient names using Gemini"""
        if not self.gemini_client:
            return []

        language_names = {
            'ru': 'Russian',
            'he': 'Hebrew',
            'en': 'English'
        }

        target_lang_name = language_names.get(target_language, target_language)

        prompt = f"""Translate these ingredient names to {target_lang_name}. 
Return ONLY the translations, one per line, in the same order.
Do NOT add numbers, bullets, or explanations.

Ingredients:
{chr(10).join(f'- {name}' for name in ingredient_names)}

Translations ({target_lang_name}):"""

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
                    f"[GEMINI] Translation count mismatch: {len(translations)} != {len(ingredient_names)}")
                return []

        except Exception as e:
            logger.error(f"[GEMINI] Translation error: {e}")
            return []

    def _get_cache_key(self, ingredients: List[Dict], target_language: str) -> str:
        """Generate cache key for ingredient batch"""
        import hashlib
        ingredient_str = '|'.join(
            [ing.get('name', '') for ing in ingredients])
        hash_str = hashlib.md5(
            f"{ingredient_str}_{target_language}".encode()).hexdigest()
        return f"gemini_translate_{hash_str}"

    def _merge_translations(
        self,
        original_ingredients: List[Dict],
        translations: List[str]
    ) -> List[Dict]:
        """Merge translations back into ingredient list"""
        result = original_ingredients.copy()
        synthetic_idx = 0
        for i, ing in enumerate(result):
            if ing.get('ingredient_key', '').startswith('synthetic_'):
                if synthetic_idx < len(translations):
                    result[i] = ing.copy()
                    result[i]['name'] = translations[synthetic_idx]
                    synthetic_idx += 1
        return result
