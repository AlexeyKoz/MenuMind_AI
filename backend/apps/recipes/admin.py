from django.contrib import admin
from .models import (
    Recipe, UserRecipe, CanonicalRecipe,
    RecipeLike, RecipeRating, RecipeReview, RecipeReviewHelpful
)


@admin.register(CanonicalRecipe)
class CanonicalRecipeAdmin(admin.ModelAdmin):
    """Admin interface for CanonicalRecipe model"""

    list_display = ['name', 'source_type', 'cuisine', 'difficulty',
                    'total_saves', 'average_rating', 'total_reviews',
                    'is_published', 'is_featured', 'created_at']
    list_filter = ['source_type', 'difficulty', 'cuisine',
                   'is_published', 'is_featured', 'diet_labels']
    search_fields = ['name', 'description']
    readonly_fields = ['recipe_hash', 'total_saves', 'total_cooked', 'total_views',
                       'average_rating', 'total_ratings', 'total_reviews',
                       'created_at', 'updated_at']
    list_editable = ['is_published', 'is_featured']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'source_type', 'ai_source_url', 'original_creator')
        }),
        ('Recipe Content', {
            'fields': ('base_ingredients', 'base_steps')
        }),
        ('Metadata', {
            'fields': ('prep_time_minutes', 'cook_time_minutes', 'total_time_minutes',
                       'servings', 'difficulty', 'cuisine', 'diet_labels')
        }),
        ('Deduplication', {
            'fields': ('recipe_hash',)
        }),
        ('Statistics', {
            'fields': ('total_saves', 'total_cooked', 'total_views',
                       'average_rating', 'total_ratings', 'total_reviews')
        }),
        ('Publication', {
            'fields': ('is_published', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    actions = ['make_featured', 'remove_featured', 'update_statistics']

    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(
            request, f"{queryset.count()} recipes marked as featured")
    make_featured.short_description = "Mark selected recipes as featured"

    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(
            request, f"{queryset.count()} recipes removed from featured")
    remove_featured.short_description = "Remove featured status"

    def update_statistics(self, request, queryset):
        for recipe in queryset:
            recipe.update_statistics()
        self.message_user(
            request, f"Updated statistics for {queryset.count()} recipes")
    update_statistics.short_description = "Recalculate statistics"


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin interface for Recipe model"""

    list_display = ['name', 'created_by', 'is_fork', 'canonical_recipe', 'difficulty',
                    'cuisine', 'version', 'is_latest_version', 'times_cooked', 'created_at']
    list_filter = ['is_fork', 'difficulty',
                   'cuisine', 'is_latest_version', 'diet_labels']
    search_fields = ['name', 'description', 'author']
    readonly_fields = ['recipe_hash', 'version', 'created_at',
                       'updated_at', 'times_added_to_lists', 'times_cooked']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'author', 'source_url', 'created_by')
        }),
        ('Fork System (NEW)', {
            'fields': ('canonical_recipe', 'is_fork', 'user_modifications')
        }),
        ('Recipe Content', {
            'fields': ('ingredients', 'steps')
        }),
        ('Metadata', {
            'fields': ('prep_time_minutes', 'cook_time_minutes', 'total_time_minutes',
                       'servings', 'difficulty', 'cuisine', 'diet_labels')
        }),
        ('Versioning & Deduplication', {
            'fields': ('recipe_hash', 'version', 'parent_recipe', 'is_latest_version')
        }),
        ('Statistics', {
            'fields': ('times_added_to_lists', 'times_cooked')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(UserRecipe)
class UserRecipeAdmin(admin.ModelAdmin):
    """Admin interface for UserRecipe model"""

    list_display = ['user', 'recipe', 'rating',
                    'times_cooked', 'last_cooked', 'saved_at']
    list_filter = ['rating', 'saved_at']
    search_fields = ['user__username', 'recipe__name']
    readonly_fields = ['saved_at']

    fieldsets = (
        ('User & Recipe', {
            'fields': ('user', 'recipe')
        }),
        ('User Data', {
            'fields': ('notes', 'rating', 'times_cooked', 'last_cooked')
        }),
        ('Timestamps', {
            'fields': ('saved_at',)
        }),
    )


# ============================================================================
# SOCIAL FEATURES ADMIN
# ============================================================================

@admin.register(RecipeLike)
class RecipeLikeAdmin(admin.ModelAdmin):
    """Admin interface for RecipeLike model"""

    list_display = ['user', 'canonical_recipe', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'canonical_recipe__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(RecipeRating)
class RecipeRatingAdmin(admin.ModelAdmin):
    """Admin interface for RecipeRating model"""

    list_display = ['user', 'canonical_recipe',
                    'rating', 'created_at', 'updated_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'canonical_recipe__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(RecipeReview)
class RecipeReviewAdmin(admin.ModelAdmin):
    """Admin interface for RecipeReview model"""

    list_display = ['user', 'canonical_recipe', 'title', 'rating',
                    'helpful_count', 'is_approved', 'is_reported', 'created_at']
    list_filter = ['rating', 'is_approved', 'is_reported', 'created_at']
    search_fields = ['user__username',
                     'canonical_recipe__name', 'title', 'content']
    readonly_fields = ['helpful_count', 'created_at', 'updated_at']
    list_editable = ['is_approved']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Review Information', {
            'fields': ('user', 'canonical_recipe', 'title', 'content', 'rating')
        }),
        ('Engagement', {
            'fields': ('helpful_count',)
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_reported')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    actions = ['approve_reviews', 'flag_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} reviews approved")
    approve_reviews.short_description = "Approve selected reviews"

    def flag_reviews(self, request, queryset):
        queryset.update(is_reported=True)
        self.message_user(request, f"{queryset.count()} reviews flagged")
    flag_reviews.short_description = "Flag selected reviews"


@admin.register(RecipeReviewHelpful)
class RecipeReviewHelpfulAdmin(admin.ModelAdmin):
    """Admin interface for RecipeReviewHelpful model"""

    list_display = ['user', 'review', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'review__canonical_recipe__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
