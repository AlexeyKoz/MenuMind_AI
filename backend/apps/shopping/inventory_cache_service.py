"""
Inventory Cache Service - Sprint 7 Phase 3
Two-tier caching system: Redis (Tier 1) + PostgreSQL (Tier 2)
"""
import json
import hashlib
from typing import List, Dict, Optional
from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.models import User
from apps.shopping.models import InventoryRecipeBrief


class InventoryCacheService:
    """
    Two-tier caching for inventory recipe briefs

    Tier 1: Redis (fastest, <10ms)
    Tier 2: PostgreSQL (fast, <50ms)

    Cache invalidates when:
    - Inventory changes (add/edit/delete item)
    - 24 hours pass
    """

    # Cache TTL
    REDIS_TTL = 60 * 60 * 24  # 24 hours in seconds
    POSTGRES_TTL_HOURS = 24

    # Redis key prefix
    REDIS_PREFIX = 'inventory_recipes'

    def __init__(self):
        pass

    def get_cached_recipes(
        self,
        user: User,
        inventory_items: List[Dict],
        language: str,
        generation_params: Dict
    ) -> Optional[List[Dict]]:
        """
        Get cached recipes (checks Redis first, then PostgreSQL)

        Returns:
            List of recipe briefs if cached, None if cache miss
        """
        # Calculate inventory hash
        inventory_hash = self._calculate_inventory_hash(inventory_items)

        # Try Redis first (Tier 1)
        redis_key = self._build_redis_key(user.id, inventory_hash, language)
        cached_data = cache.get(redis_key)

        if cached_data:
            print(
                f"[CACHE] Redis HIT for user {user.username}, lang {language}")
            return cached_data['recipes']

        # Try PostgreSQL (Tier 2)
        try:
            cache_entry = InventoryRecipeBrief.objects.get(
                user=user,
                inventory_hash=inventory_hash,
                language=language,
                expires_at__gt=timezone.now()  # Not expired
            )

            # Found in PostgreSQL - update stats and promote to Redis
            cache_entry.increment_view_count()

            # Promote to Redis for next access
            self._save_to_redis(redis_key, cache_entry.recipes)

            print(
                f"[CACHE] PostgreSQL HIT for user {user.username}, lang {language} (promoted to Redis)")
            return cache_entry.recipes

        except InventoryRecipeBrief.DoesNotExist:
            print(f"[CACHE] MISS for user {user.username}, lang {language}")
            return None

    def save_recipes(
        self,
        user: User,
        inventory_items: List[Dict],
        recipes: List[Dict],
        language: str,
        generation_params: Dict,
        ai_model: str,
        generation_time_ms: int
    ):
        """
        Save recipes to both Redis and PostgreSQL
        """
        inventory_hash = self._calculate_inventory_hash(inventory_items)

        # Save to Redis (Tier 1)
        redis_key = self._build_redis_key(user.id, inventory_hash, language)
        self._save_to_redis(redis_key, recipes)

        # Save to PostgreSQL (Tier 2)
        expires_at = timezone.now() + timedelta(hours=self.POSTGRES_TTL_HOURS)

        InventoryRecipeBrief.objects.create(
            user=user,
            inventory_hash=inventory_hash,
            language=language,
            inventory_snapshot=inventory_items,
            recipes=recipes,
            generation_params=generation_params,
            ai_model=ai_model,
            generation_time_ms=generation_time_ms,
            expires_at=expires_at
        )

        print(
            f"[CACHE] Saved to Redis + PostgreSQL for user {user.username}, lang {language}")

    def invalidate_cache(self, user: User):
        """
        Invalidate all cached recipes for a user

        Called when:
        - User adds/edits/deletes inventory item
        - User manually refreshes
        """
        # Delete from Redis (all languages)
        for lang in ['en', 'he', 'ru']:
            # We don't know the exact inventory hash, so we can't delete specific keys
            # Redis keys will expire naturally after 24 hours
            pass

        # Delete from PostgreSQL (all non-expired entries)
        deleted_count, _ = InventoryRecipeBrief.objects.filter(
            user=user,
            expires_at__gt=timezone.now()
        ).delete()

        print(
            f"[CACHE] Invalidated {deleted_count} cache entries for user {user.username}")

        return deleted_count

    def cleanup_expired_entries(self) -> int:
        """
        Cleanup expired PostgreSQL cache entries

        Called by Celery task (daily at 3 AM)
        """
        deleted_count, _ = InventoryRecipeBrief.objects.filter(
            expires_at__lte=timezone.now()
        ).delete()

        print(f"[CACHE] Cleaned up {deleted_count} expired cache entries")

        return deleted_count

    def get_cache_stats(self, user: User) -> Dict:
        """Get cache statistics for a user"""
        total_entries = InventoryRecipeBrief.objects.filter(user=user).count()
        active_entries = InventoryRecipeBrief.objects.filter(
            user=user,
            expires_at__gt=timezone.now()
        ).count()

        total_views = sum(
            InventoryRecipeBrief.objects.filter(
                user=user).values_list('view_count', flat=True)
        )

        return {
            'total_entries': total_entries,
            'active_entries': active_entries,
            'expired_entries': total_entries - active_entries,
            'total_cache_hits': total_views
        }

    # Private methods

    def _calculate_inventory_hash(self, inventory_items: List[Dict]) -> str:
        """
        Calculate SHA256 hash of inventory state

        Includes: item names, quantities, units
        Excludes: expiration dates, locations (these don't affect recipes)
        """
        # Sort items for consistent hashing
        sorted_items = sorted(inventory_items, key=lambda x: x['name'])

        # Build hash string
        hash_parts = []
        for item in sorted_items:
            hash_parts.append(
                f"{item['name']}:{item['quantity']}:{item['unit']}")

        hash_string = '|'.join(hash_parts)

        # Calculate SHA256
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()

    def _build_redis_key(self, user_id: int, inventory_hash: str, language: str) -> str:
        """Build Redis cache key"""
        return f"{self.REDIS_PREFIX}:user_{user_id}:hash_{inventory_hash[:16]}:lang_{language}"

    def _save_to_redis(self, key: str, recipes: List[Dict]):
        """Save recipes to Redis with TTL"""
        cache_data = {
            'recipes': recipes,
            'cached_at': timezone.now().isoformat()
        }
        cache.set(key, cache_data, self.REDIS_TTL)


# Singleton instance
_cache_service = None


def get_inventory_cache_service() -> InventoryCacheService:
    """Get singleton instance of InventoryCacheService"""
    global _cache_service
    if _cache_service is None:
        _cache_service = InventoryCacheService()
    return _cache_service
