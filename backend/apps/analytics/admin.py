from django.contrib import admin
from .models import DashboardCache, Achievement, UserStreak, RecipeCookingLog


@admin.register(DashboardCache)
class DashboardCacheAdmin(admin.ModelAdmin):
    list_display = ['user', 'period', 'updated_at', 'expires_at', 'is_expired']
    list_filter = ['period', 'expires_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'ai_generated_at']

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'badge_id',
                    'icon', 'earned_at', 'notified']
    list_filter = ['badge_id', 'earned_at', 'notified']
    search_fields = ['user__username', 'name']
    readonly_fields = ['id', 'earned_at']
    ordering = ['-earned_at']


@admin.register(UserStreak)
class UserStreakAdmin(admin.ModelAdmin):
    list_display = ['user', 'streak_type', 'current_count',
                    'longest_count', 'last_activity_date']
    list_filter = ['streak_type']
    search_fields = ['user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(RecipeCookingLog)
class RecipeCookingLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipe', 'cooked_at', 'servings']
    list_filter = ['cooked_at']
    search_fields = ['user__username', 'recipe__name']
    readonly_fields = ['id', 'cooked_at']
    ordering = ['-cooked_at']
