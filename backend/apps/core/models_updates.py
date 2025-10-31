"""
Models for app updates and announcements
"""
from django.db import models
from django.utils import timezone
import uuid


class AppUpdate(models.Model):
    """
    App updates and announcements that appear on the What's New page
    Supports multiple languages
    """
    
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('upcoming', 'Upcoming'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('he', 'Hebrew'),
        ('ru', 'Russian'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Content
    title = models.CharField(
        max_length=200,
        help_text='Update title (e.g., "New Recipe Builder Feature")'
    )
    description = models.TextField(
        help_text='Detailed description of the update or upcoming feature'
    )
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='en',
        db_index=True,
        help_text='Language of this update'
    )
    
    # Metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        help_text='Whether this update is completed or upcoming'
    )
    version = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Version number (e.g., "2.1.0") - optional'
    )
    publish_date = models.DateTimeField(
        default=timezone.now,
        help_text='When this update was/will be published'
    )
    
    # Admin controls
    is_published = models.BooleanField(
        default=True,
        help_text='Whether this update is visible to users'
    )
    is_featured = models.BooleanField(
        default=False,
        help_text='Featured updates appear at the top with special styling'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'app_updates'
        ordering = ['-publish_date', '-created_at']
        indexes = [
            models.Index(fields=['language', 'is_published']),
            models.Index(fields=['publish_date']),
            models.Index(fields=['status']),
        ]
        verbose_name = 'App Update'
        verbose_name_plural = 'App Updates'
    
    def __str__(self):
        status_icon = '✅' if self.status == 'completed' else '🔜'
        return f"{status_icon} [{self.language.upper()}] {self.title}"
    
    @property
    def is_upcoming(self):
        return self.status == 'upcoming'
    
    @property
    def is_completed(self):
        return self.status == 'completed'



