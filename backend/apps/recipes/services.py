"""
Recipe Agent Service - AI-powered recipe search, scraping, and conversion
WITH DEDUPLICATION SUPPORT
"""


from apps.core.ingredient_mapper import IngredientMapper
from apps.core.unit_converter import UnitConverter
from apps.core.nutrition_calculator import NutritionCalculator
from apps.core.translation_service import TranslationService
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

    def __init__(self):
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
        print("[ENRICH] Starting IML enrichment...")

        user_language = user_preferences.get(
            'language', 'en') if user_preferences else 'en'
        user_unit_system = user_preferences.get(
            'unit_system', 'metric') if user_preferences else 'metric'

        # Step 1: Map ingredients to IML keys
        enriched_ingredients = []
        for ingredient in rcip_recipe.get('ingredients', []):
            ingredient_text = ingredient.get('name', '')
            quantity = ingredient.get('quantity')
            unit = ingredient.get('unit', '')

            # Map to IML
            match_result = self.ingredient_mapper.map(
                text=f"{quantity}{unit} {ingredient_text}" if quantity and unit else ingredient_text,
                language=user_language,
                user_unit_system=user_unit_system
            )

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

        nutrition = self.nutrition_calculator.calculate_recipe_nutrition(
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

        # Step 4: Prepare base_ingredients for frontend (translated)
        base_ingredients = self._prepare_base_ingredients(
            enriched_ingredients, user_language
        )
        rcip_recipe['base_ingredients'] = base_ingredients

        # Step 5: Prepare base_steps (clean, translated)
        base_steps = self._prepare_base_steps(
            rcip_recipe.get('steps', []), user_language
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
        base_ingredients = []

        for ing in enriched_ingredients:
            # Get translated name if available
            display_name = ing.get('display_name', {})
            if isinstance(display_name, dict):
                name = display_name.get(language, ing.get('name', ''))
            else:
                name = ing.get('name', '')

            # Skip empty or very short names
            if not name or len(name.strip()) < 2:
                continue

            # Skip "as needed" without actual ingredient
            name_lower = name.lower()
            if name_lower in ['as needed', 'to taste', 'optional']:
                continue

            # Format quantity
            quantity = ing.get('quantity')
            if quantity:
                if isinstance(quantity, (int, float)):
                    amount = str(int(quantity)) if quantity == int(
                        quantity) else str(quantity)
                else:
                    amount = str(quantity)
            else:
                amount = ''

            base_ingredients.append({
                'amount': amount,
                'unit': ing.get('unit', ''),
                'name': name,
                'ingredient_key': ing.get('ingredient_key'),
                'original': ing.get('original', name)
            })

        return base_ingredients

    def _prepare_base_steps(self, steps: List[Dict], language: str) -> List[Dict]:
        """
        Convert steps to frontend-friendly format, filtering out non-cooking content

        Args:
            steps: Recipe steps from RCIP
            language: User's preferred language

        Returns:
            List of clean cooking steps
        """
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
            # Get step text
            if isinstance(step, dict):
                text = step.get('instruction') or step.get(
                    'text') or step.get('step', '')
                time_minutes = step.get('time_minutes')
            else:
                text = str(step)
                time_minutes = None

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

            # Build step
            clean_step = {
                'text': text,
                'step_number': step_number
            }

            if time_minutes:
                clean_step['time_minutes'] = time_minutes

            base_steps.append(clean_step)
            step_number += 1

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

        # STEP 1: Check if canonical recipe already exists
        normalized_name = self._normalize_recipe_name(user_query)
        existing_canonical = await self._find_existing_canonical(normalized_name)

        if existing_canonical:
            print(
                f"[REUSE] Found existing canonical: {existing_canonical.name}")

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

        # STEP 2: Recipe doesn't exist - search and create new canonical
        print(f"[SEARCH] No canonical found, searching web...")
        recipe_urls = await self._search_recipes(user_query)
        if not recipe_urls:
            return False, None, "No recipes found for your query"

        # STEP 3: Scrape best recipe (try up to 5 URLs)
        scraped_data = None
        for i, url in enumerate(recipe_urls[:5], 1):
            print(f"[SCRAPE] Trying URL {i}/5...")
            scraped_data = await self._scrape_recipe(url)
            if scraped_data and len(scraped_data.get('text', '')) > 500:
                print(f"[SCRAPE] ✅ Successfully scraped from URL {i}")
                break
            else:
                print(f"[SCRAPE] ❌ URL {i} failed or had insufficient content")

        if not scraped_data:
            print(
                f"[ERROR] Failed to scrape any of the {len(recipe_urls[:5])} URLs")
            return False, None, "Could not extract recipe from websites. Please try a different recipe or check your internet connection."

        # STEP 4: Convert to RCIP format using AI
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
            return False, None, "Failed to convert recipe to standard format. The recipe content may be too complex or incomplete. Please try a different recipe."

        # STEP 5: Create canonical recipe
        canonical = await self._create_canonical_recipe(
            rcip_recipe,
            source_type='ai_generated',
            original_creator=user
        )

        # STEP 6: Create user fork
        user_fork = await self._create_user_fork(user, canonical, rcip_recipe)

        print(f"[SUCCESS] Created new canonical recipe: {canonical.name}")

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
        """Check if canonical recipe exists (by normalized name or similar)"""
        from .models import CanonicalRecipe
        from django.db.models import Q

        # Try exact normalized name match first
        canonical = CanonicalRecipe.objects.filter(
            name__iexact=normalized_name,
            is_published=True
        ).first()

        if canonical:
            print(f"[MATCH] Exact match found: {canonical.name}")
            return canonical

        # Improved partial match: require at least 70% of words to match
        words = normalized_name.split()
        if len(words) >= 2:
            # Search for recipes containing at least the first 2 significant words
            similar = CanonicalRecipe.objects.filter(
                Q(name__icontains=words[0]) & Q(name__icontains=words[1]),
                is_published=True
            ).first()

            if similar:
                print(
                    f"[MATCH] Potential match found: {similar.name} (searched for: {normalized_name})")

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
                    return None

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
            # Ensure UserRecipe entry exists
            UserRecipe.objects.get_or_create(
                user=user,
                recipe=existing_fork,
                defaults={
                    'saved_at': timezone.now(),
                    'is_archived': False
                }
            )
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

        meta = rcip_data.get('meta', {})

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
    # RECIPE SEARCH & SCRAPING (Existing Methods)
    # ============================================================================

    async def _search_recipes(self, query: str, max_results: int = 5) -> List[str]:
        """Search for recipes using DuckDuckGo"""
        print(f"[SEARCH] Searching for: '{query}'")

        if DDGS is None:
            print("[ERROR] DDGS not available. Please install: pip install ddgs")
            return []

        try:
            search_query = f"{query} recipe step by step"

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(DDGS().text(
                    search_query, max_results=max_results, region='wt-wt'))
            )

            urls = []
            for i, result in enumerate(results, 1):
                url = result.get('href', result.get('link', ''))
                title = result.get('title', '')
                print(f"   {i}. {title}")
                if url:
                    urls.append(url)

            return urls

        except Exception as e:
            print(f"[ERROR] Search error: {e}")
            return []

    async def _scrape_recipe(self, url: str) -> Optional[Dict]:
        """Scrape recipe content from URL"""
        print(f"[SCRAPE] Scraping: {url}")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, headers=headers,
                                     timeout=15, allow_redirects=True)
            )

            print(f"   [DEBUG] Status code: {response.status_code}")
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
            print(f"   [ERROR] Request error: {e}")
            return None
        except Exception as e:
            print(f"   [ERROR] Scraping error: {e}")
            import traceback
            traceback.print_exc()
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
            prompt = f"""You are extracting a recipe from a webpage. The webpage may contain comments, reviews, ads, and other text.

Recipe Name: {recipe_name}
Language: {user_language}
Units: {user_unit_system}

Webpage Text:
{scraped_data['text'][:3000]}

TASK:
Extract ONLY the actual recipe ingredients and cooking instructions. Ignore everything else (comments, reviews, blog posts, nutrition info, personal stories, ads).

INGREDIENTS FORMAT:
- Must have quantity AND unit AND ingredient name
- Example: "2 cups flour" or "200g sugar" or "3 eggs"
- If no quantity is given, skip that ingredient
- Use {user_unit_system} units ({'metric (g, kg, ml, L, pieces)' if user_unit_system == 'metric' else 'imperial (oz, lb, cups, tbsp, tsp)'})

STEPS FORMAT:
- Only actual cooking actions (Mix, Heat, Bake, Add, etc.)
- Must be instructions that tell you HOW to cook
- Skip: comments, reviews, tips, suggestions, personal stories, nutrition info
- Maximum 20 steps

Return ONLY this format (no extra text):

INGREDIENTS:
- 200g all-purpose flour
- 2 large eggs
- 100ml milk

STEPS:
1. Preheat oven to 180°C
2. Mix flour and eggs in a bowl
3. Add milk and stir until smooth
4. Bake for 25 minutes"""

            # Run in executor
            loop = asyncio.get_event_loop()
            chat_completion = await loop.run_in_executor(
                None,
                lambda: self.groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are a recipe extraction expert. Extract ONLY recipe ingredients (with quantities) and cooking instructions from webpages. Ignore comments, reviews, ads, and blog text. Output in {user_language} using {user_unit_system} units."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=self.model,
                    temperature=0.2,
                    max_tokens=2000
                )
            )

            response = chat_completion.choices[0].message.content
            print(f"   [AI] ✅ Received response: {len(response)} characters")
            print(f"   [AI] Response preview: {response[:200]}...")

            # Parse LLM response
            parts = response.split('STEPS:')
            if len(parts) != 2:
                print(
                    f"   [AI] ⚠️ Could not parse LLM response - got {len(parts)} parts instead of 2")
                print(f"   [AI] Response preview: {response[:500]}...")
                print(f"   [AI] Falling back to local parser")
                return self._fallback_conversion(scraped_data, recipe_name)

            ingredients_text = parts[0].replace('INGREDIENTS:', '').strip()
            steps_text = parts[1].strip()

            print(f"   [RCIP] Converting to RCIP format...")
            print(
                f"   [RCIP] Ingredients: {len(ingredients_text.split(chr(10)))} lines")
            print(f"   [RCIP] Steps: {len(steps_text.split(chr(10)))} lines")

            # Convert using RCIP converter
            rcip_recipe = self.rcip_converter.convert(
                name=recipe_name,
                ingredients_text=ingredients_text,
                steps_text=steps_text,
                source_url=scraped_data['url']
            )
            print(f"   [RCIP] ✅ RCIP conversion successful")
            print(
                f"   [RCIP] Recipe has {len(rcip_recipe.get('ingredients', []))} ingredients and {len(rcip_recipe.get('steps', []))} steps")

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

            # Estimate difficulty
            difficulty = self.recipe_analyzer.estimate_difficulty(
                rcip_recipe['steps'],
                rcip_recipe['ingredients']
            )
            rcip_recipe['meta']['difficulty'] = difficulty

            # NEW: Enrich with IML data
            try:
                print(f"   [IML] Starting IML enrichment...")
                rcip_recipe = await self._enrich_recipe_with_iml(rcip_recipe, user_preferences)
                print(f"   [IML] ✅ IML enrichment successful")
            except Exception as iml_error:
                print(f"   [IML] ⚠️ IML enrichment failed: {iml_error}")
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
            ingredients_text, steps_text = self._extract_structured_text(
                scraped_data['text'])

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
