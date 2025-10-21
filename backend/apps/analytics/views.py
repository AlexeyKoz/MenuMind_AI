"""
Dashboard Analytics Views

API endpoints for dashboard data and insights.
"""
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


class DashboardViewSet(viewsets.ViewSet):
    """
    Dashboard API endpoints.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='overview')
    def get_overview(self, request):
        """
        GET /api/dashboard/overview/
        Query params:
          - period: 7days|30days|90days|1year (default: 30days)
          - include_ai: true|false (default: true if AI enabled)
        """
        period = request.query_params.get('period', '30days')
        include_ai = request.query_params.get(
            'include_ai', 'true').lower() == 'true'

        # Check cache first
        cache = DashboardCache.objects.filter(
            user=request.user, period=period).first()
        if cache and not cache.is_expired():
            # Use cached data
            data = {
                'period': period,
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
                'ai_insight_of_day': None
            }

            if include_ai and cache.ai_insights:
                data.update(cache.ai_insights)
                # Generate insight of day from cached data
                ai_service = AIInsightsService(request.user)
                data['ai_insight_of_day'] = ai_service.generate_insight_of_day(
                    data)

            serializer = DashboardOverviewSerializer(data)
            return Response(serializer.data)

        # Calculate fresh data
        analytics = DashboardAnalyticsService(request.user)

        overview = analytics.get_overview(period)
        shopping = analytics.get_shopping_analytics(period)
        recipes = analytics.get_recipes_analytics(period)
        inventory = analytics.get_inventory_analytics(period)
        nutrition = analytics.get_nutrition_analytics(period)
        achievements = analytics.get_achievements_analytics()

        data = {
            'period': period,
            'overview': overview,
            'shopping': shopping,
            'recipes': recipes,
            'inventory': inventory,
            'nutrition': nutrition,
            'achievements': achievements,
            'ai_insight_of_day': None
        }

        # Generate AI insights if requested
        if include_ai:
            ai_service = AIInsightsService(request.user)
            ai_insights = async_to_sync(ai_service.generate_all_insights)(data)
            data.update(ai_insights)
            data['ai_insight_of_day'] = ai_service.generate_insight_of_day(
                data)

            # Cache the data with AI insights
            expires_at = timezone.now() + timedelta(hours=1)
            DashboardCache.objects.update_or_create(
                user=request.user,
                period=period,
                defaults={
                    'shopping_data': shopping,
                    'recipes_data': recipes,
                    'inventory_data': inventory,
                    'nutrition_data': nutrition,
                    'achievements_data': achievements,
                    'ai_insights': ai_insights,
                    'ai_generated_at': timezone.now(),
                    'expires_at': expires_at
                }
            )
        else:
            # Cache without AI insights
            expires_at = timezone.now() + timedelta(minutes=15)
            DashboardCache.objects.update_or_create(
                user=request.user,
                period=period,
                defaults={
                    'shopping_data': shopping,
                    'recipes_data': recipes,
                    'inventory_data': inventory,
                    'nutrition_data': nutrition,
                    'achievements_data': achievements,
                    'expires_at': expires_at
                }
            )

        serializer = DashboardOverviewSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='ai_insights')
    def get_ai_insights(self, request):
        """
        GET /api/dashboard/ai_insights/
        Get AI insights only.
        """
        period = request.query_params.get('period', '30days')

        # Check cache
        cache = DashboardCache.objects.filter(
            user=request.user, period=period).first()
        if cache and cache.ai_insights and not cache.is_expired():
            serializer = AIInsightsSerializer(cache.ai_insights)
            return Response(serializer.data)

        # Generate fresh insights
        analytics = DashboardAnalyticsService(request.user)
        data = {
            'shopping': analytics.get_shopping_analytics(period),
            'recipes': analytics.get_recipes_analytics(period),
            'inventory': analytics.get_inventory_analytics(period),
            'nutrition': analytics.get_nutrition_analytics(period)
        }

        ai_service = AIInsightsService(request.user)
        insights = async_to_sync(ai_service.generate_all_insights)(data)

        # Update cache
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

        # Delete cache to force regeneration
        DashboardCache.objects.filter(
            user=request.user, period=period).delete()

        # Generate fresh
        analytics = DashboardAnalyticsService(request.user)
        data = {
            'shopping': analytics.get_shopping_analytics(period),
            'recipes': analytics.get_recipes_analytics(period),
            'inventory': analytics.get_inventory_analytics(period),
            'nutrition': analytics.get_nutrition_analytics(period)
        }

        ai_service = AIInsightsService(request.user)
        insights = async_to_sync(ai_service.generate_all_insights)(data)

        serializer = AIInsightsSerializer(insights)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='achievements')
    def get_achievements(self, request):
        """
        GET /api/dashboard/achievements/
        Get achievements and streaks.
        """
        analytics = DashboardAnalyticsService(request.user)
        achievements_data = analytics.get_achievements_analytics()

        return Response(achievements_data)


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










