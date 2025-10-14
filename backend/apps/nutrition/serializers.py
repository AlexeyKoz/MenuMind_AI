from rest_framework import serializers
from .models import UserNutritionSettings, NutritionEntry
from apps.recipes.models import Recipe
from apps.shopping.models import Inventory


class UserNutritionSettingsSerializer(serializers.ModelSerializer):
    """Serializer for nutrition settings with privacy controls"""

    active_permissions = serializers.SerializerMethodField()

    class Meta:
        model = UserNutritionSettings
        fields = [
            # Master switch
            'ai_coach_enabled',

            # Content permissions
            'allow_recipes_access',
            'allow_inventory_access',
            'allow_shopping_access',

            # Personal data permissions
            'allow_personal_data_access',
            'allow_weight_data',
            'allow_height_data',
            'allow_age_data',
            'allow_gender_data',
            'allow_activity_level',
            'allow_health_conditions',

            # Goals
            'goal_mode',
            'manual_calories_goal',
            'manual_protein_goal',
            'manual_carbs_goal',
            'manual_fat_goal',

            # Coaching
            'coaching_frequency',
            'coaching_style',
            'track_calories',
            'track_protein',
            'track_carbs',
            'track_fat',
            'track_meal_timing',

            # Metadata
            'created_at',
            'updated_at',

            # Computed
            'active_permissions'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_active_permissions(self, obj):
        """Get list of active permissions"""
        return obj.get_active_permissions()

    def validate(self, data):
        """Ensure logical consistency of permissions"""
        # If AI coach is disabled, ignore all permission settings
        if not data.get('ai_coach_enabled', False):
            return data

        # If personal data access is disabled, disable all granular permissions
        if not data.get('allow_personal_data_access', False):
            data['allow_weight_data'] = False
            data['allow_height_data'] = False
            data['allow_age_data'] = False
            data['allow_gender_data'] = False
            data['allow_activity_level'] = False
            data['allow_health_conditions'] = False

        # If goal mode is AI calculated, require personal data access
        if data.get('goal_mode') == 'ai_calculated' and not data.get('allow_personal_data_access', False):
            raise serializers.ValidationError({
                'goal_mode': 'AI-calculated goals require personal data access to be enabled.'
            })

        return data


class NutritionEntrySerializer(serializers.ModelSerializer):
    """Main serializer for nutrition entries"""

    recipe_name = serializers.CharField(source='recipe.name', read_only=True)
    inventory_item_name = serializers.CharField(
        source='inventory_item.name', read_only=True)
    macros_summary = serializers.SerializerMethodField()

    class Meta:
        model = NutritionEntry
        fields = [
            'id',
            'user',
            'date',
            'meal_type',
            'time',
            'entry_type',
            'recipe',
            'recipe_name',
            'inventory_item',
            'inventory_item_name',
            'food_name',
            'portion_size',
            'portion_unit',
            'calories',
            'protein',
            'carbs',
            'fat',
            'fiber',
            'sugar',
            'sodium',
            'notes',
            'photo',
            'created_at',
            'updated_at',
            'macros_summary'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_macros_summary(self, obj):
        """Get formatted macros"""
        return obj.get_macros_summary()

    def validate(self, data):
        """Validate nutrition entry data"""
        # If entry_type is 'recipe', recipe must be provided
        if data.get('entry_type') == 'recipe' and not data.get('recipe'):
            raise serializers.ValidationError({
                'recipe': 'Recipe must be provided when entry_type is "recipe".'
            })

        # If entry_type is 'product', inventory_item must be provided
        if data.get('entry_type') == 'product' and not data.get('inventory_item'):
            raise serializers.ValidationError({
                'inventory_item': 'Inventory item must be provided when entry_type is "product".'
            })

        return data


class NutritionEntryCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating entries"""

    class Meta:
        model = NutritionEntry
        fields = [
            'date',
            'meal_type',
            'time',
            'entry_type',
            'food_name',
            'portion_size',
            'portion_unit',
            'calories',
            'protein',
            'carbs',
            'fat',
            'fiber',
            'sugar',
            'sodium',
            'notes',
            'photo'
        ]


class LogFromRecipeSerializer(serializers.Serializer):
    """Serializer for logging nutrition from a recipe"""

    recipe_id = serializers.UUIDField()
    portion_multiplier = serializers.FloatField(
        min_value=0.1,
        max_value=10.0,
        default=1.0,
        help_text="1.0 = 1 serving, 0.5 = half serving, 2.0 = double serving"
    )
    meal_type = serializers.ChoiceField(
        choices=['breakfast', 'lunch', 'dinner', 'snack']
    )
    date = serializers.DateField()
    time = serializers.TimeField(required=False, allow_null=True)
    notes = serializers.CharField(
        required=False, allow_blank=True, max_length=500)

    def validate_recipe_id(self, value):
        """Ensure recipe exists and belongs to user"""
        user = self.context['request'].user
        try:
            recipe = Recipe.objects.get(id=value, created_by=user)
            return value
        except Recipe.DoesNotExist:
            raise serializers.ValidationError(
                "Recipe not found or doesn't belong to you.")


class LogFromInventorySerializer(serializers.Serializer):
    """Serializer for logging nutrition from inventory item"""

    inventory_item_id = serializers.UUIDField()
    amount_grams = serializers.FloatField(
        min_value=0.1,
        help_text="Amount consumed in grams"
    )
    meal_type = serializers.ChoiceField(
        choices=['breakfast', 'lunch', 'dinner', 'snack']
    )
    date = serializers.DateField()
    time = serializers.TimeField(required=False, allow_null=True)
    update_inventory = serializers.BooleanField(
        default=True,
        help_text="Whether to deduct from inventory stock"
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, max_length=500)

    def validate_inventory_item_id(self, value):
        """Ensure inventory item exists and has nutrition data"""
        user = self.context['request'].user
        try:
            item = Inventory.objects.get(id=value, user=user)
            # Check if item has nutrition data
            if not hasattr(item, 'calories_per_100g') or item.calories_per_100g is None:
                raise serializers.ValidationError(
                    "This inventory item doesn't have nutrition information."
                )
            return value
        except Inventory.DoesNotExist:
            raise serializers.ValidationError("Inventory item not found.")

    def validate_amount_grams(self, value):
        """Ensure amount is reasonable"""
        if value > 10000:  # 10kg limit
            raise serializers.ValidationError(
                "Amount seems too large (max 10kg).")
        return value


class DailySummarySerializer(serializers.Serializer):
    """Serializer for daily nutrition summary"""

    date = serializers.DateField()
    goals = serializers.DictField()
    consumed = serializers.DictField()
    remaining = serializers.DictField()
    percentage = serializers.DictField()
    meals = NutritionEntrySerializer(many=True)


class WeeklySummarySerializer(serializers.Serializer):
    """Serializer for weekly nutrition summary"""

    week_start = serializers.DateField()
    week_end = serializers.DateField()
    daily_averages = serializers.DictField()
    weekly_totals = serializers.DictField()
    goal_adherence = serializers.DictField()
    days = serializers.ListField()


class AISuggestionRequestSerializer(serializers.Serializer):
    """Request serializer for AI suggestions"""

    meal_type = serializers.ChoiceField(
        choices=['breakfast', 'lunch', 'dinner', 'snack'],
        required=False,
        allow_null=True
    )
    max_calories = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=50,
        max_value=2000
    )


class AISuggestionResponseSerializer(serializers.Serializer):
    """Response serializer for AI suggestions"""

    ai_enabled = serializers.BooleanField()
    message = serializers.CharField()
    suggestions = serializers.ListField(required=False)


class AICoachingRequestSerializer(serializers.Serializer):
    """Request serializer for AI coaching"""

    question = serializers.CharField(max_length=500)


class AICoachingResponseSerializer(serializers.Serializer):
    """Response serializer for AI coaching"""

    advice = serializers.CharField()
    suggestions = serializers.ListField(required=False)
