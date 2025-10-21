"""
Dashboard Analytics Models

Caches dashboard data and tracks achievements/streaks.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class DashboardCache(models.Model):
    """
    Caches dashboard analytics data to avoid expensive recalculations.
    Invalidated when source data changes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard_caches')
    period = models.CharField(max_length=20, choices=[
        ('7days', 'Last 7 days'),
        ('30days', 'Last 30 days'),
        ('90days', 'Last 90 days'),
        ('1year', 'Last year'),
    ])

    # Cached data (JSON)
    shopping_data = models.JSONField(default=dict, blank=True)
    recipes_data = models.JSONField(default=dict, blank=True)
    inventory_data = models.JSONField(default=dict, blank=True)
    nutrition_data = models.JSONField(
        default=dict, blank=True, null=True)  # null if AI disabled
    achievements_data = models.JSONField(default=dict, blank=True)

    # AI insights (only if AI enabled)
    ai_insights = models.JSONField(default=dict, blank=True, null=True)
    ai_generated_at = models.DateTimeField(null=True, blank=True)

    # Cache metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()  # Cache expiration

    class Meta:
        db_table = 'dashboard_cache'
        unique_together = [['user', 'period']]
        indexes = [
            models.Index(fields=['user', 'period']),
            models.Index(fields=['expires_at']),
        ]

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.username} - {self.period} - {'expired' if self.is_expired() else 'valid'}"


class Achievement(models.Model):
    """
    Tracks user achievements/badges.
    """
    BADGE_CHOICES = [
        # Cooking achievements
        ('first_cook', 'First Cook'),
        ('chef_level_1', 'Chef Level 1'),
        ('chef_level_2', 'Chef Level 2'),
        ('chef_level_3', 'Chef Level 3'),
        ('master_chef', 'Master Chef'),

        # Nutrition achievements
        ('streak_3', '3-Day Streak'),
        ('streak_7', '7-Day Streak'),
        ('streak_14', '14-Day Streak'),
        ('streak_30', '30-Day Streak'),
        ('streak_100', '100-Day Streak'),
        ('protein_pro', 'Protein Pro'),
        ('balanced_eater', 'Balanced Eater'),
        ('consistent_logger', 'Consistent Logger'),

        # Shopping achievements
        ('budget_saver', 'Budget Saver'),
        ('smart_shopper', 'Smart Shopper'),
        ('deal_hunter', 'Deal Hunter'),

        # Inventory achievements
        ('waste_warrior', 'Waste Warrior'),
        ('zero_waste_week', 'Zero Waste Week'),
        ('organization_master', 'Organization Master'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achievements')
    badge_id = models.CharField(max_length=50, choices=BADGE_CHOICES)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10)  # Emoji
    description = models.TextField()

    earned_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)  # Whether user was notified

    class Meta:
        db_table = 'achievements'
        unique_together = [['user', 'badge_id']]
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user', '-earned_at']),
            models.Index(fields=['badge_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class UserStreak(models.Model):
    """
    Tracks user streaks (consecutive days of activity).
    """
    STREAK_TYPES = [
        ('nutrition_logging', 'Nutrition Logging'),
        ('recipe_cooking', 'Recipe Cooking'),
        ('budget_tracking', 'Budget Tracking'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='streaks')
    streak_type = models.CharField(max_length=50, choices=STREAK_TYPES)

    current_count = models.IntegerField(default=0)
    longest_count = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_streaks'
        unique_together = [['user', 'streak_type']]
        indexes = [
            models.Index(fields=['user', 'streak_type']),
        ]

    def increment(self, activity_date=None):
        """
        Increment streak if activity is on consecutive day.
        """
        if activity_date is None:
            activity_date = timezone.now().date()

        if self.last_activity_date is None:
            # First activity
            self.current_count = 1
            self.longest_count = 1
            self.last_activity_date = activity_date
        elif activity_date == self.last_activity_date:
            # Same day, don't change
            pass
        elif activity_date == self.last_activity_date + timezone.timedelta(days=1):
            # Consecutive day
            self.current_count += 1
            self.longest_count = max(self.longest_count, self.current_count)
            self.last_activity_date = activity_date
        elif activity_date > self.last_activity_date + timezone.timedelta(days=1):
            # Streak broken
            self.current_count = 1
            self.last_activity_date = activity_date

        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.get_streak_type_display()}: {self.current_count} days"


class RecipeCookingLog(models.Model):
    """
    Logs when a user cooks a recipe (for achievements and analytics).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cooking_logs')
    recipe = models.ForeignKey(
        'recipes.Recipe', on_delete=models.CASCADE, related_name='cooking_logs')
    canonical_recipe = models.ForeignKey(
        'recipes.CanonicalRecipe', on_delete=models.CASCADE, related_name='cooking_logs', null=True, blank=True)

    cooked_at = models.DateTimeField(auto_now_add=True)
    servings = models.IntegerField(default=1)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'recipe_cooking_logs'
        ordering = ['-cooked_at']
        indexes = [
            models.Index(fields=['user', '-cooked_at']),
            models.Index(fields=['recipe']),
        ]

    def __str__(self):
        return f"{self.user.username} cooked {self.recipe.name} on {self.cooked_at.date()}"










