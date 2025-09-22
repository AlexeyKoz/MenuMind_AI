from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.core.cache import cache
import redis
from django.conf import settings


@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint for Docker containers
    """
    health_status = {
        'status': 'healthy',
        'timestamp': None,
        'services': {}
    }

    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'

    # Check Cache connection (Redis or in-memory)
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        health_status['services']['cache'] = 'healthy'
    except Exception as e:
        health_status['services']['cache'] = f'unhealthy: {str(e)}'
        # Don't mark as unhealthy for cache issues in development
        if 'redis' in str(e).lower():
            health_status['services']['cache'] = 'redis_unavailable_using_dummy'

    # Add timestamp
    from datetime import datetime
    health_status['timestamp'] = datetime.now().isoformat()

    # Return appropriate status code
    status_code = 200 if health_status['status'] == 'healthy' else 503

    return JsonResponse(health_status, status=status_code)


def api_root(request):
    return JsonResponse({
        'message': 'Welcome to MenuMind AI API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health/',
            'admin': '/admin/',
            'api': '/api/',
            'shopping': '/api/shopping/',
            'nutrition': '/api/nutrition/',
            'ai': '/api/ai/',
            'users': '/api/users/',
        },
        'status': 'running'
    })
