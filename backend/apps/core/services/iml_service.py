"""
IML Service - In-Memory Caching for Ingredient Master List

Provides <1ms ingredient lookups by loading all data into memory on startup.

Features:
- Instant translation lookups (en/he/ru)
- Batch translation support
- Amount validation with thresholds
- Category-based filtering
- Search by name/alias
- Automatic cache warming on startup
"""
import logging
from typing import Dict, List, Optional, Tuple
from django.core.cache import cache
from apps.core.models import IngredientCache, IngredientTranslation
import re

logger = logging.getLogger(__name__)


class IMLService:
    """
    Ingredient Master List Service

    Memory-cached ingredient translation and validation service.
    Loads all ingredients from PostgreSQL into memory on initialization.

    Performance: <1ms for single lookups, <5ms for batch operations
    """

    def __init__(self):
        self._cache = {}  # {ingredient_key: ingredient_data}
        self._category_index = {}  # {category: [ingredient_keys]}
        self._search_index = {}  # {search_term: [ingredient_keys]}
        self._loaded = False

    def initialize(self):
        """
        Load all ingredients from PostgreSQL into memory
        Call this on Django startup
        """
        if self._loaded:
            logger.info("[IML] Service already initialized, skipping...")
            return

        logger.info(
            "[IML] 🔄 Loading ingredients from PostgreSQL into memory...")

        # Query all ingredients with translations
        ingredients = IngredientCache.objects.prefetch_related(
            'translations').all()

        if not ingredients.exists():
            logger.warning(
                "[IML] ⚠️  No ingredients found in database. Run import to populate.")
            self._loaded = True
            return

        # Build memory cache
        for ingredient in ingredients:
            ingredient_key = ingredient.ingredient_key

            # Get translations
            translations = {}
            aliases = {}
            for trans in ingredient.translations.all():
                translations[trans.language] = trans.name
                if trans.aliases:
                    aliases[trans.language] = trans.aliases

            # Store in main cache
            self._cache[ingredient_key] = {
                'ingredient_key': ingredient_key,
                'category': ingredient.category,
                'translations': translations,
                'aliases': aliases,
                'validation': {
                    'typical_amount_min': ingredient.typical_amount_min,
                    'typical_amount_max': ingredient.typical_amount_max,
                    'typical_amount_avg': ingredient.typical_amount_avg,
                    'max_per_serving': ingredient.max_per_serving,
                    'warning_threshold': ingredient.warning_threshold,
                },
                'metadata': {
                    'nutrition_per_100g': ingredient.nutrition_per_100g,
                    'common_units': ingredient.common_units,
                    'unit_conversions': ingredient.unit_conversions,
                    'shelf_life': ingredient.shelf_life,
                    'storage_recommendations': ingredient.storage_recommendations,
                }
            }

            # Build category index
            if ingredient.category:
                if ingredient.category not in self._category_index:
                    self._category_index[ingredient.category] = []
                self._category_index[ingredient.category].append(
                    ingredient_key)

            # Build search index (lowercase for case-insensitive search)
            for lang, name in translations.items():
                if name:
                    search_key = name.lower().strip()
                    if search_key not in self._search_index:
                        self._search_index[search_key] = []
                    if ingredient_key not in self._search_index[search_key]:
                        self._search_index[search_key].append(ingredient_key)

            # Add aliases to search index
            for lang, lang_aliases in aliases.items():
                for alias in lang_aliases:
                    alias_key = alias.lower().strip()
                    if alias_key not in self._search_index:
                        self._search_index[alias_key] = []
                    if ingredient_key not in self._search_index[alias_key]:
                        self._search_index[alias_key].append(ingredient_key)

        self._loaded = True

        logger.info(
            f"[IML] ✅ Loaded {len(self._cache)} ingredients into memory")
        logger.info(f"[IML]    Categories: {len(self._category_index)}")
        logger.info(f"[IML]    Search terms: {len(self._search_index)}")

    def reload(self):
        """
        Reload data from PostgreSQL
        Call after admin imports new data
        """
        logger.info("[IML] 🔄 Reloading ingredients from database...")
        self._cache.clear()
        self._category_index.clear()
        self._search_index.clear()
        self._loaded = False
        self.initialize()

    def get_ingredient(self, ingredient_key: str) -> Optional[Dict]:
        """
        Get ingredient data by key

        Args:
            ingredient_key: Unique ingredient identifier

        Returns:
            Dict with translations, category, validation data, metadata
            None if not found

        Performance: <1ms
        """
        return self._cache.get(ingredient_key)

    def translate_ingredient(self, ingredient_key: str, target_lang: str) -> Optional[str]:
        """
        Get translated name for ingredient

        Args:
            ingredient_key: Ingredient identifier
            target_lang: Target language code ('en', 'he', 'ru')

        Returns:
            Translated name or None if not found

        Performance: <1ms

        Example:
            >>> iml_service.translate_ingredient('all-purpose-flour', 'he')
            'קמח לבן'
        """
        ingredient = self.get_ingredient(ingredient_key)
        if ingredient:
            return ingredient['translations'].get(target_lang)
        return None

    def batch_translate(
        self,
        ingredient_keys: List[str],
        target_lang: str
    ) -> Dict[str, str]:
        """
        Translate multiple ingredients at once

        Args:
            ingredient_keys: List of ingredient identifiers
            target_lang: Target language code

        Returns:
            Dict of {ingredient_key: translated_name}

        Performance: <5ms for typical recipe (20-30 ingredients)

        Example:
            >>> iml_service.batch_translate(['flour', 'salt', 'water'], 'ru')
            {'flour': 'Мука', 'salt': 'Соль', 'water': 'Вода'}
        """
        result = {}
        for key in ingredient_keys:
            translation = self.translate_ingredient(key, target_lang)
            if translation:
                result[key] = translation
        return result

    def validate_amount(
        self,
        ingredient_key: str,
        amount: float,
        unit: str = 'g'
    ) -> Tuple[bool, str, str]:
        """
        Validate ingredient amount using validation thresholds

        Args:
            ingredient_key: Ingredient identifier
            amount: Quantity value
            unit: Unit of measurement

        Returns:
            Tuple of (is_valid, warning_level, message)
            warning_level: 'ok', 'info', 'warning', 'critical'

        Example:
            >>> iml_service.validate_amount('flour', 10000, 'g')
            (False, 'critical', 'Suspicious amount: 10000g of flour...')
        """
        ingredient = self.get_ingredient(ingredient_key)

        if not ingredient:
            return (False, 'critical', f"Unknown ingredient: {ingredient_key}")

        # Convert to grams for comparison
        amount_g = self._convert_to_grams(amount, unit)

        validation = ingredient['validation']
        en_name = ingredient['translations'].get('en', ingredient_key)

        # Check if validation data exists
        if not validation['max_per_serving']:
            return (True, 'ok', 'No validation data available')

        # Critical: Way too much
        if amount_g > validation['max_per_serving']:
            typical = validation['typical_amount_avg']
            return (
                False,
                'critical',
                f"⚠️ Suspicious amount: {amount}{unit} of {en_name}. "
                f"Typical amount is around {typical}g per serving."
            )

        # Warning: Large amount
        if validation['warning_threshold'] and amount_g > validation['warning_threshold']:
            return (
                True,
                'warning',
                f"⚡ Large amount: {amount}{unit} of {en_name}. Please verify this is correct."
            )

        # Info: Small amount
        if validation['typical_amount_min'] and amount_g < validation['typical_amount_min']:
            return (
                True,
                'info',
                f"ℹ️ Small amount: {amount}{unit} of {en_name}. This is less than typical."
            )

        return (True, 'ok', '✅ Amount looks good')

    def _convert_to_grams(self, amount: float, unit: str) -> float:
        """
        Convert various units to grams for validation

        Simplified conversion - real implementation would use ingredient-specific
        conversions from metadata
        """
        conversions = {
            # Weight
            'g': 1,
            'gram': 1,
            'grams': 1,
            'kg': 1000,
            'kilogram': 1000,
            'mg': 0.001,
            'oz': 28.35,
            'lb': 453.592,
            'pound': 453.592,

            # Volume (approximate for water-like liquids)
            'ml': 1,
            'milliliter': 1,
            'l': 1000,
            'liter': 1000,
            'cup': 240,
            'cups': 240,
            'tbsp': 15,
            'tablespoon': 15,
            'tsp': 5,
            'teaspoon': 5,
        }

        unit_lower = unit.lower().strip()
        multiplier = conversions.get(unit_lower, 1)

        return amount * multiplier

    def search_ingredient(
        self,
        query: str,
        language: str = 'en',
        limit: int = 10
    ) -> List[Dict]:
        """
        Search ingredients by name or alias

        Args:
            query: Search term
            language: Language to search in (filters results)
            limit: Maximum results to return

        Returns:
            List of matching ingredient dicts

        Performance: <5ms

        Example:
            >>> iml_service.search_ingredient('flour', 'en')
            [{'ingredient_key': 'all-purpose-flour', ...}, ...]
        """
        query_lower = query.lower().strip()
        results = []
        seen_keys = set()

        # Exact match
        if query_lower in self._search_index:
            for ingredient_key in self._search_index[query_lower]:
                if ingredient_key not in seen_keys:
                    results.append(self._cache[ingredient_key])
                    seen_keys.add(ingredient_key)

        # Partial match (contains query)
        if len(results) < limit:
            for search_term, ingredient_keys in self._search_index.items():
                if query_lower in search_term:
                    for ingredient_key in ingredient_keys:
                        if ingredient_key not in seen_keys:
                            results.append(self._cache[ingredient_key])
                            seen_keys.add(ingredient_key)
                            if len(results) >= limit:
                                break
                if len(results) >= limit:
                    break

        return results[:limit]

    def get_by_category(self, category: str) -> List[Dict]:
        """
        Get all ingredients in a category

        Args:
            category: Category name (e.g., 'grain', 'meat', 'vegetable')

        Returns:
            List of ingredient dicts in that category
        """
        ingredient_keys = self._category_index.get(category, [])
        return [self._cache[key] for key in ingredient_keys]

    def get_all_categories(self) -> List[str]:
        """Get list of all available categories"""
        return sorted(list(self._category_index.keys()))

    def get_stats(self) -> Dict:
        """Get service statistics"""
        return {
            'total_ingredients': len(self._cache),
            'categories': len(self._category_index),
            'search_terms': len(self._search_index),
            'loaded': self._loaded,
            'cache_size_kb': self._estimate_cache_size(),
        }

    def _estimate_cache_size(self) -> int:
        """Estimate memory cache size in KB (rough estimate)"""
        import sys
        return sys.getsizeof(self._cache) // 1024

    def is_loaded(self) -> bool:
        """Check if service is initialized"""
        return self._loaded


# Global singleton instance
iml_service = IMLService()


def get_iml_service() -> IMLService:
    """
    Get the global IML service instance

    Usage:
        from apps.core.services.iml_service import get_iml_service

        iml = get_iml_service()
        translation = iml.translate_ingredient('flour', 'he')
    """
    return iml_service
