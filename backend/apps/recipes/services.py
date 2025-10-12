"""
Recipe Agent Service - AI-powered recipe search, scraping, and conversion
WITH DEDUPLICATION SUPPORT
"""
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

    async def find_and_convert_recipe(
        self,
        user_query: str,
        user,  # Django User object
        user_preferences: Dict = None
    ) -> Tuple[bool, Optional[Dict], str]:
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

        # STEP 3: Scrape best recipe
        scraped_data = None
        for url in recipe_urls[:3]:  # Try first 3 URLs
            scraped_data = await self._scrape_recipe(url)
            if scraped_data and len(scraped_data.get('text', '')) > 500:
                break

        if not scraped_data:
            return False, None, "Could not extract recipe from websites"

        # STEP 4: Convert to RCIP format using AI
        rcip_recipe = await self._convert_to_rcip(
            scraped_data,
            user_query,
            user_preferences
        )

        if not rcip_recipe:
            return False, None, "Failed to convert recipe to standard format"

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
            recipe_hash=hash_string
        )

        print(
            f"[CANONICAL] Created: {canonical.name} (hash: {hash_string[:8]}...)")
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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, headers=headers, timeout=10)
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Remove unwanted tags
            for script in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
                script.decompose()

            # Extract text
            text = soup.get_text(separator='\n', strip=True)

            # Filter meaningful lines
            lines = text.split('\n')
            filtered_lines = [line for line in lines if len(line) > 20]
            # First 150 meaningful lines
            text = '\n'.join(filtered_lines[:150])

            print(f"   [OK] Extracted {len(text)} characters")

            return {
                'url': url,
                'text': text
            }

        except Exception as e:
            print(f"   [ERROR] Scraping error: {e}")
            return None

    async def _convert_to_rcip(
        self,
        scraped_data: Dict,
        recipe_name: str,
        user_preferences: Dict = None
    ) -> Optional[Dict]:
        """Convert scraped recipe to RCIP format using Groq LLM"""
        print(f"[AI] Converting to RCIP format...")

        # If no Groq client, use fallback
        if not self.groq_client:
            print("   [WARNING] No AI available, using fallback parser")
            return self._fallback_conversion(scraped_data, recipe_name)

        try:
            # First, extract structured data using LLM
            prompt = f"""Extract from the recipe text ONLY the list of ingredients and cooking steps.

Recipe Name: {recipe_name}
User Preferences: {user_preferences or 'None'}

Text:
{scraped_data['text'][:3000]}

CRITICAL MEASUREMENT RULES:
1. ALWAYS include specific measurements (never "to taste" or "some")
2. For solids (flour, sugar, meat, vegetables): use WEIGHT (g, kg, oz, lb)
3. For liquids (water, milk, oil, juice): use VOLUME (ml, l, cups, fl oz)
4. For small amounts: use weight (10g butter) not vague terms (tablespoon)
5. For eggs/items: use COUNT (2 eggs, 3 tomatoes)
6. If original recipe is vague, estimate reasonable amounts based on servings

Return in this exact format:

INGREDIENTS:
- 300g flour
- 250ml milk
- 2 eggs
- 100g butter
- 5ml vanilla extract
...

STEPS:
1. Mix flour with eggs
2. Add water
..."""

            # Run in executor
            loop = asyncio.get_event_loop()
            chat_completion = await loop.run_in_executor(
                None,
                lambda: self.groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You extract ingredients and steps from recipes. Be precise and clear. Always separate ingredients and steps clearly."
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

            # Parse LLM response
            parts = response.split('STEPS:')
            if len(parts) != 2:
                print(
                    "   [WARNING] Could not parse LLM response, using local parser")
                return self._fallback_conversion(scraped_data, recipe_name)

            ingredients_text = parts[0].replace('INGREDIENTS:', '').strip()
            steps_text = parts[1].strip()

            # Convert using RCIP converter
            rcip_recipe = self.rcip_converter.convert(
                name=recipe_name,
                ingredients_text=ingredients_text,
                steps_text=steps_text,
                source_url=scraped_data['url']
            )

            # Enhance with AI analysis
            times = self.recipe_analyzer.estimate_times(
                rcip_recipe['steps'],
                rcip_recipe['ingredients']
            )
            rcip_recipe['meta'].update(times)

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

            print(f"   [OK] Conversion successful!")
            return rcip_recipe

        except Exception as e:
            print(f"   [ERROR] AI conversion failed: {e}")
            return self._fallback_conversion(scraped_data, recipe_name)

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
        """Calculate similarity score between two recipes (0-1)"""
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
