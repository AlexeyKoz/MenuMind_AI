from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_google import google_login

# Create router for viewsets
router = DefaultRouter()
router.register(r'profile', views.UserProfileViewSet, basename='userprofile')

def users_root(request):
    from django.http import JsonResponse
    return JsonResponse({
        'message': 'Users API',
        'endpoints': {
            'login': '/api/users/auth/login/',
            'register': '/api/users/auth/register/',
            'profile': '/api/users/profile/',
        }
    })

urlpatterns = [
    path('', users_root, name='users_root'),
    
    # Authentication endpoints
    path('auth/login/', views.login_view, name='login'),
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/google/', google_login, name='google_login'),
    
    # User profile endpoints
    path('', include(router.urls)),
]