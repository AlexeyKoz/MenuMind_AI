from rest_framework import serializers
from django.db.models import Q
from .models import (
    Recipe, UserRecipe, CanonicalRecipe,
    RecipeLike, RecipeRating, RecipeReview, RecipeReviewHelpful
)


# ============================================================================
# CANONICAL RECIPE SERIALIZERS
# ============================================================================

class CanonicalRecipeSerializer(serializers.ModelSerializer):
    """Serializer for canonical recipes"""

    user_liked = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    user_has_fork = serializers.SerializerMethodField()
    original_creator_username = serializers.CharField(
        source='original_creator.username', read_only=True, allow_null=True
    )
    original_creator_first_name = serializers.CharField(
        source='original_creator.first_name', read_only=True, allow_null=True
    )
    original_creator_last_name = serializers.CharField(
        source='original_creator.last_name', read_only=True, allow_null=True
    )
    original_creator_color = serializers.CharField(
        source='original_creator.personal_color', read_only=True, allow_null=True
    )

    class Meta:
        model = CanonicalRecipe
        fields = [
            'id', 'name', 'description', 'source_type', 'ai_source_url',
            'original_creator', 'original_creator_username',
            'original_creator_first_name', 'original_creator_last_name', 'original_creator_color',
            'base_ingredients', 'base_steps', 'cuisine', 'difficulty',
            'diet_labels', 'allergens', 'prep_time_minutes', 'cook_time_minutes',
            'total_time_minutes', 'servings', 'recipe_hash',
            'total_saves', 'total_cooked', 'total_views',
            'average_rating', 'total_ratings', 'total_reviews',
            'is_published', 'is_featured', 'created_at', 'updated_at',
            'user_liked', 'user_rating', 'user_has_fork'
        ]
        read_only_fields = [
            'id', 'recipe_hash', 'created_at', 'updated_at',
            'total_saves', 'total_cooked', 'total_views',
            'average_rating', 'total_ratings', 'total_reviews'
        ]

    def get_user_liked(self, obj):
        """Check if current user has liked this recipe"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return RecipeLike.objects.filter(
                user=request.user,
                canonical_recipe=obj
            ).exists()
        return False

    def get_user_rating(self, obj):
        """Get current user's rating for this recipe"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            rating = RecipeRating.objects.filter(
                user=request.user,
                canonical_recipe=obj
            ).first()
            return rating.rating if rating else None
        return None

    def get_user_has_fork(self, obj):
        """Check if user has a fork of this canonical recipe"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Recipe.objects.filter(
                created_by=request.user,
                canonical_recipe=obj,
                is_fork=True
            ).exists()
        return False


class CanonicalRecipeListSerializer(serializers.ModelSerializer):
    """Lighter serializer for listing canonical recipes"""

    original_creator_username = serializers.CharField(
        source='original_creator.username', read_only=True, allow_null=True
    )
    original_creator_first_name = serializers.CharField(
        source='original_creator.first_name', read_only=True, allow_null=True
    )
    original_creator_last_name = serializers.CharField(
        source='original_creator.last_name', read_only=True, allow_null=True
    )
    original_creator_color = serializers.CharField(
        source='original_creator.personal_color', read_only=True, allow_null=True
    )
    user_liked = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    user_has_fork = serializers.SerializerMethodField()

    class Meta:
        model = CanonicalRecipe
        fields = [
            'id', 'name', 'description', 'source_type',
            'original_creator_username', 'original_creator_first_name',
            'original_creator_last_name', 'original_creator_color',
            'cuisine', 'difficulty',
            'diet_labels', 'allergens', 'total_time_minutes', 'servings',
            'total_saves', 'total_cooked', 'average_rating', 'total_ratings',
            'is_featured', 'created_at', 'user_liked', 'user_rating', 'user_has_fork'
        ]

    def get_user_liked(self, obj):
        """Check if current user has liked this recipe"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return RecipeLike.objects.filter(
                user=request.user,
                canonical_recipe=obj
            ).exists()
        return False

    def get_user_rating(self, obj):
        """Get current user's rating for this recipe"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            rating = RecipeRating.objects.filter(
                user=request.user,
                canonical_recipe=obj
            ).first()
            return rating.rating if rating else None
        return None

    def get_user_has_fork(self, obj):
        """Check if user has a fork of this canonical recipe"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Recipe.objects.filter(
                created_by=request.user,
                canonical_recipe=obj
            ).exists()
        return False


# ============================================================================
# RECIPE SERIALIZERS (User Forks)
# ============================================================================

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for Recipe model (includes fork functionality)"""

    versions_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(
        source='created_by.username', read_only=True)
    canonical_recipe_data = CanonicalRecipeListSerializer(
        source='canonical_recipe', read_only=True
    )
    effective_recipe = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'description', 'author', 'source_url',
            'ingredients', 'steps', 'prep_time_minutes', 'cook_time_minutes',
            'total_time_minutes', 'servings', 'difficulty', 'cuisine',
            'diet_labels', 'allergens', 'version', 'is_latest_version', 'versions_count',
            'times_added_to_lists', 'times_cooked', 'is_saved',
            'created_by_username', 'created_at', 'updated_at',
            # New fork fields
            'canonical_recipe', 'canonical_recipe_data', 'is_fork',
            'user_modifications', 'effective_recipe'
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

    def get_effective_recipe(self, obj):
        """Get the merged recipe data (canonical + user modifications)"""
        if obj.is_fork and obj.canonical_recipe:
            return obj.get_effective_recipe()
        return None


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Serializer for creating recipes"""

    class Meta:
        model = Recipe
        fields = [
            'name', 'description', 'author', 'source_url',
            'ingredients', 'steps', 'prep_time_minutes', 'cook_time_minutes',
            'total_time_minutes', 'servings', 'difficulty', 'cuisine',
            'diet_labels', 'allergens'
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


# ============================================================================
# SOCIAL FEATURES SERIALIZERS
# ============================================================================

class RecipeLikeSerializer(serializers.ModelSerializer):
    """Serializer for recipe likes"""

    user_username = serializers.CharField(
        source='user.username', read_only=True)

    class Meta:
        model = RecipeLike
        fields = ['id', 'user', 'user_username',
                  'canonical_recipe', 'created_at']
        read_only_fields = ['id', 'created_at']


class RecipeRatingSerializer(serializers.ModelSerializer):
    """Serializer for recipe ratings"""

    user_username = serializers.CharField(
        source='user.username', read_only=True)

    class Meta:
        model = RecipeRating
        fields = ['id', 'user', 'user_username', 'canonical_recipe',
                  'rating', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_rating(self, value):
        """Ensure rating is between 1 and 5"""
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class RecipeReviewSerializer(serializers.ModelSerializer):
    """Serializer for recipe reviews"""

    user_username = serializers.CharField(
        source='user.username', read_only=True)
    user_first_name = serializers.CharField(
        source='user.first_name', read_only=True)
    user_marked_helpful = serializers.SerializerMethodField()
    canonical_recipe_name = serializers.CharField(
        source='canonical_recipe.name', read_only=True
    )

    class Meta:
        model = RecipeReview
        fields = [
            'id', 'user', 'user_username', 'user_first_name',
            'canonical_recipe', 'canonical_recipe_name',
            'title', 'content', 'rating', 'helpful_count',
            'is_reported', 'is_approved',
            'created_at', 'updated_at', 'user_marked_helpful'
        ]
        read_only_fields = [
            'id', 'helpful_count', 'is_reported',
            'created_at', 'updated_at'
        ]

    def get_user_marked_helpful(self, obj):
        """Check if current user marked this review as helpful"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return RecipeReviewHelpful.objects.filter(
                user=request.user,
                review=obj
            ).exists()
        return False

    def validate_rating(self, value):
        """Ensure rating is between 1 and 5"""
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def validate(self, data):
        """Ensure user hasn't already reviewed this recipe"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            canonical_recipe = data.get('canonical_recipe')
            if canonical_recipe and not self.instance:  # Only on create
                if RecipeReview.objects.filter(
                    user=request.user,
                    canonical_recipe=canonical_recipe
                ).exists():
                    raise serializers.ValidationError(
                        "You have already reviewed this recipe"
                    )
        return data


class CreateReviewSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews (simplified)"""

    class Meta:
        model = RecipeReview
        fields = ['title', 'content', 'rating']

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
