from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Extended user model with nutrition and couple features"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Profile Information
    birth_date = models.DateField(null=True, blank=True)
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

    def connect_partner(self, partner_user):
        """Connect two users as partners"""
        self.partner = partner_user
        partner_user.partner = self
        self.couple_connected_at = timezone.now()
        partner_user.couple_connected_at = timezone.now()
        self.save()
        partner_user.save()

    def calculate_bmr(self):
        """Calculate Basal Metabolic Rate"""
        if not all([self.birth_date, self.height_cm, self.weight_kg]):
            return None

        age = (timezone.now().date() - self.birth_date).days // 365

        # Mifflin-St Jeor Equation
        if self.username:  # Placeholder for gender
            # Male formula
            bmr = 10 * float(self.weight_kg) + 6.25 * \
                self.height_cm - 5 * age + 5
        else:
            # Female formula
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

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['couple_code']),
            models.Index(fields=['partner']),
            models.Index(fields=['collaboration_key']),
            models.Index(fields=['shopping_role']),
        ]
