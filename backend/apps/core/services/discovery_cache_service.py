"""
Discovery Cache Service - Two-Tier Caching for Fast Discovery Page

Architecture:
- Tier 1: Redis (in-memory, <10ms)
- Tier 2: PostgreSQL DiscoveryCache table (fast, <50ms)
- Auto-refresh: Background agents maintain cache

Performance Target: <500ms for discovery page load

Features:
- Cache recipe cards (title, brief, image, tags)
- Language-specific caching
- Automatic invalidation on recipe updates
- Background refresh every hour
- Stale entry cleanup
"""
import logging
import json
from typing import Dict, List, Optional
from django.core.cache import cache
from django.db.models import Q

logger = logging.getLogger(__name__)


class DiscoveryCacheService:
    """
    Discovery Cache Service

    Two-tier caching system:
    1. Redis: Ultra-fast (<10ms) but volatile
    2. PostgreSQL: Fast (<50ms) and persistent

    Performance: <500ms for full discovery page load
    """

    # Cache key prefixes
    REDIS_PREFIX = "discovery"
    REDIS_TTL = 3600  # 1 hour

    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    def __init__(self):
        self._stats = {
            'redis_hits': 0,
            'postgres_hits': 0,
            'cache_misses': 0,
            'total_requests': 0
        }

    def get_discovery_page(
        self,
        language: str,
        page: int = 1,
        page_size: int = 20,
        tags: Optional[List[str]] = None
    ) -> Dict:
        """
        Get discovery page data with two-tier caching

        Args:
            language: Language code ('en', 'he', 'ru')
            page: Page number (1-based)
            page_size: Items per page (max 100)

        Returns:
            Dict with recipes, pagination info, and cache stats

        Performance: <500ms target
        """
        import time
        start_time = time.time()

        self._stats['total_requests'] += 1

        # Validate inputs
        page = max(1, page)
        page_size = min(page_size, self.MAX_PAGE_SIZE)

        # Build cache key
        cache_key = self._build_cache_key(language, page, page_size, tags)

        # Try Redis first (Tier 1)
        cached_data = cache.get(cache_key)
        if cached_data:
            self._stats['redis_hits'] += 1
            logger.info(f"[DISCOVERY] Redis hit: {cache_key}")
            cached_data['cache_source'] = 'redis'
            cached_data['execution_time_ms'] = (
                time.time() - start_time) * 1000
            return cached_data

        # Try PostgreSQL (Tier 2)
        pg_data = self._get_from_postgres(language, page, page_size, tags)
        if pg_data:
            self._stats['postgres_hits'] += 1
            logger.info(f"[DISCOVERY] PostgreSQL hit: {cache_key}")

            # Store in Redis for next time
            cache.set(cache_key, pg_data, self.REDIS_TTL)

            pg_data['cache_source'] = 'postgresql'
            pg_data['execution_time_ms'] = (time.time() - start_time) * 1000
            return pg_data

        # Cache miss - need to generate
        self._stats['cache_misses'] += 1
        logger.warning(f"[DISCOVERY] Cache miss: {cache_key}")

        # Generate from source
        generated_data = self._generate_discovery_data(
            language, page, page_size, tags)

        # Store in both tiers
        self._store_in_postgres(generated_data['recipes'], language)
        cache.set(cache_key, generated_data, self.REDIS_TTL)

        generated_data['cache_source'] = 'generated'
        generated_data['execution_time_ms'] = (time.time() - start_time) * 1000

        return generated_data

    def _build_cache_key(
        self,
        language: str,
        page: int,
        page_size: int,
        tags: Optional[List[str]] = None
    ) -> str:
        """Build Redis cache key"""
        tags_str = ','.join(sorted(tags)) if tags else 'all'
        return f"{self.REDIS_PREFIX}:{language}:p{page}:s{page_size}:t{tags_str}"

    def _get_from_postgres(
        self,
        language: str,
        page: int,
        page_size: int,
        tags: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """
        Get cached data from PostgreSQL DiscoveryCache table

        Performance: <50ms
        """
        try:
            from apps.recipes.models import DiscoveryCache

            # Build query
            query = DiscoveryCache.objects.filter(language=language)

            # Filter by tags if provided
            if tags:
                # PostgreSQL JSONB contains query
                for tag in tags:
                    query = query.filter(tags__contains=[tag])

            # Pagination
            offset = (page - 1) * page_size
            entries = query.order_by('-cached_at')[offset:offset + page_size]

            if not entries:
                return None

            # Count total
            total_count = query.count()

            # Convert to dict
            recipes = []
            for entry in entries:
                recipes.append({
                    'id': str(entry.canonical_recipe.id),
                    'title': entry.title,
                    'brief': entry.brief,
                    'image_url': entry.image_url,
                    'tags': entry.tags,
                    'cached_at': entry.cached_at.isoformat()
                })

            return {
                'recipes': recipes,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }

        except Exception as e:
            logger.error(f"[DISCOVERY] PostgreSQL error: {e}")
            return None

    def _generate_discovery_data(
        self,
        language: str,
        page: int,
        page_size: int,
        tags: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate discovery data from CanonicalRecipe

        This is called when both cache tiers miss
        """
        from apps.recipes.models import CanonicalRecipe, RecipeTranslation

        # Get recipes
        query = CanonicalRecipe.objects.filter(is_published=True)

        # Filter by tags if provided
        if tags:
            # Assuming tags are stored in a JSONField or similar
            for tag in tags:
                query = query.filter(tags__contains=[tag])

        # Pagination
        offset = (page - 1) * page_size
        total_count = query.count()
        recipes_qs = query.order_by('-created_at')[offset:offset + page_size]

        recipes = []
        for recipe in recipes_qs:
            # Try to get translation
            translation = RecipeTranslation.objects.filter(
                canonical_recipe=recipe,
                language=language,
                status='completed'
            ).first()

            title = translation.name if translation else recipe.name
            description = translation.description if translation else (
                recipe.description or '')

            recipes.append({
                'id': str(recipe.id),
                'title': title,
                'brief': description[:200] if description else '',
                'image_url': recipe.image_url if hasattr(recipe, 'image_url') else None,
                'tags': recipe.tags if hasattr(recipe, 'tags') else [],
                'cached_at': None  # Not cached yet
            })

        return {
            'recipes': recipes,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        }

    def _store_in_postgres(self, recipes: List[Dict], language: str):
        """
        Store recipe cards in PostgreSQL DiscoveryCache

        Uses bulk operations for performance
        """
        try:
            from apps.recipes.models import DiscoveryCache, CanonicalRecipe
            from django.utils import timezone

            for recipe_data in recipes:
                recipe_id = recipe_data['id']

                # Get or create cache entry
                DiscoveryCache.objects.update_or_create(
                    canonical_recipe_id=recipe_id,
                    language=language,
                    defaults={
                        'title': recipe_data['title'],
                        'brief': recipe_data['brief'],
                        'image_url': recipe_data.get('image_url'),
                        'tags': recipe_data.get('tags', []),
                        'cached_at': timezone.now()
                    }
                )

            logger.info(
                f"[DISCOVERY] Stored {len(recipes)} entries in PostgreSQL for {language}")

        except Exception as e:
            logger.error(f"[DISCOVERY] Failed to store in PostgreSQL: {e}")

    def invalidate_recipe(self, recipe_id: str):
        """
        Invalidate cache for a specific recipe across all languages

        Call this when a recipe is updated or deleted
        """
        from apps.recipes.models import DiscoveryCache

        # Delete from PostgreSQL
        deleted_count = DiscoveryCache.objects.filter(
            canonical_recipe_id=recipe_id
        ).delete()[0]

        # Invalidate Redis (delete all discovery keys)
        # Note: In production, you'd use a more targeted approach
        cache.delete_pattern(f"{self.REDIS_PREFIX}:*")

        logger.info(
            f"[DISCOVERY] Invalidated cache for recipe {recipe_id} ({deleted_count} entries)")

    def invalidate_language(self, language: str):
        """
        Invalidate all cache entries for a specific language

        Call this when language data is updated
        """
        from apps.recipes.models import DiscoveryCache

        # Delete from PostgreSQL
        deleted_count = DiscoveryCache.objects.filter(
            language=language).delete()[0]

        # Invalidate Redis for this language
        cache.delete_pattern(f"{self.REDIS_PREFIX}:{language}:*")

        logger.info(
            f"[DISCOVERY] Invalidated cache for language {language} ({deleted_count} entries)")

    def refresh_all(self, language: str):
        """
        Refresh all cache entries for a language

        This is called by background agents hourly
        """
        from apps.recipes.models import CanonicalRecipe, RecipeTranslation, DiscoveryCache
        from django.utils import timezone

        logger.info(f"[DISCOVERY] Starting cache refresh for {language}")

        recipes = CanonicalRecipe.objects.filter(is_published=True)
        refreshed = 0

        for recipe in recipes:
            try:
                # Get translation
                translation = RecipeTranslation.objects.filter(
                    canonical_recipe=recipe,
                    language=language,
                    status='completed'
                ).first()

                title = translation.name if translation else recipe.name
                description = translation.description if translation else (
                    recipe.description or '')

                # Update or create cache entry
                DiscoveryCache.objects.update_or_create(
                    canonical_recipe=recipe,
                    language=language,
                    defaults={
                        'title': title,
                        'brief': description[:200] if description else '',
                        'image_url': recipe.image_url if hasattr(recipe, 'image_url') else None,
                        'tags': recipe.tags if hasattr(recipe, 'tags') else [],
                        'cached_at': timezone.now()
                    }
                )
                refreshed += 1

            except Exception as e:
                logger.error(
                    f"[DISCOVERY] Failed to refresh recipe {recipe.id}: {e}")

        # Clear Redis cache for this language to force reload
        cache.delete_pattern(f"{self.REDIS_PREFIX}:{language}:*")

        logger.info(
            f"[DISCOVERY] Refreshed {refreshed} entries for {language}")
        return refreshed

    def cleanup_stale(self, days_old: int = 30):
        """
        Clean up stale cache entries

        Removes entries older than specified days
        """
        from apps.recipes.models import DiscoveryCache
        from django.utils import timezone
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=days_old)

        deleted_count = DiscoveryCache.objects.filter(
            cached_at__lt=cutoff_date
        ).delete()[0]

        logger.info(
            f"[DISCOVERY] Cleaned up {deleted_count} stale entries (>{days_old} days old)")
        return deleted_count

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        stats = self._stats.copy()

        if stats['total_requests'] > 0:
            stats['redis_hit_rate'] = (
                stats['redis_hits'] / stats['total_requests']) * 100
            stats['postgres_hit_rate'] = (
                stats['postgres_hits'] / stats['total_requests']) * 100
            stats['cache_miss_rate'] = (
                stats['cache_misses'] / stats['total_requests']) * 100
        else:
            stats['redis_hit_rate'] = 0
            stats['postgres_hit_rate'] = 0
            stats['cache_miss_rate'] = 0

        return stats


# Global singleton instance
discovery_cache_service = DiscoveryCacheService()


def get_discovery_cache_service() -> DiscoveryCacheService:
    """
    Get the global Discovery Cache Service instance

    Usage:
        from apps.core.services.discovery_cache_service import get_discovery_cache_service

        cache_service = get_discovery_cache_service()
        result = cache_service.get_discovery_page('he', page=1, page_size=20)

        print(f"Loaded in {result['execution_time_ms']:.2f}ms")
        print(f"Cache source: {result['cache_source']}")
        print(f"Recipes: {len(result['recipes'])}")
    """
    return discovery_cache_service
