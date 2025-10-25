from django.utils import timezone
from datetime import timedelta
from .models import AIRateLimitLog, AIRateLimitSettings


class AIRateLimiter:
    """
    Hybrid rate limiter with Redis caching and PostgreSQL fallback.

    Strategy:
    1. Try Redis first (fast path - sub-millisecond)
    2. Fall back to PostgreSQL if Redis unavailable
    3. Always log to PostgreSQL for analytics

    Rules:
    - Max 5 recipes per minute per user
    - Max 25 recipes per day per user
    - testuser1 and testuser2 are exempt from limits
    """

    @staticmethod
    def get_settings():
        """Get or create rate limit settings"""
        settings, created = AIRateLimitSettings.objects.get_or_create(
            id=1,
            defaults={
                'max_recipes_per_minute': 5,
                'max_recipes_per_day': 25,
                'exempted_users': 'testuser1,testuser2'
            }
        )
        return settings

    @staticmethod
    def is_user_exempt(user):
        """Check if user is exempt from rate limits"""
        settings = AIRateLimiter.get_settings()
        exempted = settings.get_exempted_users()
        is_exempt = user.username in exempted

        if is_exempt:
            print(
                f"[RATE LIMIT] User {user.username} is EXEMPT from rate limits")

        return is_exempt

    @staticmethod
    def check_rate_limit(user, recipes_count=1):
        """
        Check if user has exceeded rate limits.

        Uses Redis for fast checking with PostgreSQL fallback.

        Returns:
            tuple: (allowed: bool, message: str, limit_type: str)
        """
        # Check if user is exempt
        if AIRateLimiter.is_user_exempt(user):
            return True, "Unlimited access", None

        settings = AIRateLimiter.get_settings()

        # Try Redis first (fast path)
        try:
            from .redis_rate_limiter import get_redis_limiter
            redis_limiter = get_redis_limiter()

            if redis_limiter.available:
                return AIRateLimiter._check_rate_limit_redis(
                    user, recipes_count, settings, redis_limiter
                )
        except Exception as e:
            print(f"[RATE LIMIT] Redis check failed, using DB: {e}")

        # Fall back to PostgreSQL
        return AIRateLimiter._check_rate_limit_db(user, recipes_count, settings)

    @staticmethod
    def _check_rate_limit_redis(user, recipes_count, settings, redis_limiter):
        """
        Fast Redis-based rate limit check.

        Returns:
            tuple: (allowed: bool, message: str, limit_type: str)
        """
        # Check per-minute limit
        minute_allowed, minute_remaining = redis_limiter.check_minute_limit(
            user, settings.max_recipes_per_minute
        )

        if not minute_allowed:
            cooldown_remaining = redis_limiter.check_cooldown(user) or 0
            wait_time = max(60 - cooldown_remaining, 0)
            message = (
                f"You've reached the limit of {settings.max_recipes_per_minute} recipes per minute. "
                f"Please wait {wait_time} seconds and try again."
            )
            print(
                f"[REDIS RATE LIMIT] ❌ {user.username} minute limit: {settings.max_recipes_per_minute}")
            return False, message, 'minute'

        # Check daily limit
        daily_allowed, daily_remaining = redis_limiter.check_daily_limit(
            user, settings.max_recipes_per_day
        )

        if not daily_allowed:
            hours_until_reset = (24 - timezone.now().hour)
            message = (
                f"You've reached your daily limit of {settings.max_recipes_per_day} recipes. "
                f"Your limit will reset in approximately {hours_until_reset} hour(s). "
                f"Try again tomorrow!"
            )
            print(
                f"[REDIS RATE LIMIT] ❌ {user.username} daily limit: {settings.max_recipes_per_day}")
            return False, message, 'daily'

        # All checks passed
        print(
            f"[REDIS RATE LIMIT] ✅ {user.username} allowed: minute {minute_remaining}, daily {daily_remaining} remaining")
        return True, "OK", None

    @staticmethod
    def _check_rate_limit_db(user, recipes_count, settings):
        """
        PostgreSQL-based rate limit check (fallback).

        Returns:
            tuple: (allowed: bool, message: str, limit_type: str)
        """
        now = timezone.now()

        # Check per-minute limit (last 60 seconds)
        one_minute_ago = now - timedelta(minutes=1)
        recent_logs = AIRateLimitLog.objects.filter(
            user=user,
            endpoint='recipe_generation',
            timestamp__gte=one_minute_ago
        )

        recipes_last_minute = sum(log.recipes_generated for log in recent_logs)

        if recipes_last_minute + recipes_count > settings.max_recipes_per_minute:
            remaining_time = 60 - (now - recent_logs.first().timestamp).seconds
            message = (
                f"You've reached the limit of {settings.max_recipes_per_minute} recipes per minute. "
                f"Please wait {remaining_time} seconds and try again."
            )
            print(
                f"[DB RATE LIMIT] ❌ {user.username} exceeded per-minute limit: {recipes_last_minute + recipes_count}/{settings.max_recipes_per_minute}")
            return False, message, 'minute'

        # Check daily limit (last 24 hours)
        one_day_ago = now - timedelta(days=1)
        daily_logs = AIRateLimitLog.objects.filter(
            user=user,
            endpoint='recipe_generation',
            timestamp__gte=one_day_ago
        )

        recipes_today = sum(log.recipes_generated for log in daily_logs)

        if recipes_today + recipes_count > settings.max_recipes_per_day:
            remaining = settings.max_recipes_per_day - recipes_today
            hours_until_reset = 24 - \
                (now - daily_logs.first().timestamp).seconds // 3600

            if remaining > 0:
                message = (
                    f"You're close to your daily limit! "
                    f"You can generate {remaining} more recipe(s) today. "
                    f"Daily limit: {settings.max_recipes_per_day} recipes. "
                    f"Resets in approximately {hours_until_reset} hour(s)."
                )
            else:
                message = (
                    f"You've reached your daily limit of {settings.max_recipes_per_day} recipes. "
                    f"Your limit will reset in approximately {hours_until_reset} hour(s). "
                    f"Try again tomorrow!"
                )

            print(
                f"[DB RATE LIMIT] ❌ {user.username} exceeded daily limit: {recipes_today + recipes_count}/{settings.max_recipes_per_day}")
            return False, message, 'daily'

        # All checks passed
        print(f"[DB RATE LIMIT] ✅ {user.username} allowed: {recipes_last_minute + recipes_count}/{settings.max_recipes_per_minute} per minute, {recipes_today + recipes_count}/{settings.max_recipes_per_day} today")
        return True, "OK", None

    @staticmethod
    def log_request(user, recipes_count=1):
        """Log a recipe generation request"""
        log = AIRateLimitLog.objects.create(
            user=user,
            endpoint='recipe_generation',
            recipes_generated=recipes_count
        )
        print(
            f"[RATE LIMIT] 📝 Logged {recipes_count} recipe(s) for {user.username}")
        return log

    @staticmethod
    def get_user_stats(user):
        """
        Get current usage statistics for a user.

        Tries Redis first for speed, falls back to PostgreSQL.
        """
        if AIRateLimiter.is_user_exempt(user):
            return {
                'exempt': True,
                'recipes_last_minute': 0,
                'recipes_today': 0,
                'limit_per_minute': 'unlimited',
                'limit_per_day': 'unlimited'
            }

        settings = AIRateLimiter.get_settings()

        # Try Redis first
        try:
            from .redis_rate_limiter import get_redis_limiter
            redis_limiter = get_redis_limiter()

            if redis_limiter.available:
                usage = redis_limiter.get_current_usage(user)
                if usage:
                    return {
                        'exempt': False,
                        'recipes_last_minute': usage['minute'],
                        'recipes_today': usage['daily'],
                        'limit_per_minute': settings.max_recipes_per_minute,
                        'limit_per_day': settings.max_recipes_per_day,
                        'remaining_today': max(0, settings.max_recipes_per_day - usage['daily'])
                    }
        except Exception as e:
            print(f"[RATE LIMIT] Redis stats failed, using DB: {e}")

        # Fall back to PostgreSQL
        now = timezone.now()

        # Per-minute stats
        one_minute_ago = now - timedelta(minutes=1)
        recipes_last_minute = sum(
            log.recipes_generated for log in AIRateLimitLog.objects.filter(
                user=user,
                endpoint='recipe_generation',
                timestamp__gte=one_minute_ago
            )
        )

        # Daily stats
        one_day_ago = now - timedelta(days=1)
        recipes_today = sum(
            log.recipes_generated for log in AIRateLimitLog.objects.filter(
                user=user,
                endpoint='recipe_generation',
                timestamp__gte=one_day_ago
            )
        )

        return {
            'exempt': False,
            'recipes_last_minute': recipes_last_minute,
            'recipes_today': recipes_today,
            'limit_per_minute': settings.max_recipes_per_minute,
            'limit_per_day': settings.max_recipes_per_day,
            'remaining_today': max(0, settings.max_recipes_per_day - recipes_today)
        }

    @staticmethod
    def get_rate_limit_headers(user):
        """
        Get HTTP headers for rate limit information.

        Returns headers compatible with standard rate limiting conventions:
        - X-RateLimit-Limit-Minute: Maximum requests per minute
        - X-RateLimit-Remaining-Minute: Remaining requests this minute
        - X-RateLimit-Reset-Minute: Unix timestamp when minute limit resets
        - X-RateLimit-Limit-Daily: Maximum requests per day
        - X-RateLimit-Remaining-Daily: Remaining requests today
        - X-RateLimit-Reset-Daily: Unix timestamp when daily limit resets
        """
        stats = AIRateLimiter.get_user_stats(user)

        # Exempt users don't need headers
        if stats.get('exempt'):
            return {}

        settings = AIRateLimiter.get_settings()
        now = timezone.now()

        # Calculate reset times
        next_minute = (now + timedelta(minutes=1)
                       ).replace(second=0, microsecond=0)
        next_day = (now + timedelta(days=1)).replace(hour=0,
                                                     minute=0, second=0, microsecond=0)

        # Calculate remaining for minute
        remaining_minute = max(
            0, settings.max_recipes_per_minute - stats['recipes_last_minute'])

        return {
            'X-RateLimit-Limit-Minute': str(settings.max_recipes_per_minute),
            'X-RateLimit-Remaining-Minute': str(remaining_minute),
            'X-RateLimit-Reset-Minute': str(int(next_minute.timestamp())),
            'X-RateLimit-Limit-Daily': str(settings.max_recipes_per_day),
            'X-RateLimit-Remaining-Daily': str(stats['remaining_today']),
            'X-RateLimit-Reset-Daily': str(int(next_day.timestamp())),
        }
