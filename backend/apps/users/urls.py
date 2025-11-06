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
            'export-data': '/api/users/export-data/',
            'delete-account': '/api/users/delete-account/',
        }
    })


urlpatterns = [
    path('', users_root, name='users_root'),

    # Authentication endpoints
    path('auth/login/', views.login_view, name='login'),
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/google/', google_login, name='google_login'),
    path('auth/resend-verification/',
         views.resend_verification_email, name='resend_verification'),

    # GDPR/CCPA Compliance - Data Rights
    path('export-data/', views.export_user_data, name='export_user_data'),
    path('get-data/', views.get_user_data_export, name='get_user_data_export'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('cancel-deletion/', views.cancel_account_deletion,
         name='cancel_account_deletion'),
    
    # AI Quota & Feature Access
    path('quota-status/', views.quota_status, name='quota_status'),
    path('dashboard-status/', views.dashboard_status, name='dashboard_status'),
    path('shopping-access-status/', views.shopping_access_status, name='shopping_access_status'),

    # User profile endpoints
    path('', include(router.urls)),
]
