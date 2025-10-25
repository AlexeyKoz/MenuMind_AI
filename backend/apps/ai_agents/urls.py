from django.urls import path
from django.http import JsonResponse
from . import views


def ai_root(request):
    return JsonResponse({
        'message': 'AI Agents API',
        'endpoints': {
            'assistant': '/api/ai/assistant/',
            'recipes': '/api/ai/recipes/',
            'coaching': '/api/ai/coaching/',
            'rate_limit_status': '/api/ai/rate-limit-status/',
            'admin_metrics': '/api/ai/admin/metrics/ (admin only)',
        }
    })


urlpatterns = [
    path('', ai_root, name='ai_root'),
    path('recipes/', views.generate_recipes_from_inventory, name='ai_recipes'),
    path('assistant/', views.ai_assistant, name='ai_assistant'),
    path('coaching/', views.ai_coaching, name='ai_coaching'),
    path('rate-limit-status/', views.rate_limit_status, name='rate_limit_status'),
    path('admin/metrics/', views.admin_metrics, name='admin_metrics'),
]
