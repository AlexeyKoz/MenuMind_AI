from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from datetime import date, timedelta, datetime
from decimal import Decimal

from .models import UserNutritionSettings, NutritionEntry
from .serializers import (
    UserNutritionSettingsSerializer,
    NutritionEntrySerializer,
    NutritionEntryCreateSerializer,
    LogFromRecipeSerializer,
    LogFromInventorySerializer,
    DailySummarySerializer,
    WeeklySummarySerializer,
    AISuggestionRequestSerializer,
    AISuggestionResponseSerializer,
    AICoachingRequestSerializer,
    AICoachingResponseSerializer
)
from .services import (
    NutritionGoalCalculator,
    NutritionCoach,
    NutritionSummaryService
)


class UserNutritionSettingsViewSet(viewsets.ModelViewSet):
    """
    Nutrition settings with privacy controls

    GET    /api/nutrition/settings/      - Get user's settings
    PUT    /api/nutrition/settings/      - Update all settings
    PATCH  /api/nutrition/settings/      - Partial update
    """
    serializer_class = UserNutritionSettingsSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'put', 'patch']  # No POST or DELETE

    def get_object(self):
        """Get or create settings for current user"""
        settings, created = UserNutritionSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings

    def list(self, request, *args, **kwargs):
        """Override list to return single object"""
        settings = self.get_object()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to always return current user's settings"""
        settings = self.get_object()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update settings"""
        settings = self.get_object()
        serializer = self.get_serializer(
            settings, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'success': True,
            'message': 'Settings updated successfully',
            'settings': serializer.data
        })

    def partial_update(self, request, *args, **kwargs):
        """Partial update settings (PATCH)"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=False, methods=['patch'], url_path='update')
    def update_settings(self, request):
        """Custom endpoint for updating settings without requiring ID"""
        settings = self.get_object()
        serializer = self.get_serializer(
            settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def goals(self, request):
        """Get calculated nutrition goals based on current settings"""
        settings = self.get_object()
        goals = NutritionGoalCalculator.calculate_goals(request.user, settings)

        return Response({
            'goals': goals,
            'source': goals.get('source', 'manual'),
            'ai_coach_enabled': settings.ai_coach_enabled,
            'goal_mode': settings.goal_mode
        })


class NutritionEntryViewSet(viewsets.ModelViewSet):
    """
    Nutrition entry CRUD operations

    List entries (with date filtering)
    Create manual entries
    Update/delete entries
    """
    serializer_class = NutritionEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get user's nutrition entries with optional date filtering"""
        queryset = NutritionEntry.objects.filter(user=self.request.user)

        # Date filtering
        date_param = self.request.query_params.get('date')
        if date_param:
            try:
                target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
                queryset = queryset.filter(date=target_date)
            except ValueError:
                pass

        # Date range filtering
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start, date__lte=end)
            except ValueError:
                pass

        # Meal type filtering
        meal_type = self.request.query_params.get('meal_type')
        if meal_type:
            queryset = queryset.filter(meal_type=meal_type)

        return queryset.order_by('-date', '-time', '-created_at')

    def perform_create(self, serializer):
        """Create entry for current user"""
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        """Use simplified serializer for creation"""
        if self.action == 'create':
            return NutritionEntryCreateSerializer
        return NutritionEntrySerializer

    @action(detail=False, methods=['post'])
    def from_recipe(self, request):
        """
        Log nutrition from a recipe

        POST /api/nutrition/entries/from_recipe/
        {
            "recipe_id": "uuid",
            "portion_multiplier": 1.0,
            "meal_type": "dinner",
            "date": "2025-10-12",
            "time": "18:30:00",
            "notes": "optional"
        }
        """
        serializer = LogFromRecipeSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Get recipe
        from apps.recipes.models import Recipe
        recipe = Recipe.objects.get(id=serializer.validated_data['recipe_id'])

        # Calculate nutrition based on portion
        multiplier = serializer.validated_data['portion_multiplier']

        # Get recipe nutrition (assuming Recipe model has these fields)
        # If not, we'll need to calculate from ingredients
        calories = getattr(recipe, 'calories', 0) * multiplier
        protein = getattr(recipe, 'protein', 0) * multiplier
        carbs = getattr(recipe, 'carbs', 0) * multiplier
        fat = getattr(recipe, 'fat', 0) * multiplier

        # Create entry
        entry = NutritionEntry.objects.create(
            user=request.user,
            date=serializer.validated_data['date'],
            time=serializer.validated_data.get('time'),
            meal_type=serializer.validated_data['meal_type'],
            entry_type='recipe',
            recipe=recipe,
            food_name=recipe.name,
            portion_size=multiplier,
            portion_unit='serving',
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            notes=serializer.validated_data.get('notes', '')
        )

        return Response({
            'success': True,
            'message': f'Logged {recipe.name} to nutrition tracker',
            'entry': NutritionEntrySerializer(entry).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def from_inventory(self, request):
        """
        Log nutrition from inventory item

        POST /api/nutrition/entries/from_inventory/
        {
            "inventory_item_id": "uuid",
            "amount_grams": 150,
            "meal_type": "snack",
            "date": "2025-10-12",
            "time": "16:00:00",
            "update_inventory": true,
            "notes": "optional"
        }
        """
        serializer = LogFromInventorySerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Get inventory item
        from apps.shopping.models import Inventory
        item = Inventory.objects.get(
            id=serializer.validated_data['inventory_item_id'])

        # Calculate nutrition per 100g
        amount_grams = serializer.validated_data['amount_grams']
        multiplier = amount_grams / 100.0

        # Calculate nutrition (assuming nutrition per 100g)
        calories = getattr(item, 'calories_per_100g', 0) * multiplier
        protein = getattr(item, 'protein_per_100g', 0) * multiplier
        carbs = getattr(item, 'carbs_per_100g', 0) * multiplier
        fat = getattr(item, 'fat_per_100g', 0) * multiplier

        # Create entry
        entry = NutritionEntry.objects.create(
            user=request.user,
            date=serializer.validated_data['date'],
            time=serializer.validated_data.get('time'),
            meal_type=serializer.validated_data['meal_type'],
            entry_type='product',
            inventory_item=item,
            food_name=item.name,
            portion_size=amount_grams,
            portion_unit='grams',
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            notes=serializer.validated_data.get('notes', '')
        )

        # Update inventory if requested
        if serializer.validated_data.get('update_inventory', True):
            # Convert grams to item's unit
            # This is simplified - you'd need more logic based on item.unit
            current_quantity = float(item.quantity)
            deduction = amount_grams / 1000.0  # Assume kg
            item.quantity = str(max(0, current_quantity - deduction))
            item.save()

        return Response({
            'success': True,
            'message': f'Logged {item.name} to nutrition tracker',
            'entry': NutritionEntrySerializer(entry).data,
            'inventory_updated': serializer.validated_data.get('update_inventory', True)
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def today_summary(self, request):
        """
        Get today's nutrition summary

        GET /api/nutrition/entries/today_summary/
        """
        # Get user's nutrition settings
        settings, _ = UserNutritionSettings.objects.get_or_create(
            user=request.user)

        # Get summary
        today = date.today()
        summary_data = NutritionSummaryService.get_daily_summary(
            request.user,
            today,
            settings
        )

        # Serialize
        serializer = DailySummarySerializer(summary_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def weekly_summary(self, request):
        """
        Get weekly nutrition summary

        GET /api/nutrition/entries/weekly_summary/
        Optional query param: week_start (YYYY-MM-DD)
        """
        # Get user's nutrition settings
        settings, _ = UserNutritionSettings.objects.get_or_create(
            user=request.user)

        # Get week start (default to current week Monday)
        week_start_param = request.query_params.get('week_start')
        if week_start_param:
            try:
                week_start = datetime.strptime(
                    week_start_param, '%Y-%m-%d').date()
            except ValueError:
                week_start = date.today() - timedelta(days=date.today().weekday())
        else:
            week_start = date.today() - timedelta(days=date.today().weekday())

        # Get summary
        summary_data = NutritionSummaryService.get_weekly_summary(
            request.user,
            week_start,
            settings
        )

        # Serialize
        serializer = WeeklySummarySerializer(summary_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """
        Get monthly nutrition summary

        GET /api/nutrition/entries/monthly_summary/
        Optional query param: month (YYYY-MM)
        """
        # Get user's nutrition settings
        settings, _ = UserNutritionSettings.objects.get_or_create(
            user=request.user)

        # Get month
        month_param = request.query_params.get('month')
        if month_param:
            try:
                year, month = map(int, month_param.split('-'))
                month_start = date(year, month, 1)
            except ValueError:
                month_start = date.today().replace(day=1)
        else:
            month_start = date.today().replace(day=1)

        # Calculate month end
        if month_start.month == 12:
            month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(month_start.year,
                             month_start.month + 1, 1) - timedelta(days=1)

        # Get entries for month
        entries = NutritionEntry.objects.filter(
            user=request.user,
            date__gte=month_start,
            date__lte=month_end
        )

        # Calculate totals
        from django.db.models import Sum
        totals = entries.aggregate(
            total_calories=Sum('calories'),
            total_protein=Sum('protein'),
            total_carbs=Sum('carbs'),
            total_fat=Sum('fat')
        )

        # Get goals
        goals = NutritionGoalCalculator.calculate_goals(request.user, settings)

        # Daily averages
        days_in_month = (month_end - month_start).days + 1
        entry_days = entries.values('date').distinct().count() or 1

        return Response({
            'month': month_start.strftime('%Y-%m'),
            'month_start': month_start,
            'month_end': month_end,
            'days_logged': entry_days,
            'days_in_month': days_in_month,
            'totals': {
                'calories': float(totals['total_calories'] or 0),
                'protein': float(totals['total_protein'] or 0),
                'carbs': float(totals['total_carbs'] or 0),
                'fat': float(totals['total_fat'] or 0)
            },
            'daily_averages': {
                'calories': float(totals['total_calories'] or 0) / entry_days,
                'protein': float(totals['total_protein'] or 0) / entry_days,
                'carbs': float(totals['total_carbs'] or 0) / entry_days,
                'fat': float(totals['total_fat'] or 0) / entry_days
            },
            'goals': goals
        })


class NutritionAIViewSet(viewsets.ViewSet):
    """
    AI Coach endpoints (only work when AI coach is enabled)
    """
    permission_classes = [IsAuthenticated]

    def _check_ai_enabled(self, user):
        """Check if AI coach is enabled for user"""
        settings, _ = UserNutritionSettings.objects.get_or_create(user=user)
        return settings, settings.ai_coach_enabled

    @action(detail=False, methods=['post'])
    def suggestions(self, request):
        """
        Get AI meal suggestions

        POST /api/nutrition/ai/suggestions/
        {
            "meal_type": "dinner",  # optional
            "max_calories": 600     # optional
        }
        """
        settings, ai_enabled = self._check_ai_enabled(request.user)

        if not ai_enabled:
            return Response({
                'ai_enabled': False,
                'message': 'AI Coach is disabled. Enable it in settings to get personalized suggestions.'
            })

        # Validate request
        serializer = AISuggestionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get today's summary
        today_summary = NutritionSummaryService.get_daily_summary(
            request.user,
            date.today(),
            settings
        )

        # Get AI suggestions
        coach = NutritionCoach()
        result = coach.generate_daily_suggestion(
            request.user,
            settings,
            today_summary,
            meal_type=serializer.validated_data.get('meal_type'),
            max_calories=serializer.validated_data.get('max_calories')
        )

        return Response(result)

    @action(detail=False, methods=['post'])
    def coaching(self, request):
        """
        Ask AI coach a question

        POST /api/nutrition/ai/coaching/
        {
            "question": "I'm still hungry after dinner, what should I do?"
        }
        """
        settings, ai_enabled = self._check_ai_enabled(request.user)

        if not ai_enabled:
            return Response({
                'advice': 'AI Coach is disabled. Enable it in settings to ask questions.'
            })

        # Validate request
        serializer = AICoachingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get today's summary
        today_summary = NutritionSummaryService.get_daily_summary(
            request.user,
            date.today(),
            settings
        )

        # Get AI coaching
        coach = NutritionCoach()
        result = coach.answer_coaching_question(
            request.user,
            settings,
            serializer.validated_data['question'],
            today_summary
        )

        return Response(result)

    @action(detail=False, methods=['get'])
    def weekly_report(self, request):
        """
        Get AI-generated weekly insights

        GET /api/nutrition/ai/weekly_report/
        """
        settings, ai_enabled = self._check_ai_enabled(request.user)

        if not ai_enabled:
            return Response({
                'ai_enabled': False,
                'message': 'AI Coach is disabled. Enable it in settings for weekly insights.'
            })

        # Get week start
        week_start = date.today() - timedelta(days=date.today().weekday())

        # Get weekly summary
        weekly_data = NutritionSummaryService.get_weekly_summary(
            request.user,
            week_start,
            settings
        )

        # Generate AI insights (simplified for now)
        coach = NutritionCoach()

        # Build summary context
        avg_calories = weekly_data['daily_averages']['calories']
        avg_protein = weekly_data['daily_averages']['protein']
        goals = NutritionGoalCalculator.calculate_goals(request.user, settings)

        adherence = weekly_data['goal_adherence']

        insights = {
            'week_start': week_start,
            'week_end': week_start + timedelta(days=6),
            'summary': {
                'average_calories': avg_calories,
                'average_protein': avg_protein,
                'goal_adherence': adherence
            },
            'message': f"You averaged {int(avg_calories)} calories and {int(avg_protein)}g protein this week. Keep up the great work!",
            'recommendations': [
                f"Your calorie adherence was {adherence['calories']:.1f}%",
                f"Your protein adherence was {adherence['protein']:.1f}%"
            ]
        }

        return Response(insights)
