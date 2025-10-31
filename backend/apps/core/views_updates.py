"""
API views for App Updates
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from apps.core.models import AppUpdate


@api_view(['GET'])
@permission_classes([AllowAny])
def get_app_updates(request):
    """
    Get all published app updates filtered by language
    
    Query params:
    - language: Language code (en, he, ru) - defaults to 'en'
    - limit: Number of updates to return - defaults to 50
    """
    language = request.GET.get('language', 'en')
    limit = int(request.GET.get('limit', 50))
    
    # Validate language
    if language not in ['en', 'he', 'ru']:
        language = 'en'
    
    # Fetch published updates for the language
    updates = AppUpdate.objects.filter(
        is_published=True,
        language=language
    ).order_by('-is_featured', '-publish_date', '-created_at')[:limit]
    
    # Serialize the updates
    updates_data = []
    for update in updates:
        updates_data.append({
            'id': str(update.id),
            'title': update.title,
            'description': update.description,
            'status': update.status,
            'version': update.version,
            'publish_date': update.publish_date.isoformat(),
            'is_featured': update.is_featured,
            'language': update.language,
        })
    
    return Response({
        'success': True,
        'language': language,
        'count': len(updates_data),
        'updates': updates_data,
    }, status=status.HTTP_200_OK)



