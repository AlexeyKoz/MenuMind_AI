from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.db import transaction
from .models import IngredientCache, IngredientTranslation
from .services import IMLSyncService


class IngredientTranslationInline(admin.TabularInline):
    """Inline translations for ingredients"""
    model = IngredientTranslation
    extra = 0
    fields = ['language', 'name', 'description', 'aliases', 'storage_tips']
    readonly_fields = []


@admin.register(IngredientCache)
class IngredientCacheAdmin(admin.ModelAdmin):
    """Admin interface for Ingredient Cache (IML data)"""

    list_display = [
        'ingredient_key',
        'category',
        'source',
        'nutrition_preview',
        'translation_count',
        'last_synced'
    ]

    list_filter = ['source', 'category', 'last_synced']

    search_fields = [
        'ingredient_key',
        'category',
        'translations__name'
    ]

    readonly_fields = [
        'ingredient_key',
        'last_synced',
        'created_at',
        'nutrition_display',
        'conversions_display',
        'shelf_life_display',
        'storage_display'
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'ingredient_key',
                'category',
                'source',
            )
        }),
        ('Nutrition (per 100g)', {
            'fields': ('nutrition_display',),
            'classes': ('collapse',)
        }),
        ('Unit Conversions', {
            'fields': ('common_units', 'conversions_display'),
            'classes': ('collapse',)
        }),
        ('Storage Information', {
            'fields': ('shelf_life_display', 'storage_display'),
            'classes': ('collapse',)
        }),
        ('Raw Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('last_synced', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [IngredientTranslationInline]

    # Custom actions
    actions = ['delete_selected_ingredients']

    # Show all ingredients per page by default
    list_per_page = 100
    list_max_show_all = 2000

    def nutrition_preview(self, obj):
        """Show key nutrition facts"""
        nutrition = obj.nutrition_per_100g
        if not nutrition:
            return '-'

        cal = nutrition.get('calories', 0)
        protein = nutrition.get('protein', 0)
        carbs = nutrition.get('carbohydrates', 0)
        fat = nutrition.get('fat', 0)

        return format_html(
            '<span style="font-size: 11px;">'
            '🔥 {}kcal | 💪 {}g P | 🍞 {}g C | 🥑 {}g F'
            '</span>',
            cal, protein, carbs, fat
        )
    nutrition_preview.short_description = 'Nutrition (100g)'

    def translation_count(self, obj):
        """Count of translations"""
        count = obj.translations.count()
        if count == 0:
            return format_html('<span style="color: red;">⚠️ No translations</span>')
        elif count < 3:
            return format_html('<span style="color: orange;">⚠️ {} languages</span>', count)
        else:
            return format_html('<span style="color: green;">✅ {} languages</span>', count)
    translation_count.short_description = 'Translations'

    def nutrition_display(self, obj):
        """Formatted nutrition display"""
        nutrition = obj.nutrition_per_100g
        if not nutrition:
            return 'No nutrition data'

        lines = []
        for key, value in nutrition.items():
            lines.append(f"{key}: {value}")

        return format_html('<pre style="margin: 0;">{}</pre>', '\n'.join(lines))
    nutrition_display.short_description = 'Nutrition Facts (per 100g)'

    def conversions_display(self, obj):
        """Formatted unit conversions"""
        conversions = obj.unit_conversions
        if not conversions:
            return 'No conversions'

        lines = []
        for unit, conversion in conversions.items():
            lines.append(f"{unit} = {conversion}")

        return format_html('<pre style="margin: 0;">{}</pre>', '\n'.join(lines))
    conversions_display.short_description = 'Unit Conversions'

    def shelf_life_display(self, obj):
        """Formatted shelf life display"""
        shelf_life = obj.shelf_life
        if not shelf_life:
            return 'No data'

        lines = []
        for location, days in shelf_life.items():
            icon = '🌡️' if location == 'room_temperature' else '❄️' if location == 'freezer' else '🧊'
            lines.append(
                f"{icon} {location.replace('_', ' ').title()}: {days} days")

        return format_html('<div>{}</div>', '<br>'.join(lines))
    shelf_life_display.short_description = 'Shelf Life'

    def storage_display(self, obj):
        """Formatted storage recommendations"""
        storage = obj.storage_recommendations
        if not storage:
            return 'No recommendations'

        lines = []
        for key, value in storage.items():
            lines.append(f"{key.replace('_', ' ').title()}: {value}")

        return format_html('<div>{}</div>', '<br>'.join(lines))
    storage_display.short_description = 'Storage Recommendations'

    def has_add_permission(self, request):
        """Disable manual add - data comes from sync"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion to clean up old/invalid data"""
        return True

    def delete_selected_ingredients(self, request, queryset):
        """Delete selected ingredients and their translations"""
        count = queryset.count()
        translation_count = IngredientTranslation.objects.filter(
            ingredient__in=queryset
        ).count()

        with transaction.atomic():
            # Delete translations first
            IngredientTranslation.objects.filter(
                ingredient__in=queryset
            ).delete()
            # Then delete ingredients
            queryset.delete()

        self.message_user(
            request,
            f'Successfully deleted {count} ingredients and {translation_count} translations.',
            messages.SUCCESS
        )
    delete_selected_ingredients.short_description = "Delete selected ingredients"

    def get_urls(self):
        """Add custom URLs for sync and delete all"""
        urls = super().get_urls()
        custom_urls = [
            path(
                'sync-from-sqlite/',
                self.admin_site.admin_view(self.sync_from_sqlite_view),
                name='core_ingredientcache_sync',
            ),
            path(
                'delete-all/',
                self.admin_site.admin_view(self.delete_all_view),
                name='core_ingredientcache_delete_all',
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """Add custom buttons to the changelist"""
        extra_context = extra_context or {}
        extra_context['show_sync_button'] = True
        extra_context['show_delete_all_button'] = True
        return super().changelist_view(request, extra_context)

    def sync_from_sqlite_view(self, request):
        """Custom view to sync from SQLite"""
        if request.method == 'POST':
            try:
                sync_service = IMLSyncService()
                result = sync_service.sync_from_iml(force=True)

                self.message_user(
                    request,
                    f'Successfully synced! Created: {result["created"]}, '
                    f'Updated: {result["updated"]}, Errors: {result["errors"]}',
                    messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Error syncing from SQLite: {str(e)}',
                    messages.ERROR
                )

            return redirect('..')

        # Show confirmation page
        context = {
            **self.admin_site.each_context(request),
            'title': 'Sync from SQLite Database',
            'opts': self.model._meta,
            'current_count': IngredientCache.objects.count(),
            'translation_count': IngredientTranslation.objects.count(),
        }
        return render(request, 'admin/core/sync_confirm.html', context)

    def delete_all_view(self, request):
        """Custom view to delete all ingredients"""
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    translation_count = IngredientTranslation.objects.count()
                    ingredient_count = IngredientCache.objects.count()

                    IngredientTranslation.objects.all().delete()
                    IngredientCache.objects.all().delete()

                self.message_user(
                    request,
                    f'Successfully deleted all {ingredient_count} ingredients '
                    f'and {translation_count} translations.',
                    messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Error deleting ingredients: {str(e)}',
                    messages.ERROR
                )

            return redirect('..')

        # Show confirmation page
        context = {
            **self.admin_site.each_context(request),
            'title': 'Delete All Ingredients',
            'opts': self.model._meta,
            'ingredient_count': IngredientCache.objects.count(),
            'translation_count': IngredientTranslation.objects.count(),
        }
        return render(request, 'admin/core/delete_all_confirm.html', context)


@admin.register(IngredientTranslation)
class IngredientTranslationAdmin(admin.ModelAdmin):
    """Admin interface for Ingredient Translations"""

    list_display = [
        'ingredient_key_display',
        'language',
        'name',
        'aliases_count',
        'has_description',
        'has_storage_tips'
    ]

    list_filter = ['language', 'ingredient__category', 'ingredient__source']

    search_fields = [
        'name',
        'ingredient__ingredient_key',
        'description',
        'aliases'
    ]

    readonly_fields = []

    fieldsets = (
        ('Link', {
            'fields': ('ingredient',)
        }),
        ('Translation', {
            'fields': ('language', 'name', 'description')
        }),
        ('Additional Info', {
            'fields': ('aliases', 'storage_tips'),
            'classes': ('collapse',)
        }),
    )

    def ingredient_key_display(self, obj):
        """Display ingredient key"""
        return obj.ingredient.ingredient_key
    ingredient_key_display.short_description = 'Ingredient'
    ingredient_key_display.admin_order_field = 'ingredient__ingredient_key'

    def aliases_count(self, obj):
        """Count of aliases"""
        count = len(obj.aliases) if obj.aliases else 0
        if count == 0:
            return '-'
        return f"{count} aliases"
    aliases_count.short_description = 'Aliases'

    def has_description(self, obj):
        """Has description"""
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.description else 'gray',
            '✅' if obj.description else '⬜'
        )
    has_description.short_description = 'Description'

    def has_storage_tips(self, obj):
        """Has storage tips"""
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.storage_tips else 'gray',
            '✅' if obj.storage_tips else '⬜'
        )
    has_storage_tips.short_description = 'Storage Tips'

    def has_add_permission(self, request):
        """Disable manual add - data comes from sync"""
        return False
