from rest_framework import serializers
from .models import Achievement, UserStreak, RecipeCookingLog


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'badge_id', 'name', 'icon', 'description', 'earned_at']
        read_only_fields = ['id', 'earned_at']


class UserStreakSerializer(serializers.ModelSerializer):
    streak_type_display = serializers.CharField(
        source='get_streak_type_display', read_only=True)

    class Meta:
        model = UserStreak
        fields = ['id', 'streak_type', 'streak_type_display',
                  'current_count', 'longest_count', 'last_activity_date']
        read_only_fields = ['id', 'current_count',
                            'longest_count', 'last_activity_date']


class RecipeCookingLogSerializer(serializers.ModelSerializer):
    recipe_name = serializers.CharField(source='recipe.name', read_only=True)

    class Meta:
        model = RecipeCookingLog
        fields = ['id', 'recipe', 'recipe_name',
                  'canonical_recipe', 'cooked_at', 'servings', 'notes']
        read_only_fields = ['id', 'cooked_at']


class DashboardOverviewSerializer(serializers.Serializer):
    """Dashboard overview data"""
    period = serializers.CharField()
    overview = serializers.DictField()
    shopping = serializers.DictField()
    recipes = serializers.DictField()
    inventory = serializers.DictField()
    nutrition = serializers.DictField(allow_null=True)
    achievements = serializers.DictField()
    ai_insight_of_day = serializers.CharField(allow_null=True)


class AIInsightsSerializer(serializers.Serializer):
    """AI-generated insights"""
    shopping_insights = serializers.ListField(child=serializers.DictField())
    recipe_recommendations = serializers.ListField(
        child=serializers.DictField())
    inventory_warnings = serializers.ListField(child=serializers.DictField())
    nutrition_coaching = serializers.DictField(allow_null=True)
    generated_at = serializers.DateTimeField()








