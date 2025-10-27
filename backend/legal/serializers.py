"""
REST API Serializers for Legal Compliance
"""
from rest_framework import serializers
from .models import (
    LegalDocument,
    LegalAcceptance,
    CookieConsent,
    DataExportRequest,
    AccountDeletionRequest
)


class LegalDocumentSerializer(serializers.ModelSerializer):
    """Serializer for legal documents"""
    document_name = serializers.CharField(
        source='get_document_type_display', read_only=True)

    class Meta:
        model = LegalDocument
        fields = [
            'id',
            'document_type',
            'document_name',
            'content',
            'version',
            'effective_date',
            'updated_at'
        ]
        read_only_fields = ['id', 'document_name', 'updated_at']


class LegalAcceptanceSerializer(serializers.ModelSerializer):
    """Serializer for legal acceptance records"""
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = LegalAcceptance
        fields = [
            'id',
            'user',
            'user_email',
            'terms_version',
            'privacy_version',
            'cookie_version',
            'accepted_at',
            'consent_method'
        ]
        read_only_fields = [
            'id',
            'user_email',
            'accepted_at'
        ]


class CookieConsentSerializer(serializers.ModelSerializer):
    """Serializer for cookie consent preferences"""
    active_cookies = serializers.ListField(
        source='get_active_cookies',
        read_only=True
    )

    class Meta:
        model = CookieConsent
        fields = [
            'id',
            'consent_type',
            'essential_cookies',
            'functional_cookies',
            'analytics_cookies',
            'performance_cookies',
            'gpc_signal_detected',
            'active_cookies',
            'consented_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'essential_cookies',  # Always true
            'gpc_signal_detected',
            'active_cookies',
            'consented_at',
            'updated_at'
        ]

    def validate_consent_type(self, value):
        """Validate consent type"""
        if value not in ['all', 'essential', 'custom', 'rejected']:
            raise serializers.ValidationError("Invalid consent type")
        return value


class CookieConsentCreateSerializer(serializers.Serializer):
    """Serializer for creating/updating cookie consent"""
    consent_type = serializers.ChoiceField(
        choices=['all', 'essential', 'custom', 'rejected']
    )
    functional = serializers.BooleanField(required=False, default=False)
    analytics = serializers.BooleanField(required=False, default=False)
    performance = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        """Validate consent choices"""
        consent_type = data.get('consent_type')

        # If 'all', enable all cookies
        if consent_type == 'all':
            data['functional'] = True
            data['analytics'] = True
            data['performance'] = True

        # If 'essential' or 'rejected', disable all non-essential
        elif consent_type in ['essential', 'rejected']:
            data['functional'] = False
            data['analytics'] = False
            data['performance'] = False

        # For 'custom', use provided values

        return data


class DataExportRequestSerializer(serializers.ModelSerializer):
    """Serializer for data export requests"""
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = DataExportRequest
        fields = [
            'id',
            'user_email',
            'requested_at',
            'status',
            'export_format',
            'file_size_bytes',
            'completed_at',
            'downloaded',
            'download_count'
        ]
        read_only_fields = [
            'id',
            'user_email',
            'requested_at',
            'status',
            'file_size_bytes',
            'completed_at',
            'downloaded',
            'download_count'
        ]


class AccountDeletionRequestSerializer(serializers.ModelSerializer):
    """Serializer for account deletion requests"""
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = AccountDeletionRequest
        fields = [
            'id',
            'user_email',
            'requested_at',
            'status',
            'grace_period_ends',
            'reason',
            'completed_at',
            'cancelled_at'
        ]
        read_only_fields = [
            'id',
            'user_email',
            'requested_at',
            'status',
            'grace_period_ends',
            'completed_at',
            'cancelled_at'
        ]
