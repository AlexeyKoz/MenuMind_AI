"""
AI-Powered Recipe Deduplication Service
Uses Groq (primary) and Gemini (fallback) for semantic duplicate detection
"""

import asyncio
import logging
from typing import List, Optional
from django.conf import settings
from groq import Groq
import google.generativeai as genai

logger = logging.getLogger(__name__)


class RecipeDeduplicationService:
    """
    Universal AI-powered recipe deduplication service
    Used by: Discovery, Shopping List, Manual Creation, Inventory agents

    Strategy:
    1. Fast DB query to get candidate recipes (partial word matching)
    2. AI semantic matching using Groq (primary) or Gemini (fallback)
    3. Returns matched CanonicalRecipe or None
    """

    def __init__(self):
        # Initialize Groq (primary)
        groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
        self.groq_client = Groq(api_key=groq_api_key) if groq_api_key else None
        self.groq_model = "llama-3.1-8b-instant"  # Fast model

        # Initialize Gemini (fallback)
        gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            # Use gemini-2.5-flash-lite for better compatibility
            self.gemini_model = genai.GenerativeModel('gemini-2.5-flash-lite')
        else:
            self.gemini_model = None

        logger.info(
            "[DEDUP] Initialized with Groq (primary) + Gemini (fallback)")

    async def find_duplicate(
        self,
        recipe_name: str,
        ingredients: Optional[List[str]] = None,
        user_language: str = 'en'
    ) -> Optional['CanonicalRecipe']:
        """
        Check if recipe already exists using AI semantic matching

        Args:
            recipe_name: User's search query (e.g., "carbonara")
            ingredients: Optional list of ingredients for stronger matching
            user_language: User's language for multilingual search

        Returns:
            CanonicalRecipe if duplicate found, None otherwise
        """
        logger.info(f"[DEDUP] Checking duplicates for: '{recipe_name}'")

        # STEP 1: Get candidate recipes (fast DB query)
        candidates = await self._get_candidate_recipes(recipe_name)

        if not candidates:
            logger.info("[DEDUP] No candidates found in DB")
            return None

        logger.info(f"[DEDUP] Found {len(candidates)} candidates")

        # STEP 2: AI semantic matching
        duplicate = await self._ai_semantic_match(
            recipe_name,
            ingredients,
            candidates,
            user_language
        )

        return duplicate

    async def _get_candidate_recipes(
        self,
        recipe_name: str,
        max_candidates: int = 10
    ) -> List['CanonicalRecipe']:
        """
        Fast DB query to get potential candidates
        Uses: partial word matching, fuzzy matching for typos, Levenshtein distance
        """
        from django.db.models import Q
        from apps.recipes.models import CanonicalRecipe, RecipeTranslation
        from asgiref.sync import sync_to_async
        import difflib

        # Extract significant words (skip common words)
        stop_words = {'the', 'a', 'an', 'with', 'and', 'or', 'recipe', 'dish',
                      'classic', 'traditional', 'easy', 'simple', 'best', 'homemade'}
        words = [w.lower() for w in recipe_name.split()
                 if w.lower() not in stop_words]

        if not words:
            return []

        logger.info(f"[DEDUP] Search words: {words}")

        # Build query with multiple strategies for better matching
        query = Q()

        # Strategy 1: Exact substring match
        for word in words:
            query |= Q(name__icontains=word)

        # Strategy 2: Fuzzy matching for typos (e.g., "margharita" → "margarita")
        # Check first 3-4 characters AND last 3-4 characters to catch variations
        for word in words:
            if len(word) >= 5:
                # Match recipes containing first 4 chars
                prefix = word[:4]
                query |= Q(name__icontains=prefix)

                # Match recipes containing last 4 chars (helps with "nargharita" → "margherita")
                suffix = word[-4:]
                query |= Q(name__icontains=suffix)
            elif len(word) >= 3:
                # For shorter words, use first 3 chars
                prefix = word[:3]
                query |= Q(name__icontains=prefix)

        # Strategy 3: Also try the full search query as-is
        normalized_query = recipe_name.lower().strip()
        query |= Q(name__icontains=normalized_query)

        # Get candidates from canonical recipes
        @sync_to_async
        def get_canonical_candidates():
            candidates = list(
                CanonicalRecipe.objects.filter(
                    query,
                    is_published=True
                    # Get more for better matching
                    # Increased for better fuzzy matching
                ).select_related()[:max_candidates * 3]
            )
            logger.info(
                f"[DEDUP] Found {len(candidates)} canonical candidates")
            for c in candidates[:5]:  # Log first 5
                logger.info(f"[DEDUP]   - {c.name}")
            return candidates

        candidates = await get_canonical_candidates()

        # Also search in translations
        @sync_to_async
        def get_translation_candidates():
            translations = RecipeTranslation.objects.filter(
                query,
                status='completed',
                canonical_recipe__is_published=True
            ).select_related('canonical_recipe')[:max_candidates]

            # Add translated recipes to candidates (avoid duplicates)
            candidate_ids = {c.id for c in candidates}
            additional = []
            for trans in translations:
                if trans.canonical_recipe.id not in candidate_ids:
                    additional.append(trans.canonical_recipe)
                    candidate_ids.add(trans.canonical_recipe.id)
                    logger.info(
                        f"[DEDUP]   - {trans.canonical_recipe.name} (from translation)")
            return additional

        additional_candidates = await get_translation_candidates()
        candidates.extend(additional_candidates)

        # STRATEGY 4: Use difflib for fuzzy string matching on candidate names
        # This catches typos like "nargharita" → "margherita"
        @sync_to_async
        def get_fuzzy_matches():
            # Get all published recipes for fuzzy matching
            all_recipes = list(
                CanonicalRecipe.objects.filter(
                    is_published=True
                ).values_list('id', 'name')[:500]  # Limit for performance
            )

            fuzzy_matches = []
            search_lower = recipe_name.lower()

            for recipe_id, recipe_name_db in all_recipes:
                recipe_lower = recipe_name_db.lower()

                # Calculate similarity ratio (0.0 to 1.0)
                ratio = difflib.SequenceMatcher(
                    None, search_lower, recipe_lower).ratio()

                # Also check each word individually
                for search_word in words:
                    for recipe_word in recipe_lower.split():
                        word_ratio = difflib.SequenceMatcher(
                            None, search_word, recipe_word).ratio()
                        if word_ratio > ratio:
                            ratio = word_ratio

                # If similarity is high (>= 0.75), it's likely a typo match
                if ratio >= 0.75:
                    fuzzy_matches.append((recipe_id, recipe_name_db, ratio))

            # Sort by similarity (highest first)
            fuzzy_matches.sort(key=lambda x: x[2], reverse=True)

            if fuzzy_matches:
                logger.info(f"[DEDUP] Fuzzy matches found:")
                for recipe_id, name, ratio in fuzzy_matches[:5]:
                    logger.info(
                        f"[DEDUP]   - {name} (similarity: {ratio:.2f})")

            return fuzzy_matches[:max_candidates]

        fuzzy_matches = await get_fuzzy_matches()

        # Add fuzzy matches to candidates
        if fuzzy_matches:
            candidate_ids = {c.id for c in candidates}

            @sync_to_async
            def get_fuzzy_recipes():
                additional = []
                for recipe_id, name, ratio in fuzzy_matches:
                    if recipe_id not in candidate_ids:
                        recipe = CanonicalRecipe.objects.filter(
                            id=recipe_id).first()
                        if recipe:
                            additional.append(recipe)
                            candidate_ids.add(recipe_id)
                return additional

            additional_fuzzy = await get_fuzzy_recipes()
            candidates.extend(additional_fuzzy)

        # Return more candidates for AI to choose from
        return candidates[:max_candidates * 2]

    async def _ai_semantic_match(
        self,
        search_query: str,
        search_ingredients: Optional[List[str]],
        candidates: List['CanonicalRecipe'],
        user_language: str
    ) -> Optional['CanonicalRecipe']:
        """
        Use AI to determine if any candidate is a semantic duplicate
        Priority: Groq (primary) → Gemini (fallback) → Simple word overlap
        """

        # Build candidate list for AI
        candidate_texts = []
        for idx, recipe in enumerate(candidates):
            # Show ALL ingredients (not just first 5) for accurate matching
            all_ingredients = ', '.join([
                ing.get('name', '')
                for ing in (recipe.base_ingredients or [])
            ])

            # If too long, show first 15 ingredients (much better than 5!)
            if len(all_ingredients) > 500:
                ingredients_preview = ', '.join([
                    ing.get('name', '')
                    for ing in (recipe.base_ingredients or [])[:15]
                ]) + '...'
            else:
                ingredients_preview = all_ingredients

            candidate_texts.append(
                f"{idx+1}. {recipe.name} (Ingredients: {ingredients_preview})"
            )

        candidates_str = '\n'.join(candidate_texts)

        # Build search context
        search_context = f"Recipe: {search_query}"
        if search_ingredients:
            ing_preview = ', '.join(search_ingredients[:5])
            search_context += f"\nIngredients: {ing_preview}"

        # Try Groq first (primary)
        if self.groq_client:
            try:
                result = await self._match_with_groq(search_context, candidates_str, candidates)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"[DEDUP] Groq failed: {e}, trying Gemini...")

        # Fallback to Gemini
        if self.gemini_model:
            try:
                result = await self._match_with_gemini(search_context, candidates_str, candidates)
                if result:
                    return result
            except Exception as e:
                logger.warning(
                    f"[DEDUP] Gemini also failed: {e}, using simple fallback...")

        # Final fallback: simple word overlap
        return await self._simple_word_overlap_match(search_query, candidates)

    async def _match_with_groq(
        self,
        search_context: str,
        candidates_str: str,
        candidates: List['CanonicalRecipe']
    ) -> Optional['CanonicalRecipe']:
        """Use Groq for semantic matching (PRIMARY)"""

        prompt = f"""You are a recipe duplicate detector. Determine if the search query matches any existing recipe.

SEARCH QUERY:
{search_context}

EXISTING RECIPES IN DATABASE:
{candidates_str}

RULES FOR MATCHING:
✅ MATCH these examples:
- "carbonara" → "Pasta Carbonara" (partial name - CLEAR MATCH!)
- "carbonara" → "Spaghetti Carbonara" (partial name - CLEAR MATCH!)
- "margherita pizza" → "Classic Margherita" (with common word)
- "chocolate cake" → "Easy Chocolate Cake Recipe" (with filler words)
- "shakshuka" → "Israeli Shakshuka" (with origin)
- "margharita" → "Margarita Recipe" (small typo: 1 letter wrong)
- "nargharita" → "Margherita Pizza" (typo: 1st letter wrong)
- "spagetti" → "Spaghetti Carbonara" (missing letter)
- "choclate" → "Chocolate Cake" (transposed letters)
- "fettucini" → "Fettuccine Alfredo" (spelling variation)

⭐ IMPORTANT: If the search query is a CORE WORD from a recipe name, it's a MATCH!
- "carbonara" is the core word in "Pasta Carbonara" → MATCH
- "pizza" is the core word in "Margherita Pizza" → but check the type!
- "hummus" is the core word in "Classic Hummus" → MATCH

❌ DO NOT MATCH:
- "pizza" → "Pasta Carbonara" (completely different dishes)
- "salad" → "Soup" (different categories)
- "margherita pizza" → "Margarita Cocktail" (pizza vs drink - different!)

TYPO HANDLING:
- Compare phonetically similar names (sound-alike)
- Tolerate 1-2 letter differences in key words
- Ignore common spelling variations
- Focus on the MAIN ingredient/dish name

RESPOND WITH ONLY ONE OF:
- "MATCH: <number>" (if duplicate found, specify which recipe number)
- "NO_MATCH" (if it's genuinely a new/different recipe)

Example responses:
- "MATCH: 3"
- "NO_MATCH"
"""

        logger.info("[DEDUP] Using Groq (primary)...")

        response = await asyncio.to_thread(
            self.groq_client.chat.completions.create,
            model=self.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise recipe duplicate detector. Only match recipes that are clearly the same dish."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Very low for consistency
            max_tokens=200  # Increased from 50 to handle longer responses
        )

        result = response.choices[0].message.content.strip()
        logger.info(f"[DEDUP] Groq result: {result}")

        return self._parse_match_result(result, candidates)

    async def _match_with_gemini(
        self,
        search_context: str,
        candidates_str: str,
        candidates: List['CanonicalRecipe']
    ) -> Optional['CanonicalRecipe']:
        """Use Gemini for semantic matching (FALLBACK)"""

        prompt = f"""You are a recipe duplicate detector. Determine if the search query matches any existing recipe.

SEARCH QUERY:
{search_context}

EXISTING RECIPES IN DATABASE:
{candidates_str}

RULES FOR MATCHING:
✅ MATCH these examples:
- "carbonara" → "Spaghetti Carbonara" (partial name)
- "margherita pizza" → "Classic Margherita" (with common word)
- "chocolate cake" → "Easy Chocolate Cake Recipe" (with filler words)
- "shakshuka" → "Israeli Shakshuka" (with origin)
- "margharita" → "Margarita Recipe" (small typo: 1 letter wrong)
- "nargharita" → "Margherita Pizza" (typo: 1st letter wrong)
- "spagetti" → "Spaghetti Carbonara" (missing letter)
- "choclate" → "Chocolate Cake" (transposed letters)
- "fettucini" → "Fettuccine Alfredo" (spelling variation)

❌ DO NOT MATCH:
- "pizza" → "Pasta Carbonara" (completely different dishes)
- "salad" → "Soup" (different categories)
- "margherita pizza" → "Margarita Cocktail" (pizza vs drink - different!)

TYPO HANDLING:
- Compare phonetically similar names (sound-alike)
- Tolerate 1-2 letter differences in key words
- Ignore common spelling variations
- Focus on the MAIN ingredient/dish name

RESPOND WITH ONLY ONE OF:
- "MATCH: <number>" (if duplicate found, specify which recipe number)
- "NO_MATCH" (if it's genuinely a new/different recipe)

Example responses:
- "MATCH: 3"
- "NO_MATCH"
"""

        logger.info("[DEDUP] Using Gemini (fallback)...")

        response = await asyncio.to_thread(
            self.gemini_model.generate_content,
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=50
            )
        )

        result = response.text.strip()
        logger.info(f"[DEDUP] Gemini result: {result}")

        return self._parse_match_result(result, candidates)

    def _parse_match_result(
        self,
        result: str,
        candidates: List['CanonicalRecipe']
    ) -> Optional['CanonicalRecipe']:
        """Parse AI response and return matched recipe"""

        # Search for ALL "MATCH: <number>" anywhere in the response
        # AI might respond with full prompt + answer, so we need to find it
        import re
        matches = re.findall(r'MATCH:\s*(\d+)', result, re.IGNORECASE)
        
        logger.info(f"[DEDUP] 🔍 Found {len(matches)} match(es) in response: {matches}")
        
        if matches:
            try:
                # Use the FIRST match (most confident)
                match_num = int(matches[0])
                logger.info(f"[DEDUP] 📌 Using first match: {match_num}")
                
                if 1 <= match_num <= len(candidates):
                    matched_recipe = candidates[match_num - 1]
                    logger.info(
                        f"[DEDUP] ✅ Found duplicate: {matched_recipe.name} (match #{match_num})")
                    return matched_recipe
                else:
                    logger.warning(
                        f"[DEDUP] ⚠️ Match number {match_num} out of range (1-{len(candidates)})")
            except (ValueError, IndexError) as e:
                logger.warning(
                    f"[DEDUP] ⚠️ Failed to parse match number: {result} - {e}")

        logger.info("[DEDUP] ❌ No duplicate found")
        return None

    async def _simple_word_overlap_match(
        self,
        search_query: str,
        candidates: List['CanonicalRecipe']
    ) -> Optional['CanonicalRecipe']:
        """
        Simple fallback: word overlap matching
        Only returns match if overlap > 70%
        """
        if not candidates:
            return None

        logger.info("[DEDUP] Using simple word overlap fallback...")

        search_words = set(search_query.lower().split())
        best_match = None
        best_overlap = 0

        for candidate in candidates:
            candidate_words = set(candidate.name.lower().split())

            # Calculate Jaccard similarity
            intersection = len(search_words & candidate_words)
            union = len(search_words | candidate_words)

            if union > 0:
                overlap = intersection / union

                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = candidate

        # Only return if overlap is significant
        if best_overlap > 0.7:
            logger.info(
                f"[DEDUP] ✅ Fallback match: {best_match.name} (overlap: {best_overlap:.2f})")
            return best_match

        logger.info("[DEDUP] ❌ No significant word overlap found")
        return None


# Singleton instance for reuse
_dedup_service_instance = None


def get_deduplication_service() -> RecipeDeduplicationService:
    """Get singleton instance of deduplication service"""
    global _dedup_service_instance
    if _dedup_service_instance is None:
        _dedup_service_instance = RecipeDeduplicationService()
    return _dedup_service_instance
