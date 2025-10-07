from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from asgiref.sync import async_to_sync

from .models import NutritionEntry, NutritionGoal, MealPlan
from .serializers import (
    NutritionEntrySerializer, NutritionGoalSerializer,
    MealPlanSerializer
)
from apps.ai_agents.services import AIOrchestrator


class NutritionEntryViewSet(viewsets.ModelViewSet):
    """Nutrition tracking and analysis"""
    serializer_class = NutritionEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NutritionEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def ai_log_meal(self, request):
        """Log meal using natural language"""
        text = request.data.get('text', '')
        meal_type = request.data.get('meal_type', 'snack')

        orchestrator = AIOrchestrator()
        context = {
            'current_stats': {
                'calories_today': self._get_calories_today(request.user),
                'macros_today': self._get_macros_today(request.user)
            },
            'goals': {
                'daily_calories': request.user.daily_calories_goal,
                'daily_protein': request.user.daily_protein_goal
            }
        }

        # Process with AI
        result = async_to_sync(orchestrator.nutrition_coach.analyze_nutrition)(
            text, context
        )

        if result:
            # Create nutrition entry
            entry = NutritionEntry.objects.create(
                user=request.user,
                meal_type=meal_type,
                food_description=text,
                calories=result['total_nutrition']['calories'],
                protein=result['total_nutrition']['protein'],
                carbs=result['total_nutrition']['carbs'],
                fat=result['total_nutrition']['fat'],
                ai_analyzed=True
            )

            return Response({
                'success': True,
                'entry': NutritionEntrySerializer(entry).data,
                'analysis': result
            })

        return Response({
            'success': False,
            'message': 'Could not analyze meal'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def today_summary(self, request):
        """Get today's nutrition summary"""
        today_entries = self.get_queryset().filter(
            created_at__date=timezone.now().date()
        )

        total_calories = sum(e.calories for e in today_entries)
        total_protein = sum(e.protein for e in today_entries)
        total_carbs = sum(e.carbs for e in today_entries)
        total_fat = sum(e.fat for e in today_entries)

        return Response({
            'date': timezone.now().date(),
            'totals': {
                'calories': total_calories,
                'protein': total_protein,
                'carbs': total_carbs,
                'fat': total_fat
            },
            'goals': {
                'calories': request.user.daily_calories_goal,
                'protein': request.user.daily_protein_goal,
                'carbs': request.user.daily_carbs_goal,
                'fat': request.user.daily_fat_goal
            },
            'progress': {
                'calories': round((total_calories / request.user.daily_calories_goal) * 100, 1),
                'protein': round((total_protein / request.user.daily_protein_goal) * 100, 1),
                'carbs': round((total_carbs / request.user.daily_carbs_goal) * 100, 1),
                'fat': round((total_fat / request.user.daily_fat_goal) * 100, 1)
            },
            'entries': NutritionEntrySerializer(today_entries, many=True).data
        })

    @action(detail=False, methods=['get'])
    def weekly_report(self, request):
        """Get weekly nutrition report"""
        week_ago = timezone.now() - timedelta(days=7)
        week_entries = self.get_queryset().filter(
            created_at__gte=week_ago
        )

        # Calculate daily averages
        days_data = {}
        for entry in week_entries:
            date = entry.created_at.date()
            if date not in days_data:
                days_data[date] = {
                    'calories': 0, 'protein': 0,
                    'carbs': 0, 'fat': 0
                }
            days_data[date]['calories'] += entry.calories
            days_data[date]['protein'] += entry.protein
            days_data[date]['carbs'] += entry.carbs
            days_data[date]['fat'] += entry.fat

        # Generate insights
        orchestrator = AIOrchestrator()
        insights = async_to_sync(orchestrator.generate_nutrition_insights)(
            request.user.id
        )

        return Response({
            'period': {
                'start': week_ago.date(),
                'end': timezone.now().date()
            },
            'daily_data': days_data,
            'averages': {
                'calories': sum(d['calories'] for d in days_data.values()) / max(len(days_data), 1),
                'protein': sum(d['protein'] for d in days_data.values()) / max(len(days_data), 1),
                'carbs': sum(d['carbs'] for d in days_data.values()) / max(len(days_data), 1),
                'fat': sum(d['fat'] for d in days_data.values()) / max(len(days_data), 1)
            },
            'insights': insights
        })

    @action(detail=False, methods=['post'])
    def get_coaching(self, request):
        """Get AI nutrition coaching advice"""
        orchestrator = AIOrchestrator()

        # Gather context
        today_entries = self.get_queryset().filter(
            created_at__date=timezone.now().date()
        )

        context = {
            'current_stats': {
                'calories_today': sum(e.calories for e in today_entries),
                'protein_today': sum(e.protein for e in today_entries),
                'weight': float(request.user.weight_kg) if request.user.weight_kg else None,
                'activity_level': request.user.activity_level
            },
            'goals': {
                'calories': request.user.daily_calories_goal,
                'protein': request.user.daily_protein_goal,
                'carbs': request.user.daily_carbs_goal,
                'fat': request.user.daily_fat_goal
            },
            'recent_meals': [
                {
                    'meal': e.food_description,
                    'calories': e.calories,
                    'time': e.created_at.strftime('%H:%M')
                }
                for e in today_entries
            ]
        }

        advice = async_to_sync(orchestrator.nutrition_coach.generate_advice)(
            context
        )

        return Response(advice)

    def _get_calories_today(self, user):
        today_entries = NutritionEntry.objects.filter(
            user=user,
            created_at__date=timezone.now().date()
        )
        return sum(e.calories for e in today_entries)

    def _get_macros_today(self, user):
        today_entries = NutritionEntry.objects.filter(
            user=user,
            created_at__date=timezone.now().date()
        )
        return {
            'protein': sum(e.protein for e in today_entries),
            'carbs': sum(e.carbs for e in today_entries),
            'fat': sum(e.fat for e in today_entries)
        }
