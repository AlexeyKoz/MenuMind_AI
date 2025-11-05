"""
Django Admin configuration for Site Branding app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import SiteLogo, SiteSettings


@admin.register(SiteLogo)
class SiteLogoAdmin(admin.ModelAdmin):
    """Admin interface for managing site logos"""
    
    list_display = [
        'logo_preview',
        'logo_type',
        'language_code',
        'is_active',
        'dimensions',
        'file_size_display',
        'updated_at',
        'uploaded_by'
    ]
    
    list_filter = [
        'logo_type',
        'language_code',
        'is_active',
        'uploaded_at'
    ]
    
    search_fields = [
        'alt_text',
        'uploaded_by'
    ]
    
    readonly_fields = [
        'logo_preview_large',
        'uploaded_at',
        'updated_at',
        'width',
        'height',
        'file_size',
        'dimensions',
        'file_size_display',
        'file_url'
    ]
    
    fieldsets = (
        ('Logo Information', {
            'fields': ('logo_type', 'language_code', 'is_active')
        }),
        ('Upload Logo', {
            'fields': ('image_file', 'alt_text'),
            'description': 'Upload a logo file. SVG format is recommended for best quality.'
        }),
        ('Preview', {
            'fields': ('logo_preview_large',),
            'classes': ('wide',)
        }),
        ('File Information', {
            'fields': ('file_url', 'dimensions', 'file_size_display', 'width', 'height', 'file_size'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def logo_preview(self, obj):
        """Small logo preview for list view"""
        if obj.image_file:
            return format_html(
                '<img src="{}" style="max-height: 40px; max-width: 100px; object-fit: contain;" />',
                obj.file_url
            )
        return "No image"
    logo_preview.short_description = 'Preview'
    
    def logo_preview_large(self, obj):
        """Large logo preview for detail view"""
        if obj.image_file:
            return format_html(
                '<div style="padding: 20px; background: #f5f5f5; border-radius: 8px; text-align: center;">'
                '<img src="{}" style="max-height: 300px; max-width: 100%; object-fit: contain;" />'
                '</div>',
                obj.file_url
            )
        return "No image uploaded"
    logo_preview_large.short_description = 'Logo Preview'
    
    def save_model(self, request, obj, form, change):
        """Track who uploaded/updated the logo"""
        obj.uploaded_by = request.user.username
        super().save_model(request, obj, form, change)
    
    def get_urls(self):
        """Add custom URL for bulk upload"""
        urls = super().get_urls()
        custom_urls = [
            path('quick-setup/', self.admin_site.admin_view(self.quick_setup_view), name='branding_sitelogo_quick_setup'),
        ]
        return custom_urls + urls
    
    def quick_setup_view(self, request):
        """Quick setup view for uploading multiple logos at once"""
        if request.method == 'POST':
            # Handle bulk upload
            uploaded_count = 0
            
            for logo_type in ['navbar_desktop', 'navbar_mobile', 'login_page', 'favicon', 'app_icon']:
                for lang in ['en', 'ru', 'he']:
                    file_key = f"{logo_type}_{lang}"
                    if file_key in request.FILES:
                        try:
                            logo, created = SiteLogo.objects.update_or_create(
                                logo_type=logo_type,
                                language_code=lang,
                                defaults={
                                    'image_file': request.FILES[file_key],
                                    'is_active': True,
                                    'uploaded_by': request.user.username
                                }
                            )
                            uploaded_count += 1
                        except Exception as e:
                            messages.error(request, f'Error uploading {file_key}: {str(e)}')
            
            if uploaded_count > 0:
                messages.success(request, f'Successfully uploaded {uploaded_count} logo(s)!')
            return redirect('admin:branding_sitelogo_changelist')
        
        context = {
            'title': 'Quick Logo Setup',
            'site_title': 'BishulSheli Admin',
            'site_header': 'BishulSheli Administration',
            'opts': self.model._meta,
        }
        return render(request, 'admin/branding/quick_setup.html', context)
    
    def changelist_view(self, request, extra_context=None):
        """Add quick setup button to changelist"""
        extra_context = extra_context or {}
        extra_context['show_quick_setup_button'] = True
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin interface for site settings"""
    
    fieldsets = (
        ('Site Names (Multi-language)', {
            'fields': ('site_name_en', 'site_name_ru', 'site_name_he')
        }),
        ('Brand Colors', {
            'fields': ('primary_color', 'secondary_color'),
            'description': 'Use hex color codes (e.g., #9B59B6)'
        }),
        ('Metadata', {
            'fields': ('updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        """Prevent adding multiple settings (singleton)"""
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings"""
        return False
    
    def save_model(self, request, obj, form, change):
        """Track who updated settings"""
        obj.updated_by = request.user.username
        super().save_model(request, obj, form, change)

