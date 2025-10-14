"""
Dashboard Analytics Services

Calculates analytics data from shopping, recipes, inventory, and nutrition modules.
Generates AI-powered insights and recommendations.
"""
import json
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
from .models import Achievement, UserStreak, RecipeCookingLog


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
    """Main service for calculating dashboard analytics."""

    def __init__(self, user):
        self.user = user

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

    def get_shopping_analytics(self, period: str) -> Dict:
        """Get shopping insights."""
        start_date, end_date = self.get_period_dates(period)
        prev_start = start_date - (end_date - start_date)

        # Current period shopping
        shopping_lists = ShoppingList.objects.filter(
            creator=self.user,
            completed_at__isnull=False,  # Only completed lists
            updated_at__range=[start_date, end_date]
        )

        total_spent = 0
        category_totals = {}
        item_counts = {}

        for sl in shopping_lists:
            items = ShoppingItem.objects.filter(
                shopping_list=sl, purchased=True)
            for item in items:
                if item.price:
                    price = float(item.price)
                    total_spent += price

                    # Category breakdown
                    category = item.category or 'Other'
                    category_totals[category] = category_totals.get(
                        category, 0) + price

                    # Item frequency
                    item_name = item.name.lower()
                    if item_name not in item_counts:
                        item_counts[item_name] = {
                            'name': item.name, 'count': 0}
                    item_counts[item_name]['count'] += 1

        # Previous period for comparison
        prev_shopping_lists = ShoppingList.objects.filter(
            creator=self.user,
            completed_at__isnull=False,  # Only completed lists
            updated_at__range=[prev_start, start_date]
        )
        prev_total_spent = 0
        for sl in prev_shopping_lists:
            items = ShoppingItem.objects.filter(
                shopping_list=sl, purchased=True)
            for item in items:
                if item.price:
                    prev_total_spent += float(item.price)

        # Category breakdown
        category_breakdown = []
        for category, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total_spent * 100) if total_spent > 0 else 0
            category_breakdown.append({
                'category': category,
                'amount': round(amount, 2),
                'percentage': round(percentage, 1)
            })

        # Top items
        top_items = []
        for item_data in sorted(item_counts.values(), key=lambda x: x['count'], reverse=True)[:10]:
            # Calculate frequency (rough estimate)
            days_in_period = (end_date - start_date).days
            frequency_days = days_in_period // item_data['count'] if item_data['count'] > 0 else days_in_period
            top_items.append({
                'name': item_data['name'],
                'count': item_data['count'],
                'frequency': f"~{frequency_days} days"
            })

        # Budget info (default $400/month)
        budget = 400  # Could be user setting in future
        avg_per_week = total_spent / ((end_date - start_date).days / 7)

        return convert_decimals({
            'total_spent': round(total_spent, 2),
            'budget': budget,
            'budget_percentage': round((total_spent / budget * 100) if budget > 0 else 0, 1),
            'vs_last_period': {
                'spent': round(prev_total_spent, 2),
                'difference': round(total_spent - prev_total_spent, 2),
                'percentage_change': round(((total_spent - prev_total_spent) / prev_total_spent * 100) if prev_total_spent > 0 else 0, 1)
            },
            'avg_per_week': round(avg_per_week, 2),
            'category_breakdown': category_breakdown,
            'top_items': top_items
        })

    def get_recipes_analytics(self, period: str) -> Dict:
        """Get recipe insights."""
        start_date, end_date = self.get_period_dates(period)

        # Cooking logs
        cooking_logs = RecipeCookingLog.objects.filter(
            user=self.user,
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
        reviews = RecipeReview.objects.filter(user=self.user)
        reviews_written = reviews.count()
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

        # Category distribution
        user_recipes = Recipe.objects.filter(created_by=self.user)
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
            'category_distribution': category_distribution
        })

    def get_inventory_analytics(self, period: str) -> Dict:
        """Get inventory insights."""
        inventory_items = Inventory.objects.filter(user=self.user)
        total_items = inventory_items.count()

        # Low stock items (quantity < threshold)
        low_stock_items = []
        for item in inventory_items:
            # Simple heuristic: if quantity is numeric and < 3, it's low
            try:
                qty = float(item.quantity)
                if qty < 3:
                    low_stock_items.append({
                        'name': item.name,
                        'quantity': item.quantity,
                        'unit': item.unit,
                        'threshold': 3
                    })
            except (ValueError, TypeError):
                pass

        # Expiring soon (≤3 days)
        now = timezone.now().date()
        expiring_soon = []
        expiring_tomorrow = []
        expiring_2_3_days = []

        for item in inventory_items:
            if item.expiration_date:
                days_until_expiry = (item.expiration_date - now).days
                item_data = {
                    'name': item.name,
                    'quantity': item.quantity,
                    'unit': item.unit,
                    'expires_in_days': days_until_expiry
                }

                if days_until_expiry <= 1:
                    expiring_tomorrow.append(item_data)
                    expiring_soon.append(item_data)
                elif days_until_expiry <= 3:
                    expiring_2_3_days.append(item_data)
                    expiring_soon.append(item_data)

        # Storage distribution
        storage_counts = inventory_items.values(
            'location').annotate(count=Count('id'))
        total = sum(item['count'] for item in storage_counts)
        storage_distribution = {}
        for item in storage_counts:
            location = item['location'] or 'unknown'
            percentage = (item['count'] / total * 100) if total > 0 else 0
            storage_distribution[location] = round(percentage, 0)

        # Waste count (placeholder - would need waste tracking)
        waste_count = 0  # TODO: implement waste tracking

        return convert_decimals({
            'total_items': total_items,
            'low_stock_count': len(low_stock_items),
            'expiring_soon_count': len(expiring_soon),
            'expiring_items': {
                'tomorrow': expiring_tomorrow,
                'in_2_3_days': expiring_2_3_days
            },
            'low_stock_items': low_stock_items,
            'waste_count': waste_count,
            'avg_turnover_days': 7,  # Placeholder
            'storage_distribution': storage_distribution
        })

    def get_nutrition_analytics(self, period: str) -> Optional[Dict]:
        """Get nutrition insights (only if AI coach enabled)."""
        if not hasattr(self.user, 'nutrition_settings') or not self.user.nutrition_settings.ai_coach_enabled:
            return None

        start_date, end_date = self.get_period_dates(period)

        # Get all entries in period
        entries = NutritionEntry.objects.filter(
            user=self.user,
            date__range=[start_date.date(), end_date.date()]
        )

        # Days logged
        days_logged = entries.values('date').distinct().count()
        total_days = (end_date.date() - start_date.date()).days + 1
        logging_percentage = round(
            (days_logged / total_days * 100) if total_days > 0 else 0, 0)

        # Goal achievement
        settings_obj = self.user.nutrition_settings
        # Get goals based on goal_mode
        if settings_obj.goal_mode == 'manual':
            calories_goal = float(
                settings_obj.manual_calories_goal or self.user.daily_calories_goal or 2000)
            protein_goal = float(
                settings_obj.manual_protein_goal or self.user.daily_protein_goal or 150)
        else:  # ai_calculated
            calories_goal = float(self.user.daily_calories_goal or 2000)
            protein_goal = float(self.user.daily_protein_goal or 150)

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
            user=self.user, streak_type='nutrition_logging').first()
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

    def get_achievements_analytics(self) -> Dict:
        """Get achievements and streaks data."""
        # Current streaks
        streaks = UserStreak.objects.filter(user=self.user)
        current_streaks = {}
        for streak in streaks:
            current_streaks[streak.streak_type] = streak.current_count

        # Badges earned
        achievements = Achievement.objects.filter(
            user=self.user).order_by('-earned_at')
        badges_earned = []
        for achievement in achievements:
            badges_earned.append({
                'id': achievement.badge_id,
                'name': achievement.name,
                'icon': achievement.icon,
                'description': achievement.description,
                'earned_at': achievement.earned_at.isoformat()
            })

        # Next goals (placeholder - would need to check conditions)
        next_goals = []

        # Check for chef level progress
        recipes_cooked = RecipeCookingLog.objects.filter(
            user=self.user).values('recipe').distinct().count()
        if recipes_cooked < 23:
            next_goals.append({
                'badge': 'chef_level_3',
                'name': 'Chef Level 3',
                'progress': recipes_cooked,
                'target': 23,
                'remaining': 23 - recipes_cooked
            })

        # Check for streak progress
        nutrition_streak = current_streaks.get('nutrition_logging', 0)
        if nutrition_streak >= 7 and nutrition_streak < 14:
            next_goals.append({
                'badge': 'streak_14',
                'name': '14-Day Streak',
                'progress': nutrition_streak,
                'target': 14,
                'remaining': 14 - nutrition_streak
            })

        return convert_decimals({
            'current_streaks': current_streaks,
            'badges_earned': badges_earned,
            'next_goals': next_goals
        })


class AIInsightsService:
    """Service for generating AI-powered insights using Groq."""

    def __init__(self, user):
        self.user = user
        self.api_key = os.getenv('GROQ_API_KEY', '')

    async def generate_all_insights(self, analytics_data: Dict) -> Dict:
        """Generate all AI insights."""
        insights = {
            'shopping_insights': [],
            'recipe_recommendations': [],
            'inventory_warnings': [],
            'nutrition_coaching': None,
            'generated_at': timezone.now().isoformat()
        }

        # Only generate if we have the API key
        if not self.api_key:
            return insights

        # Generate shopping insights
        if analytics_data.get('shopping'):
            insights['shopping_insights'] = await self._generate_shopping_insights(analytics_data['shopping'])

        # Generate recipe recommendations
        if analytics_data.get('recipes') and analytics_data.get('inventory'):
            insights['recipe_recommendations'] = await self._generate_recipe_recommendations(
                analytics_data['recipes'],
                analytics_data['inventory']
            )

        # Generate inventory warnings
        if analytics_data.get('inventory'):
            insights['inventory_warnings'] = await self._generate_inventory_warnings(analytics_data['inventory'])

        # Generate nutrition coaching
        if analytics_data.get('nutrition'):
            insights['nutrition_coaching'] = await self._generate_nutrition_coaching(analytics_data['nutrition'])

        return insights

    async def _generate_shopping_insights(self, shopping_data: Dict) -> List[Dict]:
        """Generate AI-powered shopping insights."""
        # Placeholder - would call Groq AI
        insights = []

        # Check for frequent purchases
        if shopping_data.get('top_items'):
            for item in shopping_data['top_items'][:3]:
                if item['count'] >= 3:
                    insights.append({
                        'type': 'bulk_buy',
                        'title': f"Consider bulk buying {item['name']}",
                        'message': f"You purchase {item['name']} {item['count']}x. Buying in bulk could save ~$5-10/month.",
                        'impact': 'medium'
                    })

        # Check budget performance
        if shopping_data.get('vs_last_period'):
            diff = shopping_data['vs_last_period']['difference']
            if diff < -20:
                insights.append({
                    'type': 'savings',
                    'title': 'Great savings this month!',
                    'message': f"You saved ${abs(diff):.2f} compared to last month. Keep it up!",
                    'impact': 'positive'
                })

        return insights

    async def _generate_recipe_recommendations(self, recipes_data: Dict, inventory_data: Dict) -> List[Dict]:
        """Generate AI-powered recipe recommendations."""
        # Placeholder - would call Groq AI with user preferences and inventory
        recommendations = []

        # Simple rule-based recommendations
        if recipes_data.get('favorite'):
            recommendations.append({
                'name': 'Similar to your favorite',
                'description': f"Since you love {recipes_data['favorite']['name']}, try similar recipes",
                'matches': ['Favorite category'],
                'confidence': 0.85
            })

        return recommendations

    async def _generate_inventory_warnings(self, inventory_data: Dict) -> List[Dict]:
        """Generate inventory warnings and suggestions."""
        warnings = []

        # Expiring items
        if inventory_data.get('expiring_items', {}).get('tomorrow'):
            for item in inventory_data['expiring_items']['tomorrow']:
                warnings.append({
                    'type': 'urgent',
                    'title': f"Use {item['name']} today!",
                    'message': f"{item['quantity']} {item['unit']} expiring tomorrow",
                    'suggestion': f"Quick recipe suggestion using {item['name']}",
                    'priority': 'high'
                })

        # Low stock
        if inventory_data.get('low_stock_items'):
            for item in inventory_data['low_stock_items']:
                warnings.append({
                    'type': 'low_stock',
                    'title': f"Low on {item['name']}",
                    'message': f"Only {item['quantity']} {item['unit']} remaining",
                    'suggestion': 'Add to shopping list?',
                    'priority': 'medium'
                })

        return warnings

    async def _generate_nutrition_coaching(self, nutrition_data: Dict) -> Dict:
        """Generate AI nutrition coaching insights."""
        coaching = {
            'summary': '',
            'strengths': [],
            'improvements': [],
            'prediction': {}
        }

        # Analyze performance
        logging_pct = nutrition_data.get('logging_percentage', 0)
        if logging_pct >= 90:
            coaching['strengths'].append('Excellent logging consistency!')

        calories_achievement = nutrition_data.get(
            'goal_achievement', {}).get('calories', {}).get('percentage', 0)
        protein_achievement = nutrition_data.get(
            'goal_achievement', {}).get('protein', {}).get('percentage', 0)

        if protein_achievement < 70:
            coaching['improvements'].append({
                'area': 'Protein intake',
                'current': f"{protein_achievement}% of days",
                'goal': '80%+ of days',
                'tip': 'Add Greek yogurt (150g) or 2 egg whites to breakfast'
            })

        coaching['summary'] = f"You've logged {logging_pct}% of days with {calories_achievement}% calorie goal achievement."

        return coaching

    def generate_insight_of_day(self, analytics_data: Dict) -> str:
        """Generate a single insight of the day message."""
        shopping = analytics_data.get('shopping', {})
        recipes = analytics_data.get('recipes', {})

        # Compare spending to recipes cooked
        spent = shopping.get('total_spent', 0)
        cooked = recipes.get('total_cooked', 0)
        vs_last = shopping.get('vs_last_period', {})
        pct_change = vs_last.get('percentage_change', 0)

        if pct_change < 0 and cooked > 10:
            return f"You're spending {abs(pct_change)}% less than last month while cooking {cooked} recipes. Excellent balance of budget and variety! 🎉"
        elif cooked > 20:
            return f"Impressive! You've cooked {cooked} recipes this period. You're a home chef! 👨‍🍳"
        elif spent < 300:
            return f"Great budget management! Spent only ${spent} this period. 💰"
        else:
            return "Keep tracking your food journey! Every meal logged helps you reach your goals. 🎯"
