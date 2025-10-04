from rest_framework import serializers
from django.db.models import Q
from .models import Recipe, UserRecipe


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for Recipe model"""

    versions_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(
        source='created_by.username', read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'description', 'author', 'source_url',
            'ingredients', 'steps', 'prep_time_minutes', 'cook_time_minutes',
            'total_time_minutes', 'servings', 'difficulty', 'cuisine',
            'diet_labels', 'version', 'is_latest_version', 'versions_count',
            'times_added_to_lists', 'times_cooked', 'is_saved',
            'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'version', 'recipe_hash',
                            'created_at', 'updated_at', 'is_latest_version']

    def get_versions_count(self, obj):
        if obj.parent_recipe:
            return Recipe.objects.filter(
                Q(parent_recipe=obj.parent_recipe) | Q(id=obj.parent_recipe.id)
            ).count()
        return Recipe.objects.filter(parent_recipe=obj).count() + 1

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserRecipe.objects.filter(user=request.user, recipe=obj).exists()
        return False


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Serializer for creating recipes"""

    class Meta:
        model = Recipe
        fields = [
            'name', 'description', 'author', 'source_url',
            'ingredients', 'steps', 'prep_time_minutes', 'cook_time_minutes',
            'total_time_minutes', 'servings', 'difficulty', 'cuisine',
            'diet_labels'
        ]


class UserRecipeSerializer(serializers.ModelSerializer):
    """Serializer for UserRecipe model"""

    recipe = RecipeSerializer(read_only=True)
    recipe_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = UserRecipe
        fields = ['id', 'recipe', 'recipe_id', 'notes',
                  'rating', 'times_cooked', 'last_cooked', 'saved_at']
        read_only_fields = ['id', 'saved_at']


class RCIPFormatSerializer(serializers.Serializer):
    """Serializer for full RCIP format export"""

    rcip_version = serializers.CharField()
    id = serializers.CharField()
    meta = serializers.DictField()
    ingredients = serializers.ListField()
    steps = serializers.ListField()
    extensions = serializers.DictField()



