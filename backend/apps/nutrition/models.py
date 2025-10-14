from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid


class UserNutritionSettings(models.Model):
    """Privacy-first nutrition settings with granular AI permissions"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='nutrition_settings',
        primary_key=True
    )

    # === AI COACH MASTER SWITCH ===
    ai_coach_enabled = models.BooleanField(
        default=False,
        help_text="Master toggle for AI nutrition coach"
    )

    # === DATA ACCESS PERMISSIONS ===
    # Content Access
    allow_recipes_access = models.BooleanField(
        default=False,
        help_text="Allow AI to view and suggest from user's recipes"
    )
    allow_inventory_access = models.BooleanField(
        default=False,
        help_text="Allow AI to view user's inventory items"
    )
    allow_shopping_access = models.BooleanField(
        default=False,
        help_text="Allow AI to view shopping patterns"
    )

    # Personal Data Access
    allow_personal_data_access = models.BooleanField(
        default=False,
        help_text="Master toggle for personal profile data"
    )

    # Granular personal data permissions (only if allow_personal_data_access=True)
    allow_weight_data = models.BooleanField(
        default=False,
        help_text="Allow AI to see weight data"
    )
    allow_height_data = models.BooleanField(
        default=False,
        help_text="Allow AI to see height data"
    )
    allow_age_data = models.BooleanField(
        default=False,
        help_text="Allow AI to see age/birth date"
    )
    allow_gender_data = models.BooleanField(
        default=False,
        help_text="Allow AI to see gender data"
    )
    allow_activity_level = models.BooleanField(
        default=False,
        help_text="Allow AI to see activity level"
    )
    allow_health_conditions = models.BooleanField(
        default=False,
        help_text="Allow AI to see dietary restrictions and allergies"
    )

    # === GOAL SETTING MODE ===
    GOAL_MODE_CHOICES = [
        ('manual', 'Manual - I set my own goals'),
        ('ai_calculated', 'AI Calculated - Based on my profile')
    ]
    goal_mode = models.CharField(
        max_length=20,
        choices=GOAL_MODE_CHOICES,
        default='manual',
        help_text="How nutrition goals are determined"
    )

    # Manual Goals (when goal_mode='manual')
    manual_calories_goal = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(500)],
        help_text="Daily calorie goal (manual mode)"
    )
    manual_protein_goal = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Daily protein goal in grams (manual mode)"
    )
    manual_carbs_goal = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Daily carbs goal in grams (manual mode)"
    )
    manual_fat_goal = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Daily fat goal in grams (manual mode)"
    )

    # === COACHING PREFERENCES ===
    COACHING_FREQUENCY_CHOICES = [
        ('daily', 'Daily check-ins'),
        ('weekly', 'Weekly summaries'),
        ('never', 'No coaching messages')
    ]
    coaching_frequency = models.CharField(
        max_length=20,
        choices=COACHING_FREQUENCY_CHOICES,
        default='daily',
        help_text="How often AI coach provides feedback"
    )

    COACHING_STYLE_CHOICES = [
        ('supportive', 'Supportive & Encouraging'),
        ('strict', 'Strict & Disciplined'),
        ('balanced', 'Balanced Approach')
    ]
    coaching_style = models.CharField(
        max_length=20,
        choices=COACHING_STYLE_CHOICES,
        default='supportive',
        help_text="AI coaching personality"
    )

    # Focus Areas
    track_calories = models.BooleanField(default=True)
    track_protein = models.BooleanField(default=True)
    track_carbs = models.BooleanField(default=False)
    track_fat = models.BooleanField(default=False)
    track_meal_timing = models.BooleanField(default=False)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_nutrition_settings'
        verbose_name = 'User Nutrition Settings'
        verbose_name_plural = 'User Nutrition Settings'

    def __str__(self):
        return f"Nutrition Settings for {self.user.username}"

    def get_active_permissions(self):
        """Get list of active AI permissions"""
        permissions = []
        if self.allow_recipes_access:
            permissions.append('recipes')
        if self.allow_inventory_access:
            permissions.append('inventory')
        if self.allow_shopping_access:
            permissions.append('shopping')
        if self.allow_personal_data_access:
            permissions.append('personal_data')
        return permissions


class NutritionEntry(models.Model):
    """Individual nutrition log entry"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='nutrition_entries'
    )

    # === TIMING ===
    date = models.DateField(
        help_text="Date when food was consumed"
    )
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack')
    ]
    meal_type = models.CharField(
        max_length=20,
        choices=MEAL_TYPE_CHOICES,
        help_text="Which meal this entry belongs to"
    )
    time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time when food was consumed"
    )

    # === SOURCE ===
    ENTRY_TYPE_CHOICES = [
        ('manual', 'Manual Entry'),
        ('recipe', 'From Recipe'),
        ('product', 'From Inventory Product'),
        ('ai_suggested', 'AI Suggested')
    ]
    entry_type = models.CharField(
        max_length=20,
        choices=ENTRY_TYPE_CHOICES,
        default='manual',
        help_text="How this entry was created"
    )

    # Optional links to recipes/inventory
    recipe = models.ForeignKey(
        'recipes.Recipe',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='nutrition_logs'
    )
    inventory_item = models.ForeignKey(
        'shopping.Inventory',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='nutrition_logs'
    )

    # === FOOD DETAILS ===
    food_name = models.CharField(
        max_length=200,
        help_text="Name of the food/dish"
    )
    portion_size = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Amount consumed"
    )
    portion_unit = models.CharField(
        max_length=50,
        default='grams',
        help_text="Unit of measurement (grams, ml, pieces, serving, etc.)"
    )

    # === NUTRITION DATA (REQUIRED) ===
    calories = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Total calories"
    )
    protein = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Protein in grams"
    )
    carbs = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Carbohydrates in grams"
    )
    fat = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Fat in grams"
    )

    # Optional detailed nutrients
    fiber = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Fiber in grams"
    )
    sugar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Sugar in grams"
    )
    sodium = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Sodium in milligrams"
    )

    # === METADATA ===
    notes = models.TextField(
        blank=True,
        help_text="Optional notes about the meal"
    )
    photo = models.ImageField(
        upload_to='nutrition_photos/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text="Optional photo of the meal"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'nutrition_entries'
        verbose_name = 'Nutrition Entry'
        verbose_name_plural = 'Nutrition Entries'
        ordering = ['-date', '-time', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'meal_type']),
            models.Index(fields=['date', 'meal_type']),
            models.Index(fields=['user', '-date']),
        ]

    def __str__(self):
        return f"{self.food_name} - {self.meal_type} on {self.date}"

    def get_macros_summary(self):
        """Get formatted macro summary"""
        return {
            'calories': float(self.calories),
            'protein': float(self.protein),
            'carbs': float(self.carbs),
            'fat': float(self.fat)
        }
