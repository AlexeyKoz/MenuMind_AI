from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardViewSet,
    AchievementViewSet,
    UserStreakViewSet,
    RecipeCookingLogViewSet
)

router = DefaultRouter()
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'achievements', AchievementViewSet, basename='achievement')
router.register(r'streaks', UserStreakViewSet, basename='streak')
router.register(r'cooking-logs', RecipeCookingLogViewSet,
                basename='cooking-log')

urlpatterns = [
    path('', include(router.urls)),
]



