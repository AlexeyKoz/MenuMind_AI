"""
Custom throttle classes for recipe API endpoints

Throttles prevent abuse and ensure fair usage:
1. ReviewRateThrottle - Limit review creation (5/hour, 20/day)
2. LikeRateThrottle - Limit like/unlike actions (100/hour)
3. RatingRateThrottle - Limit rating submissions (50/hour)
4. RecipeBuilderThrottle - Limit recipe creation (10/hour, 30/day)
5. RecipeSearchThrottle - Limit AI recipe searches (20/hour, 100/day)

Usage in views:
    class MyViewSet(viewsets.ViewSet):
        throttle_classes = [ReviewRateThrottle]
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class ReviewRateThrottle(UserRateThrottle):
    """
    Throttle for review creation/updates

    Prevents review spam by limiting to:
    - 5 reviews per hour
    - 20 reviews per day
    """
    scope = 'review'
    rate = '5/hour'


class ReviewDailyThrottle(UserRateThrottle):
    """Daily limit for reviews"""
    scope = 'review_daily'
    rate = '20/day'


class LikeRateThrottle(UserRateThrottle):
    """
    Throttle for like/unlike actions

    Higher limit as likes are quick actions:
    - 100 likes per hour
    """
    scope = 'like'
    rate = '100/hour'


class RatingRateThrottle(UserRateThrottle):
    """
    Throttle for rating submissions

    Moderate limit:
    - 50 ratings per hour
    """
    scope = 'rating'
    rate = '50/hour'


class RecipeBuilderThrottle(UserRateThrottle):
    """
    Throttle for recipe builder creation

    Limits recipe creation to prevent spam:
    - 10 recipes per hour
    - 30 recipes per day
    """
    scope = 'recipe_builder'
    rate = '10/hour'


class RecipeBuilderDailyThrottle(UserRateThrottle):
    """Daily limit for recipe creation"""
    scope = 'recipe_builder_daily'
    rate = '30/day'


class RecipeSearchThrottle(UserRateThrottle):
    """
    Throttle for AI recipe searches

    AI searches are expensive, so limit to:
    - 20 searches per hour
    - 100 searches per day
    """
    scope = 'recipe_search'
    rate = '100/hour'


class RecipeSearchDailyThrottle(UserRateThrottle):
    """Daily limit for AI searches"""
    scope = 'recipe_search_daily'
    rate = '100/day'


class MarkHelpfulThrottle(UserRateThrottle):
    """
    Throttle for marking reviews as helpful

    Moderate limit:
    - 50 helpful marks per hour
    """
    scope = 'mark_helpful'
    rate = '50/hour'


class AnonRecipeViewThrottle(AnonRateThrottle):
    """
    Throttle for anonymous users viewing recipes

    More restrictive to encourage registration:
    - 100 views per hour
    """
    scope = 'anon_recipe_view'
    rate = '100/hour'


class BurstRateThrottle(UserRateThrottle):
    """
    Short burst throttle for rapid actions

    Allows quick interactions but prevents rapid spam:
    - 10 actions per minute
    """
    scope = 'burst'
    rate = '10/min'


# Configuration for settings.py
"""
Add to REST_FRAMEWORK settings:

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'review': '5/hour',
        'review_daily': '20/day',
        'like': '100/hour',
        'rating': '50/hour',
        'recipe_builder': '10/hour',
        'recipe_builder_daily': '30/day',
        'recipe_search': '20/hour',
        'recipe_search_daily': '100/day',
        'mark_helpful': '50/hour',
        'anon_recipe_view': '100/hour',
        'burst': '10/min',
    }
}

Usage in views:

from apps.recipes.throttles import (
    ReviewRateThrottle,
    ReviewDailyThrottle,
    LikeRateThrottle,
    RatingRateThrottle,
    RecipeBuilderThrottle,
    RecipeSearchThrottle
)

class CanonicalRecipeViewSet(viewsets.ReadOnlyModelViewSet):
    
    @action(detail=True, methods=['post'], throttle_classes=[ReviewRateThrottle, ReviewDailyThrottle])
    def add_review(self, request, pk=None):
        # Review creation logic
        pass
    
    @action(detail=True, methods=['post'], throttle_classes=[LikeRateThrottle])
    def like(self, request, pk=None):
        # Like logic
        pass
"""
