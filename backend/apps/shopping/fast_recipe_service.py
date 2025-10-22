"""
Fast Recipe Ingredient Extraction Service
For shopping lists - extracts ingredients quickly without full recipe processing
"""

import asyncio
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from asgiref.sync import sync_to_async
from groq import Groq
import os

from apps.core.ingredient_mapper import IngredientMapper
from apps.core.google_translate_service import get_google_translate_service
from rcip_converter import RecipeAnalyzer

logger = logging.getLogger(__name__)


class FastRecipeIngredientService:
    """
    Quick ingredient extraction for shopping lists

    PHASE 1 (FAST - 5-10 seconds):
    - Extract ingredients only (skip steps)
    - Map to IML database
    - Translate to user's language only
    - Return immediately for shopping list

    PHASE 2 (Background via Celery):
    - Full recipe extraction (steps, times, etc)
    - Translate to remaining languages
    - Create canonical recipe
    """

    def __init__(self):
        groq_api_key = os.getenv('GROQ_API_KEY') or getattr(
            settings, 'GROQ_API_KEY', None)
        if not groq_api_key:
            logger.warning(
                "[FAST RECIPE] GROQ_API_KEY not found. Will use fallback.")
            self.groq_client = None
        else:
            self.groq_client = Groq(api_key=groq_api_key)

        self.ingredient_mapper = IngredientMapper()
        self.google_translate = get_google_translate_service()
        self.recipe_analyzer = RecipeAnalyzer()
        self.model = "llama-3.1-8b-instant"  # Fast, lightweight model

    async def extract_ingredients_fast(
        self,
        scraped_data: Dict,
        recipe_name: str,
        user_language: str = 'en',
        user_unit_system: str = 'metric'
    ) -> Dict:
        """
        FAST PATH: Extract ONLY ingredients from scraped recipe

        Args:
            scraped_data: {'url': str, 'text': str} from Firecrawl
            recipe_name: Recipe name from search query
            user_language: User's preferred language (en, ru, he)
            user_unit_system: User's unit preference (metric, imperial)

        Returns:
            {
                'recipe_name': str,  # Cleaned name
                'recipe_name_translated': str,  # In user's language
                'ingredients': List[Dict],  # With IML mapping + user language
                'source_url': str,
                'recipe_hash': str,  # For deduplication
                'scraped_data': Dict  # Pass through for Phase 2
            }
        """
        logger.info(
            f"[FAST RECIPE] Starting fast extraction for: {recipe_name}")
        logger.info(
            f"[FAST RECIPE] User language: {user_language}, Unit system: {user_unit_system}")

        try:
            # STEP 1: AI Extract ingredients ONLY (English)
            ingredients_en = await self._extract_ingredients_with_ai(
                scraped_data['content'],
                recipe_name
            )

            if not ingredients_en:
                logger.error("[FAST RECIPE] No ingredients extracted")
                return None

            logger.info(
                f"[FAST RECIPE] ✅ Extracted {len(ingredients_en)} ingredients in English")

            # STEP 2: Map to IML database (get ingredient_keys)
            mapped_ingredients = await self._map_ingredients_to_iml(
                ingredients_en,
                user_unit_system
            )

            logger.info(
                f"[FAST RECIPE] ✅ Mapped {len(mapped_ingredients)} ingredients to IML")

            # STEP 3: Translate to USER LANGUAGE (if not English)
            if user_language != 'en':
                mapped_ingredients = await self._translate_ingredients_to_user_language(
                    mapped_ingredients,
                    user_language
                )
                logger.info(
                    f"[FAST RECIPE] ✅ Translated ingredients to {user_language}")

            # STEP 4: Translate recipe name to user language
            recipe_name_translated = recipe_name
            if user_language != 'en':
                recipe_name_translated = self.google_translate.translate_text(
                    recipe_name,
                    target_language=user_language,
                    source_language='en'
                ) or recipe_name
                logger.info(
                    f"[FAST RECIPE] ✅ Translated name: {recipe_name} → {recipe_name_translated}")

            # STEP 5: Calculate hash for deduplication
            recipe_hash = self._calculate_recipe_hash(
                recipe_name, ingredients_en)

            result = {
                'recipe_name': recipe_name,  # English
                'recipe_name_translated': recipe_name_translated,  # User language
                'ingredients': mapped_ingredients,  # With IML + user language
                'source_url': scraped_data['url'],
                'recipe_hash': recipe_hash,
                'scraped_data': scraped_data  # For Phase 2 background processing
            }

            logger.info(
                f"[FAST RECIPE] ✅ Fast extraction complete in user language: {user_language}")
            return result

        except Exception as e:
            logger.error(f"[FAST RECIPE] ❌ Fast extraction failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def _extract_ingredients_with_ai(
        self,
        scraped_text: str,
        recipe_name: str
    ) -> List[Dict]:
        """
        Use AI to extract ONLY ingredients (skip steps for speed)
        """
        if not self.groq_client:
            logger.warning("[FAST RECIPE] Groq not available, using fallback")
            return self._fallback_ingredient_extraction(scraped_text)

        # Truncate text to avoid token limits (focus on beginning where ingredients usually are)
        max_chars = 8000
        if len(scraped_text) > max_chars:
            scraped_text = scraped_text[:max_chars] + "..."
            logger.info(f"[FAST RECIPE] Truncated text to {max_chars} chars")

        prompt = f"""Extract ONLY the ingredients from this recipe: "{recipe_name}"

Recipe content:
{scraped_text}

IMPORTANT:
- Extract ONLY ingredients (DO NOT extract cooking steps)
- Return in this EXACT format (one per line):
- [quantity] [unit] [ingredient name]
- Examples: "2 cups flour", "500 g chicken breast", "1 tsp salt"
- If no quantity, just write ingredient name
- Output ONLY ingredients list (no explanations, no steps)

INGREDIENTS:"""

        try:
            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a fast recipe ingredient extractor. Extract ONLY ingredients, ignore cooking steps."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1500  # Short output for speed
            )

            ingredients_text = response.choices[0].message.content.strip()
            logger.info(
                f"[FAST RECIPE] AI extracted {len(ingredients_text.split(chr(10)))} ingredient lines")

            # Parse ingredient lines
            ingredients = []
            for line in ingredients_text.split('\n'):
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('INGREDIENTS'):
                    continue

                # Remove leading dashes/bullets
                line = line.lstrip('- •*')

                if len(line) > 3:  # Reasonable ingredient text
                    ingredients.append({
                        'original': line,
                        'name': line  # Will be parsed by IML mapper
                    })

            logger.info(f"[FAST RECIPE] Parsed {len(ingredients)} ingredients")
            return ingredients

        except Exception as e:
            logger.error(f"[FAST RECIPE] AI extraction failed: {e}")
            return self._fallback_ingredient_extraction(scraped_text)

    def _fallback_ingredient_extraction(self, scraped_text: str) -> List[Dict]:
        """
        Fallback: Basic regex-based ingredient extraction
        """
        logger.info("[FAST RECIPE] Using fallback extraction")

        # Look for common ingredient section markers
        import re

        # Find ingredient section
        patterns = [
            r'ingredients?:?\s*(.*?)(?:instructions?|directions?|method|steps?|preparation)',
            r'ingredients?:?\s*(.*?)(?:\n\n|\Z)',
        ]

        for pattern in patterns:
            match = re.search(pattern, scraped_text, re.IGNORECASE | re.DOTALL)
            if match:
                ingredient_text = match.group(1)
                lines = [line.strip()
                         for line in ingredient_text.split('\n') if line.strip()]

                ingredients = []
                for line in lines[:20]:  # Limit to first 20 lines
                    # Skip very short lines or section headers
                    if len(line) < 5 or line.endswith(':'):
                        continue

                    ingredients.append({
                        'original': line,
                        'name': line
                    })

                if ingredients:
                    logger.info(
                        f"[FAST RECIPE] Fallback found {len(ingredients)} ingredients")
                    return ingredients

        logger.warning("[FAST RECIPE] Fallback found no ingredients")
        return []

    async def _map_ingredients_to_iml(
        self,
        ingredients: List[Dict],
        user_unit_system: str
    ) -> List[Dict]:
        """
        Map ingredients to IML database for ingredient_keys and unit conversion
        """
        mapped = []

        for idx, ing in enumerate(ingredients):
            ingredient_text = ing.get('name', ing.get('original', ''))

            # Map to IML (sync_to_async for Django ORM)
            match_result = await sync_to_async(self.ingredient_mapper.map)(
                text=ingredient_text,
                language='en',  # Always map from English first
                user_unit_system=user_unit_system
            )

            mapped_ing = {
                'name': ingredient_text,
                'name_translated': ingredient_text,  # Will be translated in next step
                'quantity': match_result.quantity,
                'unit': match_result.unit,
                'ingredient_key': match_result.ingredient_key,
                'unit_type': match_result.unit_type,
                'match_confidence': match_result.confidence,
                'display_name': match_result.display_name,
                'original': ing.get('original', ingredient_text)
            }

            if match_result.ingredient_key:
                logger.info(
                    f"[FAST RECIPE] {idx+1}. Mapped: {ingredient_text} → {match_result.ingredient_key} ({match_result.confidence:.2f})")
            else:
                logger.warning(
                    f"[FAST RECIPE] {idx+1}. No match: {ingredient_text}")

            mapped.append(mapped_ing)

        return mapped

    async def _translate_ingredients_to_user_language(
        self,
        ingredients: List[Dict],
        target_language: str
    ) -> List[Dict]:
        """
        Translate ingredient names to user's language using Google Translate
        FAST: Only translate to ONE language (user's language)
        """
        logger.info(
            f"[FAST RECIPE] Translating {len(ingredients)} ingredients to {target_language}")

        # Batch translate all ingredient names
        ingredient_names = [ing['name'] for ing in ingredients]

        translated_names = self.google_translate.translate_batch(
            ingredient_names,
            target_language=target_language,
            source_language='en'
        )

        if translated_names and len(translated_names) == len(ingredients):
            for ing, translated in zip(ingredients, translated_names):
                ing['name_translated'] = translated
                logger.info(f"[FAST RECIPE] {ing['name']} → {translated}")
        else:
            logger.warning(
                f"[FAST RECIPE] Translation failed, keeping English names")

        return ingredients

    def _calculate_recipe_hash(self, name: str, ingredients: List[Dict]) -> str:
        """
        Calculate hash for deduplication
        Same logic as RecipeAgentService
        """
        # Normalize name
        normalized_name = ' '.join(name.lower().split())

        # Sort ingredients
        sorted_ingredients = sorted([
            ing.get('name', '').lower() for ing in ingredients
        ])

        hash_string = f"{normalized_name}:{','.join(sorted_ingredients)}"
        return hashlib.sha256(hash_string.encode()).hexdigest()
