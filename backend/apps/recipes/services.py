"""
Recipe Agent Service - AI-powered recipe search, scraping, and conversion
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

# Import RCIP converter
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class RecipeAgentService:
    """Service for searching, scraping, and converting recipes using AI"""

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
        user_preferences: Dict = None
    ) -> Tuple[bool, Optional[Dict], str]:
        """
        Main method: Search, scrape, convert recipe from user query

        Args:
            user_query: What user wants to cook (e.g., "Italian pasta carbonara")
            user_preferences: User dietary restrictions, allergies, etc.

        Returns:
            (success: bool, recipe_data: Dict, message: str)
        """
        print(f"[RECIPE AGENT] Processing query: '{user_query}'")

        # Step 1: Search for recipes
        recipe_urls = await self._search_recipes(user_query)
        if not recipe_urls:
            return False, None, "No recipes found for your query"

        # Step 2: Scrape best recipe
        scraped_data = None
        for url in recipe_urls[:3]:  # Try first 3 URLs
            scraped_data = await self._scrape_recipe(url)
            if scraped_data and len(scraped_data.get('text', '')) > 500:
                break

        if not scraped_data:
            return False, None, "Could not extract recipe from websites"

        # Step 3: Convert to RCIP format using AI
        rcip_recipe = await self._convert_to_rcip(
            scraped_data,
            user_query,
            user_preferences
        )

        if not rcip_recipe:
            return False, None, "Failed to convert recipe to standard format"

        print(
            f"[SUCCESS] Recipe Agent: Successfully processed '{rcip_recipe['meta']['name']}'")
        return True, rcip_recipe, f"Found recipe: {rcip_recipe['meta']['name']}"

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

Return in this exact format:

INGREDIENTS:
- 300g flour
- 2 eggs
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
