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
            # Changed from preferred_language to language
            return prefs.language if prefs else 'en'
        except Exception:
            return 'en'


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    preferred_language = serializers.CharField(
        required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name',
                  'last_name', 'preferred_language']

    def validate_email(self, value):
        """Validate that email is unique and properly formatted"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError(
                "This email address is already registered. Please use a different email or try logging in."
            )

        # Additional email format validation
        if not value or '@' not in value:
            raise serializers.ValidationError(
                "Please enter a valid email address."
            )

        return value.lower()

    def validate_password(self, value):
        """
        Validate password requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one number
        - No emojis or special unicode characters
        """
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )

        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )

        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )

        # Check for emojis and non-ASCII characters
        try:
            value.encode('ascii')
        except UnicodeEncodeError:
            raise serializers.ValidationError(
                "Password must only contain standard characters (no emojis or special symbols)."
            )

        return value

    def create(self, validated_data):
        preferred_language = validated_data.pop('preferred_language', 'en')
        email = validated_data.pop('email')

        # Create username from email (everything before @)
        username = email.split('@')[0]

        # Make username unique if it already exists
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Create user with email as username
        user = User.objects.create_user(
            username=username,
            email=email,
            **validated_data
        )

        # Create/update UserPreferences
        from .models import UserPreferences
        prefs, _ = UserPreferences.objects.get_or_create(user=user)
        prefs.language = preferred_language
        prefs.save()

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
