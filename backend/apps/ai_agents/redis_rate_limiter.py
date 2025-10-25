# -*- coding: utf-8 -*-
"""
Redis-based rate limiter for AI recipe generation.

Provides ultra-fast rate limiting with Redis, with automatic fallback to PostgreSQL.
Designed for high-concurrency scenarios with minimal latency.
"""

import redis
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, datetime
import logging

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """
    High-performance Redis-based rate limiter.

    Features:
    - Sub-millisecond rate limit checks
    - Atomic counter operations
    - Automatic TTL management
    - Graceful fallback to PostgreSQL
    - Thread-safe operations
    """

    def __init__(self):
        """Initialize Redis connection with fallback handling"""
        self.redis_client = None
        self.available = False

        try:
            # Get Redis URL from settings
            redis_url = getattr(settings, 'REDIS_URL',
                                'redis://localhost:6379/0')

            # Create Redis client
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1
            )

            # Test connection
            self.redis_client.ping()
            self.available = True
            logger.info("[REDIS RATE LIMITER] ✅ Connected successfully")

        except Exception as e:
            self.available = False
            logger.warning(
                f"[REDIS RATE LIMITER] ⚠️ Redis unavailable, using DB fallback: {e}")

    def _get_minute_key(self, user):
        """Generate Redis key for per-minute counter"""
        now = timezone.now()
        minute_stamp = now.strftime('%Y%m%d%H%M')
        return f"rate:minute:{user.username}:{minute_stamp}"

    def _get_daily_key(self, user):
        """Generate Redis key for daily counter"""
        today = timezone.now().date().isoformat()
        return f"rate:daily:{user.username}:{today}"

    def _get_cooldown_key(self, user):
        """Generate Redis key for cooldown tracking"""
        return f"rate:cooldown:{user.username}"

    def _calculate_ttl_to_next_minute(self):
        """Calculate seconds until next minute"""
        now = timezone.now()
        next_minute = (now + timedelta(minutes=1)
                       ).replace(second=0, microsecond=0)
        return int((next_minute - now).total_seconds())

    def _calculate_ttl_to_next_day(self):
        """Calculate seconds until midnight"""
        now = timezone.now()
        next_day = (now + timedelta(days=1)).replace(hour=0,
                                                     minute=0, second=0, microsecond=0)
        return int((next_day - now).total_seconds())

    def check_minute_limit(self, user, max_limit):
        """
        Check per-minute rate limit using Redis.

        Returns:
            tuple: (allowed: bool, remaining: int) or None if Redis unavailable
        """
        if not self.available:
            return None

        try:
            key = self._get_minute_key(user)

            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.get(key)
            pipe.ttl(key)
            results = pipe.execute()

            current_count = int(results[0]) if results[0] else 0
            ttl = results[1]

            # Check if limit exceeded
            if current_count >= max_limit:
                logger.info(
                    f"[REDIS] ❌ {user.username} minute limit exceeded: {current_count}/{max_limit}")
                return False, 0

            # Increment counter atomically
            pipe = self.redis_client.pipeline()
            pipe.incr(key)

            # Set TTL if key is new (TTL = -2 means key doesn't exist, -1 means no TTL)
            if ttl < 0:
                pipe.expire(key, self._calculate_ttl_to_next_minute())

            pipe.execute()

            remaining = max_limit - current_count - 1
            logger.info(
                f"[REDIS] ✅ {user.username} minute check: {current_count + 1}/{max_limit}, {remaining} remaining")
            return True, remaining

        except Exception as e:
            logger.error(f"[REDIS] ⚠️ Minute limit check failed: {e}")
            self.available = False
            return None

    def check_daily_limit(self, user, max_limit):
        """
        Check daily rate limit using Redis.

        Returns:
            tuple: (allowed: bool, remaining: int) or None if Redis unavailable
        """
        if not self.available:
            return None

        try:
            key = self._get_daily_key(user)

            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.get(key)
            pipe.ttl(key)
            results = pipe.execute()

            current_count = int(results[0]) if results[0] else 0
            ttl = results[1]

            # Check if limit exceeded
            if current_count >= max_limit:
                logger.info(
                    f"[REDIS] ❌ {user.username} daily limit exceeded: {current_count}/{max_limit}")
                return False, 0

            # Increment counter atomically
            pipe = self.redis_client.pipeline()
            pipe.incr(key)

            # Set TTL if key is new
            if ttl < 0:
                pipe.expire(key, self._calculate_ttl_to_next_day())

            pipe.execute()

            remaining = max_limit - current_count - 1
            logger.info(
                f"[REDIS] ✅ {user.username} daily check: {current_count + 1}/{max_limit}, {remaining} remaining")
            return True, remaining

        except Exception as e:
            logger.error(f"[REDIS] ⚠️ Daily limit check failed: {e}")
            self.available = False
            return None

    def get_current_usage(self, user):
        """
        Get current usage from Redis.

        Returns:
            dict: {'minute': int, 'daily': int} or None if Redis unavailable
        """
        if not self.available:
            return None

        try:
            minute_key = self._get_minute_key(user)
            daily_key = self._get_daily_key(user)

            pipe = self.redis_client.pipeline()
            pipe.get(minute_key)
            pipe.get(daily_key)
            results = pipe.execute()

            usage = {
                'minute': int(results[0]) if results[0] else 0,
                'daily': int(results[1]) if results[1] else 0
            }

            return usage

        except Exception as e:
            logger.error(f"[REDIS] ⚠️ Get usage failed: {e}")
            return None

    def set_cooldown(self, user, seconds=30):
        """
        Set cooldown flag in Redis.

        Args:
            user: User object
            seconds: Cooldown duration in seconds
        """
        if not self.available:
            return

        try:
            key = self._get_cooldown_key(user)
            self.redis_client.setex(key, seconds, '1')
            logger.info(
                f"[REDIS] 🕐 Cooldown set for {user.username}: {seconds}s")

        except Exception as e:
            logger.error(f"[REDIS] ⚠️ Set cooldown failed: {e}")

    def check_cooldown(self, user):
        """
        Check if user is in cooldown period.

        Returns:
            int: Remaining cooldown seconds, or 0 if not in cooldown, or None if Redis unavailable
        """
        if not self.available:
            return None

        try:
            key = self._get_cooldown_key(user)
            ttl = self.redis_client.ttl(key)

            # TTL returns -2 if key doesn't exist, -1 if no expiry
            if ttl <= 0:
                return 0

            logger.info(
                f"[REDIS] ⏳ {user.username} in cooldown: {ttl}s remaining")
            return ttl

        except Exception as e:
            logger.error(f"[REDIS] ⚠️ Check cooldown failed: {e}")
            return None

    def invalidate_user_cache(self, user):
        """
        Invalidate all rate limit cache for a user.
        Useful when user upgrades plan or gets exempted.
        """
        if not self.available:
            return

        try:
            # Delete all keys for this user
            pattern = f"rate:*:{user.username}:*"
            keys = self.redis_client.keys(pattern)

            if keys:
                self.redis_client.delete(*keys)
                logger.info(
                    f"[REDIS] 🗑️ Invalidated cache for {user.username}: {len(keys)} keys")

        except Exception as e:
            logger.error(f"[REDIS] ⚠️ Cache invalidation failed: {e}")

    def get_stats(self):
        """
        Get Redis rate limiter statistics.

        Returns:
            dict: Statistics about Redis rate limiter
        """
        if not self.available:
            return {'available': False, 'reason': 'Redis connection failed'}

        try:
            info = self.redis_client.info('stats')

            # Count rate limit keys
            minute_keys = len(self.redis_client.keys('rate:minute:*'))
            daily_keys = len(self.redis_client.keys('rate:daily:*'))
            cooldown_keys = len(self.redis_client.keys('rate:cooldown:*'))

            return {
                'available': True,
                'total_connections': info.get('total_connections_received', 0),
                'total_commands': info.get('total_commands_processed', 0),
                'active_keys': {
                    'minute': minute_keys,
                    'daily': daily_keys,
                    'cooldown': cooldown_keys,
                    'total': minute_keys + daily_keys + cooldown_keys
                }
            }

        except Exception as e:
            logger.error(f"[REDIS] ⚠️ Get stats failed: {e}")
            return {'available': False, 'error': str(e)}


# Global Redis rate limiter instance
_redis_limiter = None


def get_redis_limiter():
    """Get or create Redis rate limiter singleton"""
    global _redis_limiter
    if _redis_limiter is None:
        _redis_limiter = RedisRateLimiter()
    return _redis_limiter
