from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


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
