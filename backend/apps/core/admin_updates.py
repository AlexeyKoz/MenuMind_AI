"""
Admin interface for App Updates
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.core.models import AppUpdate


@admin.register(AppUpdate)
class AppUpdateAdmin(admin.ModelAdmin):
    list_display = [
        'status_badge',
        'title',
        'language',
        'version',
        'publish_date',
        'featured_badge',
        'published_badge',
    ]
    list_filter = ['language', 'status', 'is_published', 'is_featured', 'publish_date']
    search_fields = ['title', 'description', 'version']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'publish_date'
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'description', 'language')
        }),
        ('Status & Metadata', {
            'fields': ('status', 'version', 'publish_date', 'is_published', 'is_featured')
        }),
        ('System', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            'completed': '#10b981',  # green
            'upcoming': '#3b82f6',   # blue
        }
        icon = '✅' if obj.status == 'completed' else '🔜'
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">'
            '{} {}'
            '</span>',
            color, icon, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def featured_badge(self, obj):
        """Display featured status"""
        if obj.is_featured:
            return format_html(
                '<span style="background-color: #f59e0b; color: white; padding: 3px 8px; border-radius: 10px; font-size: 10px;">⭐ FEATURED</span>'
            )
        return '-'
    featured_badge.short_description = 'Featured'
    
    def published_badge(self, obj):
        """Display published status"""
        if obj.is_published:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">✓ Published</span>'
            )
        return format_html(
            '<span style="color: #ef4444; font-weight: bold;">✗ Draft</span>'
        )
    published_badge.short_description = 'Published'
    
    actions = ['mark_as_published', 'mark_as_draft', 'mark_as_featured']
    
    def mark_as_published(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} update(s) marked as published.')
    mark_as_published.short_description = 'Mark selected updates as published'
    
    def mark_as_draft(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} update(s) marked as draft.')
    mark_as_draft.short_description = 'Mark selected updates as draft'
    
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} update(s) marked as featured.')
    mark_as_featured.short_description = 'Mark selected updates as featured'



