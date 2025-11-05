"""
URL Configuration for Branding app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SiteLogoViewSet, SiteSettingsViewSet

router = DefaultRouter()
router.register(r'logos', SiteLogoViewSet, basename='logo')
router.register(r'settings', SiteSettingsViewSet, basename='settings')

app_name = 'branding'

urlpatterns = [
    path('', include(router.urls)),
]

