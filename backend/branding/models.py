"""
Models for managing site branding (logos, icons, etc.) with multi-language support.
"""
from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
import uuid
import os


def logo_upload_path(instance, filename):
    """Generate upload path for logo files"""
    ext = os.path.splitext(filename)[1]
    filename = f"{instance.logo_type}_{instance.language_code}_{uuid.uuid4().hex[:8]}{ext}"
    return os.path.join('branding', 'logos', filename)


class SiteLogo(models.Model):
    """
    Store site logos with multi-language support.
    
    Allows uploading different logos for different languages and different positions
    (navbar, login, mobile, favicon, etc.)
    """
    
    LOGO_TYPES = [
        ('navbar_desktop', 'Navbar Logo (Desktop)'),
        ('navbar_mobile', 'Navbar Logo (Mobile)'),
        ('login_page', 'Login Page Logo'),
        ('favicon', 'Favicon (Browser Tab)'),
        ('app_icon', 'App Icon (PWA)'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ru', 'Russian'),
        ('he', 'Hebrew'),
        ('all', 'All Languages (Default)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    logo_type = models.CharField(
        max_length=20,
        choices=LOGO_TYPES,
        help_text='Where this logo will be displayed'
    )
    language_code = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='all',
        help_text='Language for this logo (use "All Languages" for universal logos)'
    )
    
    # File upload
    image_file = models.ImageField(
        upload_to=logo_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['svg', 'png', 'jpg', 'jpeg', 'webp', 'ico'])],
        help_text='Upload logo file (SVG recommended for best quality)'
    )
    
    # Alternative text for accessibility
    alt_text = models.CharField(
        max_length=100,
        default='BishulSheli',
        help_text='Alternative text for accessibility'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Set to active to use this logo'
    )
    
    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.CharField(
        max_length=100,
        blank=True,
        help_text='Admin username who uploaded the logo'
    )
    
    # Optional: Custom dimensions (for validation/display)
    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Logo width in pixels (auto-detected)'
    )
    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Logo height in pixels (auto-detected)'
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='File size in bytes (auto-detected)'
    )
    
    class Meta:
        db_table = 'site_logos'
        ordering = ['logo_type', 'language_code', '-updated_at']
        indexes = [
            models.Index(fields=['logo_type', 'language_code', 'is_active']),
        ]
        unique_together = [['logo_type', 'language_code']]
        verbose_name = 'Site Logo'
        verbose_name_plural = 'Site Logos'
    
    def __str__(self):
        lang_display = dict(self.LANGUAGE_CHOICES).get(self.language_code, self.language_code)
        logo_display = dict(self.LOGO_TYPES).get(self.logo_type, self.logo_type)
        status = "✓" if self.is_active else "✗"
        return f"{status} {logo_display} ({lang_display})"
    
    def save(self, *args, **kwargs):
        """Auto-detect image dimensions and file size"""
        if self.image_file:
            # Get file size
            self.file_size = self.image_file.size
            
            # Try to get image dimensions
            try:
                from PIL import Image
                img = Image.open(self.image_file)
                self.width, self.height = img.size
            except Exception:
                pass
        
        # Ensure only one active logo per type and language
        if self.is_active:
            SiteLogo.objects.filter(
                logo_type=self.logo_type,
                language_code=self.language_code,
                is_active=True
            ).exclude(id=self.id).update(is_active=False)
        
        super().save(*args, **kwargs)
    
    @property
    def file_url(self):
        """Get the URL of the logo file"""
        if self.image_file:
            return self.image_file.url
        return None
    
    @property
    def dimensions(self):
        """Get dimensions as string"""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return "Unknown"
    
    @property
    def file_size_display(self):
        """Get human-readable file size"""
        if self.file_size:
            size = self.file_size
            for unit in ['B', 'KB', 'MB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
        return "Unknown"


class SiteSettings(models.Model):
    """
    General site settings (for future expansion).
    Singleton model - only one instance should exist.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Site name per language
    site_name_en = models.CharField(max_length=100, default='BishulSheli')
    site_name_ru = models.CharField(max_length=100, default='BishulSheli')
    site_name_he = models.CharField(max_length=100, default='בישול שלי')
    
    # Theme colors
    primary_color = models.CharField(
        max_length=7,
        default='#9B59B6',
        help_text='Primary brand color (hex code)'
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#8E44AD',
        help_text='Secondary brand color (hex code)'
    )
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'site_settings'
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return f"Site Settings (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton)"""
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

