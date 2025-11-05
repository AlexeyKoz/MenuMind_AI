"""
Django Admin configuration for Legal Compliance app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (
    LegalAcceptance,
    CookieConsent,
    LegalDocument,
    DataExportRequest,
    AccountDeletionRequest
)
from .forms import LegalDocumentAdminForm, LegalDocumentUploadForm


@admin.register(LegalAcceptance)
class LegalAcceptanceAdmin(admin.ModelAdmin):
    """Admin interface for legal acceptances"""
    list_display = [
        'user_email',
        'terms_version',
        'privacy_version',
        'cookie_version',
        'accepted_at',
        'consent_method',
        'ip_address'
    ]
    list_filter = [
        'consent_method',
        'accepted_at',
        'terms_version'
    ]
    search_fields = [
        'user__email',
        'user__username',
        'ip_address'
    ]
    readonly_fields = [
        'user',
        'terms_version',
        'privacy_version',
        'cookie_version',
        'accepted_at',
        'ip_address',
        'user_agent',
        'consent_method'
    ]
    date_hierarchy = 'accepted_at'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'

    def has_add_permission(self, request):
        """Prevent manual creation - only via registration"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - audit trail required"""
        return False


@admin.register(CookieConsent)
class CookieConsentAdmin(admin.ModelAdmin):
    """Admin interface for cookie consents"""
    list_display = [
        'user_display',
        'consent_type',
        'essential_cookies',
        'functional_cookies',
        'analytics_cookies',
        'performance_cookies',
        'gpc_signal_detected',
        'consented_at',
        'updated_at'
    ]
    list_filter = [
        'consent_type',
        'functional_cookies',
        'analytics_cookies',
        'performance_cookies',
        'gpc_signal_detected',
        'consented_at'
    ]
    search_fields = [
        'user__email',
        'user__username',
        'session_id'
    ]
    readonly_fields = [
        'user',
        'session_id',
        'consented_at',
        'ip_address',
        'gpc_signal_detected'
    ]
    date_hierarchy = 'consented_at'

    def user_display(self, obj):
        if obj.user:
            return obj.user.email
        return f"Anonymous ({obj.session_id[:8]}...)"
    user_display.short_description = 'User/Session'

    def has_delete_permission(self, request, obj=None):
        """Allow deletion only for old anonymous consents"""
        if obj and not obj.user:
            return True
        return False


@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    """Admin interface for legal documents with file upload support"""
    form = LegalDocumentAdminForm
    
    list_display = [
        'document_type',
        'language_code',
        'version',
        'effective_date',
        'is_active',
        'word_count',
        'updated_at',
        'updated_by'
    ]
    list_filter = [
        'document_type',
        'language_code',
        'is_active',
        'effective_date'
    ]
    search_fields = [
        'document_type',
        'version',
        'content'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'word_count'
    ]
    fieldsets = (
        ('Document Information', {
            'fields': ('document_type', 'language_code', 'version', 'effective_date', 'is_active')
        }),
        ('Upload File (Optional)', {
            'fields': ('markdown_file',),
            'description': 'Upload a .md file to replace the content below, or edit the content directly.'
        }),
        ('Content', {
            'fields': ('content',),
            'classes': ('wide',),
            'description': 'Markdown content - will be replaced if you upload a file above'
        }),
        ('Metadata', {
            'fields': ('updated_by', 'created_at', 'updated_at', 'word_count'),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        """Add custom URL for bulk upload"""
        urls = super().get_urls()
        custom_urls = [
            path('upload/', self.admin_site.admin_view(self.upload_view), name='legal_legaldocument_upload'),
        ]
        return custom_urls + urls

    def upload_view(self, request):
        """Custom view for uploading legal documents"""
        if request.method == 'POST':
            form = LegalDocumentUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    # Read the uploaded file
                    markdown_file = form.cleaned_data['markdown_file']
                    content = markdown_file.read().decode('utf-8')
                    
                    # Create or update the document
                    doc, created = LegalDocument.objects.update_or_create(
                        document_type=form.cleaned_data['document_type'],
                        language_code=form.cleaned_data['language_code'],
                        defaults={
                            'content': content,
                            'version': form.cleaned_data['version'],
                            'effective_date': form.cleaned_data['effective_date'],
                            'is_active': form.cleaned_data['is_active'],
                            'updated_by': request.user.username
                        }
                    )
                    
                    action = 'created' if created else 'updated'
                    messages.success(
                        request,
                        f'Legal document {doc.get_document_type_display()} '
                        f'({doc.get_language_code_display()}) was {action} successfully!'
                    )
                    return redirect('admin:legal_legaldocument_changelist')
                    
                except Exception as e:
                    messages.error(request, f'Error uploading document: {str(e)}')
        else:
            form = LegalDocumentUploadForm()
        
        context = {
            'form': form,
            'title': 'Upload Legal Document',
            'site_title': 'BishulSheli Admin',
            'site_header': 'BishulSheli Administration',
            'opts': self.model._meta,
        }
        return render(request, 'admin/legal/upload_document.html', context)

    def word_count(self, obj):
        """Display word count"""
        return len(obj.content.split())
    word_count.short_description = 'Word Count'

    def save_model(self, request, obj, form, change):
        """Track who updated the document"""
        obj.updated_by = request.user.username
        super().save_model(request, obj, form, change)

    def changelist_view(self, request, extra_context=None):
        """Add upload button to the changelist"""
        extra_context = extra_context or {}
        extra_context['show_upload_button'] = True
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(DataExportRequest)
class DataExportRequestAdmin(admin.ModelAdmin):
    """Admin interface for data export requests"""
    list_display = [
        'user_email',
        'status',
        'export_format',
        'file_size_display',
        'requested_at',
        'completed_at',
        'download_count'
    ]
    list_filter = [
        'status',
        'export_format',
        'downloaded',
        'requested_at'
    ]
    search_fields = [
        'user__email',
        'user__username'
    ]
    readonly_fields = [
        'user',
        'requested_at',
        'completed_at',
        'downloaded_at',
        'file_path',
        'file_size_bytes'
    ]
    date_hierarchy = 'requested_at'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'

    def file_size_display(self, obj):
        if obj.file_size_bytes:
            # Convert bytes to human-readable format
            for unit in ['B', 'KB', 'MB', 'GB']:
                if obj.file_size_bytes < 1024.0:
                    return f"{obj.file_size_bytes:.1f} {unit}"
                obj.file_size_bytes /= 1024.0
        return 'N/A'
    file_size_display.short_description = 'File Size'


@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(admin.ModelAdmin):
    """Admin interface for account deletion requests"""
    list_display = [
        'user_email',
        'status',
        'requested_at',
        'grace_period_ends',
        'completed_at',
        'days_until_deletion'
    ]
    list_filter = [
        'status',
        'requested_at'
    ]
    search_fields = [
        'user__email',
        'user__username',
        'reason'
    ]
    readonly_fields = [
        'user',
        'requested_at',
        'grace_period_ends',
        'completed_at',
        'cancelled_at'
    ]
    date_hierarchy = 'requested_at'

    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'status', 'requested_at')
        }),
        ('Timeline', {
            'fields': ('grace_period_ends', 'completed_at', 'cancelled_at')
        }),
        ('User Feedback', {
            'fields': ('reason',),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'

    def days_until_deletion(self, obj):
        if obj.status == 'pending':
            from django.utils import timezone
            days = (obj.grace_period_ends - timezone.now()).days
            if days > 0:
                return format_html('<span style="color: orange;">{} days</span>', days)
            else:
                return format_html('<span style="color: red;">Overdue</span>')
        return 'N/A'
    days_until_deletion.short_description = 'Days Until Deletion'
