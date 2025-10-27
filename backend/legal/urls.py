"""
URL routing for Legal Compliance app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LegalViewSet, PrivacyViewSet

# Create router for viewsets
router = DefaultRouter()
router.register(r'legal', LegalViewSet, basename='legal')
router.register(r'privacy', PrivacyViewSet, basename='privacy')

urlpatterns = [
    path('', include(router.urls)),
]
