"""
Recipe Agent Service - AI-powered recipe search, scraping, and conversion
WITH DEDUPLICATION SUPPORT
"""


from apps.core.ingredient_mapper import IngredientMapper
from apps.core.unit_converter import UnitConverter
from apps.core.nutrition_calculator import NutritionCalculator
from apps.core.translation_service import TranslationService
from apps.core.cooking_terms_service import CookingTermsTranslationService
from rcip_converter import RCIPConverter, RecipeAnalyzer
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncio
import requests
from bs4 import BeautifulSoup
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        print(
            "[ERROR] Neither 'ddgs' nor 'duckduckgo_search' found. Please install: pip install ddgs")
        DDGS = None
from groq import Groq
from django.conf import settings
from asgiref.sync import sync_to_async
import hashlib
import re

# Import RCIP converter
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class RecipeAgentService:
    """Service for searching, scraping, and converting recipes using AI with deduplication"""

    def __init__(self, user_language='en', user_preferences=None):
    	groq_api_key = os.getenv('GROQ_API_KEY') or settings.GROQ_API_KEY if hasattr(
        	settings, 'GROQ_API_KEY') else None
    	if not groq_api_key:
        	print("[WARNING] GROQ_API_KEY not found. AI conversion will be limited.")
        	self.groq_client = None
    	else:
        	self.groq_client = Groq(api_key=groq_api_key)
    	self.rcip_converter = RCIPConverter()
    	self.recipe_analyzer = RecipeAnalyzer()
    	self.model = "llama-3.1-8b-instant"
    	# NEW: Initialize new services
    	self.ingredient_mapper = IngredientMapper()
    	self.unit_converter = UnitConverter()
    	self.nutrition_calculator = NutritionCalculator()
    	self.translation_service = TranslationService()
    	self.cooking_terms_service = CookingTermsTranslationService()
   	# Store user preferences
    	self.user_language = user_language
    	self.user_preferences = user_preferences or {}

    async def _enrich_recipe_with_iml(
        self,
        rcip_recipe: Dict,
        user_preferences: Dict = None
    ) -> Dict:
        """
        Enrich recipe with IML data:
        - Map ingredients to ingredient_keys
        - Calculate nutrition from IML
        - Add unit alternatives
        - Apply user unit preferences

        Args:
            rcip_recipe: Recipe in RCIP format from AI
            user_preferences: User preferences (language, unit_system)

        Returns:
            Enhanced RCIP recipe
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info("[ENRICH] Starting IML enrichment...")

        user_language = user_preferences.get(
            'language', 'en') if user_preferences else 'en'
        user_unit_system = user_preferences.get(
            'unit_system', 'metric') if user_preferences else 'metric'

        logger.info(
            f"[ENRICH] User language: {user_language}, unit system: {user_unit_system}")

        # Step 1: Map ingredients to IML keys
        enriched_ingredients = []
        ingredient_count = len(rcip_recipe.get('ingredients', []))
        logger.info(f"[ENRICH] Processing {ingredient_count} ingredients...")

        for idx, ingredient in enumerate(rcip_recipe.get('ingredients', [])):
            ingredient_text = ingredient.get('name', '')
            # RCIP converter uses 'amount', not 'quantity'
            quantity = ingredient.get('quantity') or ingredient.get('amount')
            unit = ingredient.get('unit', '')

            # Map to IML (wrap in sync_to_async since it uses Django ORM)
            match_result = await sync_to_async(self.ingredient_mapper.map)(
                text=f"{quantity}{unit} {ingredient_text}" if quantity and unit else ingredient_text,
                language=user_language,
                user_unit_system=user_unit_system
            )

            if match_result.ingredient_key:
                logger.info(
                    f"[ENRICH] {idx+1}/{ingredient_count}: Mapped '{ingredient_text}' → {match_result.ingredient_key} (confidence: {match_result.confidence})")
            else:
                logger.warning(
                    f"[ENRICH] {idx+1}/{ingredient_count}: No match for '{ingredient_text}'")

            # Build enriched ingredient
            enriched = {
                'name': ingredient_text,
                'quantity': match_result.quantity or quantity,
                'unit': match_result.unit or unit,
                'ingredient_key': match_result.ingredient_key,
                'unit_type': match_result.unit_type,
                'match_confidence': match_result.confidence,
                'display_name': match_result.display_name,
                'original': ingredient.get('original', ingredient_text)
            }

            # Add unit alternatives (metric/imperial)
            if match_result.unit and match_result.quantity:
                alternatives = self.unit_converter.get_conversion_alternatives(
                    match_result.quantity,
                    match_result.unit
                )
                enriched['alternatives'] = {
                    'metric': alternatives.get('display_metric'),
                    'imperial': alternatives.get('display_imperial')
                }

            enriched_ingredients.append(enriched)

            if match_result.ingredient_key:
                print(
                    f"   ✅ Mapped: {ingredient_text} → {match_result.ingredient_key} ({match_result.confidence})")
            else:
                print(f"   ⚠️  No match: {ingredient_text}")

        # Step 2: Calculate nutrition from IML
        nutrition_ingredients = [
            {
                'ingredient_key': ing.get('ingredient_key'),
                'quantity': ing.get('quantity'),
                'unit': ing.get('unit')
            }
            for ing in enriched_ingredients
            if ing.get('ingredient_key')
        ]

        servings = rcip_recipe.get('meta', {}).get(
            'servings', {}).get('amount', 4)
        if isinstance(servings, dict):
            servings = servings.get('amount', 4)

        nutrition = await sync_to_async(self.nutrition_calculator.calculate_recipe_nutrition)(
            nutrition_ingredients,
            servings=servings
        )

        print(
            f"   🍎 Nutrition calculated: {nutrition['coverage']*100:.0f}% coverage")
        print(
            f"      Per serving: {nutrition['per_serving']['calories']:.0f} cal, {nutrition['per_serving']['protein']:.1f}g protein")

        # Step 3: Update recipe with enriched data
        rcip_recipe['ingredients'] = enriched_ingredients
        rcip_recipe['meta']['nutrition_per_serving'] = nutrition['per_serving']
        rcip_recipe['meta']['nutrition_total'] = nutrition['total']
        rcip_recipe['meta']['nutrition_coverage'] = nutrition['coverage']

        # Step 4: Prepare base_ingredients for frontend (ALWAYS IN ENGLISH for storage)
        # Frontend will translate using the translation tables
        base_ingredients = self._prepare_base_ingredients(
            enriched_ingredients, 'en'  # Always store in English
        )
        rcip_recipe['base_ingredients'] = base_ingredients

        # Step 5: Prepare base_steps (ALWAYS IN ENGLISH for storage)
        # Frontend will translate using cooking terms database
        base_steps = self._prepare_base_steps(
            rcip_recipe.get('steps', []), 'en'  # Always store in English
        )
        rcip_recipe['base_steps'] = base_steps

        return rcip_recipe

    def _prepare_base_ingredients(self, enriched_ingredients: List[Dict], language: str) -> List[Dict]:
        """
        Convert enriched ingredients to frontend-friendly format with translations

        Args:
            enriched_ingredients: Ingredients enriched with IML data
            language: User's preferred language

        Returns:
            List of ingredients in format: {amount, unit, name}
        """
        print(
            f"[PREPARE_INGREDIENTS] Starting with {len(enriched_ingredients)} ingredients")
        base_ingredients = []

        for ing in enriched_ingredients:
            # Get translated name if available
            display_name = ing.get('display_name', {})
            if isinstance(display_name, dict):
                # IML database match - has translations
                name = display_name.get(language, ing.get('name', ''))
            elif isinstance(display_name, str):
                # Synthetic key - display_name is already a string (English name)
                name = display_name
            else:
                # Fallback to original name
                name = ing.get('name', '')

            # Skip empty or very short names
            if not name or len(name.strip()) < 2:
                continue

            # Skip generic non-ingredients (AGGRESSIVE FILTERING)
            name_lower = name.lower().strip()
            skip_terms = [
                'as needed', 'to taste', 'optional', 'for serving', 'for garnish',
                'needed', 'analyzing', 'webpage', 'content', 'found', 'recipe',
                'however', 'extract', 'complete', '***'
            ]
            # Skip if name matches any skip term
            if any(term in name_lower for term in skip_terms):
                continue

            # Format quantity
            quantity = ing.get('quantity')
            unit = ing.get('unit', '')

            # Skip if unit contains "as" or "needed" (from "as needed")
            unit_lower = unit.lower().strip() if unit else ''
            invalid_units = [
                'as', 'needed', 'taste', 'quantity', 'optional'
            ]
            # Check if unit is invalid
            if any(invalid in unit_lower for invalid in invalid_units):
                print(
                    f"[FILTER] Skipping ingredient with invalid unit: {name} ({quantity} {unit})")
                continue

            if quantity:
                if isinstance(quantity, (int, float)):
                    # Skip if quantity is exactly 1 and name is vague or contains skip terms
                    if quantity == 1:
                        if any(term in name_lower for term in skip_terms):
                            continue
                        # Also skip if name is just 1-2 words with no real content
                        if len(name_lower) < 4:
                            continue
                    amount = str(int(quantity)) if quantity == int(
                        quantity) else str(quantity)
                else:
                    amount = str(quantity).strip()
                    # Skip if amount is "1" and name is vague
                    if amount == "1" and len(name_lower) < 4:
                        continue
            else:
                # No quantity - use empty string (will be displayed without amount)
                amount = ''

            # Final check: skip if name is just a number or single character
            if name_lower.isdigit() or len(name_lower) == 1:
                continue

            base_ingredients.append({
                'amount': amount,
                'unit': unit,  # Use filtered unit variable
                'name': name,
                'ingredient_key': ing.get('ingredient_key'),
                'original': ing.get('original', name)
            })
            print(f"   [PREPARE] Added: {amount} {unit} {name}")

        return base_ingredients

    def _prepare_base_steps(self, steps: List[Dict], language: str) -> List[Dict]:
        """
        Convert steps to frontend-friendly format, filtering out non-cooking content

        Args:
            steps: Recipe steps from RCIP
            language: User's preferred language

        Returns:
            List of clean cooking steps with translated cooking terms
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"[PREPARE_STEPS] Starting with {len(steps)} steps")

        base_steps = []
        step_number = 1

        # Obvious non-cooking phrases to filter out
        skip_phrases = [
            'subscribe', 'click here', 'visit', 'follow me', 'instagram',
            'facebook', 'twitter', 'pinterest', 'blog', 'website',
            'thank you for reading', 'if you like this recipe',
            'ever imagined', 'make it come true', 'lands you here',
            'coincidences', 'gratitude', 'productive', 'creative',
            'trying this at home', 'tag me on instagram'
        ]

        for step in steps:
            # Get step text and remember which field it came from
            text = None
            text_field_name = None
            time_minutes = None
            order = None
            equipment = None

            if isinstance(step, dict):
                # Try 'instruction' first (RCIP standard), then 'text'
                if 'instruction' in step:
                    text = step['instruction']
                    text_field_name = 'instruction'
                elif 'text' in step:
                    text = step['text']
                    text_field_name = 'text'
                elif 'step' in step:
                    text = step['step']
                    text_field_name = 'instruction'

                time_minutes = step.get('time_minutes')
                order = step.get('order')
                equipment = step.get('equipment')
            else:
                text = str(step)
                text_field_name = 'instruction'

            # Skip empty steps
            if not text or not text.strip():
                continue

            text = text.strip()
            text_lower = text.lower()

            # Skip obvious website/blog content
            should_skip = False
            for phrase in skip_phrases:
                if phrase in text_lower:
                    should_skip = True
                    break

            if should_skip:
                continue

            # Store in English - preserve original field name for consistency
            # Build step with the SAME field name as the source
            clean_step = {
                text_field_name: text,  # Use original field name
                'step_number': step_number
            }

            # Preserve additional fields if present
            if order is not None:
                clean_step['order'] = order
            if time_minutes:
                clean_step['time_minutes'] = time_minutes
            if equipment:
                clean_step['equipment'] = equipment

            base_steps.append(clean_step)
            step_number += 1

        logger.info(
            f"[PREPARE_STEPS] Finished: {len(base_steps)} steps survived filtering (from {len(steps)} original)")
        if len(base_steps) == 0 and len(steps) > 0:
            logger.warning(f"[PREPARE_STEPS] ⚠️ ALL STEPS WERE FILTERED OUT!")
            logger.warning(
                f"[PREPARE_STEPS] First original step was: {steps[0] if steps else 'None'}")

        return base_steps

    async def _translate_recipe(
        self,
        rcip_recipe: Dict,
        original_language: str
    ) -> Dict:
        """
        Translate recipe to all supported languages

        Args:
            rcip_recipe: Recipe in RCIP format
            original_language: Language recipe was created in

        Returns:
            Recipe with translations
        """
        print(f"[TRANSLATE] Translating from {original_language}...")

        content = {
            'title': rcip_recipe['meta']['name'],
            'description': rcip_recipe['meta'].get('description', ''),
            'steps': rcip_recipe.get('steps', [])
        }

        translations = self.translation_service.translate_recipe(
            content,
            from_language=original_language,
            to_languages=None  # Translate to all other languages
        )

        # Add translations to recipe
        rcip_recipe['meta']['title_translations'] = translations['title_translations']
        rcip_recipe['meta']['description_translations'] = translations['description_translations']
        rcip_recipe['meta']['steps_translations'] = translations['steps_translations']
        rcip_recipe['meta']['original_language'] = original_language

        print(
            f"   ✅ Translated to: {', '.join(translations['title_translations'].keys())}")

        return rcip_recipe

    async def process_recipe_query(self, user_query: str, user, user_preferences: Dict = None):
        """
        Main method: Search, scrape, convert recipe from user query WITH DEDUPLICATION

        NEW: Real-time progress updates via WebSocket!

        NEW FLOW:
        1. Check if canonical recipe exists (by normalized name)
        2. If EXISTS: Return existing canonical + create user fork
        3. If NOT EXISTS: Search web → Create canonical → Create user fork

        Args:
            user_query: What user wants to cook (e.g., "Italian pasta carbonara")
            user: Django User object (for creating fork)
            user_preferences: User dietary restrictions, allergies, etc.

        Returns:
            (success: bool, result_data: Dict, message: str)
            result_data contains: canonical_recipe, user_recipe, is_new
        """
        print(f"[RECIPE AGENT] Processing query: '{user_query}'")

        # Initialize progress tracker
        from .progress_tracker import RecipeGenerationProgress
        user_language = user_preferences.get(
            'language', 'en') if user_preferences else 'en'
        progress = RecipeGenerationProgress(str(user.id), user_language)

        try:
            # STEP 1: Check if canonical recipe already exists using AI deduplication
            print(f"[DISCOVERY] Checking for duplicates using AI...")
            from apps.core.deduplication_service import get_deduplication_service

            dedup_service = get_deduplication_service()
            existing_canonical = await dedup_service.find_duplicate(
                recipe_name=user_query,
                user_language=user_language
            )

            if existing_canonical:
                print(
                    f"[REUSE] ✅ AI found existing canonical: {existing_canonical.name}")

                # Send complete immediately (recipe already exists!)
                progress.update_complete()

                # Create or get user fork
                user_fork = await self._create_or_get_user_fork(user, existing_canonical)

                # Serialize for response
                from .serializers import CanonicalRecipeSerializer, RecipeSerializer

                @sync_to_async
                def serialize_recipes():
                    canonical_data = CanonicalRecipeSerializer(
                        existing_canonical).data
                    fork_data = RecipeSerializer(user_fork).data
                    return canonical_data, fork_data

                canonical_data, fork_data = await serialize_recipes()

                return True, {
                    'canonical_recipe': canonical_data,
                    'user_recipe': fork_data,
                    'is_new': False
                }, f"Found existing recipe: {existing_canonical.name}"

            # STEP 2: Recipe doesn't exist - search and scrape using Brave + Firecrawl
            progress.update_searching()  # 10% - Searching the internet...
            print(f"[SEARCH] No canonical found, searching web...")
            scraped_recipes = await self._search_and_scrape_recipes(user_query, max_results=3)

            if not scraped_recipes:
                progress.update_error()
                return False, None, "No recipes found for your query"

            # 25% - Found recipes! Extracting content...
            progress.update_scraping(len(scraped_recipes))

            # DEBUG: Log scraped recipes structure
            print(f"[DEBUG] Got {len(scraped_recipes)} scraped recipes")
            for i, recipe in enumerate(scraped_recipes, 1):
                print(f"[DEBUG] Recipe {i} keys: {list(recipe.keys())}")
                print(f"[DEBUG] Recipe {i} URL: {recipe.get('url', 'NO URL')}")
                print(
                    f"[DEBUG] Recipe {i} content length: {len(recipe.get('content', ''))} chars")

            # STEP 3: Try each scraped recipe until we get a good one
            scraped_data = None
            for i, recipe in enumerate(scraped_recipes, 1):
                url = recipe.get('url', '')
                content = recipe.get('content', '')

                print(f"[CONVERT] Trying recipe {i}/{len(scraped_recipes)}...")
                print(f"[CONVERT] Content length: {len(content)} characters")

                if len(content) < 500:
                    print(f"[CONVERT] ⚠️ Content too short, skipping...")
                    continue

                # Use the content directly (already scraped by Firecrawl)
                scraped_data = {
                    'url': url,
                    'text': content
                }
                break

            if not scraped_data:
                print(f"[ERROR] Failed to scrape any recipes")
                progress.update_error()
                return False, None, "Could not extract recipe from websites. Please try a different recipe or check your internet connection."

            # STEP 4: Convert to RCIP format using AI (Stage 1: Extraction)
            # 40% - Converting recipe to standard format...
            progress.update_converting()
            print(f"[CONVERT] Converting scraped content to RCIP format...")
            print(
                f"[CONVERT] Content length: {len(scraped_data.get('text', ''))} characters")

            rcip_recipe = await self._convert_to_rcip(
                scraped_data,
                user_query,
                user_preferences
            )

            if not rcip_recipe:
                print(f"[ERROR] ❌ AI conversion returned None")
                progress.update_error()
                return False, None, "Failed to convert recipe to standard format. The recipe content may be too complex or incomplete. Please try a different recipe."

            # VALIDATION: Check for placeholder/failed extractions
            recipe_name = rcip_recipe.get('meta', {}).get('name', '').lower()
            ingredients = rcip_recipe.get('ingredients', [])
            steps = rcip_recipe.get('steps', [])

            # Check for obvious extraction failures
            is_placeholder = (
                'placeholder' in recipe_name or
                recipe_name == 'untitled recipe' or
                recipe_name == 'untitled' or
                not recipe_name or
                len(ingredients) == 0 or
                (len(ingredients) == 1 and 'no ingredients' in str(ingredients[0]).lower()) or
                len(steps) == 0 or
                (len(steps) == 1 and 'no steps' in str(steps[0]).lower())
            )

            if is_placeholder:
                print(f"[ERROR] ❌ Failed extraction detected - placeholder content")
                print(
                    f"[ERROR] Name: {recipe_name}, Ingredients: {len(ingredients)}, Steps: {len(steps)}")
                progress.update_error()
                # Return with show_suggestions flag
                return False, None, {
                    'message': 'Could not find a valid recipe',
                    'show_suggestions': True,
                    'failed_query': user_query
                }

            # STEP 4.5: Enriching with nutrition data
            # 55% - Adding nutritional information...
            progress.update_enriching()

            # STEP 5: Validate Recipe Quality (Stage 2: Auto-Validation + Stage 3: AI Fix)
            progress.update_validating()  # 70% - Checking recipe quality...
            print(f"[VALIDATION] Starting quality validation...")
            rcip_recipe = await self._validate_and_fix_recipe(rcip_recipe)

            if not rcip_recipe:
                print(f"[ERROR] ❌ Recipe validation failed - unusable quality")
                progress.update_error()
                return False, None, "Could not extract a valid recipe. The content may not contain a proper recipe. Please try a different search."

            # STEP 6: Create canonical recipe
            # 85% - Translating to your language...
            progress.update_translating()

            # DEBUG: Check meta before creating canonical
            print(f"[DEBUG] Before _create_canonical_recipe:")
            print(f"[DEBUG] rcip_recipe keys: {list(rcip_recipe.keys())}")
            print(
                f"[DEBUG] rcip_recipe['meta'] type: {type(rcip_recipe.get('meta'))}")
            print(
                f"[DEBUG] rcip_recipe['meta'] value: {rcip_recipe.get('meta')}")
            if isinstance(rcip_recipe.get('meta'), dict):
                print(
                    f"[DEBUG] meta.get('name'): {rcip_recipe['meta'].get('name')}")

            canonical = await self._create_canonical_recipe(
                rcip_recipe,
                source_type='ai_generated',
                original_creator=user
            )

            # STEP 7: Create user fork
            # 95% - Almost done! Finalizing recipe...
            progress.update_finalizing()
            user_fork = await self._create_user_fork(user, canonical, rcip_recipe)

            print(f"[SUCCESS] Created new canonical recipe: {canonical.name}")

            # STEP 8: Complete!
            progress.update_complete()  # 100% - Recipe ready! 🎉

            # Serialize for response
            from .serializers import CanonicalRecipeSerializer, RecipeSerializer

            @sync_to_async
            def serialize_recipes():
                canonical_data = CanonicalRecipeSerializer(canonical).data
                fork_data = RecipeSerializer(user_fork).data
                return canonical_data, fork_data

            canonical_data, fork_data = await serialize_recipes()

            return True, {
                'canonical_recipe': canonical_data,
                'user_recipe': fork_data,
                'is_new': True
            }, f"Created new recipe: {canonical.name}"

        except Exception as e:
            # Send error to user
            progress.update_error(str(e))
            print(f"[ERROR] ❌ Recipe generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False, None, f"An error occurred: {str(e)}"

    # ============================================================================
    # DEDUPLICATION HELPER METHODS
    # ============================================================================

    def _normalize_recipe_name(self, name: str) -> str:
        """Normalize recipe name for comparison (lowercase, remove special chars, extra spaces)"""
        normalized = name.lower().strip()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = ' '.join(normalized.split())

        # Remove common words that don't help with matching
        stop_words = {'and', 'or', 'with', 'the', 'a', 'an', 'in', 'to', 'for'}
        words = normalized.split()
        filtered_words = [w for w in words if w not in stop_words]
        if filtered_words:  # Only filter if we have remaining words
            normalized = ' '.join(filtered_words)

        return normalized

    @sync_to_async
    def _find_existing_canonical(self, normalized_name: str):
        """
        Check if canonical recipe exists in ANY language (multilingual search)
        Searches:
        1. CanonicalRecipe.name (original English name)
        2. RecipeTranslation.name (Russian, Hebrew translations)
        """
        from .models import CanonicalRecipe, RecipeTranslation
        from django.db.models import Q

        print(
            f"[MATCH] Searching for recipe: '{normalized_name}' in all languages")

        # STEP 1: Try exact match on canonical recipe name (original)
        canonical = CanonicalRecipe.objects.filter(
            name__iexact=normalized_name,
            is_published=True
        ).first()

        if canonical:
            print(f"[MATCH] ✅ Exact match in original name: {canonical.name}")
            return canonical

        # STEP 2: Try exact match in translations (all languages)
        translation = RecipeTranslation.objects.filter(
            name__iexact=normalized_name,
            status='completed',
            canonical_recipe__is_published=True
        ).select_related('canonical_recipe').first()

        if translation:
            print(
                f"[MATCH] ✅ Exact match in {translation.language} translation: {translation.name}")
            print(
                f"[MATCH]    Original name: {translation.canonical_recipe.name}")
            return translation.canonical_recipe

        # STEP 2.5: **CRITICAL** - Translate search query to all languages
        # This catches duplicates even if translations haven't been generated yet!
        print(f"[MATCH] No direct match, translating search query to all languages...")

        from apps.core.smart_translator import SmartTranslationService
        translator = SmartTranslationService()
        search_variations = {}

        # Translate to English, Russian, Hebrew
        for lang in ['en', 'ru', 'he']:
            try:
                translated = translator.translate_recipe_name(
                    normalized_name, lang)
                if translated and translated.lower().strip() != normalized_name.lower():
                    translated_normalized = self._normalize_recipe_name(
                        translated)
                    search_variations[lang] = translated_normalized
                    print(
                        f"[MATCH] → Translated to {lang}: '{translated_normalized}'")
            except Exception as e:
                print(f"[MATCH] ⚠️ Translation to {lang} failed: {e}")

        # Search using all translated variations
        for lang_key, search_term in search_variations.items():
            # Search canonical names
            canonical = CanonicalRecipe.objects.filter(
                name__iexact=search_term,
                is_published=True
            ).first()

            if canonical:
                print(
                    f"[MATCH] ✅ Found via {lang_key} translation: '{search_term}' matches '{canonical.name}'")
                return canonical

            # Search existing translations
            translation = RecipeTranslation.objects.filter(
                name__iexact=search_term,
                status='completed',
                canonical_recipe__is_published=True
            ).select_related('canonical_recipe').first()

            if translation:
                print(
                    f"[MATCH] ✅ Found in translations via {lang_key}: '{search_term}' matches '{translation.name}'")
                return translation.canonical_recipe

        # STEP 3: Partial match in canonical names
        words = normalized_name.split()
        if len(words) >= 2:
            # Search for recipes containing at least the first 2 significant words
            similar = CanonicalRecipe.objects.filter(
                Q(name__icontains=words[0]) & Q(name__icontains=words[1]),
                is_published=True
            ).first()

            if similar:
                print(
                    f"[MATCH] Potential match in original: {similar.name} (searched for: {normalized_name})")

                # Strict validation: normalize the similar recipe name and check word overlap
                similar_normalized = self._normalize_recipe_name(similar.name)
                similar_words = set(similar_normalized.split())
                search_words = set(words)

                # Calculate overlap percentage (intersection / search words)
                overlap = similar_words.intersection(search_words)
                overlap_percentage = len(
                    overlap) / len(search_words) if search_words else 0

                print(
                    f"[MATCH] Word overlap: {overlap} ({overlap_percentage * 100:.0f}% of search terms)")

                # Only accept if at least 70% of search words match
                if overlap_percentage >= 0.7:
                    print(f"[MATCH] ✅ Accepted match (sufficient overlap)")
                    return similar
                else:
                    print(
                        f"[MATCH] ❌ Rejected match (insufficient overlap: {overlap_percentage * 100:.0f}% < 70%)")

            # STEP 4: Partial match in translations (if not found in originals)
            if not similar or (similar and overlap_percentage < 0.7):
                similar_translation = RecipeTranslation.objects.filter(
                    Q(name__icontains=words[0]) & Q(name__icontains=words[1]),
                    status='completed',
                    canonical_recipe__is_published=True
                ).select_related('canonical_recipe').first()

                if similar_translation:
                    print(
                        f"[MATCH] Potential match in {similar_translation.language} translation: {similar_translation.name}")

                    # Normalize and check overlap
                    similar_normalized = self._normalize_recipe_name(
                        similar_translation.name)
                    similar_words = set(similar_normalized.split())
                    overlap = similar_words.intersection(search_words)
                    overlap_percentage = len(
                        overlap) / len(search_words) if search_words else 0

                    print(
                        f"[MATCH] Translation word overlap: {overlap} ({overlap_percentage * 100:.0f}% of search terms)")

                    if overlap_percentage >= 0.7:
                        print(f"[MATCH] ✅ Accepted translation match")
                        return similar_translation.canonical_recipe
                    else:
                        print(
                            f"[MATCH] ❌ Rejected translation match (insufficient overlap: {overlap_percentage * 100:.0f}% < 70%)")

        # If single word or no good match, don't match partially
        # Let the AI search for the exact recipe instead
        print(f"[MATCH] No existing recipe found, will search web")
        return None

    @sync_to_async
    def _create_or_get_user_fork(self, user, canonical_recipe):
        """Create or retrieve user's fork of canonical recipe"""
        from .models import Recipe, UserRecipe
        from django.utils import timezone

        # Check if user already has a fork
        existing_fork = Recipe.objects.filter(
            created_by=user,
            canonical_recipe=canonical_recipe,
            is_fork=True
        ).first()

        if existing_fork:
            print(f"[FORK] User already has fork: {existing_fork.id}")
            # Ensure UserRecipe entry exists and is NOT archived
            user_recipe, created = UserRecipe.objects.get_or_create(
                user=user,
                recipe=existing_fork,
                defaults={
                    'saved_at': timezone.now(),
                    'is_archived': False
                }
            )

            # If the UserRecipe already existed but was archived, unarchive it
            if not created and user_recipe.is_archived:
                user_recipe.is_archived = False
                # Update saved_at to show as recently saved
                user_recipe.saved_at = timezone.now()
                user_recipe.save(update_fields=['is_archived', 'saved_at'])
                print(f"[FORK] Unarchived recipe: {existing_fork.id}")

            return existing_fork

        # Create new fork
        fork = Recipe.objects.create(
            canonical_recipe=canonical_recipe,
            is_fork=True,
            created_by=user,
            name=canonical_recipe.name,
            description=canonical_recipe.description,
            ingredients=canonical_recipe.base_ingredients,
            steps=canonical_recipe.base_steps,
            cuisine=canonical_recipe.cuisine,
            difficulty=canonical_recipe.difficulty,
            diet_labels=canonical_recipe.diet_labels,
            prep_time_minutes=canonical_recipe.prep_time_minutes,
            cook_time_minutes=canonical_recipe.cook_time_minutes,
            total_time_minutes=canonical_recipe.total_time_minutes,
            servings=canonical_recipe.servings,
            user_modifications={},  # No modifications yet
            recipe_hash=None  # NULL for forks - bypasses unique constraint
        )

        # Create UserRecipe entry to make it appear in "My Recipes"
        UserRecipe.objects.create(
            user=user,
            recipe=fork,
            saved_at=timezone.now(),
            is_archived=False,
            times_cooked=0
        )

        # Update canonical statistics
        canonical_recipe.total_saves += 1
        canonical_recipe.save(update_fields=['total_saves'])

        print(f"[FORK] Created new fork: {fork.id} with UserRecipe entry")
        return fork

    @sync_to_async
    def _create_canonical_recipe(self, rcip_data: Dict, source_type: str, original_creator):
        """Create new canonical recipe from RCIP data"""
        from .models import CanonicalRecipe

        # DEBUG: Deep inspection
        print(f"[CREATE_CANONICAL] === DEEP DEBUG ===")
        print(f"[CREATE_CANONICAL] rcip_data type: {type(rcip_data)}")
        print(f"[CREATE_CANONICAL] rcip_data keys: {list(rcip_data.keys())}")
        print(f"[CREATE_CANONICAL] 'meta' in rcip_data: {'meta' in rcip_data}")

        meta = rcip_data.get('meta', {})
        print(f"[CREATE_CANONICAL] meta type: {type(meta)}")
        print(f"[CREATE_CANONICAL] meta is dict: {isinstance(meta, dict)}")

        if isinstance(meta, dict):
            print(f"[CREATE_CANONICAL] meta keys: {list(meta.keys())}")
            print(f"[CREATE_CANONICAL] 'name' in meta: {'name' in meta}")
            if 'name' in meta:
                print(
                    f"[CREATE_CANONICAL] meta['name'] direct access: '{meta['name']}'")

        # DEBUG: Log what we're receiving
        recipe_name = meta.get('name', 'Untitled Recipe')
        print(
            f"[CREATE_CANONICAL] Received recipe name from RCIP: '{recipe_name}'")
        print(
            f"[CREATE_CANONICAL] Full meta keys: {list(meta.keys()) if isinstance(meta, dict) else 'NOT A DICT'}")
        print(f"[CREATE_CANONICAL] === END DEBUG ===\n")

        # Calculate hash for deduplication
        hash_string = self._calculate_recipe_hash(
            meta.get('name', 'Untitled'),
            rcip_data.get('ingredients', [])
        )

        # Check if hash already exists (race condition protection)
        existing = CanonicalRecipe.objects.filter(
            recipe_hash=hash_string).first()
        if existing:
            print(
                f"[RACE CONDITION] Canonical with hash already exists: {existing.name}")
            return existing

        canonical = CanonicalRecipe.objects.create(
            name=meta.get('name', 'Untitled Recipe'),
            description=meta.get('description', ''),
            source_type=source_type,
            ai_source_url=meta.get('source_url'),
            original_creator=original_creator,
            base_ingredients=rcip_data.get('ingredients', []),
            base_steps=rcip_data.get('steps', []),
            cuisine=meta.get('keywords', [''])[
                0] if meta.get('keywords') else '',
            difficulty=meta.get('difficulty', 'intermediate'),
            diet_labels=meta.get('diet_labels', []),
            allergens=meta.get('allergens', []),
            prep_time_minutes=meta.get('prep_time_minutes'),
            cook_time_minutes=meta.get('cook_time_minutes'),
            total_time_minutes=meta.get('total_time_minutes'),
            servings=meta.get('servings', {}).get('amount', 4) if isinstance(
                meta.get('servings'), dict) else meta.get('servings', 4),
            recipe_hash=hash_string,

            # NEW: Multilingual fields
            title_translations=meta.get('title_translations', {}),
            description_translations=meta.get('description_translations', {}),
            steps_translations=meta.get('steps_translations', {}),
            nutrition_per_serving=meta.get('nutrition_per_serving', {}),
            original_language=meta.get('original_language', 'en')
        )

        print(
            f"[CANONICAL] Created: {canonical.name} (hash: {hash_string[:8]}...)")
        print(
            f"   Languages: {', '.join(canonical.title_translations.keys())}")
        print(
            f"   Nutrition: {canonical.nutrition_per_serving.get('calories', 0):.0f} cal/serving")

        # Queue background translations to all supported languages
        try:
            from .tasks import translate_recipe_to_language
            from apps.core.models import IngredientCache
            from apps.core.cooking_terms_service import CookingTermsTranslationService
            from .models import RecipeTranslation
            from django.utils import timezone

            user_language = rcip_data.get(
                'meta', {}).get('original_language', 'en')

            # If user language is NOT English, translate IMMEDIATELY (synchronously)
            if user_language and user_language != 'en':
                import logging
                logger = logging.getLogger(__name__)
                logger.info(
                    f"[TRANSLATION] ⚡ Translating IMMEDIATELY to {user_language} (user's language)")
                logger.info(
                    f"[TRANSLATION] Recipe has {len(canonical.base_ingredients)} base_ingredients")
                logger.info(
                    f"[TRANSLATION] First ingredient: {canonical.base_ingredients[0] if canonical.base_ingredients else 'None'}")
                try:
                    # Get or create translation record
                    translation, created = RecipeTranslation.objects.get_or_create(
                        canonical_recipe=canonical,
                        language=user_language,
                        defaults={'status': 'in_progress'}
                    )

                    if not created and translation.status == 'completed':
                        logger.info(
                            f"[TRANSLATION] ✅ Translation already exists for {user_language}")
                    else:
                        # Update status
                        translation.status = 'in_progress'
                        translation.save()

                        # Check if recipe has content to translate
                        if not canonical.base_ingredients and not canonical.base_steps:
                            logger.warning(
                                f"[TRANSLATION] ⚠️ Recipe has no ingredients or steps - marking translation as failed")
                            translation.status = 'failed'
                            translation.save()
                            logger.info(
                                f"[TRANSLATION] ❌ Skipped translation - no content to translate")
                        else:
                            # Initialize SMART translator (uses databases first, Gemini as fallback)
                            from apps.core.smart_translator import SmartTranslationService
                            smart_translator = SmartTranslationService()

                            # Translate recipe name
                            translated_name = smart_translator.translate_recipe_name(
                                canonical.name,
                                user_language
                            )

                            # Translate ingredients using SMART approach
                            # 1. Check IML database (exact + fuzzy match)
                            # 2. Check cache for previous translations
                            # 3. Use Gemini only for unknowns (batch)
                            logger.info(
                                f"[TRANSLATION] Starting smart translation for {len(canonical.base_ingredients)} ingredients")

                            translated_ingredients = smart_translator.translate_ingredients_batch(
                                canonical.base_ingredients,
                                user_language
                            )

                            # Translate cooking steps using SMART approach with CookLingo glossary
                            # 1. Build glossary of cooking terms from CookLingo database
                            # 2. Translate full sentences with Gemini using glossary
                            logger.info(
                                f"[TRANSLATION] Starting smart translation for {len(canonical.base_steps)} steps (with CookLingo glossary)")

                            translated_steps = smart_translator.translate_cooking_steps_batch(
                                canonical.base_steps,
                                user_language
                            )

                            # Save translation
                            translation.name = translated_name  # Use translated name
                            translation.description = canonical.description
                            translation.base_ingredients = translated_ingredients
                            translation.base_steps = translated_steps
                            translation.status = 'completed'
                            translation.completed_at = timezone.now()

                            # DEBUG: Log what we're saving
                            logger.info(
                                f"[TRANSLATION] Saving translation with:")
                            logger.info(f"   - Name: {translated_name}")
                            logger.info(
                                f"   - {len(translated_ingredients)} ingredients")
                            logger.info(f"   - {len(translated_steps)} steps")
                            logger.info(
                                f"   - First ingredient: {translated_ingredients[0] if translated_ingredients else 'NONE'}")
                            logger.info(
                                f"   - First step: {translated_steps[0] if translated_steps else 'NONE'}")

                            translation.save()

                            # DEBUG: Verify it was saved
                            translation.refresh_from_db()
                            logger.info(f"[TRANSLATION] ✅ Verified save:")
                            logger.info(
                                f"   - Ingredients in DB: {len(translation.base_ingredients)}")
                            logger.info(
                                f"   - Steps in DB: {len(translation.base_steps)}")
                            logger.info(
                                f"   - First DB step: {translation.base_steps[0] if translation.base_steps else 'NONE'}")

                            logger.info(
                                f"[TRANSLATION] ✅ Completed immediate translation to {user_language}")
                            logger.info(
                                f"   - Translated {len(translated_ingredients)} ingredients")
                            logger.info(
                                f"   - Translated {len(translated_steps)} steps")

                except Exception as e:
                    logger.error(
                        f"[TRANSLATION] ⚠️ Immediate translation failed: {e}")
                    import traceback
                    traceback.print_exc()

            # Queue background translations for OTHER languages (including English!)
            all_languages = ['en', 'ru', 'he']
            other_languages = [
                lang for lang in all_languages if lang != user_language]

            for lang in other_languages:
                translate_recipe_to_language.delay(str(canonical.id), lang)

            logger.info(
                f"[TRANSLATION] ✅ Queued background translations for: {other_languages}")
        except Exception as e:
            print(f"[TRANSLATION] ⚠️ Could not queue translations: {e}")
            import traceback
            traceback.print_exc()
            # Don't fail recipe creation if translation queuing fails

        return canonical

    @sync_to_async
    def _create_user_fork(self, user, canonical_recipe, rcip_data: Dict):
        """Create user's fork from canonical recipe"""
        from .models import Recipe

        fork = Recipe.objects.create(
            canonical_recipe=canonical_recipe,
            is_fork=True,
            created_by=user,
            name=canonical_recipe.name,
            description=canonical_recipe.description,
            ingredients=canonical_recipe.base_ingredients,
            steps=canonical_recipe.base_steps,
            cuisine=canonical_recipe.cuisine,
            difficulty=canonical_recipe.difficulty,
            diet_labels=canonical_recipe.diet_labels,
            prep_time_minutes=canonical_recipe.prep_time_minutes,
            cook_time_minutes=canonical_recipe.cook_time_minutes,
            total_time_minutes=canonical_recipe.total_time_minutes,
            servings=canonical_recipe.servings,
            user_modifications={},
            recipe_hash=None  # NULL for forks - bypasses unique constraint
        )

        # Update canonical statistics
        canonical_recipe.total_saves += 1
        canonical_recipe.save(update_fields=['total_saves'])

        return fork

    def _calculate_recipe_hash(self, name: str, ingredients: List[Dict]) -> str:
        """Calculate hash based on recipe content for deduplication"""
        # Normalize recipe name (lowercase, remove extra spaces)
        normalized_name = ' '.join(name.lower().split())

        # Sort ingredients by name for consistent hashing
        sorted_ingredients = sorted(
            [ing.get('name', '').lower()
             for ing in ingredients if ing.get('name')]
        )

        # Create hash string
        hash_string = f"{normalized_name}:{','.join(sorted_ingredients)}"

        return hashlib.sha256(hash_string.encode()).hexdigest()

    # ============================================================================
    # RECIPE SEARCH & SCRAPING (NEW: Brave + Firecrawl)
    # ============================================================================

    async def _search_and_scrape_recipes(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        Search and scrape recipes using Brave Search API + Firecrawl
        Falls back to DuckDuckGo + BeautifulSoup if Brave is unavailable
        
        STRATEGY:
        1. Try Brave Search + Firecrawl (PREFERRED)
        2. If Brave fails/unavailable → Fallback to DuckDuckGo + BeautifulSoup
        
        Returns list of dicts with 'url' and 'content'
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"[SEARCH+SCRAPE] Starting for query: '{query}'")

        # STEP 1: Try Brave + Firecrawl first (PREFERRED)
        try:
            from apps.recipes.brave_firecrawl_scraper import BraveFirecrawlScraper

            loop = asyncio.get_event_loop()
            scraper = BraveFirecrawlScraper()

            # Check if Brave API is available
            if scraper.brave_api_key:
                logger.info("[SEARCH+SCRAPE] Using Brave Search + Firecrawl (PRIMARY)")
                
                recipes = await loop.run_in_executor(
                    None,
                    lambda: scraper.search_and_scrape(query, max_results)
                )

                if recipes:
                    logger.info(
                        f"[SEARCH+SCRAPE] ✅ Got {len(recipes)} recipes via Brave+Firecrawl")
                    return recipes
                else:
                    logger.warning(
                        "[SEARCH+SCRAPE] ⚠️ Brave+Firecrawl returned no results, falling back to DuckDuckGo")
            else:
                logger.warning(
                    "[SEARCH+SCRAPE] ⚠️ Brave API key not configured, using DuckDuckGo fallback")
        except Exception as e:
            logger.error(
                f"[SEARCH+SCRAPE] ❌ Brave+Firecrawl failed: {e}, falling back to DuckDuckGo")

        # STEP 2: Fallback to DuckDuckGo + BeautifulSoup
        logger.info(
            "[SEARCH+SCRAPE] Using DuckDuckGo + BeautifulSoup fallback")

        # Search with DuckDuckGo
        urls = await self._search_with_duckduckgo(query, max_results)
        if not urls:
            logger.error("[SEARCH+SCRAPE] ❌ No URLs found")
            return []

        # Scrape with BeautifulSoup
        recipes = []
        for idx, url in enumerate(urls[:max_results], 1):
            logger.info(
                f"[SEARCH+SCRAPE] Scraping {idx}/{len(urls[:max_results])}: {url}")

            scraped_data = await self._scrape_recipe(url)
            if scraped_data and len(scraped_data.get('content') or scraped_data.get('text', '')) > 500:
                recipes.append({
                    'url': url,
                    'content': scraped_data.get('content') or scraped_data.get('text', '')
                })
                logger.info(
                    f"[SEARCH+SCRAPE] ✅ Successfully scraped {idx}/{len(urls[:max_results])}")
            else:
                logger.warning(
                    f"[SEARCH+SCRAPE] ⚠️ Failed to scrape {idx}/{len(urls[:max_results])}")

        logger.info(
            f"[SEARCH+SCRAPE] ✅ Got {len(recipes)} recipes via DuckDuckGo+BeautifulSoup")
        return recipes

    async def _search_with_brave(self, query: str, max_results: int = 5) -> List[str]:
        """Search using Brave Search API (direct)"""
        try:
            import aiohttp
            search_query = f"{query} recipe step by step"

            # Brave Search web endpoint (no API key needed for basic search)
            search_url = f"https://search.brave.com/search?q={requests.utils.quote(search_query)}&source=web"

            print(f"[BRAVE] Searching: {search_query}")

            # Use requests to scrape Brave Search results
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(
                    search_url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Connection': 'keep-alive',
                    },
                    timeout=10
                )
            )

            if response.status_code != 200:
                print(f"[BRAVE] Failed with status {response.status_code}")
                return []

            # Parse HTML to extract recipe URLs
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            urls = []
            # Brave Search uses specific classes for search results
            for result in soup.select('div.snippet[data-type="web"]')[:max_results]:
                link_elem = result.select_one('a[href]')
                if link_elem and link_elem.get('href'):
                    url = link_elem['href']
                    # Filter for recipe sites
                    if any(domain in url.lower() for domain in ['recipe', 'cooking', 'kitchen', 'food', 'chef', 'allrecipes', 'foodnetwork', 'epicurious', 'seriouseats', 'bonappetit']):
                        title_elem = result.select_one('.title')
                        title = title_elem.get_text(
                            strip=True) if title_elem else url
                        urls.append(url)
                        print(f"   {len(urls)}. {title[:60]}...")

            if urls:
                print(f"[BRAVE] ✅ Found {len(urls)} recipe URLs")
                return urls

            # If no filtered URLs, get any URLs
            for result in soup.select('div.snippet[data-type="web"]')[:max_results]:
                link_elem = result.select_one('a[href]')
                if link_elem and link_elem.get('href'):
                    url = link_elem['href']
                    urls.append(url)
                    print(f"   {len(urls)}. {url[:80]}")

            if urls:
                print(f"[BRAVE] ✅ Found {len(urls)} URLs (unfiltered)")
            else:
                print(f"[BRAVE] ⚠️ No results found")

            return urls

        except Exception as e:
            print(f"[BRAVE] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def _search_with_duckduckgo(self, query: str, max_results: int = 5) -> List[str]:
        """Search using DuckDuckGo (primary, free & unlimited)"""
        if DDGS is None:
            print(
                "[DDGS] ⚠️ DDGS not available. Please install: pip install duckduckgo-search")
            return []

        try:
            search_query = f"{query} recipe step by step"
            print(f"[DDGS] Searching: {search_query}")

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(DDGS().text(
                    search_query,
                    max_results=max_results * 2,  # Get more results to filter
                    region='us-en',  # US English region for better recipe results
                    safesearch='moderate'
                ))
            )

            urls = []
            skipped_chinese = 0
            for i, result in enumerate(results, 1):
                url = result.get('href', result.get('link', ''))
                title = result.get('title', '')

                if not url:
                    continue

                # Skip Chinese sites (zhihu, baidu, etc.)
                if any(domain in url.lower() for domain in ['zhihu.com', 'baidu.com', 'bilibili.com', 'weibo.com', '163.com', 'sina.com']):
                    skipped_chinese += 1
                    continue

                # Skip Wikipedia and other non-recipe sites
                skip_domains = [
                    'wikipedia.org', 'wiki', 'amazon', 'youtube', 'pinterest',
                    # News sites
                    't-online.de', 'bild.de', 'spiegel.de', 'focus.de',
                    'news', 'nachrichten',  # Generic news
                    # Social media
                    'facebook.com', 'instagram.com', 'twitter.com', 'tiktok.com',
                    # Non-food sites
                    'reddit.com', 'quora.com'
                ]
                if any(domain in url.lower() for domain in skip_domains):
                    print(f"   [SKIP] Non-recipe site: {url[:60]}...")
                    continue

                # Skip if title contains too many Chinese characters
                chinese_chars = sum(
                    1 for char in title if '\u4e00' <= char <= '\u9fff')
                if chinese_chars > len(title) * 0.3:  # More than 30% Chinese
                    skipped_chinese += 1
                    continue

                # Prioritize recipe sites
                is_recipe_site = any(domain in url.lower() for domain in [
                    'recipe', 'cooking', 'kitchen', 'food', 'chef',
                    'allrecipes', 'foodnetwork', 'epicurious', 'seriouseats',
                    'bonappetit', 'tasty', 'delish', 'yummly', 'simplyrecipes',
                    'cookieandkate', 'budgetbytes', 'thekitchn'
                ])

                if is_recipe_site:
                    print(f"   {i}. ⭐ {title[:60]}...")
                else:
                    print(f"   {i}. {title[:60]}...")

                urls.append(url)

                # Stop after we have enough English results
                if len(urls) >= max_results:
                    break

            if skipped_chinese > 0:
                print(f"[DDGS] Skipped {skipped_chinese} Chinese sites")

            if urls:
                print(f"[DDGS] ✅ Found {len(urls)} English recipe URLs")
            else:
                print(f"[DDGS] ⚠️ No English results found for '{query}'")

            return urls

        except Exception as e:
            print(f"[DDGS] ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def _scrape_recipe(self, url: str) -> Optional[Dict]:
        """Scrape recipe content from URL with better anti-blocking"""
        print(f"[SCRAPE] Scraping: {url}")

        # List of user agents to rotate
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]

        import random

        for attempt in range(2):  # Try twice with different user agents
            try:
                headers = {
                    'User-Agent': random.choice(user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                }

                # Run in executor to avoid blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.get(url, headers=headers,
                                         timeout=15, allow_redirects=True)
                )

                print(f"   [DEBUG] Status code: {response.status_code}")

                if response.status_code == 403 and attempt == 0:
                    print(
                        f"   [RETRY] 403 Forbidden, trying with different user agent...")
                    await asyncio.sleep(1)  # Wait 1 second before retry
                    continue

                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Remove unwanted tags
                for script in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript", "form", "button"]):
                    script.decompose()

                # Try to find recipe content first (common recipe containers)
                recipe_content = None
                for selector in [
                    'article', '.recipe', '#recipe', '.recipe-content',
                    '.recipe-instructions', '.post-content', 'main',
                    '[itemtype*="Recipe"]', '.entry-content'
                ]:
                    recipe_content = soup.select_one(selector)
                    if recipe_content:
                        print(f"   [DEBUG] Found content in: {selector}")
                        break

                # Extract text from recipe content or full page
                if recipe_content:
                    text = recipe_content.get_text(separator='\n', strip=True)
                else:
                    text = soup.get_text(separator='\n', strip=True)
                    print(f"   [DEBUG] Using full page content")

                # Filter meaningful lines
                lines = text.split('\n')
                filtered_lines = [line for line in lines if len(
                    line) > 15 and not line.startswith('×')]

                # Take more lines for better extraction
                text = '\n'.join(filtered_lines[:200])

                print(
                    f"   [OK] Extracted {len(text)} characters from {len(filtered_lines)} lines")

                # Check if we got meaningful content
                if len(text) < 500:
                    print(f"   [WARNING] Content too short: {len(text)} chars")
                    return None

                return {
                    'url': url,
                    'text': text
                }

            except requests.exceptions.Timeout:
                print(f"   [ERROR] Timeout error for {url}")
                return None
            except requests.exceptions.RequestException as e:
                if attempt == 0 and '403' in str(e):
                    print(f"   [RETRY] {e}, trying with different approach...")
                    await asyncio.sleep(1)
                    continue
                print(f"   [ERROR] Request error: {e}")
                return None
            except Exception as e:
                print(f"   [ERROR] Scraping error: {e}")
                import traceback
                traceback.print_exc()
                return None

        print(f"   [FAILED] All scraping attempts failed")
        return None

    async def _validate_and_fix_recipe(self, rcip_recipe: Dict) -> Optional[Dict]:
        """
        Validate recipe quality and fix issues if needed
        Stage 2: Auto-validation (FREE)
        Stage 3: AI re-validation (only if needed)
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(
            f"[VALIDATION] Starting validation for recipe: {rcip_recipe.get('meta', {}).get('name', 'Unknown')}")

        # Stage 2: Auto-validation using free rules
        from apps.recipes.quality_checker import RecipeValidator

        validator = RecipeValidator()

        # Run validation in sync context (uses Django ORM for database loading)
        validation_report = await sync_to_async(validator.validate_recipe)(rcip_recipe)

        logger.info(
            f"[VALIDATION] Confidence: {validation_report['confidence']}%")
        logger.info(f"[VALIDATION] Status: {validation_report['status']}")
        logger.info(
            f"[VALIDATION] Issues found: {len(validation_report['issues'])}")

        # If validation passed, return as-is
        if validation_report['status'] == 'pass':
            logger.info("[VALIDATION] ✅ Recipe passed auto-validation!")
            return rcip_recipe

        # Stage 3: AI re-validation for flagged recipes
        if validation_report['needs_ai_validation']:
            logger.info(
                "[VALIDATION] ⚠️ Recipe flagged - attempting AI fix...")

            from apps.recipes.ai_validator import AIRecipeValidator

            ai_validator = AIRecipeValidator()
            fixed_recipe = ai_validator.fix_recipe(
                rcip_recipe, validation_report)

            if fixed_recipe:
                logger.info("[VALIDATION] ✅ Recipe fixed by AI")
                logger.info(
                    f"[VALIDATION] Fixed recipe has {len(fixed_recipe.get('ingredients', []))} ingredients and {len(fixed_recipe.get('steps', []))} steps")

                # IMPORTANT: Preserve the original recipe structure and ALL metadata
                original_meta = rcip_recipe.get('meta', {})

                # AI validator returns wrong format (name at root, not in meta)
                # We need to fix this and preserve ALL original metadata
                if 'meta' not in fixed_recipe or not isinstance(fixed_recipe.get('meta'), dict):
                    fixed_recipe['meta'] = {}

                # If AI put name at root level, move it to meta
                if 'name' in fixed_recipe and 'name' not in fixed_recipe['meta']:
                    fixed_recipe['meta']['name'] = fixed_recipe.pop('name')
                    logger.info(
                        f"[VALIDATION] Moved name from root to meta: {fixed_recipe['meta']['name']}")

                # Preserve ALL original metadata (AI validator doesn't return most of it)
                for key, value in original_meta.items():
                    if key not in fixed_recipe['meta']:
                        fixed_recipe['meta'][key] = value
                        logger.info(
                            f"[VALIDATION] Preserved meta.{key} from original")

                # Ensure name is preserved
                if not fixed_recipe['meta'].get('name') and original_meta.get('name'):
                    fixed_recipe['meta']['name'] = original_meta['name']
                    logger.info(
                        f"[VALIDATION] Restored original name: {original_meta['name']}")

                # Preserve other RCIP structure fields
                for key in ['rcip_version', 'id', 'extensions', 'base_ingredients', 'base_steps']:
                    if key in rcip_recipe and key not in fixed_recipe:
                        fixed_recipe[key] = rcip_recipe[key]

                # Re-validate the fixed recipe
                revalidation = await sync_to_async(validator.validate_recipe)(fixed_recipe)
                logger.info(
                    f"[VALIDATION] Re-validation confidence: {revalidation['confidence']}%")

                # Lower threshold for fixed recipes
                if revalidation['confidence'] >= 60:
                    logger.info("[VALIDATION] ✅ Fixed recipe accepted")
                    return fixed_recipe
                else:
                    logger.warning(
                        "[VALIDATION] ⚠️ AI fix insufficient, using best available")
                    # Return the better of the two
                    if revalidation['confidence'] > validation_report['confidence']:
                        logger.info(
                            "[VALIDATION] Using AI-fixed recipe (better confidence)")
                        return fixed_recipe
                    else:
                        logger.info(
                            "[VALIDATION] Using original recipe (better confidence)")
                        return rcip_recipe
            else:
                logger.warning(
                    "[VALIDATION] ⚠️ AI could not fix recipe, using original")
                logger.info(
                    f"[VALIDATION] Original recipe has {len(rcip_recipe.get('ingredients', []))} ingredients and {len(rcip_recipe.get('steps', []))} steps")
                # Still return original - better than nothing
                return rcip_recipe

        # Recipe has warnings but might be usable
        if validation_report['confidence'] >= 40:
            logger.info("[VALIDATION] ⚠️ Recipe has warnings but usable")
            return rcip_recipe

        # Recipe is too poor quality
        logger.error("[VALIDATION] ❌ Recipe quality too poor")
        return None

    async def _convert_to_rcip(
        self,
        scraped_data: Dict,
        recipe_name: str,
        user_preferences: Dict = None
    ) -> Optional[Dict]:
        """Convert scraped recipe to RCIP format using Groq LLM"""
        print(f"[AI] Converting to RCIP format for recipe: {recipe_name}")

        # If no Groq client, use fallback
        if not self.groq_client:
            print("   [WARNING] No Groq AI client available, using fallback parser")
            print("   [WARNING] Install Groq: pip install groq")
            print("   [WARNING] Set GROQ_API_KEY environment variable")
            return self._fallback_conversion(scraped_data, recipe_name)

        try:
            # Get user preferences
            user_language = user_preferences.get(
                'language', 'en') if user_preferences else 'en'
            user_unit_system = user_preferences.get(
                'unit_system', 'metric') if user_preferences else 'metric'

            # First, extract structured data using LLM
            prompt = f"""You are a professional recipe extraction expert. Extract the COMPLETE recipe with ALL ingredients and ALL cooking steps.

═══════════════════════════════════════════════════════════════
🚨 CRITICAL REQUIREMENT - ENGLISH ONLY OUTPUT 🚨
═══════════════════════════════════════════════════════════════

YOU MUST output EVERYTHING in ENGLISH language ONLY.

❌ FORBIDDEN:
- Russian (Cyrillic): Доведите, кипения, приготовить, etc.
- Hebrew: לחתוך, לבשל, להוסיף, etc.
- Any other non-English characters
- Mixed language: "Bring воду to a boil" ❌
- Partial translations: "Довести water до boil" ❌

✅ REQUIRED:
- ALL text must be in English: "Bring water to a boil" ✅
- If the webpage is in Russian/Hebrew/other language, TRANSLATE TO ENGLISH first
- Every word must be recognizable English

LANGUAGE VERIFICATION:
Before responding, verify:
1. ✓ All ingredient names are English
2. ✓ All step instructions are English  
3. ✓ No Cyrillic (Russian) characters
4. ✓ No Hebrew characters
5. ✓ No mixed-language text

═══════════════════════════════════════════════════════════════

Search Query: {recipe_name}

Webpage Content:
{scraped_data.get('content') or scraped_data.get('text', '')[:4000]}

CRITICAL RULES:

RECIPE TITLE:
- Extract the EXACT title from the webpage
- If the webpage says "Classic Spaghetti Carbonara", use that exact title
- If title is in another language, TRANSLATE IT TO ENGLISH
- DO NOT use the search query as the title
- The title should be the recipe's real name from the webpage

INGREDIENTS - FORMAT STRICTLY AS:
- quantity unit ingredient_name
- Examples: "200g flour", "2 eggs", "1 tsp salt", "100ml milk", "400g spaghetti"
- NEVER write "as needed", "to taste", "optional" - if no specific quantity, skip that ingredient
- NEVER write "1 as needed" or similar vague amounts
- ONLY include ingredients with SPECIFIC, MEASURABLE quantities
- Each line must be ONE ingredient with quantity + unit + name
- OUTPUT IN ENGLISH (translate if source is in another language)

COOKING STEPS - FORMAT STRICTLY AS:
- Extract ALL steps from start to finish
- One action per step
- Number each step: 1., 2., 3., etc.
- Typical recipes have 10-20 steps
- DO NOT summarize or combine steps
- OUTPUT IN ENGLISH (translate if source is in another language)

FORBIDDEN:
- NO "as needed", "to taste", "optional" ingredients
- NO explanations like "After analyzing..." or "I found..."
- NO commentary or analysis
- NO duplicate ingredients
- NO vague quantities
- NO non-English words (Russian, Hebrew, etc.)
- JUST the recipe data with SPECIFIC amounts in ENGLISH

OUTPUT FORMAT (NOTHING ELSE):

TITLE: [Extract exact recipe title from webpage, IN ENGLISH]

INGREDIENTS:
- 500g all-purpose flour
- 3 large eggs
- 250ml milk

STEPS:
1. [First step in English]
2. [Second step in English]
...

START YOUR RESPONSE WITH "TITLE:" - NOTHING BEFORE IT.
REMEMBER: ALL OUTPUT MUST BE IN ENGLISH LANGUAGE ONLY!"""

            # Use Gemini Flash 2.5 for extraction (better rate limits than Groq)
            try:
                import google.generativeai as genai

                # Configure Gemini
                api_key = getattr(settings, 'GEMINI_API_KEY', None)
                if not api_key:
                    print("[AI] ⚠️ No Gemini API key, falling back to Groq")
                    raise ImportError("No Gemini API key")

                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.0-flash-lite')

                # Run in executor
                loop = asyncio.get_event_loop()
                gemini_response = await loop.run_in_executor(
                    None,
                    lambda: model.generate_content(
                        prompt,
                        generation_config={
                            'temperature': 0.1,
                            'max_output_tokens': 3000,
                        }
                    )
                )

                response = gemini_response.text
                print(
                    f"   [GEMINI] ✅ Received response: {len(response)} characters")

            except Exception as gemini_error:
                print(
                    f"   [GEMINI] ⚠️ Failed: {gemini_error}, falling back to Groq")

                # Fallback to Groq if Gemini fails
                if not self.groq_client:
                    print(f"   [AI] ❌ No Groq client available either")
                    return None

                loop = asyncio.get_event_loop()
                chat_completion = await loop.run_in_executor(
                    None,
                    lambda: self.groq_client.chat.completions.create(
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a professional recipe extraction expert. Extract the COMPLETE recipe with ALL ingredients and ALL cooking steps. Never skip steps or summarize. Always output in English - we will translate later."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        model=self.model,
                        temperature=0.1,
                        max_tokens=3000
                    )
                )

                response = chat_completion.choices[0].message.content
                print(
                    f"   [GROQ] ✅ Received response: {len(response)} characters")

            print(f"   [AI] Response preview: {response[:200]}...")

            # Strip any text before "TITLE:" (AI sometimes adds explanation)
            if 'TITLE:' in response:
                response = 'TITLE:' + response.split('TITLE:', 1)[1]
                print(f"   [AI] ✅ Cleaned response, starts with TITLE")
            else:
                print(f"   [AI] ⚠️ Response doesn't contain 'TITLE:' marker")
                print(f"   [AI] Full response: {response[:1000]}...")
                print(f"   [AI] Falling back to local parser")
                return self._fallback_conversion(scraped_data, recipe_name)

            # Parse LLM response - now includes TITLE
            if 'INGREDIENTS:' not in response or 'STEPS:' not in response:
                print(f"   [AI] ⚠️ Missing INGREDIENTS or STEPS markers")
                print(f"   [AI] Falling back to local parser")
                return self._fallback_conversion(scraped_data, recipe_name)

            # Extract title
            title_section = response.split('INGREDIENTS:')[0]
            extracted_title = title_section.replace('TITLE:', '').strip()

            print(f"   [AI] DEBUG: Raw title section: '{title_section[:100]}'")
            print(f"   [AI] DEBUG: Extracted title: '{extracted_title}'")
            print(f"   [AI] DEBUG: Search query: '{recipe_name}'")

            # Validate title
            if not extracted_title or len(extracted_title) > 200 or extracted_title.lower() == recipe_name.lower():
                # AI failed to extract a good title, use user's search query
                extracted_title = recipe_name.title()  # Capitalize properly
                print(
                    f"   [AI] ⚠️ Using search query as title: '{extracted_title}'")
            else:
                print(f"   [AI] ✅ Using extracted title: '{extracted_title}'")

            # Parse ingredients and steps
            parts = response.split('STEPS:')
            if len(parts) != 2:
                print(
                    f"   [AI] ⚠️ Could not parse LLM response - got {len(parts)} parts instead of 2")
                print(f"   [AI] Response preview: {response[:500]}...")
                print(f"   [AI] Falling back to local parser")
                return self._fallback_conversion(scraped_data, recipe_name)

            ingredients_section = parts[0].split('INGREDIENTS:')[1].strip()
            steps_text = parts[1].strip()
            ingredients_text = ingredients_section

            print(f"   [RCIP] Converting to RCIP format...")
            print(
                f"   [RCIP] Ingredients: {len(ingredients_text.split(chr(10)))} lines")
            print(f"   [RCIP] Steps: {len(steps_text.split(chr(10)))} lines")

            # DEBUG: Show first 3 ingredient lines
            ing_lines = ingredients_text.split('\n')[:3]
            print(f"   [RCIP] First 3 ingredient lines:")
            for i, line in enumerate(ing_lines, 1):
                print(f"      {i}. {line}")

            # Convert using RCIP converter
            rcip_recipe = self.rcip_converter.convert(
                name=extracted_title,  # Use AI-extracted title, not search query
                ingredients_text=ingredients_text,
                steps_text=steps_text,
                source_url=scraped_data['url']
            )
            print(f"   [RCIP] ✅ RCIP conversion successful")
            print(
                f"   [RCIP] Recipe has {len(rcip_recipe.get('ingredients', []))} ingredients and {len(rcip_recipe.get('steps', []))} steps")
            # NEW DEBUG - check correct path
            print(
                f"   [RCIP] Recipe name (meta): '{rcip_recipe.get('meta', {}).get('name', 'NO NAME IN META')}'")
            print(
                # Debug: show what title we used
                f"   [RCIP] Title used: '{extracted_title}'")

            # DEBUG: Log first few steps
            if rcip_recipe.get('steps'):
                print(f"   [RCIP] First 3 steps preview:")
                for i, step in enumerate(rcip_recipe.get('steps', [])[:3], 1):
                    step_text = step.get('instruction') or step.get(
                        'text') or str(step)
                    print(f"      Step {i}: {step_text[:80]}...")
            else:
                print(f"   [RCIP] ⚠️ No steps found in RCIP conversion!")
                print(f"   [RCIP] Steps text was: {steps_text[:200]}...")

            # Enhance with AI analysis
            print(f"   [ANALYZE] Estimating times...")
            times = self.recipe_analyzer.estimate_times(
                rcip_recipe['steps'],
                rcip_recipe['ingredients']
            )
            rcip_recipe['meta'].update(times)
            print(f"   [ANALYZE] ✅ Times estimated: {times}")

            # Detect diet labels
            diet_labels = self.recipe_analyzer.detect_diet_labels(
                rcip_recipe['ingredients'])
            rcip_recipe['meta']['diet_labels'] = diet_labels

            # Detect allergens
            allergens = self.recipe_analyzer.detect_allergens(
                rcip_recipe['ingredients'])
            rcip_recipe['meta']['allergens'] = allergens
            print(
                f"   [ANALYZE] ✅ Allergens detected: {allergens if allergens else 'none'}")

            # Estimate difficulty
            difficulty = self.recipe_analyzer.estimate_difficulty(
                rcip_recipe['steps'],
                rcip_recipe['ingredients']
            )
            rcip_recipe['meta']['difficulty'] = difficulty

            # NEW: Enrich with IML data
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"[IML] Starting IML enrichment...")
                rcip_recipe = await self._enrich_recipe_with_iml(rcip_recipe, user_preferences)
                logger.info(f"[IML] ✅ IML enrichment successful")
                logger.info(
                    f"[IML] Recipe now has {len(rcip_recipe.get('base_ingredients', []))} base_ingredients")
            except Exception as iml_error:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"[IML] ⚠️ IML enrichment failed: {iml_error}")
                import traceback
                logger.error(traceback.format_exc())
                print(f"   [IML] Continuing without IML data...")

            # NEW: Translate to all languages
            try:
                user_language = user_preferences.get(
                    'language', 'en') if user_preferences else 'en'
                print(
                    f"   [TRANSLATE] Starting translation to {user_language}...")
                rcip_recipe = await self._translate_recipe(rcip_recipe, user_language)
                print(f"   [TRANSLATE] ✅ Translation successful")
            except Exception as translate_error:
                print(
                    f"   [TRANSLATE] ⚠️ Translation failed: {translate_error}")
                print(f"   [TRANSLATE] Continuing without translation...")

            print(f"   [OK] ✅ Conversion successful!")
            return rcip_recipe

        except Exception as e:
            print(
                f"   [ERROR] ❌ AI conversion failed with exception: {type(e).__name__}: {e}")
            import traceback
            print("   [ERROR] Full traceback:")
            traceback.print_exc()
            print(f"   [FALLBACK] Attempting local parser...")
            fallback_result = self._fallback_conversion(
                scraped_data, recipe_name)
            if fallback_result:
                print(f"   [FALLBACK] ✅ Local parser succeeded")
            else:
                print(f"   [FALLBACK] ❌ Local parser also failed")
            return fallback_result

    def _fallback_conversion(self, scraped_data: Dict, recipe_name: str) -> Optional[Dict]:
        """Fallback: Use local RCIP converter without AI"""
        try:
            scraped_text = scraped_data.get(
                'content') or scraped_data.get('text', '')
            ingredients_text, steps_text = self._extract_structured_text(
                scraped_text)

            if ingredients_text and steps_text:
                rcip_recipe = self.rcip_converter.convert(
                    name=recipe_name,
                    ingredients_text=ingredients_text,
                    steps_text=steps_text,
                    source_url=scraped_data['url']
                )

                # Enhance with analysis
                times = self.recipe_analyzer.estimate_times(
                    rcip_recipe['steps'],
                    rcip_recipe['ingredients']
                )
                rcip_recipe['meta'].update(times)

                diet_labels = self.recipe_analyzer.detect_diet_labels(
                    rcip_recipe['ingredients'])
                rcip_recipe['meta']['diet_labels'] = diet_labels

                # Detect allergens
                allergens = self.recipe_analyzer.detect_allergens(
                    rcip_recipe['ingredients'])
                rcip_recipe['meta']['allergens'] = allergens

                difficulty = self.recipe_analyzer.estimate_difficulty(
                    rcip_recipe['steps'],
                    rcip_recipe['ingredients']
                )
                rcip_recipe['meta']['difficulty'] = difficulty

                return rcip_recipe

            return None
        except Exception as e:
            print(f"   [ERROR] Fallback conversion failed: {e}")
            return None

    def _extract_structured_text(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract ingredients and steps from raw text"""
        import re

        lines = text.split('\n')
        ingredients = []
        steps = []
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            line_lower = line.lower()

            # Detect sections
            if any(word in line_lower for word in ['ingredient', 'ingredients', 'what you need', 'you will need']):
                current_section = 'ingredients'
                continue
            elif any(word in line_lower for word in ['instruction', 'instructions', 'method', 'step', 'steps', 'directions', 'preparation']):
                current_section = 'steps'
                continue

            # Add to sections
            if current_section == 'ingredients':
                if re.match(r'^\d+[\s\w]+', line) or re.match(r'^[-•*]', line) or len(line) > 5:
                    ingredients.append(line)
            elif current_section == 'steps':
                if re.match(r'^\d+[\.)]', line) or len(line) > 30:
                    steps.append(line)

        ingredients_text = '\n'.join(
            # Limit to 50 ingredients
            ingredients[:50]) if ingredients else None
        steps_text = '\n'.join(
            steps[:30]) if steps else None  # Limit to 30 steps

        return ingredients_text, steps_text


class RecipeDeduplicationService:
    """Service for handling recipe deduplication and versioning"""

    @staticmethod
    def find_duplicate_recipes(recipe_data: Dict) -> List['Recipe']:
        """Find existing recipes that might be duplicates"""
        from .models import Recipe
        import hashlib

        # Calculate hash
        name_normalized = ' '.join(recipe_data['meta']['name'].lower().split())
        ingredients_sorted = sorted([
            ing.get('name', '').lower()
            for ing in recipe_data.get('ingredients', [])
        ])
        hash_string = f"{name_normalized}:{','.join(ingredients_sorted)}"
        recipe_hash = hashlib.sha256(hash_string.encode()).hexdigest()

        # Find existing recipes with same hash
        return Recipe.objects.filter(recipe_hash=recipe_hash).order_by('-version')

    @staticmethod
    def should_create_new_version(existing_recipe: 'Recipe', new_recipe_data: Dict) -> bool:
        """Determine if we should create a new version or use existing"""
        # Compare ingredients count
        existing_count = len(existing_recipe.ingredients)
        new_count = len(new_recipe_data.get('ingredients', []))

        # If significantly different ingredient count, it's a different recipe
        if abs(existing_count - new_count) > 3:
            return True

        # Compare steps count
        existing_steps = len(existing_recipe.steps)
        new_steps = len(new_recipe_data.get('steps', []))

        if abs(existing_steps - new_steps) > 2:
            return True

        # Default: use existing recipe
        return False

    @staticmethod
    def get_similarity_score(recipe1: 'Recipe', recipe2_data: Dict) -> float:
        """Calculate similarity score between two recipes(0-1)"""
        score = 0.0

        # Name similarity (30%)
        name1 = recipe1.name.lower()
        name2 = recipe2_data['meta']['name'].lower()
        if name1 == name2:
            score += 0.3
        elif name1 in name2 or name2 in name1:
            score += 0.15

        # Ingredients overlap (40%)
        ing1 = set(ing.get('name', '').lower() for ing in recipe1.ingredients)
        ing2 = set(ing.get('name', '').lower()
                   for ing in recipe2_data.get('ingredients', []))
        if ing1 and ing2:
            overlap = len(ing1 & ing2) / len(ing1 | ing2)
            score += overlap * 0.4

        # Steps count similarity (30%)
        steps1 = len(recipe1.steps)
        steps2 = len(recipe2_data.get('steps', []))
        if steps1 and steps2:
            steps_sim = 1 - abs(steps1 - steps2) / max(steps1, steps2)
            score += steps_sim * 0.3

        return score
