from django.contrib import admin
from .models import AIRateLimitLog, AIRateLimitSettings


@admin.register(AIRateLimitSettings)
class AIRateLimitSettingsAdmin(admin.ModelAdmin):
    list_display = ['max_recipes_per_minute',
                    'max_recipes_per_day', 'exempted_users', 'last_updated']
    fields = ['max_recipes_per_minute',
              'max_recipes_per_day', 'exempted_users']

    def has_add_permission(self, request):
        # Only allow one settings instance
        return not AIRateLimitSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False


@admin.register(AIRateLimitLog)
class AIRateLimitLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'endpoint', 'recipes_generated', 'timestamp']
    list_filter = ['endpoint', 'timestamp', 'user']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['user', 'endpoint', 'timestamp', 'recipes_generated']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        # Don't allow manual creation
        return False

    def has_change_permission(self, request, obj=None):
        # Don't allow editing
        return False
