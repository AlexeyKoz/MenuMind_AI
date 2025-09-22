from django.urls import path
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

def nutrition_root(request):
    return JsonResponse({
        'message': 'Nutrition API',
        'endpoints': {
            'today_summary': '/api/nutrition/entries/today_summary/',
            'weekly_report': '/api/nutrition/entries/weekly_report/',
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def today_summary(request):
    """Return today's nutrition summary (stub implementation)"""
    return Response({
        'totals': {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0
        },
        'goals': {
            'calories': request.user.daily_calories_goal,
            'protein': request.user.daily_protein_goal,
            'carbs': request.user.daily_carbs_goal,
            'fat': request.user.daily_fat_goal
        },
        'progress': {
            'calories': 0
        },
        'message': 'Nutrition tracking not yet implemented'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weekly_report(request):
    """Return weekly nutrition report (stub implementation)"""
    return Response({
        'daily_data': {},
        'insights': [
            {
                'type': 'info',
                'title': 'Nutrition Tracking Coming Soon',
                'description': 'Advanced nutrition tracking features are being developed.'
            }
        ],
        'message': 'Weekly reports not yet implemented'
    })

urlpatterns = [
    path('', nutrition_root, name='nutrition_root'),
    path('entries/today_summary/', today_summary, name='today_summary'),
    path('entries/weekly_report/', weekly_report, name='weekly_report'),
]