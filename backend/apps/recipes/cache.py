"""
Caching utilities for recipe system

Cache Strategy:
1. Canonical Recipe Lists - 5 minutes TTL (frequently accessed, rarely changes)
2. Recipe Statistics - 10 minutes TTL (updated by background tasks)
3. Review Counts - 15 minutes TTL (less critical, can be slightly stale)
4. User-specific data - 5 minutes TTL (likes, ratings)

Invalidation:
- On recipe update: Clear recipe cache
- On social action: Clear statistics cache
- On review: Clear review count cache
"""

from django.core.cache import cache
from django.conf import settings
from typing import Optional, Any, List, Dict
import hashlib
import json


class RecipeCache:
    """Centralized caching for recipe system"""

    # Cache key prefixes
    PREFIX_CANONICAL_LIST = 'canonical_list'
    PREFIX_CANONICAL_DETAIL = 'canonical_detail'
    PREFIX_RECIPE_STATS = 'recipe_stats'
    PREFIX_REVIEW_LIST = 'review_list'
    PREFIX_USER_LIKES = 'user_likes'
    PREFIX_USER_RATINGS = 'user_ratings'

    # Cache timeouts (seconds)
    TIMEOUT_SHORT = 300  # 5 minutes
    TIMEOUT_MEDIUM = 600  # 10 minutes
    TIMEOUT_LONG = 900  # 15 minutes

    @staticmethod
    def _make_key(*args) -> str:
        """Generate cache key from arguments"""
        key_parts = [str(arg) for arg in args]
        key_string = ':'.join(key_parts)
        # Hash long keys to keep them under Redis limits
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{key_parts[0]}:{key_hash}"
        return key_string

    # ========================================================================
    # CANONICAL RECIPE LIST CACHING
    # ========================================================================

    @classmethod
    def get_canonical_list(
        cls,
        search: Optional[str] = None,
        cuisine: Optional[str] = None,
        difficulty: Optional[str] = None,
        diet_labels: Optional[List[str]] = None,
        ordering: Optional[str] = None,
        page: int = 1
    ) -> Optional[List[Dict]]:
        """Get cached canonical recipe list"""
        cache_key = cls._make_key(
            cls.PREFIX_CANONICAL_LIST,
            search or '',
            cuisine or '',
            difficulty or '',
            json.dumps(sorted(diet_labels or [])),
            ordering or '',
            page
        )
        return cache.get(cache_key)

    @classmethod
    def set_canonical_list(
        cls,
        data: List[Dict],
        search: Optional[str] = None,
        cuisine: Optional[str] = None,
        difficulty: Optional[str] = None,
        diet_labels: Optional[List[str]] = None,
        ordering: Optional[str] = None,
        page: int = 1
    ) -> None:
        """Cache canonical recipe list"""
        cache_key = cls._make_key(
            cls.PREFIX_CANONICAL_LIST,
            search or '',
            cuisine or '',
            difficulty or '',
            json.dumps(sorted(diet_labels or [])),
            ordering or '',
            page
        )
        cache.set(cache_key, data, cls.TIMEOUT_SHORT)

    @classmethod
    def invalidate_canonical_lists(cls) -> None:
        """Invalidate all canonical recipe list caches"""
        # Note: This is a simple implementation
        # For production, use Redis pattern matching to delete all matching keys
        # cache.delete_pattern(f'{cls.PREFIX_CANONICAL_LIST}:*')
        pass

    # ========================================================================
    # CANONICAL RECIPE DETAIL CACHING
    # ========================================================================

    @classmethod
    def get_canonical_detail(cls, recipe_id: str) -> Optional[Dict]:
        """Get cached canonical recipe detail"""
        cache_key = cls._make_key(cls.PREFIX_CANONICAL_DETAIL, recipe_id)
        return cache.get(cache_key)

    @classmethod
    def set_canonical_detail(cls, recipe_id: str, data: Dict) -> None:
        """Cache canonical recipe detail"""
        cache_key = cls._make_key(cls.PREFIX_CANONICAL_DETAIL, recipe_id)
        cache.set(cache_key, data, cls.TIMEOUT_MEDIUM)

    @classmethod
    def invalidate_canonical_detail(cls, recipe_id: str) -> None:
        """Invalidate specific canonical recipe cache"""
        cache_key = cls._make_key(cls.PREFIX_CANONICAL_DETAIL, recipe_id)
        cache.delete(cache_key)
        # Also invalidate list caches since statistics may have changed
        cls.invalidate_canonical_lists()

    # ========================================================================
    # RECIPE STATISTICS CACHING
    # ========================================================================

    @classmethod
    def get_recipe_stats(cls, recipe_id: str) -> Optional[Dict]:
        """Get cached recipe statistics"""
        cache_key = cls._make_key(cls.PREFIX_RECIPE_STATS, recipe_id)
        return cache.get(cache_key)

    @classmethod
    def set_recipe_stats(cls, recipe_id: str, stats: Dict) -> None:
        """Cache recipe statistics"""
        cache_key = cls._make_key(cls.PREFIX_RECIPE_STATS, recipe_id)
        cache.set(cache_key, stats, cls.TIMEOUT_MEDIUM)

    @classmethod
    def invalidate_recipe_stats(cls, recipe_id: str) -> None:
        """Invalidate recipe statistics cache"""
        cache_key = cls._make_key(cls.PREFIX_RECIPE_STATS, recipe_id)
        cache.delete(cache_key)

    # ========================================================================
    # REVIEW LIST CACHING
    # ========================================================================

    @classmethod
    def get_review_list(
        cls,
        recipe_id: str,
        ordering: str = '-helpful_count',
        page: int = 1
    ) -> Optional[Dict]:
        """Get cached review list"""
        cache_key = cls._make_key(
            cls.PREFIX_REVIEW_LIST,
            recipe_id,
            ordering,
            page
        )
        return cache.get(cache_key)

    @classmethod
    def set_review_list(
        cls,
        recipe_id: str,
        data: Dict,
        ordering: str = '-helpful_count',
        page: int = 1
    ) -> None:
        """Cache review list"""
        cache_key = cls._make_key(
            cls.PREFIX_REVIEW_LIST,
            recipe_id,
            ordering,
            page
        )
        cache.set(cache_key, data, cls.TIMEOUT_LONG)

    @classmethod
    def invalidate_review_list(cls, recipe_id: str) -> None:
        """Invalidate all review list caches for a recipe"""
        # In production, use pattern matching to delete all pages/orderings
        pass

    # ========================================================================
    # USER-SPECIFIC CACHING
    # ========================================================================

    @classmethod
    def get_user_likes(cls, user_id: str) -> Optional[List[str]]:
        """Get cached list of recipe IDs user has liked"""
        cache_key = cls._make_key(cls.PREFIX_USER_LIKES, user_id)
        return cache.get(cache_key)

    @classmethod
    def set_user_likes(cls, user_id: str, recipe_ids: List[str]) -> None:
        """Cache list of recipe IDs user has liked"""
        cache_key = cls._make_key(cls.PREFIX_USER_LIKES, user_id)
        cache.set(cache_key, recipe_ids, cls.TIMEOUT_SHORT)

    @classmethod
    def invalidate_user_likes(cls, user_id: str) -> None:
        """Invalidate user's like cache"""
        cache_key = cls._make_key(cls.PREFIX_USER_LIKES, user_id)
        cache.delete(cache_key)

    @classmethod
    def get_user_ratings(cls, user_id: str) -> Optional[Dict[str, int]]:
        """Get cached dictionary of recipe_id -> rating"""
        cache_key = cls._make_key(cls.PREFIX_USER_RATINGS, user_id)
        return cache.get(cache_key)

    @classmethod
    def set_user_ratings(cls, user_id: str, ratings: Dict[str, int]) -> None:
        """Cache dictionary of recipe_id -> rating"""
        cache_key = cls._make_key(cls.PREFIX_USER_RATINGS, user_id)
        cache.set(cache_key, ratings, cls.TIMEOUT_SHORT)

    @classmethod
    def invalidate_user_ratings(cls, user_id: str) -> None:
        """Invalidate user's rating cache"""
        cache_key = cls._make_key(cls.PREFIX_USER_RATINGS, user_id)
        cache.delete(cache_key)

    # ========================================================================
    # BULK INVALIDATION
    # ========================================================================

    @classmethod
    def invalidate_all_for_recipe(cls, recipe_id: str) -> None:
        """Invalidate all caches related to a recipe"""
        cls.invalidate_canonical_detail(recipe_id)
        cls.invalidate_recipe_stats(recipe_id)
        cls.invalidate_review_list(recipe_id)
        cls.invalidate_canonical_lists()


# Convenience functions for common operations

def cache_canonical_list(func):
    """Decorator to cache canonical recipe list queries"""
    def wrapper(*args, **kwargs):
        # Extract cache parameters from kwargs
        search = kwargs.get('search')
        cuisine = kwargs.get('cuisine')
        difficulty = kwargs.get('difficulty')
        diet_labels = kwargs.get('diet_labels')
        ordering = kwargs.get('ordering')
        page = kwargs.get('page', 1)

        # Try to get from cache
        cached_data = RecipeCache.get_canonical_list(
            search, cuisine, difficulty, diet_labels, ordering, page
        )

        if cached_data is not None:
            return cached_data

        # Cache miss - call function
        result = func(*args, **kwargs)

        # Store in cache
        RecipeCache.set_canonical_list(
            result, search, cuisine, difficulty, diet_labels, ordering, page
        )

        return result

    return wrapper

