"""
Recipe Matcher Service - Sprint 7 Phase 4
Checks if a similar recipe already exists in the database
Uses PostgreSQL trigram similarity search
"""
from typing import Optional, Dict, List
from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity
from apps.recipes.models import CanonicalRecipe


class RecipeMatcherService:
    """
    Check if a recipe similar to the generated brief already exists

    Matching criteria:
    1. Name similarity (PostgreSQL trigram) - 30% weight
    2. Ingredient overlap - 70% weight

    If similarity > 75%, consider it a match
    """

    # Thresholds
    NAME_SIMILARITY_THRESHOLD = 0.5  # 50% name similarity
    INGREDIENT_OVERLAP_THRESHOLD = 0.6  # 60% ingredient overlap
    OVERALL_MATCH_THRESHOLD = 0.75  # 75% overall similarity

    def __init__(self):
        pass

    def find_matching_recipe(
        self,
        recipe_name: str,
        ingredients: List[str],
        language: str = 'en'
    ) -> Optional[Dict]:
        """
        Find matching recipe in database

        Args:
            recipe_name: Name of the recipe to match
            ingredients: List of ingredient names
            language: Language for name matching

        Returns:
            Dict with recipe data if match found, None otherwise
        """
        # Search for recipes with similar names (PostgreSQL trigram)
        try:
            # Use trigram similarity for fuzzy name matching
            similar_recipes = CanonicalRecipe.objects.annotate(
                similarity=TrigramSimilarity(
                    'canonical_data__metadata__title', recipe_name)
            ).filter(
                similarity__gte=self.NAME_SIMILARITY_THRESHOLD
            ).order_by('-similarity')[:10]  # Top 10 similar names

            if not similar_recipes:
                print(
                    f"[MATCHER] No similar recipes found for '{recipe_name}'")
                return None

            # Check ingredient overlap for each candidate
            best_match = None
            best_score = 0

            for recipe in similar_recipes:
                # Calculate match score
                name_similarity = recipe.similarity
                ingredient_overlap = self._calculate_ingredient_overlap(
                    ingredients,
                    recipe
                )

                # Weighted score: 30% name, 70% ingredients
                overall_score = (name_similarity * 0.3) + \
                    (ingredient_overlap * 0.7)

                print(
                    f"[MATCHER] Candidate: '{recipe.canonical_data.get('metadata', {}).get('title', 'N/A')}'")
                print(f"   Name similarity: {name_similarity:.2f}")
                print(f"   Ingredient overlap: {ingredient_overlap:.2f}")
                print(f"   Overall score: {overall_score:.2f}")

                if overall_score > best_score:
                    best_score = overall_score
                    best_match = recipe

            # Check if best match exceeds threshold
            if best_match and best_score >= self.OVERALL_MATCH_THRESHOLD:
                print(f"[MATCHER] ✅ Match found! Score: {best_score:.2f}")
                return {
                    'recipe_id': str(best_match.id),
                    'title': best_match.canonical_data.get('metadata', {}).get('title', 'N/A'),
                    'match_score': best_score,
                    'name_similarity': best_match.similarity,
                    'ingredient_overlap': self._calculate_ingredient_overlap(ingredients, best_match)
                }
            else:
                print(
                    f"[MATCHER] No match above threshold (best: {best_score:.2f})")
                return None

        except Exception as e:
            # Fallback if trigram extension not available (e.g., SQLite)
            print(f"[MATCHER] Trigram search failed: {e}")
            return self._fallback_simple_match(recipe_name, ingredients)

    def _calculate_ingredient_overlap(
        self,
        brief_ingredients: List[str],
        recipe: CanonicalRecipe
    ) -> float:
        """
        Calculate ingredient overlap between brief and recipe

        Returns:
            Float between 0 and 1 (percentage of matching ingredients)
        """
        # Normalize brief ingredients
        brief_set = set(ing.lower().strip() for ing in brief_ingredients)

        # Get recipe ingredients from canonical data
        recipe_ingredients = recipe.canonical_data.get(
            'structure', {}).get('ingredients', [])

        if not recipe_ingredients:
            return 0.0

        # Extract ingredient keys/names
        recipe_set = set()
        for ing in recipe_ingredients:
            if isinstance(ing, dict):
                # Could be iml_key or name
                key = ing.get('iml_key', ing.get('name', '')).lower().strip()
                recipe_set.add(key)
            else:
                recipe_set.add(str(ing).lower().strip())

        if not recipe_set:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(brief_set & recipe_set)
        union = len(brief_set | recipe_set)

        if union == 0:
            return 0.0

        return intersection / union

    def _fallback_simple_match(
        self,
        recipe_name: str,
        ingredients: List[str]
    ) -> Optional[Dict]:
        """
        Simple fallback matching without trigram (for SQLite)
        """
        # Search for exact or partial name matches
        recipes = CanonicalRecipe.objects.filter(
            Q(canonical_data__metadata__title__icontains=recipe_name) |
            Q(canonical_data__metadata__title__icontains=recipe_name.split()
              [0])
        )[:10]

        if not recipes:
            return None

        best_match = None
        best_score = 0

        for recipe in recipes:
            ingredient_overlap = self._calculate_ingredient_overlap(
                ingredients, recipe)

            if ingredient_overlap > best_score:
                best_score = ingredient_overlap
                best_match = recipe

        if best_match and best_score >= self.INGREDIENT_OVERLAP_THRESHOLD:
            return {
                'recipe_id': str(best_match.id),
                'title': best_match.canonical_data.get('metadata', {}).get('title', 'N/A'),
                'match_score': best_score,
                'ingredient_overlap': best_score
            }

        return None


# Singleton instance
_matcher_service = None


def get_recipe_matcher_service() -> RecipeMatcherService:
    """Get singleton instance of RecipeMatcherService"""
    global _matcher_service
    if _matcher_service is None:
        _matcher_service = RecipeMatcherService()
    return _matcher_service
