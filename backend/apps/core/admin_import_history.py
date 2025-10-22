"""
Additional Django admin interfaces for Sprint 1 improvements
Add this to backend/apps/core/admin.py at the end
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import ImportHistory


@admin.register(ImportHistory)
class ImportHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Import History tracking
    Shows all IML and CookLingo import operations
    """

    list_display = [
        'imported_at',
        'import_type',
        'imported_by',
        'status_indicator',
        'records_summary',
        'success_rate_display',
        'source_file'
    ]

    list_filter = [
        'import_type',
        'status',
        'imported_at',
        'imported_by'
    ]

    search_fields = [
        'source_file',
        'imported_by',
        'error_log'
    ]

    readonly_fields = [
        'import_type',
        'source_file',
        'records_imported',
        'records_updated',
        'records_failed',
        'imported_by',
        'imported_at',
        'status',
        'error_log_display',
        'summary_display',
        'success_rate_display',
        'total_records_display'
    ]

    fieldsets = (
        ('Import Information', {
            'fields': (
                'import_type',
                'source_file',
                'imported_by',
                'imported_at',
                'status'
            )
        }),
        ('Statistics', {
            'fields': (
                'total_records_display',
                'records_imported',
                'records_updated',
                'records_failed',
                'success_rate_display'
            )
        }),
        ('Details', {
            'fields': (
                'summary_display',
                'error_log_display'
            ),
            'classes': ('collapse',)
        }),
    )

    date_hierarchy = 'imported_at'
    list_per_page = 50

    def has_add_permission(self, request):
        """Disable manual add - records created by import system"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup"""
        return True

    def status_indicator(self, obj):
        """Visual status indicator"""
        colors = {
            'success': 'green',
            'partial': 'orange',
            'failed': 'red'
        }
        icons = {
            'success': '✅',
            'partial': '⚠️',
            'failed': '❌'
        }

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            colors.get(obj.status, 'gray'),
            icons.get(obj.status, '?'),
            obj.get_status_display()
        )
    status_indicator.short_description = 'Status'
    status_indicator.admin_order_field = 'status'

    def records_summary(self, obj):
        """Summary of records"""
        return format_html(
            '<span style="font-size: 11px;">✨ {} new | 🔄 {} updated | ❌ {} failed</span>',
            obj.records_imported,
            obj.records_updated,
            obj.records_failed
        )
    records_summary.short_description = 'Records'

    def success_rate_display(self, obj):
        """Success rate as percentage"""
        rate = obj.get_success_rate()
        color = 'green' if rate >= 95 else 'orange' if rate >= 80 else 'red'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color,
            rate
        )
    success_rate_display.short_description = 'Success Rate'

    def total_records_display(self, obj):
        """Total records processed"""
        return obj.get_total_records()
    total_records_display.short_description = 'Total Records'

    def error_log_display(self, obj):
        """Formatted error log"""
        if not obj.error_log:
            return 'No errors'

        try:
            import json
            errors = json.loads(obj.error_log)
            if not errors:
                return 'No errors'

            errors_display = errors[:10]
            html = '<ul style="margin: 0; padding-left: 20px;">'
            for error in errors_display:
                html += f'<li>{error}</li>'
            html += '</ul>'

            if len(errors) > 10:
                html += f'<p><em>... and {len(errors) - 10} more errors</em></p>'

            return format_html(html)
        except:
            return obj.error_log
    error_log_display.short_description = 'Errors'

    def summary_display(self, obj):
        """Formatted summary"""
        if not obj.summary:
            return 'No summary'

        lines = []
        for key, value in obj.summary.items():
            lines.append(f'{key}: {value}')

        return format_html('<pre style="margin: 0;">{}</pre>', '\n'.join(lines))
    summary_display.short_description = 'Summary'
