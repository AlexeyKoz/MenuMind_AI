from django.contrib import admin
from .models import Recipe, UserRecipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin interface for Recipe model"""

    list_display = ['name', 'author', 'difficulty', 'cuisine',
                    'version', 'is_latest_version', 'times_cooked', 'created_at']
    list_filter = ['difficulty', 'cuisine', 'is_latest_version', 'diet_labels']
    search_fields = ['name', 'description', 'author']
    readonly_fields = ['recipe_hash', 'version', 'created_at',
                       'updated_at', 'times_added_to_lists', 'times_cooked']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'author', 'source_url', 'created_by')
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



