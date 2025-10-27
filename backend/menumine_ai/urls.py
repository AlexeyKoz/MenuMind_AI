"""
URL configuration for menumine_ai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.core.views import health_check, api_root
from apps.users.views import verify_email

urlpatterns = [
    path('', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('api/', include('apps.core.urls')),
    path('api/recipes/', include('apps.recipes.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/', include('legal.urls')),  # Legal compliance endpoints
    # Django-allauth URLs (for email confirmation)
    path('accounts/', include('allauth.urls')),

    # Custom email verification endpoint (must be before dj-rest-auth)
    path('dj-rest-auth/registration/verify-email/',
         verify_email, name='verify_email'),

    # dj-rest-auth URLs (JWT-based auth)
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
]
