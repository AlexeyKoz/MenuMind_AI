from django.contrib import admin
from .models import UserNutritionSettings, NutritionEntry


@admin.register(UserNutritionSettings)
class UserNutritionSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'ai_coach_enabled',
                    'goal_mode', 'coaching_frequency', 'coaching_style']
    list_filter = ['ai_coach_enabled', 'goal_mode',
                   'coaching_frequency', 'coaching_style']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('AI Coach', {
            'fields': ('ai_coach_enabled',)
        }),
        ('Content Access Permissions', {
            'fields': ('allow_recipes_access', 'allow_inventory_access', 'allow_shopping_access')
        }),
        ('Personal Data Access', {
            'fields': (
                'allow_personal_data_access',
                'allow_weight_data',
                'allow_height_data',
                'allow_age_data',
                'allow_gender_data',
                'allow_activity_level',
                'allow_health_conditions'
            )
        }),
        ('Goals', {
            'fields': (
                'goal_mode',
                'manual_calories_goal',
                'manual_protein_goal',
                'manual_carbs_goal',
                'manual_fat_goal'
            )
        }),
        ('Coaching Preferences', {
            'fields': (
                'coaching_frequency',
                'coaching_style',
                'track_calories',
                'track_protein',
                'track_carbs',
                'track_fat',
                'track_meal_timing'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(NutritionEntry)
class NutritionEntryAdmin(admin.ModelAdmin):
    list_display = ['food_name', 'user', 'date',
                    'meal_type', 'calories', 'protein', 'entry_type']
    list_filter = ['meal_type', 'entry_type', 'date']
    search_fields = ['food_name', 'user__username', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'

    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'date', 'time', 'meal_type', 'entry_type')
        }),
        ('Food Details', {
            'fields': ('food_name', 'portion_size', 'portion_unit')
        }),
        ('Linked Items', {
            'fields': ('recipe', 'inventory_item')
        }),
        ('Nutrition Data', {
            'fields': ('calories', 'protein', 'carbs', 'fat')
        }),
        ('Additional Nutrients', {
            'fields': ('fiber', 'sugar', 'sodium')
        }),
        ('Notes & Media', {
            'fields': ('notes', 'photo')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        })
    )
