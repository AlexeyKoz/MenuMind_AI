"""
Serializers for Site Branding API.
"""
from rest_framework import serializers
from .models import SiteLogo, SiteSettings


class SiteLogoSerializer(serializers.ModelSerializer):
    """Serializer for SiteLogo model"""
    
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SiteLogo
        fields = [
            'id',
            'logo_type',
            'language_code',
            'file_url',
            'alt_text',
            'is_active',
            'width',
            'height',
            'dimensions'
        ]
        read_only_fields = ['id', 'width', 'height', 'dimensions']
    
    def get_file_url(self, obj):
        """Get full URL for logo file"""
        request = self.context.get('request')
        if obj.image_file and request:
            return request.build_absolute_uri(obj.file_url)
        return obj.file_url


class SiteSettingsSerializer(serializers.ModelSerializer):
    """Serializer for SiteSettings model"""
    
    class Meta:
        model = SiteSettings
        fields = [
            'site_name_en',
            'site_name_ru',
            'site_name_he',
            'primary_color',
            'secondary_color'
        ]

