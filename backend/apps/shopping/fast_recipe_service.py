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
from apps.shopping.multilang_translator import get_multilang_translator
from rcip_converter import RecipeAnalyzer

logger = logging.getLogger(__name__)


class FastRecipeIngredientService:
    """
    Quick ingredient extraction for shopping lists

    PHASE 1 (FAST - 5-10 seconds):
    - Extract ingredients only (skip steps)
    - Map to IML database
    - Translate to ALL languages (smart multilang system)
    - Return immediately for shopping list

    PHASE 2 (Background via Celery):
    - Full recipe extraction (steps, times, etc)
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
        self.multilang_translator = get_multilang_translator()  # NEW!
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

            # STEP 3: Translate to ALL LANGUAGES (Smart Multilang System)
            # This replaces the old single-language translation
            import time
            start_time = time.time()

            logger.info(
                "[FAST RECIPE] 🚀 Starting smart multilang translation...")
            translated_ingredients = await sync_to_async(
                self.multilang_translator.translate_ingredients_batch
            )(mapped_ingredients, source_language='en')

            translation_time = time.time() - start_time
            logger.info(
                f"[FAST RECIPE] ✅ Smart translation complete in {translation_time:.2f}s")

            # Calculate translation stats
            iml_hits = sum(
                1 for ing in translated_ingredients
                if ing.get('_translation_source') == 'iml'
            )
            google_hits = sum(
                1 for ing in translated_ingredients
                if ing.get('_translation_source') == 'google'
            )
            ai_hits = len(translated_ingredients) - iml_hits - google_hits

            logger.info(
                f"[FAST RECIPE] 📊 Translation sources: "
                f"IML={iml_hits} (instant), Google={google_hits} (fast), AI={ai_hits} (fallback)"
            )

            # STEP 4: Translate recipe name to ALL languages
            recipe_name_translations = {'en': recipe_name}

            for lang in ['ru', 'he']:
                try:
                    translated = self.google_translate.translate_text(
                        recipe_name,
                        target_language=lang,
                        source_language='en'
                    ) or recipe_name
                    recipe_name_translations[lang] = translated
                    logger.info(
                        f"[FAST RECIPE] Recipe name → [{lang}] {translated}")
                except Exception as e:
                    logger.warning(
                        f"[FAST RECIPE] Recipe name translation to {lang} failed: {e}")
                    recipe_name_translations[lang] = recipe_name

            # STEP 5: Calculate hash for deduplication
            recipe_hash = self._calculate_recipe_hash(
                recipe_name, ingredients_en)

            result = {
                'recipe_name': recipe_name,  # English (base)
                'recipe_name_translations': recipe_name_translations,  # All languages
                # With name_translations for all languages
                'ingredients': translated_ingredients,
                'source_url': scraped_data['url'],
                'recipe_hash': recipe_hash,
                'scraped_data': scraped_data  # For Phase 2 background processing
            }

            logger.info(
                f"[FAST RECIPE] ✅ Fast extraction complete with ALL language support")
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

        # VALIDATION: Check if this is actually a recipe page
        if not self._is_recipe_content(scraped_text, recipe_name):
            logger.warning(
                f"[FAST RECIPE] ❌ Content does not appear to be a recipe for '{recipe_name}'")
            return []

        # Focus on the INGREDIENTS SECTION only. Scraped pages (especially markdown from
        # Firecrawl) contain navigation menus, related-recipe links and comment sections
        # that the model otherwise extracts as fake "ingredients" (author names, links, etc.).
        # First drop everything from the comments/related section onward.
        scraped_text = self._strip_after_comments(scraped_text)
        focused_text = self._extract_ingredients_section(scraped_text)
        if focused_text:
            logger.info(
                f"[FAST RECIPE] Focused on ingredients section ({len(focused_text)} chars)")
            scraped_text = focused_text

        # Truncate text to avoid token limits (focus on beginning where ingredients usually are)
        max_chars = 8000
        if len(scraped_text) > max_chars:
            scraped_text = scraped_text[:max_chars] + "..."
            logger.info(f"[FAST RECIPE] Truncated text to {max_chars} chars")

        prompt = f"""Extract ONLY the ingredients from this recipe: "{recipe_name}"

Recipe content:
{scraped_text}

IMPORTANT RULES:
1. Extract ONLY food ingredients (DO NOT extract tools, equipment, steps, or non-food items)
2. Return in this EXACT format (one per line):
   - [quantity] [unit] [ingredient name]
   - Examples: "2 cups flour", "500 g chicken breast", "1 tsp salt"
3. If no quantity, just write ingredient name
4. Output ONLY ingredients list (no explanations, no steps)
5. Maximum 30 ingredients (this is a safety limit)
6. DO NOT include: pens, papers, computers, blogs, schools, restaurants, etc.
7. NEVER include recipe metadata such as: Prep Time, Cook Time, Total Time, "X mins"/"X minutes"/"X hours", Servings, Serves, Yield, Makes, Calories, Nutrition, Course, Cuisine, Difficulty, Author, Rating, Reviews
8. ONLY include: actual food items, spices, liquids used in cooking
9. List each distinct ingredient ONLY ONCE (no duplicates)
10. If the recipe lists ALTERNATIVES or SUBSTITUTES (e.g. "00 flour or all-purpose flour", "butter or margarine"), pick ONLY the FIRST/primary option
11. Do NOT list multiple varieties of the same base ingredient (e.g. several different flours) unless the recipe genuinely uses each in its OWN separate measured quantity. This is the actual ingredient list for ONE recipe, not a catalog of options.
12. IGNORE navigation menus, related-recipe links, hyperlinks/URLs, markdown headings, ratings/votes, and the comments section (commenter names, "Post Your Comment", "your email", "Reply", etc.)

INGREDIENTS:"""

        try:
            # Use Gemini 2.0 Flash as primary (same model as the Discovery agent, far better
            # at following "ingredients only / ignore comments & nav" than llama-8b),
            # with Groq llama as fallback.
            ingredients_text = await self._call_extraction_ai(prompt)
            if not ingredients_text:
                logger.warning(
                    "[FAST RECIPE] AI returned no text, using fallback extraction")
                return self._fallback_ingredient_extraction(scraped_text)

            ingredients_text = ingredients_text.strip()

            # Parse ingredient lines
            ingredients = []
            import re

            for line in ingredients_text.split('\n'):
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('INGREDIENTS'):
                    continue

                # Remove leading dashes/bullets/checkboxes (▢ ☐ □ ● ○ ✓ ✔)
                line = line.lstrip('- •*\u25a2\u2610\u25a1\u25cf\u25cb\u2713\u2714\t ')

                # Remove leading numbers like "1.", "2.", etc.
                line = re.sub(r'^\d+\.\s*', '', line)

                if len(line) > 3:  # Reasonable ingredient text
                    # VALIDATION: Skip obviously non-food items
                    non_food_keywords = ['pen', 'paper', 'computer', 'blog', 'school', 'restaurant',
                                         'channel', 'social media', 'pinterest', 'google', 'subway',
                                         'nyc', 'doc', 'youtube', 'high school', 'culinary school']

                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in non_food_keywords):
                        logger.warning(
                            f"[FAST RECIPE] Skipping non-food item: {line}")
                        continue

                    # VALIDATION: Skip recipe metadata (times, servings, yield, nutrition, etc.)
                    if self._is_recipe_metadata(line):
                        logger.warning(
                            f"[FAST RECIPE] Skipping recipe metadata: {line}")
                        continue

                    # VALIDATION: Skip non-ingredient junk (links, headings, comments, UI)
                    if self._is_non_ingredient_line(line):
                        logger.warning(
                            f"[FAST RECIPE] Skipping non-ingredient line: {line}")
                        continue

                    ingredients.append({
                        'original': line,
                        'name': line  # Will be parsed by IML mapper
                    })

                    # SAFETY LIMIT: Stop at 30 ingredients
                    if len(ingredients) >= 30:
                        logger.warning(
                            f"[FAST RECIPE] ⚠️ Reached safety limit of 30 ingredients, stopping extraction")
                        break

            logger.info(f"[FAST RECIPE] Parsed {len(ingredients)} ingredients")

            # VALIDATION: Check if we got a reasonable number of ingredients
            if len(ingredients) == 0:
                logger.error("[FAST RECIPE] ❌ No valid ingredients found")
                return []

            if len(ingredients) > 25:
                logger.warning(
                    f"[FAST RECIPE] ⚠️ Unusually high ingredient count ({len(ingredients)}), may indicate extraction error")

            return ingredients

        except Exception as e:
            logger.error(f"[FAST RECIPE] AI extraction failed: {e}")
            return self._fallback_ingredient_extraction(scraped_text)

    async def _call_extraction_ai(self, prompt: str) -> Optional[str]:
        """
        Get ingredient text from AI. Primary: Gemini 2.0 Flash (same model the Discovery
        agent uses - much better at following 'ingredients only' instructions). Fallback:
        Groq llama. Returns raw text or None.
        """
        # PRIMARY: Gemini 2.0 Flash
        try:
            import google.generativeai as genai
            api_key = getattr(settings, 'GEMINI_API_KEY', None)
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash-lite')
                loop = asyncio.get_event_loop()
                resp = await loop.run_in_executor(
                    None,
                    lambda: model.generate_content(
                        prompt,
                        generation_config={
                            'temperature': 0.1,
                            'max_output_tokens': 1000,
                        }
                    )
                )
                text = (getattr(resp, 'text', '') or '').strip()
                if text:
                    logger.info(
                        "[FAST RECIPE] ✅ Ingredients extracted via Gemini 2.5 Flash Lite")
                    return text
                logger.warning("[FAST RECIPE] Gemini returned empty text")
            else:
                logger.info(
                    "[FAST RECIPE] No GEMINI_API_KEY, using Groq for extraction")
        except Exception as e:
            logger.warning(
                f"[FAST RECIPE] Gemini extraction failed: {e}, falling back to Groq")

        # FALLBACK: Groq llama
        if not self.groq_client:
            return None
        try:
            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a recipe ingredient extractor. Extract ONLY food ingredients. Ignore tools, equipment, navigation, comments, and non-food items. Maximum 30 ingredients."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            logger.info("[FAST RECIPE] ✅ Ingredients extracted via Groq (fallback)")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"[FAST RECIPE] Groq extraction failed: {e}")
            return None

    def _is_recipe_content(self, scraped_text: str, recipe_name: str) -> bool:
        """
        Validate that the scraped content is actually a recipe, not a generic article
        """
        text_lower = scraped_text.lower()

        # Check for recipe indicators
        recipe_keywords = ['ingredients', 'instructions', 'directions', 'servings', 'cook time',
                           'prep time', 'recipe', 'cooking', 'bake', 'minutes', 'oven', 'heat']

        # Check for non-recipe indicators (articles about writing recipes, blogging,
        # or "guide/listicle" pages that enumerate many options rather than ONE recipe)
        non_recipe_keywords = ['how to write', 'how to develop', 'blog post', 'social media',
                               'start a blog', 'recipe development', 'writing tips', 'create content',
                               'become a', 'learn how to',
                               'types of', 'different types', 'guide to', 'a complete guide',
                               'ultimate guide', 'everything you need to know', 'difference between',
                               'which one', 'explained', 'comparison', 'buying guide', 'best types']

        recipe_score = sum(
            1 for keyword in recipe_keywords if keyword in text_lower)
        non_recipe_score = sum(
            1 for keyword in non_recipe_keywords if keyword in text_lower)

        logger.info(
            f"[FAST RECIPE] Content validation - Recipe score: {recipe_score}, Non-recipe score: {non_recipe_score}")

        # If it looks like a "how to write recipes" article, reject it
        if non_recipe_score >= 2:
            logger.warning(
                "[FAST RECIPE] ❌ Content appears to be about recipe writing, not an actual recipe")
            return False

        # Must have at least 3 recipe-related keywords
        if recipe_score < 3:
            logger.warning(
                "[FAST RECIPE] ❌ Content does not have enough recipe indicators")
            return False

        return True

    def _strip_after_comments(self, text: str) -> str:
        """
        Truncate scraped text at the first comments / related-recipes / footer marker so
        commenter names and related-link lists never reach the ingredient extractor.
        """
        import re

        if not text:
            return text

        markers = [
            r'post your comment', r'leave a comment', r'leave a reply',
            r'\n#+\s*comments', r'\bcomments\s*\(', r'reader interactions',
            r'related recipes', r'you might also', r'more recipes',
            r'primary sidebar', r'explore more', r'similar recipes',
        ]
        earliest = len(text)
        low = text.lower()
        for marker in markers:
            m = re.search(marker, low)
            if m and m.start() < earliest:
                earliest = m.start()

        if earliest < len(text):
            return text[:earliest]
        return text

    def _extract_ingredients_section(self, text: str) -> Optional[str]:
        """
        Isolate the ingredients section of a scraped recipe page so that navigation,
        related-recipe links and the comments section are not sent to the AI.

        Returns the section text, or None if a clean section could not be located.
        """
        import re

        if not text:
            return None

        # Capture text from an "Ingredients" heading up to the next major section
        # (instructions / directions / method / steps / notes / nutrition / comments).
        pattern = re.compile(
            r'(?is)\bingredients?\b\s*[:\-\n]'
            r'(.*?)'
            r'(?:\b(instructions?|directions?|method|preparation|steps?|nutrition|notes?|'
            r'comments?|post your comment|leave a comment|related|you might also)\b|\Z)'
        )
        match = pattern.search(text)
        if match:
            section = match.group(1).strip()
            # Sanity: a real ingredients list is neither tiny nor enormous
            if 15 < len(section) < 4000:
                return section

        return None

    @staticmethod
    def _is_non_ingredient_line(line: str) -> bool:
        """
        Detect lines that are clearly NOT ingredients: markdown links/headings, URLs,
        and comment/UI boilerplate (ratings, "Post Your Comment", form labels, etc.).
        """
        import re

        text = line.strip()
        low = text.lower()
        if not text:
            return True

        # Markdown link / heading / URL artifacts
        if '](' in text or 'http://' in low or 'https://' in low or 'www.' in low:
            return True
        if text.startswith('#') or text.startswith('!['):
            return True

        # Comment / navigation / UI boilerplate
        ui_keywords = [
            'post your comment', 'leave a comment', 'cancel reply', 'your comment',
            'your name', 'your email', 'your website', 'recipe rating', 'rate this',
            'jump to recipe', 'jump to', 'print recipe', 'join to print', 'save recipe',
            'explore more', 'related recipe', 'you might also', 'follow us', 'share this',
            'subscribe', 'newsletter', 'votes', 'comments', 'reply',
        ]
        for kw in ui_keywords:
            if kw in low:
                return True

        # Sentence-like lines are descriptions/intros, not ingredients.
        # Real ingredient lines are short ("1/2 pound pancetta or thick cut bacon" = 7 words).
        if len(text.split()) > 12:
            return True

        return False

    @staticmethod
    def _is_recipe_metadata(line: str) -> bool:
        """
        Detect recipe metadata lines that are NOT ingredients
        (e.g. "Cook Time: 20 mins", "Servings: 4", "Total Time", "mins", "Calories").

        Returns True if the line should be skipped (i.e. it is metadata, not food).
        """
        import re

        text = line.strip().lower()
        if not text:
            return True

        # Standalone noise words that sometimes leak in as separate "ingredients"
        standalone_noise = {
            'mins', 'min', 'minutes', 'minute', 'hours', 'hour', 'hrs', 'hr',
            'seconds', 'secs', 'sec', 'servings', 'serving', 'serves', 'yield',
            'yields', 'makes', 'prep', 'cook', 'total', 'ingredients',
            'instructions', 'directions', 'method', 'notes', 'nutrition',
            'calories', 'difficulty', 'course', 'cuisine',
        }
        if text in standalone_noise:
            return True

        # Metadata patterns (labels / time / nutrition / yield)
        metadata_patterns = [
            r'\b(prep|cook|cooking|total|rest|resting|chill|chilling|inactive|active|marinat\w*|baking|freezing|additional|hands[\s-]?on|stand|wait)\s*time\b',
            r'\btime\s*[:：]',          # "Time:" label
            r'^\W*time\b',               # line starting with "Time"
            r'\bserv(e|es|ing|ings)\b',  # servings / serves
            r'\byield(s)?\b',
            r'\bmakes\s+\d',
            r'\bcalor(ie|ies)\b',
            r'\bnutrition\b',
            r'\bper serving\b',
            r'\bkcal\b',
            r'\b(course|cuisine|difficulty|category|keywords?|author|rating|reviews?)\s*[:：]',
            r'^\d+(\.\d+)?\s*(mins?|minutes?|hours?|hrs?|secs?|seconds?)\b',  # "20 mins"
            # Label form without the word "time" (e.g. "Prep: 15 minutes", "Cook: 18 mins")
            r'^(prep|cook|cooking|total|rest|resting|chill|chilling|inactive|active|additional|marinat\w*)\s*[:：]',
            r'^from\s+\d+',  # "from 401" (votes/reviews fragment)
        ]
        for pattern in metadata_patterns:
            if re.search(pattern, text):
                return True

        return False

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

                    # Skip recipe metadata (times, servings, yield, etc.) and junk
                    if self._is_recipe_metadata(line) or self._is_non_ingredient_line(line):
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
                'name': match_result.display_name or ingredient_text,  # Use clean display name
                # Will be translated in next step
                'name_translated': match_result.display_name or ingredient_text,
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
