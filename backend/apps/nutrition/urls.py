from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserNutritionSettingsViewSet,
    NutritionEntryViewSet,
    NutritionAIViewSet
)

router = DefaultRouter()
router.register(r'settings', UserNutritionSettingsViewSet,
                basename='nutrition-settings')
router.register(r'entries', NutritionEntryViewSet, basename='nutrition-entry')
router.register(r'ai', NutritionAIViewSet, basename='nutrition-ai')

app_name = 'nutrition'

urlpatterns = [
    path('', include(router.urls)),
]
