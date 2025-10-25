"""
Dashboard Analytics Views

API endpoints for dashboard data and insights with multilingual support.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from asgiref.sync import async_to_sync

from .models import Achievement, UserStreak, RecipeCookingLog, DashboardCache
from .serializers import (
    AchievementSerializer,
    UserStreakSerializer,
    RecipeCookingLogSerializer,
    DashboardOverviewSerializer,
    AIInsightsSerializer
)
from .services import DashboardAnalyticsService, AIInsightsService
from .language_utils import get_user_language

# Initialize logger
logger = logging.getLogger(__name__)


class DashboardViewSet(viewsets.ViewSet):
    """
    Dashboard API endpoints.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='overview')
    def get_overview(self, request):
        """
        Get complete dashboard overview

        NEW: Returns data in user's language

        Query Parameters:
            - period: '7days' | '30days' | '90days' | '1year' (default: '30days')
            - include_ai: 'true' | 'false' (default: 'true')
            - lang: 'en' | 'he' | 'ru' (optional, auto-detected)

        Response:
            Complete dashboard data with all analytics and AI insights
            in the requested language
        """
        # Detect language
        user_language = get_user_language(request, request.user)

        # Get parameters
        period = request.query_params.get('period', '30days')
        include_ai = request.query_params.get(
            'include_ai', 'true').lower() == 'true'

        # Log request
        logger.info(f"Dashboard overview requested: user={request.user.username}, "
                    f"period={period}, language={user_language}, include_ai={include_ai}")

        # Check cache first (language-specific)
        cache = DashboardCache.objects.filter(
            user=request.user,
            period=period,
            language=user_language  # ← NEW: Language-specific cache lookup
        ).first()

        if cache and not cache.is_expired():
            logger.info(
                f"Dashboard cache HIT for {request.user.username} ({user_language})")

            # Use cached data
            data = {
                'period': period,
                'language': user_language,  # ← NEW: Add language to cached response
                'overview': {
                    'total_spent': cache.shopping_data.get('total_spent', 0),
                    'recipes_cooked': cache.recipes_data.get('total_cooked', 0),
                    'inventory_items': cache.inventory_data.get('total_items', 0),
                    'nutrition_days_logged': cache.nutrition_data.get('days_logged') if cache.nutrition_data else None
                },
                'shopping': cache.shopping_data,
                'recipes': cache.recipes_data,
                'inventory': cache.inventory_data,
                'nutrition': cache.nutrition_data,
                'achievements': cache.achievements_data,
                'cached': True,  # ← NEW: Cache metadata
                'generated_at': cache.created_at,  # ← NEW: When data was generated
                'cached_at': cache.updated_at.isoformat()
            }

            if include_ai and cache.ai_insights:
                # AI insights are already cached, just include them
                data['ai_insights'] = cache.ai_insights

            serializer = DashboardOverviewSerializer(data)
            return Response(serializer.data)

        # Calculate fresh data with language support
        logger.info(
            f"Dashboard cache MISS for {request.user.username} ({user_language}) - generating fresh data")

        analytics = DashboardAnalyticsService(request.user)

        # NEW: Get complete dashboard overview with language support
        data = analytics.get_dashboard_overview(
            user=request.user,
            period=period,
            include_ai=include_ai,
            language=user_language  # ← NEW: Pass language to service
        )

        # Add response metadata
        data['language'] = user_language  # ← NEW: Language metadata
        data['period'] = period
        data['generated_at'] = timezone.now().isoformat()
        data['cached'] = False  # ← NEW: Cache metadata

        serializer = DashboardOverviewSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='ai_insights')
    def get_ai_insights(self, request):
        """
        GET /api/dashboard/ai_insights/
        Get AI insights only.

        NEW: Language-aware AI insights
        """
        period = request.query_params.get('period', '30days')
        user_language = get_user_language(request, request.user)

        # Check cache (language-specific)
        cache = DashboardCache.objects.filter(
            user=request.user,
            period=period,
            language=user_language  # ← NEW: Language-specific cache lookup
        ).first()

        if cache and cache.ai_insights and not cache.is_expired():
            serializer = AIInsightsSerializer(cache.ai_insights)
            return Response(serializer.data)

        # Generate fresh insights with language support
        analytics = DashboardAnalyticsService(request.user)
        period_days = analytics._get_period_days(period)
        start_date = timezone.now() - timedelta(days=period_days)

        data = {
            'shopping': analytics.get_shopping_analytics(request.user, start_date, user_language),
            'recipes': analytics.get_recipes_analytics(request.user, start_date, user_language),
            'inventory': analytics.get_inventory_analytics(request.user, user_language),
            'nutrition': analytics.get_nutrition_analytics(request.user, start_date, user_language)
        }

        ai_service = AIInsightsService()
        insights = ai_service.generate_all_insights(
            request.user, data, user_language)

        # Update cache (language-specific)
        if cache:
            cache.ai_insights = insights
            cache.ai_generated_at = timezone.now()
            cache.save()

        serializer = AIInsightsSerializer(insights)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='ai_insights/regenerate')
    def regenerate_ai_insights(self, request):
        """
        POST /api/dashboard/ai_insights/regenerate/
        Force regenerate AI insights (rate limited).
        """
        period = request.data.get('period', '30days')

        # Delete cache to force regeneration (all languages)
        DashboardCache.objects.filter(
            user=request.user, period=period).delete()

        # Generate fresh
        analytics = DashboardAnalyticsService(request.user)
        period_days = analytics._get_period_days(period)
        start_date = timezone.now() - timedelta(days=period_days)

        data = {
            # Default to English for regeneration
            'shopping': analytics.get_shopping_analytics(request.user, start_date, 'en'),
            'recipes': analytics.get_recipes_analytics(request.user, start_date, 'en'),
            'inventory': analytics.get_inventory_analytics(request.user, 'en'),
            'nutrition': analytics.get_nutrition_analytics(request.user, start_date, 'en')
        }

        ai_service = AIInsightsService()
        insights = ai_service.generate_all_insights(request.user, data, 'en')

        serializer = AIInsightsSerializer(insights)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='achievements')
    def get_achievements(self, request):
        """
        GET /api/dashboard/achievements/
        Get achievements and streaks.

        NEW: Language-aware achievements
        """
        user_language = get_user_language(request, request.user)

        analytics = DashboardAnalyticsService(request.user)
        achievements_data = analytics.get_achievements_data(
            request.user, user_language)

        return Response(achievements_data)

    @action(detail=False, methods=['post'], url_path='invalidate-cache')
    def invalidate_cache(self, request):
        """
        Invalidate dashboard cache

        NEW: Can invalidate specific language or all languages

        Body:
            {
                "language": "en",  // optional: specific language
                "period": "30days"  // optional: specific period
            }
        """
        language = request.data.get('language')
        period = request.data.get('period')

        # Build filter
        filters = {'user': request.user}
        if language:
            filters['language'] = language
        if period:
            filters['period'] = period

        # Delete cache
        deleted_count, _ = DashboardCache.objects.filter(**filters).delete()

        logger.info(f"Invalidated {deleted_count} dashboard cache entries for "
                    f"user={request.user.username}, language={language or 'all'}, "
                    f"period={period or 'all'}")

        return Response({
            'success': True,
            'deleted_count': deleted_count,
            'language': language or 'all',
            'period': period or 'all'
        })

    @action(detail=False, methods=['get'], url_path='cache-stats')
    def cache_stats(self, request):
        """
        Get dashboard cache statistics

        NEW: Shows cache status for all languages
        """
        # Get all cache entries for this user
        cache_entries = DashboardCache.objects.filter(
            user=request.user
        ).values('language', 'period', 'created_at', 'expires_at')

        # Group by language
        stats_by_language = {}
        for entry in cache_entries:
            lang = entry['language']
            if lang not in stats_by_language:
                stats_by_language[lang] = []

            stats_by_language[lang].append({
                'period': entry['period'],
                'created_at': entry['created_at'].isoformat(),
                'expires_at': entry['expires_at'].isoformat(),
                'is_expired': entry['expires_at'] < timezone.now()
            })

        return Response({
            'user_id': request.user.id,
            'cache_enabled': True,
            'languages': stats_by_language,
            'total_cached': len(cache_entries)
        })


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Achievements API.
    """
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Achievement.objects.filter(user=self.request.user)


class UserStreakViewSet(viewsets.ReadOnlyModelViewSet):
    """
    User Streaks API.
    """
    serializer_class = UserStreakSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserStreak.objects.filter(user=self.request.user)


class RecipeCookingLogViewSet(viewsets.ModelViewSet):
    """
    Recipe Cooking Logs API.
    """
    serializer_class = RecipeCookingLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RecipeCookingLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        log = serializer.save(user=self.request.user)

        # Update streak
        streak, created = UserStreak.objects.get_or_create(
            user=self.request.user,
            streak_type='recipe_cooking'
        )
        streak.increment(log.cooked_at.date())
