from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    email_verified = serializers.SerializerMethodField()
    preferred_language = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email',
                  'first_name', 'last_name', 'email_verified', 'preferred_language']

    def get_email_verified(self, obj):
        """Check if user's email is verified via allauth"""
        try:
            from allauth.account.models import EmailAddress
            return EmailAddress.objects.filter(
                user=obj,
                email=obj.email,
                verified=True
            ).exists()
        except ImportError:
            return True  # If allauth not installed, assume verified
    
    def get_preferred_language(self, obj):
        """Get user's preferred language from UserPreferences"""
        try:
            from .models import UserPreferences
            prefs = UserPreferences.objects.filter(user=obj).first()
            return prefs.language if prefs else 'en'  # Changed from preferred_language to language
        except Exception:
            return 'en'


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    preferred_language = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'preferred_language']

    def create(self, validated_data):
        preferred_language = validated_data.pop('preferred_language', 'en')
        user = User.objects.create_user(**validated_data)
        
        # Set preferred_language on user if it exists as a field
        if hasattr(user, 'preferred_language'):
            user.preferred_language = preferred_language
            user.save()
        
        # Also create/update UserPreferences (field is 'language', not 'preferred_language')
        from .models import UserPreferences
        prefs, _ = UserPreferences.objects.get_or_create(user=user)
        prefs.language = preferred_language  # Changed from preferred_language to language
        prefs.save()
        
        print(f"[REGISTRATION] Created UserPreferences with language={preferred_language}", flush=True)
        
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    email_verified = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = '__all__'

    def get_email_verified(self, obj):
        """Check if user's email is verified via allauth"""
        try:
            from allauth.account.models import EmailAddress
            return EmailAddress.objects.filter(
                user=obj,
                email=obj.email,
                verified=True
            ).exists()
        except ImportError:
            return True  # If allauth not installed, assume verified


class UserSettingsSerializer(serializers.ModelSerializer):
    """Serializer for user settings and preferences"""

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'birth_date', 'height_cm', 'weight_kg', 'activity_level',
            'daily_calories_goal', 'daily_protein_goal', 'daily_carbs_goal', 'daily_fat_goal',
            'dietary_restrictions', 'allergies',
            'preferred_language', 'weight_unit', 'volume_unit', 'time_format',
            'personal_color', 'shopping_role'
        ]
        read_only_fields = ['id', 'username']

    def validate_personal_color(self, value):
        """Validate that personal_color is a valid hex color"""
        if not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError(
                "Personal color must be a valid hex color (e.g., #4F46E5)")
        return value

    def validate_weight_kg(self, value):
        """Validate weight is reasonable"""
        if value is not None and (value < 20 or value > 500):
            raise serializers.ValidationError(
                "Weight must be between 20 and 500 kg")
        return value

    def validate_height_cm(self, value):
        """Validate height is reasonable"""
        if value is not None and (value < 50 or value > 300):
            raise serializers.ValidationError(
                "Height must be between 50 and 300 cm")
        return value


class PartnerConnectionSerializer(serializers.Serializer):
    couple_code = serializers.CharField(max_length=10)
