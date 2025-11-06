from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Extended user model with nutrition and couple features"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Profile Information
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        null=True,
        blank=True
    )
    height_cm = models.IntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    activity_level = models.CharField(
        max_length=20,
        choices=[
            ('sedentary', 'Sedentary'),
            ('light', 'Lightly Active'),
            ('moderate', 'Moderately Active'),
            ('very', 'Very Active'),
            ('extra', 'Extra Active'),
        ],
        default='moderate'
    )

    # Nutrition Goals
    daily_calories_goal = models.IntegerField(default=2000)
    daily_protein_goal = models.IntegerField(default=50)
    daily_carbs_goal = models.IntegerField(default=250)
    daily_fat_goal = models.IntegerField(default=65)

    # Dietary Restrictions
    dietary_restrictions = models.JSONField(default=list, blank=True)
    allergies = models.JSONField(default=list, blank=True)

    # Partner/Couple Connection
    partner = models.OneToOneField(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='partner_of'
    )
    couple_code = models.CharField(
        max_length=10, unique=True, null=True, blank=True)
    couple_connected_at = models.DateTimeField(null=True, blank=True)

    # Preferences
    preferred_language = models.CharField(
        max_length=10,
        choices=[('en', 'English'), ('he', 'Hebrew'), ('ru', 'Russian')],
        default='en'
    )

    # Unit Preferences
    weight_unit = models.CharField(
        max_length=10,
        choices=[('kg', 'Kilograms'), ('lbs', 'Pounds')],
        default='kg',
        help_text='Preferred weight unit for display'
    )
    volume_unit = models.CharField(
        max_length=10,
        choices=[('liters', 'Liters'), ('gallons', 'Gallons')],
        default='liters',
        help_text='Preferred volume unit for display'
    )
    time_format = models.CharField(
        max_length=5,
        choices=[('24h', '24 Hour'), ('12h', '12 Hour (AM/PM)')],
        default='24h',
        help_text='Preferred time format for display'
    )

    # Collaboration Features
    collaboration_key = models.CharField(
        max_length=6,
        unique=True,
        null=True,
        blank=True,
        help_text='6-digit unique key for sharing shopping lists'
    )
    personal_color = models.CharField(max_length=7, default='#4F46E5')
    shopping_role = models.CharField(
        max_length=20,
        choices=[
            ('creator', 'List Creator'),
            ('collaborator', 'Collaborator'),
            ('both', 'Both Creator and Collaborator')
        ],
        default='both'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(default=timezone.now)

    # AI Usage Tracking
    ai_requests_today = models.IntegerField(default=0)
    ai_requests_reset_at = models.DateTimeField(default=timezone.now)
    
    # NEW: Detailed quota tracking per feature
    recipe_generations_today = models.IntegerField(default=0)
    translations_today = models.IntegerField(default=0)
    nutrition_logs_today = models.IntegerField(default=0)
    url_scrapes_today = models.IntegerField(default=0)
    
    # NEW: Abuse detection
    suspicious_activity_score = models.IntegerField(default=0)
    is_rate_limited = models.BooleanField(default=False)
    rate_limit_until = models.DateTimeField(null=True, blank=True)
    last_ai_request_at = models.DateTimeField(null=True, blank=True)

    # User Guide Tracking (which pages the user has seen the guide for)
    has_seen_guides = models.JSONField(
        default=list, 
        blank=True,
        help_text='List of page guides the user has completed (e.g. ["dashboard", "shopping", "inventory"])'
    )

    def generate_couple_code(self):
        """Generate unique couple code for partner linking"""
        import random
        import string
        while True:
            code = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=6))
            if not User.objects.filter(couple_code=code).exists():
                self.couple_code = code
                return code

    def generate_collaboration_key(self):
        """Generate unique collaboration key for shopping list sharing"""
        import random
        import string
        while True:
            key = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=6))
            if not User.objects.filter(collaboration_key=key).exists():
                self.collaboration_key = key
                self.save()  # Save the model with the new key
                return key

    def connect_partner(self, partner_user):
        """Connect two users as partners"""
        self.partner = partner_user
        partner_user.partner = self
        self.couple_connected_at = timezone.now()
        partner_user.couple_connected_at = timezone.now()
        self.save()
        partner_user.save()

    def calculate_bmr(self):
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation"""
        if not all([self.birth_date, self.height_cm, self.weight_kg]):
            return None

        age = (timezone.now().date() - self.birth_date).days // 365

        # Mifflin-St Jeor Equation
        if self.gender == 'male':
            # Male formula: BMR = 10W + 6.25H - 5A + 5
            bmr = 10 * float(self.weight_kg) + 6.25 * \
                self.height_cm - 5 * age + 5
        else:
            # Female formula (default for female/other): BMR = 10W + 6.25H - 5A - 161
            bmr = 10 * float(self.weight_kg) + 6.25 * \
                self.height_cm - 5 * age - 161

        # Activity factor
        activity_factors = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'very': 1.725,
            'extra': 1.9
        }

        return int(bmr * activity_factors.get(self.activity_level, 1.55))
    
    def reset_daily_quotas(self):
        """Reset daily AI quotas if the reset time has passed"""
        if timezone.now() >= self.ai_requests_reset_at:
            self.ai_requests_today = 0
            self.recipe_generations_today = 0
            self.translations_today = 0
            self.nutrition_logs_today = 0
            self.url_scrapes_today = 0
            self.ai_requests_reset_at = timezone.now() + timezone.timedelta(days=1)
            self.save()
    
    def get_quota_limits(self):
        """Get quota limits based on email verification status"""
        email_verified = self.emailaddress_set.filter(verified=True).exists()
        return {
            'recipe_generation': 20 if email_verified else 2,
            'translation': 50 if email_verified else 5,
            'nutrition_log': 30 if email_verified else 3,
            'url_scrape': 10 if email_verified else 1,
        }
    
    def check_quota(self, request_type):
        """Check if user has quota remaining for request type"""
        self.reset_daily_quotas()
        if self.is_rate_limited and self.rate_limit_until and timezone.now() < self.rate_limit_until:
            return False, f"Rate limited until {self.rate_limit_until}"
        
        limits = self.get_quota_limits()
        field_map = {
            'recipe_generation': 'recipe_generations_today',
            'translation': 'translations_today',
            'nutrition_log': 'nutrition_logs_today',
            'url_scrape': 'url_scrapes_today',
        }
        current = getattr(self, field_map.get(request_type, 'ai_requests_today'), 0)
        limit = limits.get(request_type, 10)
        
        if current >= limit:
            email_verified = self.emailaddress_set.filter(verified=True).exists()
            msg = f"Daily limit reached ({current}/{limit}). " + (
                "Please verify your email to increase limits." if not email_verified 
                else "Please try again tomorrow."
            )
            return False, msg
        return True, "OK"
    
    def increment_quota(self, request_type):
        """Increment quota usage for request type"""
        self.reset_daily_quotas()
        field_map = {
            'recipe_generation': 'recipe_generations_today',
            'translation': 'translations_today',
            'nutrition_log': 'nutrition_logs_today',
            'url_scrape': 'url_scrapes_today',
        }
        field_name = field_map.get(request_type)
        if field_name:
            setattr(self, field_name, getattr(self, field_name, 0) + 1)
        self.ai_requests_today += 1
        self.last_ai_request_at = timezone.now()
        self.save()

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['couple_code']),
            models.Index(fields=['partner']),
            models.Index(fields=['collaboration_key']),
            models.Index(fields=['shopping_role']),
        ]


class UserPreferences(models.Model):
    """User preferences for multilingual and unit system"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preferences'
    )

    # Language
    language = models.CharField(
        max_length=2,
        choices=[('en', 'English'), ('ru', 'Russian'), ('he', 'Hebrew')],
        default='en'
    )

    # Unit System
    unit_system = models.CharField(
        max_length=10,
        choices=[('metric', 'Metric'), ('imperial', 'Imperial')],
        default='metric'
    )

    weight_unit = models.CharField(max_length=5, default='kg')
    # kg or lb

    volume_unit = models.CharField(max_length=10, default='L')
    # L or gallon

    temperature_unit = models.CharField(max_length=1, default='C')
    # C or F

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_preferences'
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'

    def __str__(self):
        return f"{self.user.username} - {self.language}/{self.unit_system}"


class AIRequestLog(models.Model):
    """Log of AI requests for analytics and abuse detection"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_request_logs')
    request_type = models.CharField(max_length=50)
    endpoint = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_request_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.request_type} - {self.created_at}"
