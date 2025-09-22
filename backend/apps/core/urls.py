from django.urls import path, include
from . import views

urlpatterns = [
    # API root endpoint
    path('', views.api_root, name='api_root'),

    # Include other app URLs here
    path('shopping/', include('apps.shopping.urls')),
    path('nutrition/', include('apps.nutrition.urls')),
    path('ai/', include('apps.ai_agents.urls')),
    path('users/', include('apps.users.urls')),
]
