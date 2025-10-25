"""
Dashboard Analytics Services

Calculates analytics data from shopping, recipes, inventory, and nutrition modules.
Generates AI-powered insights and recommendations with multilingual support.
"""
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from django.conf import settings
import os

from apps.shopping.models import ShoppingList, ShoppingItem, Inventory
from apps.recipes.models import Recipe, CanonicalRecipe, RecipeReview
from apps.nutrition.models import NutritionEntry
from .models import Achievement, UserStreak, RecipeCookingLog, DashboardCache

# NEW: Import translation services
from apps.core.services import get_iml_service
from apps.recipes.models import RecipeTranslation

logger = logging.getLogger(__name__)


def convert_decimals(obj):
    """
    Recursively convert Decimal objects to float for JSON serialization.
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_decimals(item) for item in obj)
    return obj


class DashboardAnalyticsService:
    """Main service for calculating dashboard analytics with multilingual support."""

    def __init__(self, user):
        self.user = user
        # NEW: Import translation services
        self.iml_service = get_iml_service()

    def get_period_dates(self, period: str):
        """Get start and end dates for a period."""
        now = timezone.now()

        if period == '7days':
            start_date = now - timedelta(days=7)
        elif period == '30days':
            start_date = now - timedelta(days=30)
        elif period == '90days':
            start_date = now - timedelta(days=90)
        elif period == '1year':
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)

        return start_date, now

    def get_overview(self, period: str) -> Dict:
        """Get quick overview stats."""
        start_date, end_date = self.get_period_dates(period)

        # Shopping: total spent
        shopping_lists = ShoppingList.objects.filter(
            creator=self.user,
            completed_at__isnull=False,  # Only completed lists
            updated_at__range=[start_date, end_date]
        )
        total_spent = 0
        for sl in shopping_lists:
            items = ShoppingItem.objects.filter(
                shopping_list=sl, purchased=True)
            for item in items:
                if item.price:
                    total_spent += float(item.price)

        # Recipes: total cooked
        recipes_cooked = RecipeCookingLog.objects.filter(
            user=self.user,
            cooked_at__range=[start_date, end_date]
        ).count()

        # Inventory: current count
        inventory_items = Inventory.objects.filter(user=self.user).count()

        # Nutrition: days logged (only if AI enabled)
        nutrition_days_logged = None
        if hasattr(self.user, 'nutrition_settings') and self.user.nutrition_settings.ai_coach_enabled:
            nutrition_days_logged = NutritionEntry.objects.filter(
                user=self.user,
                date__range=[start_date.date(), end_date.date()]
            ).values('date').distinct().count()

        return convert_decimals({
            'total_spent': round(total_spent, 2),
            'recipes_cooked': recipes_cooked,
            'inventory_items': inventory_items,
            'nutrition_days_logged': nutrition_days_logged
        })

    def _get_overview_stats(self, user, start_date) -> Dict:
        """Get quick overview stats for a specific period."""
        end_date = timezone.now()

        # Shopping: total spent from items
        from apps.shopping.models import ShoppingList, ShoppingItem
        shopping_lists = ShoppingList.objects.filter(
            creator=user,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        items = ShoppingItem.objects.filter(shopping_list__in=shopping_lists)
        total_spent = items.aggregate(
            total=Sum('estimated_price'))['total'] or 0

        # Recipes: total cooked
        recipes_cooked = RecipeCookingLog.objects.filter(
            user=user,
            cooked_at__range=[start_date, end_date]
        ).count()

        # Inventory: current count
        inventory_items = Inventory.objects.filter(user=user).count()

        # Nutrition: days logged (only if AI enabled)
        nutrition_days_logged = None
        if hasattr(user, 'nutrition_settings') and user.nutrition_settings.ai_coach_enabled:
            from apps.nutrition.models import NutritionEntry
            nutrition_days_logged = NutritionEntry.objects.filter(
                user=user,
                date__range=[start_date.date(), end_date.date()]
            ).values('date').distinct().count()

        return convert_decimals({
            'total_spent': round(total_spent, 2),
            'recipes_cooked': recipes_cooked,
            'inventory_items': inventory_items,
            'nutrition_days_logged': nutrition_days_logged
        })

    def get_dashboard_overview(
        self,
        user,
        period: str = '30days',
        include_ai: bool = True,
        language: str = 'en'
    ) -> dict:
        """
        Get complete dashboard overview in specified language

        NEW: Language-aware data aggregation and caching
        """
        logger.info(f"Generating dashboard for user={user.username}, "
                    f"period={period}, language={language}")

        # Check cache first (language-specific)
        cached_data = self._get_from_cache(user, period, language)
        if cached_data:
            logger.info(
                f"Dashboard cache HIT for {user.username} ({language})")
            cached_data['cached'] = True
            return cached_data

        logger.info(f"Dashboard cache MISS for {user.username} ({language})")

        # Calculate date range
        period_days = self._get_period_days(period)
        start_date = timezone.now() - timedelta(days=period_days)

        # Aggregate data from all modules (WITH translations)
        data = {
            'overview': self._get_overview_stats(user, start_date),
            # ← Pass language
            'shopping': self.get_shopping_analytics(user, start_date, language),
            # ← Pass language
            'recipes': self.get_recipes_analytics(user, start_date, language),
            # ← Pass language
            'inventory': self.get_inventory_analytics(user, language),
            # ← Pass language
            'achievements': self.get_achievements_data(user, language),
            'cached': False
        }

        # Add nutrition if AI enabled
        if include_ai and self._is_nutrition_ai_enabled(user):
            data['nutrition'] = self.get_nutrition_analytics(
                user, start_date, language)

        # Generate AI insights if enabled
        if include_ai:
            data['ai_insights'] = self._generate_ai_insights(
                user, data, language)  # ← Pass language

        # Save to cache (language-specific)
        self._save_to_cache(user, period, language, data)

        return data

    def _get_from_cache(self, user, period: str, language: str):
        """Get cached dashboard data for specific language"""
        try:
            cache_entry = DashboardCache.objects.get(
                user=user,
                period=period,
                language=language,  # ← NEW: Language-specific lookup
                expires_at__gt=timezone.now()
            )

            return {
                'overview': cache_entry.shopping_data.get('overview', {}),
                'shopping': cache_entry.shopping_data,
                'recipes': cache_entry.recipes_data,
                'inventory': cache_entry.inventory_data,
                'nutrition': cache_entry.nutrition_data,
                'achievements': cache_entry.achievements_data,
                'ai_insights': cache_entry.ai_insights,
                'cached_at': cache_entry.updated_at.isoformat()
            }
        except DashboardCache.DoesNotExist:
            return None

    def _save_to_cache(self, user, period: str, language: str, data: dict):
        """Save dashboard data to language-specific cache"""
        # Calculate expiration (1 hour from now)
        expires_at = timezone.now() + timedelta(hours=1)

        # Update or create cache entry
        DashboardCache.objects.update_or_create(
            user=user,
            period=period,
            language=language,  # ← NEW: Language-specific cache
            defaults={
                'shopping_data': data.get('shopping', {}),
                'recipes_data': data.get('recipes', {}),
                'inventory_data': data.get('inventory', {}),
                'nutrition_data': data.get('nutrition'),
                'achievements_data': data.get('achievements', {}),
                'ai_insights': data.get('ai_insights'),
                'ai_generated_at': timezone.now() if data.get('ai_insights') else None,
                'expires_at': expires_at
            }
        )

        logger.info(
            f"Cached dashboard for {user.username} ({language}, {period})")

    def _get_period_days(self, period: str) -> int:
        """Convert period string to days"""
        period_map = {
            '7days': 7,
            '30days': 30,
            '90days': 90,
            '1year': 365
        }
        return period_map.get(period, 30)

    def _is_nutrition_ai_enabled(self, user) -> bool:
        """Check if nutrition AI is enabled for user"""
        return hasattr(user, 'nutrition_settings') and user.nutrition_settings.ai_coach_enabled

    def get_shopping_analytics(self, user, start_date, language: str = 'en') -> Dict:
        """
        Get shopping analytics with translated item names

        NEW: Uses IML service for item name translation
        """
        from apps.shopping.models import ShoppingList, ShoppingItem
        from django.db.models import Sum, Count

        # Get shopping lists in period
        shopping_lists = ShoppingList.objects.filter(
            creator=user,
            created_at__gte=start_date
        )

        # Get items in period
        items = ShoppingItem.objects.filter(
            shopping_list__in=shopping_lists
        )
        # Calculate total spent from items
        total_spent = items.aggregate(
            total=Sum('estimated_price')
        )['total'] or 0

        # Get budget (from user preferences or default)
        budget = self._get_user_budget(user)
        budget_percentage = (total_spent / budget * 100) if budget > 0 else 0

        # Calculate vs last period
        last_period_start = start_date - (timezone.now() - start_date)
        last_period_lists = ShoppingList.objects.filter(
            creator=user,
            created_at__gte=last_period_start,
            created_at__lt=start_date
        )
        last_period_spent = ShoppingItem.objects.filter(
            shopping_list__in=last_period_lists
        ).aggregate(total=Sum('estimated_price'))['total'] or 0

        difference = total_spent - last_period_spent
        percentage_change = (difference / last_period_spent *
                             100) if last_period_spent > 0 else 0

        # Count item frequencies
        item_counts = {}
        item_counts = {}
        for item in items:
            item_name = item.name.lower()
            if item_name not in item_counts:
                item_counts[item_name] = {
                    'name': item.name,
                    'count': 0,
                    'total_quantity': 0,
                    'total_price': 0
                }

            item_counts[item_name]['count'] += 1
            item_counts[item_name]['total_quantity'] += item.quantity or 0
            item_counts[item_name]['total_price'] += item.estimated_price or 0
        # Get top 10 items
        top_items = sorted(item_counts.values(),
                           key=lambda x: x['count'], reverse=True)[:10]

        # NEW: Translate item names using IML
        translated_top_items = []
        for item_data in top_items:
            # Try to translate using IML
            translated_name = self.iml_service.translate_ingredient(
                item_data['name'],
                language
            )

            translated_top_items.append({
                'name': translated_name if translated_name else item_data['name'],
                'original_name': item_data['name'],
                'count': item_data['count'],
                'total_quantity': item_data['total_quantity'],
                'total_price': round(item_data['total_price'], 2),
                'translation_source': 'iml' if translated_name else 'original'
            })

        # Get category breakdown
        category_breakdown = []
        if items.exists():
            categories = items.values('category').annotate(
                total=Sum('estimated_price'),
                count=Count('id')
            ).order_by('-total')

            for cat in categories:
                category_name = cat['category'] or 'uncategorized'

                # NEW: Translate category
                translated_category = self._translate_shopping_category(
                    category_name, language)

                category_breakdown.append({
                    'category': translated_category,
                    'total': round(cat['total'] or 0, 2),
                    'count': cat['count']
                })

        return convert_decimals({
            'total_spent': round(total_spent, 2),
            'budget': budget,
            'budget_percentage': round(budget_percentage, 1),
            'vs_last_period': {
                'difference': round(difference, 2),
                'percentage_change': round(percentage_change, 1),
                'last_period_spent': round(last_period_spent, 2)
            },
            'avg_per_week': round(total_spent / ((timezone.now() - start_date).days / 7), 2),
            'category_breakdown': category_breakdown,
            'top_items': translated_top_items,
            'language': language
        })

    def get_recipes_analytics(self, user, start_date, language: str = 'en') -> Dict:
        """Get recipe insights with translated recipe names."""
        # Implementation will be updated in Sprint 9.2
        return self._get_recipes_analytics_old(user, start_date, language)

    def _get_recipes_analytics_old(self, user, start_date, language: str = 'en') -> Dict:
        """Get recipe insights (old implementation - will be replaced)"""
        end_date = timezone.now()

        # Cooking logs
        cooking_logs = RecipeCookingLog.objects.filter(
            user=user,
            cooked_at__range=[start_date, end_date]
        )

        total_cooked = cooking_logs.count()
        unique_recipes = cooking_logs.values('recipe').distinct().count()

        # Favorite recipe
        favorite = cooking_logs.values('recipe__name').annotate(
            count=Count('id')
        ).order_by('-count').first()

        favorite_recipe = {
            'name': favorite['recipe__name'] if favorite else None,
            'count': favorite['count'] if favorite else 0
        }

        # Most recent
        most_recent = cooking_logs.order_by('-cooked_at').first()
        most_recent_recipe = None
        if most_recent:
            hours_ago = (timezone.now() -
                         most_recent.cooked_at).total_seconds() / 3600
            most_recent_recipe = {
                'name': most_recent.recipe.name,
                'hours_ago': round(hours_ago, 1)
            }

        # Reviews
        reviews = RecipeReview.objects.filter(user=user)
        reviews_written = reviews.count()
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

        # Category distribution
        user_recipes = Recipe.objects.filter(created_by=user)
        category_counts = {}
        for recipe in user_recipes:
            # Use tags or cuisine as categories (Recipe model uses 'cuisine', not 'cuisine_type')
            category = getattr(recipe, 'cuisine', 'Other') or 'Other'
            category_counts[category] = category_counts.get(category, 0) + 1

        total_recipes = sum(category_counts.values())
        category_distribution = []
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_recipes *
                          100) if total_recipes > 0 else 0
            category_distribution.append({
                'category': category,
                'count': count,
                'percentage': round(percentage, 1)
            })

        return convert_decimals({
            'total_cooked': total_cooked,
            'unique_recipes': unique_recipes,
            'favorite': favorite_recipe,
            'most_recent': most_recent_recipe,
            'reviews_written': reviews_written,
            'avg_rating_given': round(avg_rating, 1),
            'category_distribution': category_distribution,
            'recent_recipes': [],  # Placeholder - can be added later if needed
            'language': language
        })

    def _translate_recipe_name(self, recipe, language: str) -> str:
        """
        Translate recipe name using RecipeTranslation table

        Args:
            recipe: Recipe object
            language: Target language code

        Returns:
            Translated name or original if no translation exists
        """
        # If language is English or same as recipe's original language, return original
        if language == 'en' or language == recipe.language:
            return recipe.name

        # Try to find translation
        try:
            # Check if this recipe is a fork (has canonical_recipe)
            if hasattr(recipe, 'canonical_recipe') and recipe.canonical_recipe:
                canonical_recipe = recipe.canonical_recipe
            else:
                # This recipe might BE the canonical recipe
                # Check if it has translations
                canonical_recipe = recipe

            # Look for completed translation
            translation = RecipeTranslation.objects.filter(
                canonical_recipe=canonical_recipe,
                language=language,
                status='completed'
            ).first()

            if translation:
                logger.debug(
                    f"Found translation for recipe {recipe.id}: {translation.name}")
                return translation.name

            # No translation found, return original
            logger.debug(
                f"No translation found for recipe {recipe.id} in {language}")
            return recipe.name

        except Exception as e:
            logger.warning(f"Error translating recipe {recipe.id}: {e}")
            return recipe.name

    def _translate_category(self, category: str, language: str) -> str:
        """Translate category name"""
        CATEGORY_TRANSLATIONS = {
            'en': {
                'breakfast': 'Breakfast',
                'lunch': 'Lunch',
                'dinner': 'Dinner',
                'dessert': 'Dessert',
                'snack': 'Snack',
                'appetizer': 'Appetizer',
                'main_course': 'Main Course',
                'side_dish': 'Side Dish',
                'soup': 'Soup',
                'salad': 'Salad',
                'beverage': 'Beverage',
                'uncategorized': 'Uncategorized'
            },
            'he': {
                'breakfast': 'ארוחת בוקר',
                'lunch': 'ארוחת צהריים',
                'dinner': 'ארוחת ערב',
                'dessert': 'קינוח',
                'snack': 'חטיף',
                'appetizer': 'מנה ראשונה',
                'main_course': 'מנה עיקרית',
                'side_dish': 'תוספת',
                'soup': 'מרק',
                'salad': 'סלט',
                'beverage': 'משקה',
                'uncategorized': 'ללא קטגוריה'
            },
            'ru': {
                'breakfast': 'Завтрак',
                'lunch': 'Обед',
                'dinner': 'Ужин',
                'dessert': 'Десерт',
                'snack': 'Перекус',
                'appetizer': 'Закуска',
                'main_course': 'Основное блюдо',
                'side_dish': 'Гарнир',
                'soup': 'Суп',
                'salad': 'Салат',
                'beverage': 'Напиток',
                'uncategorized': 'Без категории'
            }
        }

        translations = CATEGORY_TRANSLATIONS.get(
            language, CATEGORY_TRANSLATIONS['en'])
        return translations.get(category.lower(), category)

    def _translate_shopping_category(self, category: str, language: str) -> str:
        """Translate shopping category names"""

        CATEGORY_TRANSLATIONS = {
            'en': {
                'produce': 'Produce',
                'meat': 'Meat',
                'dairy': 'Dairy',
                'bakery': 'Bakery',
                'frozen': 'Frozen',
                'beverages': 'Beverages',
                'snacks': 'Snacks',
                'pantry': 'Pantry',
                'household': 'Household',
                'personal_care': 'Personal Care',
                'uncategorized': 'Uncategorized'
            },
            'he': {
                'produce': 'פירות וירקות',
                'meat': 'בשר',
                'dairy': 'מוצרי חלב',
                'bakery': 'מאפים',
                'frozen': 'מוצרים קפואים',
                'beverages': 'משקאות',
                'snacks': 'חטיפים',
                'pantry': 'מזווה',
                'household': 'מוצרי בית',
                'personal_care': 'טיפוח אישי',
                'uncategorized': 'ללא קטגוריה'
            },
            'ru': {
                'produce': 'Фрукты и овощи',
                'meat': 'Мясо',
                'dairy': 'Молочные продукты',
                'bakery': 'Хлебобулочные изделия',
                'frozen': 'Замороженные продукты',
                'beverages': 'Напитки',
                'snacks': 'Закуски',
                'pantry': 'Бакалея',
                'household': 'Товары для дома',
                'personal_care': 'Личная гигиена',
                'uncategorized': 'Без категории'
            }
        }

        translations = CATEGORY_TRANSLATIONS.get(
            language, CATEGORY_TRANSLATIONS['en'])
        return translations.get(category.lower(), category)

    def _get_user_budget(self, user) -> float:
        """Get user's shopping budget"""
        if hasattr(user, 'preferences') and hasattr(user.preferences, 'shopping_budget'):
            return user.preferences.shopping_budget or 400.0
        return 400.0  # Default budget

    def get_inventory_analytics(self, user, language: str = 'en') -> Dict:
        """
        Get inventory insights with translated item names

        NEW: Uses IML service for inventory item translation
        """
        from apps.shopping.models import Inventory
        from datetime import date, timedelta

        # Get current inventory
        inventory_items = Inventory.objects.filter(
            user=user,
            quantity__gt=0
        )

        total_items = inventory_items.count()

        # Find low stock items (quantity < 2)
        low_stock_items = inventory_items.filter(quantity__lt=2)
        low_stock_count = low_stock_items.count()

        # Find expiring items
        today = date.today()
        tomorrow = today + timedelta(days=1)
        in_2_3_days = today + timedelta(days=3)

        expiring_tomorrow = inventory_items.filter(
            expiration_date__lte=tomorrow,
            expiration_date__gte=today
        )

        expiring_2_3_days = inventory_items.filter(
            expiration_date__gt=tomorrow,
            expiration_date__lte=in_2_3_days
        )

        expiring_soon_count = expiring_tomorrow.count() + expiring_2_3_days.count()

        # NEW: Translate expiring items
        translated_expiring_tomorrow = []
        for item in expiring_tomorrow:
            translated_name = self.iml_service.translate_ingredient(
                item.name,
                language
            )

            translated_expiring_tomorrow.append({
                'id': str(item.id),
                'name': translated_name if translated_name else item.name,
                'original_name': item.name,
                'quantity': float(item.quantity),
                'unit': item.unit,
                'expiration_date': item.expiration_date.isoformat(),
                'translation_source': 'iml' if translated_name else 'original'
            })

        translated_expiring_2_3_days = []
        for item in expiring_2_3_days:
            translated_name = self.iml_service.translate_ingredient(
                item.name,
                language
            )

            translated_expiring_2_3_days.append({
                'id': str(item.id),
                'name': translated_name if translated_name else item.name,
                'original_name': item.name,
                'quantity': float(item.quantity),
                'unit': item.unit,
                'expiration_date': item.expiration_date.isoformat(),
                'translation_source': 'iml' if translated_name else 'original'
            })

        # NEW: Translate low stock items
        translated_low_stock = []
        for item in low_stock_items[:5]:  # Top 5 low stock
            translated_name = self.iml_service.translate_ingredient(
                item.name,
                language
            )

            translated_low_stock.append({
                'id': str(item.id),
                'name': translated_name if translated_name else item.name,
                'original_name': item.name,
                'quantity': float(item.quantity),
                'unit': item.unit,
                'translation_source': 'iml' if translated_name else 'original'
            })

        return convert_decimals({
            'total_items': total_items,
            'low_stock_count': low_stock_count,
            'low_stock_items': translated_low_stock,
            'expiring_soon_count': expiring_soon_count,
            'expiring_items': {
                'tomorrow': translated_expiring_tomorrow,
                'in_2_3_days': translated_expiring_2_3_days
            },
            'language': language
        })

    def get_nutrition_analytics(self, user, start_date, language: str = 'en') -> Optional[Dict]:
        """
        Get nutrition analytics with translated food names

        NEW: Uses IML service for food name translation
        """
        from apps.nutrition.models import NutritionEntry, UserNutritionSettings
        from django.db.models import Sum, Avg
        from datetime import date

        # Get nutrition settings
        try:
            settings = UserNutritionSettings.objects.get(user=user)
            if not settings.ai_coach_enabled:
                return None  # Nutrition tracking disabled
        except UserNutritionSettings.DoesNotExist:
            return None

        # Get nutrition entries in period
        entries = NutritionEntry.objects.filter(
            user=user,
            date__gte=start_date.date()
        )

        # Calculate days logged
        days_logged = entries.values('date').distinct().count()
        total_days = (date.today() - start_date.date()).days + 1
        logging_percentage = (days_logged / total_days *
                              100) if total_days > 0 else 0

        # Calculate goal achievement
        goal_calories = settings.manual_calories_goal or 2000
        goal_protein = settings.manual_protein_goal or 150

        # Count days hitting goals
        daily_totals = entries.values('date').annotate(
            total_calories=Sum('calories'),
            total_protein=Sum('protein')
        )

        calories_hit = sum(1 for day in daily_totals if day['total_calories'] >=
                           goal_calories * 0.9 and day['total_calories'] <= goal_calories * 1.1)
        protein_hit = sum(
            1 for day in daily_totals if day['total_protein'] >= goal_protein * 0.9)

        # Calculate current streak
        current_streak = self._calculate_nutrition_streak(user)

        # Get meal distribution
        meal_distribution = entries.values('meal_type').annotate(
            count=Count('id')
        )

        # NEW: Translate meal types
        translated_meal_distribution = []
        for meal in meal_distribution:
            meal_type = meal['meal_type']
            translated_meal_type = self._translate_meal_type(
                meal_type, language)

            translated_meal_distribution.append({
                'meal_type': translated_meal_type,
                'count': meal['count']
            })

        # Get most eaten foods (top 5)
        food_counts = {}
        for entry in entries:
            food_name = entry.food_name.lower()
            food_counts[food_name] = food_counts.get(food_name, 0) + 1

        top_foods = sorted(food_counts.items(),
                           key=lambda x: x[1], reverse=True)[:5]

        # NEW: Translate top foods
        translated_top_foods = []
        for food_name, count in top_foods:
            translated_name = self.iml_service.translate_ingredient(
                food_name,
                language
            )

            translated_top_foods.append({
                'name': translated_name if translated_name else food_name,
                'original_name': food_name,
                'count': count,
                'translation_source': 'iml' if translated_name else 'original'
            })

        # Calculate monthly totals
        monthly_totals = entries.aggregate(
            total_calories=Sum('calories'),
            total_protein=Sum('protein'),
            total_carbs=Sum('carbs'),
            total_fat=Sum('fat')
        )

        return convert_decimals({
            'days_logged': days_logged,
            'logging_percentage': round(logging_percentage, 1),
            'goal_achievement': {
                'calories': {
                    'hit': calories_hit,
                    'total': days_logged,
                    'percentage': round((calories_hit / days_logged * 100) if days_logged > 0 else 0, 1)
                },
                'protein': {
                    'hit': protein_hit,
                    'total': days_logged,
                    'percentage': round((protein_hit / days_logged * 100) if days_logged > 0 else 0, 1)
                }
            },
            'current_streak': current_streak,
            'monthly_totals': {
                'calories': round(monthly_totals['total_calories'] or 0, 0),
                'protein': round(monthly_totals['total_protein'] or 0, 1),
                'carbs': round(monthly_totals['total_carbs'] or 0, 1),
                'fat': round(monthly_totals['total_fat'] or 0, 1)
            },
            'meal_distribution': translated_meal_distribution,
            'top_foods': translated_top_foods,
            'language': language
        })

    def _translate_meal_type(self, meal_type: str, language: str) -> str:
        """Translate meal type names"""

        MEAL_TYPE_TRANSLATIONS = {
            'en': {
                'breakfast': 'Breakfast',
                'lunch': 'Lunch',
                'dinner': 'Dinner',
                'snack': 'Snack'
            },
            'he': {
                'breakfast': 'ארוחת בוקר',
                'lunch': 'ארוחת צהריים',
                'dinner': 'ארוחת ערב',
                'snack': 'חטיף'
            },
            'ru': {
                'breakfast': 'Завтрак',
                'lunch': 'Обед',
                'dinner': 'Ужин',
                'snack': 'Перекус'
            }
        }

        translations = MEAL_TYPE_TRANSLATIONS.get(
            language, MEAL_TYPE_TRANSLATIONS['en'])
        return translations.get(meal_type.lower(), meal_type)

    def _calculate_nutrition_streak(self, user) -> int:
        """Calculate current nutrition logging streak"""
        from apps.nutrition.models import NutritionEntry
        from datetime import date, timedelta

        current_date = date.today()
        streak = 0

        # Check backwards from today
        while True:
            has_entry = NutritionEntry.objects.filter(
                user=user,
                date=current_date
            ).exists()

            if not has_entry:
                break

            streak += 1
            current_date -= timedelta(days=1)

        return streak

    def _get_nutrition_analytics_old(self, user, start_date, language: str = 'en') -> Optional[Dict]:
        """Get nutrition insights (old implementation - will be replaced)"""
        if not hasattr(user, 'nutrition_settings') or not user.nutrition_settings.ai_coach_enabled:
            return None

        end_date = timezone.now()

        # Get all entries in period
        entries = NutritionEntry.objects.filter(
            user=user,
            date__range=[start_date.date(), end_date.date()]
        )

        # Days logged
        days_logged = entries.values('date').distinct().count()
        total_days = (end_date.date() - start_date.date()).days + 1
        logging_percentage = round(
            (days_logged / total_days * 100) if total_days > 0 else 0, 0)

        # Goal achievement
        settings_obj = user.nutrition_settings
        # Get goals based on goal_mode
        if settings_obj.goal_mode == 'manual':
            calories_goal = float(
                settings_obj.manual_calories_goal or 2000)
            protein_goal = float(
                settings_obj.manual_protein_goal or 150)
        else:  # ai_calculated
            calories_goal = float(settings_obj.manual_calories_goal or 2000)
            protein_goal = float(settings_obj.manual_protein_goal or 150)

        # Count days where goals were hit
        days_with_goals = entries.values('date').annotate(
            total_calories=Sum('calories'),
            total_protein=Sum('protein')
        )

        calories_hit = sum(1 for day in days_with_goals if abs(
            float(day['total_calories']) - calories_goal) / calories_goal < 0.1)
        protein_hit = sum(1 for day in days_with_goals if float(
            day['total_protein']) >= protein_goal)

        # Current streak
        streak = UserStreak.objects.filter(
            user=user, streak_type='nutrition_logging').first()
        current_streak = streak.current_count if streak else 0

        # Monthly totals
        total_calories = sum(float(e.calories) for e in entries)
        total_protein = sum(float(e.protein) for e in entries)
        avg_calories = total_calories / days_logged if days_logged > 0 else 0
        avg_protein = total_protein / days_logged if days_logged > 0 else 0

        # Best day
        best_day = None
        best_achievement_rate = 0
        for day in days_with_goals:
            cal_achievement = 100 - \
                abs((float(day['total_calories']) - calories_goal) /
                    calories_goal * 100) if calories_goal > 0 else 0
            prot_achievement = min(
                float(day['total_protein']) / protein_goal * 100, 100) if protein_goal > 0 else 0
            achievement_rate = (cal_achievement + prot_achievement) / 2
            if achievement_rate > best_achievement_rate:
                best_achievement_rate = achievement_rate
                best_day = {
                    'date': day['date'].isoformat(),
                    'achievement_rate': round(achievement_rate, 0)
                }

        # Meal distribution
        meal_counts = entries.values('meal_type').annotate(count=Count('id'))
        total_meals = sum(item['count'] for item in meal_counts)
        meal_distribution = {}
        for item in meal_counts:
            percentage = (item['count'] / total_meals *
                          100) if total_meals > 0 else 0
            meal_distribution[item['meal_type']] = round(percentage, 0)

        return convert_decimals({
            'days_logged': days_logged,
            'total_days': total_days,
            'logging_percentage': logging_percentage,
            'goal_achievement': {
                'calories': {
                    'hit': calories_hit,
                    'total': days_logged,
                    'percentage': round((calories_hit / days_logged * 100) if days_logged > 0 else 0, 0)
                },
                'protein': {
                    'hit': protein_hit,
                    'total': days_logged,
                    'percentage': round((protein_hit / days_logged * 100) if days_logged > 0 else 0, 0)
                }
            },
            'current_streak': current_streak,
            'monthly_totals': {
                'calories': round(total_calories, 0),
                'protein': round(total_protein, 0),
                'avg_per_day': {
                    'calories': round(avg_calories, 0),
                    'protein': round(avg_protein, 0)
                }
            },
            'best_day': best_day,
            'meal_distribution': meal_distribution
        })

    def get_achievements_data(self, user, language: str = 'en') -> Dict:
        """
        Get achievements and streaks data

        NEW: Returns achievement names/descriptions as i18n keys
        Frontend will translate using i18n
        """
        from apps.analytics.models import Achievement, UserStreak

        # Get user's achievements
        achievements = Achievement.objects.filter(user=user)

        # Get user's streaks
        streaks = UserStreak.objects.filter(user=user)

        # Build current streaks dictionary
        current_streaks = {}
        for streak in streaks:
            current_streaks[streak.streak_type] = {
                'current': streak.current_count,
                'longest': streak.longest_count,
                # NEW: Return i18n key instead of hardcoded text
                'name_key': f'achievements.streak.{streak.streak_type}',
                'description_key': f'achievements.streak.{streak.streak_type}_description'
            }

        # Build badges earned list
        badges_earned = []
        for achievement in achievements:
            badges_earned.append({
                'badge_id': achievement.badge_id,
                # NEW: Return i18n keys for translation
                'name_key': f'achievements.badge.{achievement.badge_id}',
                'description_key': f'achievements.badge.{achievement.badge_id}_description',
                'icon': achievement.icon,
                'earned_at': achievement.created_at.isoformat() if hasattr(achievement, 'created_at') else None
            })

        # Calculate next goals (what streaks/badges are close)
        next_goals = self._calculate_next_goals(
            user, current_streaks, language)

        return convert_decimals({
            'current_streaks': current_streaks,
            'badges_earned': badges_earned,
            'next_goals': next_goals,
            'language': language
        })

    def _calculate_next_goals(self, user, current_streaks: dict, language: str) -> list:
        """
        Calculate next achievable goals

        Returns list of goals with i18n keys
        """
        goals = []

        # Nutrition logging streak goals
        if 'nutrition_logging' in current_streaks:
            current = current_streaks['nutrition_logging']['current']

            # Next milestone
            next_milestone = None
            for milestone in [7, 14, 30, 60, 90, 365]:
                if current < milestone:
                    next_milestone = milestone
                    break

            if next_milestone:
                goals.append({
                    'type': 'streak',
                    'streak_type': 'nutrition_logging',
                    'current': current,
                    'target': next_milestone,
                    'remaining': next_milestone - current,
                    # NEW: i18n keys
                    'title_key': 'achievements.goal.nutrition_streak',
                    'description_key': 'achievements.goal.nutrition_streak_description'
                })

        # Recipe cooking goals
        if 'recipe_cooking' in current_streaks:
            current = current_streaks['recipe_cooking']['current']

            next_milestone = None
            for milestone in [3, 7, 14, 30]:
                if current < milestone:
                    next_milestone = milestone
                    break

            if next_milestone:
                goals.append({
                    'type': 'streak',
                    'streak_type': 'recipe_cooking',
                    'current': current,
                    'target': next_milestone,
                    'remaining': next_milestone - current,
                    'title_key': 'achievements.goal.cooking_streak',
                    'description_key': 'achievements.goal.cooking_streak_description'
                })

        return goals

    def _generate_ai_insights(self, user, dashboard_data: dict, language: str) -> dict:
        """
        Generate AI insights for dashboard

        Delegates to AIInsightsService
        """
        try:
            insights_service = AIInsightsService()
            return insights_service.generate_all_insights(user, dashboard_data, language)
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            # Return empty insights on error
            return {
                'insight_of_day': None,
                'shopping_insights': [],
                'recipe_insights': [],
                'inventory_insights': [],
                'nutrition_insights': [],
                'language': language,
                'ai_provider': None,
                'fallback_used': True,
                'error': str(e)
            }


class AIInsightsService:
    """
    AI Insights generation service for Dashboard

    NEW: Uses Groq for multilingual insight generation
    """

    def __init__(self):
        """Initialize with Groq client"""
        from groq import Groq
        import os
        from django.conf import settings

        groq_api_key = os.getenv('GROQ_API_KEY') or getattr(
            settings, 'GROQ_API_KEY', None)
        if not groq_api_key:
            logger.warning(
                "GROQ_API_KEY not found - AI insights will use fallbacks")
            self.client = None
        else:
            self.client = Groq(api_key=groq_api_key)

        self.model = "llama-3.1-8b-instant"
        self.iml_service = get_iml_service()

    def generate_all_insights(
        self,
        user,
        dashboard_data: dict,
        language: str = 'en'
    ) -> dict:
        """
        Generate all AI insights for dashboard in target language

        NEW: Generates insights in user's language

        Args:
            user: User object
            dashboard_data: Complete dashboard data (shopping, recipes, etc.)
            language: Target language ('en', 'he', 'ru')

        Returns:
            dict with all insights in target language
        """
        logger.info(
            f"Generating AI insights for {user.username} in {language}")

        insights = {
            'insight_of_day': None,
            'shopping_insights': [],
            'recipe_insights': [],
            'inventory_insights': [],
            'nutrition_insights': [],
            'language': language,
            'ai_provider': None,
            'fallback_used': False
        }

        try:
            # Generate insight of the day
            insights['insight_of_day'] = self._generate_insight_of_day(
                dashboard_data,
                language
            )
            insights['ai_provider'] = 'groq' if self.client else 'fallback'

            # Generate section-specific insights
            if dashboard_data.get('shopping'):
                insights['shopping_insights'] = self._generate_shopping_insights(
                    dashboard_data['shopping'],
                    language
                )

            # Generate recipe insights
            if dashboard_data.get('recipes'):
                insights['recipe_insights'] = self._generate_recipe_insights(
                    dashboard_data['recipes'],
                    language
                )

            # Generate inventory insights
            if dashboard_data.get('inventory'):
                insights['inventory_insights'] = self._generate_inventory_insights(
                    dashboard_data['inventory'],
                    language
                )

            # Generate nutrition insights (if available)
            if dashboard_data.get('nutrition'):
                insights['nutrition_insights'] = self._generate_nutrition_insights(
                    dashboard_data['nutrition'],
                    language
                )

            logger.info(
                f"Successfully generated AI insights for {user.username} in {language}")

        except Exception as e:
            logger.error(f"Error generating AI insights: {e}", exc_info=True)
            insights['error'] = str(e)
            # Provide fallback
            insights['insight_of_day'] = self._get_fallback_insight(language)
            insights['fallback_used'] = True

        return insights

    def _generate_insight_of_day(self, dashboard_data: dict, language: str) -> str:
        """Generate daily insight in target language"""
        try:
            if not self.client:
                return self._get_fallback_insight(language)

            # Build system prompt
            system_prompt = self._build_system_prompt(
                'insight_of_day', language)

            # Build user prompt with data
            user_prompt = self._build_insight_of_day_prompt(
                dashboard_data, language)

            # Generate with Groq
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating insight of day: {e}")
            return self._get_fallback_insight(language)

    def _build_system_prompt(self, prompt_type: str, language: str) -> str:
        """Build language-specific system prompts"""

        # Critical language instruction
        lang_instruction = {
            'en': "You MUST respond ONLY in English. Do not mix languages.",
            'he': "אתה חייב להגיב רק בעברית. אל תערבב שפות.",
            'ru': "Вы ДОЛЖНЫ отвечать ТОЛЬКО на русском языке. Не смешивайте языки."
        }.get(language, "You MUST respond ONLY in English.")

        base_prompts = {
            'insight_of_day': {
                'en': f"""You are a helpful kitchen and nutrition assistant. 
Provide a single, encouraging insight about the user's habits based on their dashboard data.
Keep it brief (1-2 sentences), positive, and actionable.
{lang_instruction}""",
                'he': f"""אתה עוזר מטבח ותזונה מועיל.
ספק תובנה אחת ומעודדת על הרגלי המשתמש בהתבסס על נתוני הדשבורד.
שמור על תמציתיות (1-2 משפטים), חיוביות ומעשיות.
{lang_instruction}""",
                'ru': f"""Вы полезный помощник по кухне и питанию.
Предоставьте один поощряющий инсайт о привычках пользователя на основе данных панели.
Будьте краткими (1-2 предложения), позитивными и практичными.
{lang_instruction}"""
            },
            'shopping': {
                'en': f"""You are a budget-conscious shopping advisor.
Analyze shopping patterns and provide brief, practical tips.
{lang_instruction}""",
                'he': f"""אתה יועץ קניות מודע לתקציב.
נתח דפוסי קנייה וספק טיפים קצרים ומעשיים.
{lang_instruction}""",
                'ru': f"""Вы бюджетный консультант по покупкам.
Проанализируйте модели покупок и дайте краткие практические советы.
{lang_instruction}"""
            },
            'recipe': {
                'en': f"""You are a culinary creativity advisor.
Encourage cooking habits and suggest variety.
{lang_instruction}""",
                'he': f"""אתה יועץ יצירתיות קולינרית.
עודד הרגלי בישול והצע גיוון.
{lang_instruction}""",
                'ru': f"""Вы консультант по кулинарному творчеству.
Поощряйте кулинарные привычки и предлагайте разнообразие.
{lang_instruction}"""
            },
            'inventory': {
                'en': f"""You are a food waste prevention specialist.
Help manage inventory efficiently.
{lang_instruction}""",
                'he': f"""אתה מומחה למניעת בזבוז מזון.
עזור לנהל מלאי ביעילות.
{lang_instruction}""",
                'ru': f"""Вы специалист по предотвращению пищевых отходов.
Помогите эффективно управлять запасами.
{lang_instruction}"""
            },
            'nutrition': {
                'en': f"""You are a supportive nutrition coach.
Encourage healthy eating patterns.
{lang_instruction}""",
                'he': f"""אתה מאמן תזונה תומך.
עודד דפוסי אכילה בריאים.
{lang_instruction}""",
                'ru': f"""Вы поддерживающий тренер по питанию.
Поощряйте здоровые пищевые привычки.
{lang_instruction}"""
            }
        }

        return base_prompts.get(prompt_type, {}).get(language, base_prompts[prompt_type]['en'])

    def _build_insight_of_day_prompt(self, dashboard_data: dict, language: str) -> str:
        """Build user prompt for daily insight"""

        # Extract key metrics
        overview = dashboard_data.get('overview', {})
        shopping = dashboard_data.get('shopping', {})
        recipes = dashboard_data.get('recipes', {})

        # Build prompt in target language
        if language == 'he':
            return f"""נתוני דשבורד:
- סה"כ הוצאות: ${overview.get('total_spent', 0):.2f}
- מתכונים שבושלו: {overview.get('recipes_cooked', 0)}
- פריטי מלאי: {overview.get('inventory_items', 0)}
- תקציב קניות: {shopping.get('budget_percentage', 0):.0f}% נוצל

תן תובנה מעודדת אחת בעברית (1-2 משפטים)."""

        elif language == 'ru':
            return f"""Данные панели:
- Общие расходы: ${overview.get('total_spent', 0):.2f}
- Приготовлено рецептов: {overview.get('recipes_cooked', 0)}
- Товары в запасах: {overview.get('inventory_items', 0)}
- Бюджет покупок: {shopping.get('budget_percentage', 0):.0f}% использовано

Дайте один поощряющий инсайт на русском (1-2 предложения)."""

        else:  # English
            return f"""Dashboard data:
- Total spent: ${overview.get('total_spent', 0):.2f}
- Recipes cooked: {overview.get('recipes_cooked', 0)}
- Inventory items: {overview.get('inventory_items', 0)}
- Shopping budget: {shopping.get('budget_percentage', 0):.0f}% used

Provide one encouraging insight in English (1-2 sentences)."""

    def _get_fallback_insight(self, language: str) -> str:
        """Provide rule-based fallback insight"""
        fallbacks = {
            'en': "Keep up the great work managing your kitchen! Every small step counts toward better habits.",
            'he': "המשך בעבודה המצוינת בניהול המטבח שלך! כל צעד קטן נחשב להרגלים טובים יותר.",
            'ru': "Продолжайте отлично управлять своей кухней! Каждый маленький шаг ведет к лучшим привычкам."
        }
        return fallbacks.get(language, fallbacks['en'])

    def _generate_shopping_insights(self, shopping_data: dict, language: str) -> list:
        """Generate shopping-specific insights"""
        insights = []

        try:
            budget_pct = shopping_data.get('budget_percentage', 0)

            # Budget insight
            if budget_pct > 90:
                system_prompt = self._build_system_prompt('shopping', language)

                if language == 'he':
                    user_prompt = f"התקציב ב-{budget_pct:.0f}% שימוש. תן טיפ קצר לחיסכון בעברית."
                elif language == 'ru':
                    user_prompt = f"Бюджет использован на {budget_pct:.0f}%. Дайте краткий совет по экономии на русском."
                else:
                    user_prompt = f"Budget at {budget_pct:.0f}% used. Give a brief saving tip in English."

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=80,
                    temperature=0.7
                )

                insights.append({
                    'type': 'budget',
                    'text': response.choices[0].message.content.strip()
                })

        except Exception as e:
            logger.error(f"Error generating shopping insights: {e}")
            # Fallback
            insights.append({
                'type': 'budget',
                'text': self._get_fallback_shopping_insight(language),
                'fallback': True
            })

        return insights

    def _get_fallback_shopping_insight(self, language: str) -> str:
        """Fallback shopping insight"""
        fallbacks = {
            'en': "Consider planning meals in advance to optimize your shopping budget.",
            'he': "שקול לתכנן ארוחות מראש כדי לייעל את תקציב הקניות שלך.",
            'ru': "Рассмотрите возможность планирования приемов пищи заранее для оптимизации бюджета."
        }
        return fallbacks.get(language, fallbacks['en'])

    def _generate_recipe_insights(self, recipe_data: dict, language: str) -> list:
        """Generate recipe-specific insights"""
        insights = []

        try:
            total_cooked = recipe_data.get('total_cooked', 0)
            unique = recipe_data.get('unique_recipes', 0)

            if total_cooked > 0:
                system_prompt = self._build_system_prompt('recipe', language)

                if language == 'he':
                    user_prompt = f"בישל {total_cooked} מתכונים ({unique} ייחודיים). עודד המשך בישול בעברית."
                elif language == 'ru':
                    user_prompt = f"Приготовлено {total_cooked} рецептов ({unique} уникальных). Поощрите продолжить готовить на русском."
                else:
                    user_prompt = f"Cooked {total_cooked} recipes ({unique} unique). Encourage continued cooking in English."

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=80,
                    temperature=0.7
                )

                insights.append({
                    'type': 'cooking',
                    'text': response.choices[0].message.content.strip()
                })

        except Exception as e:
            logger.error(f"Error generating recipe insights: {e}")
            insights.append({
                'type': 'cooking',
                'text': self._get_fallback_recipe_insight(language),
                'fallback': True
            })

        return insights

    def _get_fallback_recipe_insight(self, language: str) -> str:
        """Fallback recipe insight"""
        fallbacks = {
            'en': "Cooking at home is a great way to control your nutrition and save money!",
            'he': "בישול בבית הוא דרך מצוינת לשלוט בתזונה ולחסוך כסף!",
            'ru': "Готовка дома - отличный способ контролировать питание и экономить деньги!"
        }
        return fallbacks.get(language, fallbacks['en'])

    def _generate_inventory_insights(self, inventory_data: dict, language: str) -> list:
        """Generate inventory-specific insights"""
        insights = []

        try:
            expiring_count = inventory_data.get('expiring_soon_count', 0)

            if expiring_count > 0:
                system_prompt = self._build_system_prompt(
                    'inventory', language)

                if language == 'he':
                    user_prompt = f"{expiring_count} פריטים מתקרבים לתפוגה. תן טיפ להשתמש בהם בעברית."
                elif language == 'ru':
                    user_prompt = f"{expiring_count} товаров истекает. Дайте совет, как их использовать на русском."
                else:
                    user_prompt = f"{expiring_count} items expiring soon. Give a tip to use them in English."

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=80,
                    temperature=0.7
                )

                insights.append({
                    'type': 'expiration',
                    'text': response.choices[0].message.content.strip()
                })

        except Exception as e:
            logger.error(f"Error generating inventory insights: {e}")
            insights.append({
                'type': 'expiration',
                'text': self._get_fallback_inventory_insight(language),
                'fallback': True
            })

        return insights

    def _get_fallback_inventory_insight(self, language: str) -> str:
        """Fallback inventory insight"""
        fallbacks = {
            'en': "Check your inventory regularly to minimize food waste.",
            'he': "בדוק את המלאי שלך באופן קבוע כדי למזער בזבוז מזון.",
            'ru': "Регулярно проверяйте запасы, чтобы минимизировать пищевые отходы."
        }
        return fallbacks.get(language, fallbacks['en'])

    def _generate_nutrition_insights(self, nutrition_data: dict, language: str) -> list:
        """Generate nutrition-specific insights"""
        insights = []

        try:
            days_logged = nutrition_data.get('days_logged', 0)
            logging_pct = nutrition_data.get('logging_percentage', 0)

            if days_logged > 0:
                system_prompt = self._build_system_prompt(
                    'nutrition', language)

                if language == 'he':
                    user_prompt = f"רשם תזונה {days_logged} ימים ({logging_pct}%). עודד המשך מעקב בעברית."
                elif language == 'ru':
                    user_prompt = f"Записано питание {days_logged} дней ({logging_pct}%). Поощрите продолжить отслеживание на русском."
                else:
                    user_prompt = f"Logged nutrition {days_logged} days ({logging_pct}%). Encourage continued tracking in English."

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=80,
                    temperature=0.7
                )

                insights.append({
                    'type': 'tracking',
                    'text': response.choices[0].message.content.strip()
                })

        except Exception as e:
            logger.error(f"Error generating nutrition insights: {e}")
            insights.append({
                'type': 'tracking',
                'text': self._get_fallback_nutrition_insight(language),
                'fallback': True
            })

        return insights

    def _get_fallback_nutrition_insight(self, language: str) -> str:
        """Fallback nutrition insight"""
        fallbacks = {
            'en': "Tracking your nutrition helps build awareness of your eating patterns!",
            'he': "מעקב אחר התזונה שלך עוזר לבנות מודעות לדפוסי האכילה שלך!",
            'ru': "Отслеживание питания помогает осознать ваши пищевые привычки!"
        }
        return fallbacks.get(language, fallbacks['en'])
