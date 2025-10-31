from django.urls import path, include
from . import views
from .views_updates import get_app_updates

urlpatterns = [
    # API root endpoint
    path('', views.api_root, name='api_root'),

    # System endpoints
    path('version/', views.version_info, name='version-info'),
    path('health/', views.health_check, name='health-check'),
    
    # App Updates endpoint
    path('updates/', get_app_updates, name='app-updates'),

    # Include other app URLs here
    path('shopping/', include('apps.shopping.urls')),
    path('nutrition/', include('apps.nutrition.urls')),
    path('ai/', include('apps.ai_agents.urls')),
    path('users/', include('apps.users.urls')),
]
