"""
Legal Compliance Models for MenuMindAI

Tracks user acceptance of legal documents and cookie consent preferences.
GDPR/CCPA/Israel Amendment 13 compliant.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class LegalAcceptance(models.Model):
    """
    Track user acceptance of legal documents during registration.

    Records which versions of legal documents the user accepted and when.
    Stores IP address and user agent for audit trail (GDPR Article 30).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='legal_acceptances'
    )

    # Document versions accepted
    terms_version = models.CharField(max_length=20, default='2.0')
    privacy_version = models.CharField(max_length=20, default='2.0')
    cookie_version = models.CharField(max_length=20, default='2.0')

    # Audit trail
    accepted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Optional: Record consent type (explicit, implied, etc.)
    consent_method = models.CharField(
        max_length=20,
        choices=[
            ('registration', 'During Registration'),
            ('update', 'Policy Update Acceptance'),
            ('manual', 'Manual Acceptance'),
        ],
        default='registration'
    )

    class Meta:
        db_table = 'legal_acceptances'
        ordering = ['-accepted_at']
        indexes = [
            models.Index(fields=['user', '-accepted_at']),
            models.Index(fields=['accepted_at']),
        ]
        verbose_name = 'Legal Acceptance'
        verbose_name_plural = 'Legal Acceptances'

    def __str__(self):
        return f"{self.user.email} - {self.accepted_at.strftime('%Y-%m-%d %H:%M')}"


class CookieConsent(models.Model):
    """
    Track user cookie preferences.

    Supports both authenticated and anonymous users (via session_id).
    Implements 2025 symmetric consent standards (equal prominence for accept/reject).
    """
    CONSENT_CHOICES = [
        ('all', 'Accept All Cookies'),
        ('essential', 'Essential Cookies Only'),
        ('custom', 'Custom Selection'),
        ('rejected', 'Rejected All Non-Essential'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Support both authenticated and anonymous users
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cookie_consent'
    )
    session_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text='For anonymous users before registration'
    )

    # Consent type
    consent_type = models.CharField(
        max_length=20,
        choices=CONSENT_CHOICES,
        default='essential'
    )

    # Granular cookie controls
    essential_cookies = models.BooleanField(
        default=True,
        help_text='Required for site functionality - cannot be disabled'
    )
    functional_cookies = models.BooleanField(
        default=False,
        help_text='Remember preferences and settings'
    )
    analytics_cookies = models.BooleanField(
        default=False,
        help_text='Help us understand site usage'
    )
    performance_cookies = models.BooleanField(
        default=False,
        help_text='Optimize site performance'
    )

    # GPC (Global Privacy Control) signal honored
    gpc_signal_detected = models.BooleanField(
        default=False,
        help_text='Whether user has GPC enabled (auto-reject tracking)'
    )

    # Audit trail
    consented_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'cookie_consents'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_id']),
            models.Index(fields=['-updated_at']),
        ]
        verbose_name = 'Cookie Consent'
        verbose_name_plural = 'Cookie Consents'

    def __str__(self):
        if self.user:
            return f"{self.user.email} - {self.consent_type}"
        return f"Session {self.session_id[:8]} - {self.consent_type}"

    def get_active_cookies(self):
        """Return list of cookie categories user has consented to"""
        active = ['essential']  # Always active

        if self.functional_cookies:
            active.append('functional')
        if self.analytics_cookies:
            active.append('analytics')
        if self.performance_cookies:
            active.append('performance')

        return active


class LegalDocument(models.Model):
    """
    Store legal document versions with multi-language support.

    Allows for version control and display of legal documents.
    Content stored in Markdown format for easy rendering.
    Supports English, Russian, and Hebrew translations.
    """
    DOCUMENT_TYPES = [
        ('terms', 'Terms of Service'),
        ('privacy', 'Privacy Policy'),
        ('cookies', 'Cookie Policy'),
        ('copyright', 'Copyright Notice'),
        ('rcip', 'RCIP License'),
    ]

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ru', 'Russian'),
        ('he', 'Hebrew'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES
    )
    language_code = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text='Language of the document (en, ru, he)'
    )
    content = models.TextField(help_text='Markdown content of the document')
    version = models.CharField(
        max_length=20, help_text='Document version (e.g., 2.0)')
    effective_date = models.DateField(
        help_text='Date when this version became effective')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True, help_text='Current active version')

    # Optional: Track who made changes
    updated_by = models.CharField(
        max_length=100,
        blank=True,
        help_text='Admin username who updated the document'
    )

    class Meta:
        db_table = 'legal_documents'
        ordering = ['document_type', 'language_code', '-effective_date']
        indexes = [
            models.Index(
                fields=['document_type', 'language_code', 'is_active']),
            models.Index(fields=['-effective_date']),
        ]
        unique_together = [['document_type', 'language_code']]
        verbose_name = 'Legal Document'
        verbose_name_plural = 'Legal Documents'

    def __str__(self):
        lang_display = dict(self.LANGUAGE_CHOICES).get(
            self.language_code, self.language_code)
        return f"{self.get_document_type_display()} ({lang_display}) v{self.version}"

    def save(self, *args, **kwargs):
        """Ensure only one active version per document type and language"""
        if self.is_active:
            # Deactivate other versions of same document type and language
            LegalDocument.objects.filter(
                document_type=self.document_type,
                language_code=self.language_code,
                is_active=True
            ).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)


class DataExportRequest(models.Model):
    """
    Track GDPR/CCPA data export requests.

    Users have right to data portability (GDPR Article 20, CCPA).
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='export_requests')

    # Request details
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')

    # Export details
    export_format = models.CharField(
        max_length=10,
        choices=[('json', 'JSON'), ('csv', 'CSV')],
        default='json'
    )
    file_path = models.CharField(max_length=500, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)

    # Completion
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Download tracking
    downloaded = models.BooleanField(default=False)
    downloaded_at = models.DateTimeField(null=True, blank=True)
    download_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'data_export_requests'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['user', '-requested_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.status} - {self.requested_at.strftime('%Y-%m-%d')}"


class AccountDeletionRequest(models.Model):
    """
    Track account deletion requests (GDPR Article 17 - Right to Erasure).

    Soft delete with grace period allows users to change their mind.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending (Grace Period)'),
        ('processing', 'Processing Deletion'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled by User'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='deletion_requests')

    # Request details
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')

    # Grace period (30 days recommended)
    grace_period_ends = models.DateTimeField(
        help_text='Date when account will be permanently deleted'
    )

    # Reason (optional - for analytics)
    reason = models.TextField(
        blank=True,
        help_text='Optional: Why user is leaving'
    )

    # Completion
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'account_deletion_requests'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['grace_period_ends']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.status} - {self.requested_at.strftime('%Y-%m-%d')}"
