from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class AIRateLimitLog(models.Model):
    """
    Track AI recipe generation requests for rate limiting.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='ai_rate_logs')
    endpoint = models.CharField(max_length=100, default='recipe_generation')
    timestamp = models.DateTimeField(auto_now_add=True)
    recipes_generated = models.IntegerField(default=1)

    class Meta:
        db_table = 'ai_rate_limit_log'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['endpoint', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.endpoint} - {self.timestamp}"


class AIRateLimitSettings(models.Model):
    """
    Global settings for AI rate limiting.
    """
    # Per-minute limits
    max_recipes_per_minute = models.IntegerField(default=5)

    # Daily limits
    max_recipes_per_day = models.IntegerField(default=25)

    # Exempted users (comma-separated usernames)
    exempted_users = models.TextField(
        default='testuser1,testuser2',
        help_text='Comma-separated list of usernames exempt from rate limits'
    )

    # When limits are updated
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_rate_limit_settings'
        verbose_name = 'AI Rate Limit Settings'
        verbose_name_plural = 'AI Rate Limit Settings'

    def get_exempted_users(self):
        """Return list of exempted usernames"""
        if not self.exempted_users:
            return []
        return [u.strip() for u in self.exempted_users.split(',') if u.strip()]

    def __str__(self):
        return f"Rate Limits: {self.max_recipes_per_minute}/min, {self.max_recipes_per_day}/day"
