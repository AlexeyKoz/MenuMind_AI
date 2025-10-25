from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import redis
import sys
from django.conf import settings


@api_view(['GET'])
@permission_classes([AllowAny])
def version_info(request):
    """
    Return application version information.
    Public endpoint, no authentication required.

    GET /api/core/version/
    """
    try:
        # Import version from __init__.py
        from menumine_ai import __version__, __author__, __license__

        version_data = {
            'version': __version__,
            'app_name': 'MenuMind AI',
            'author': __author__,
            'license': __license__,
            'build_date': getattr(settings, 'APP_BUILD_DATE', None),
            'environment': 'production' if not settings.DEBUG else 'development',
            'api_version': 'v1',
            'python_version': sys.version.split()[0],
            'django_version': __import__('django').__version__,
            'server_time': timezone.now().isoformat(),
        }

        return Response(version_data)
    except Exception as e:
        return Response({
            'error': 'Version information unavailable',
            'detail': str(e)
        }, status=500)


@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint for Docker containers
    """
    from menumine_ai import __version__

    health_status = {
        'status': 'healthy',
        'version': __version__,
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
    from menumine_ai import __version__

    return JsonResponse({
        'message': 'Welcome to MenuMind AI API',
        'version': __version__,
        'endpoints': {
            'version': '/api/core/version/',
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
