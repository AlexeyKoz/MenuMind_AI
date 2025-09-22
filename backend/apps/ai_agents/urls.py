from django.urls import path
from django.http import JsonResponse

def ai_root(request):
    return JsonResponse({
        'message': 'AI Agents API',
        'endpoints': {
            'assistant': '/api/ai/assistant/',
            'recipes': '/api/ai/recipes/',
            'coaching': '/api/ai/coaching/',
        }
    })

urlpatterns = [
    path('', ai_root, name='ai_root'),
    # AI URLs will be added here when views are implemented
]