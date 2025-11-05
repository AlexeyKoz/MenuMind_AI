"""
REST API Views for Legal Compliance
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import os

from .models import (
    LegalDocument,
    LegalAcceptance,
    CookieConsent,
    DataExportRequest,
    AccountDeletionRequest
)
from .serializers import (
    LegalDocumentSerializer,
    LegalAcceptanceSerializer,
    CookieConsentSerializer,
    CookieConsentCreateSerializer,
    DataExportRequestSerializer,
    AccountDeletionRequestSerializer
)


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def detect_gpc_signal(request):
    """Detect Global Privacy Control signal"""
    # GPC is sent via Sec-GPC header (value: 1)
    gpc_header = request.META.get('HTTP_SEC_GPC')
    return gpc_header == '1'


class LegalViewSet(viewsets.ViewSet):
    """
    API endpoints for legal documents and user consent.

    Public endpoints for viewing legal documents.
    Authenticated endpoints for recording acceptance.
    """

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def terms(self, request):
        """
        Get Terms of Service.

        GET /api/legal/terms/?lang=en|ru|he
        """
        language = request.GET.get('lang', 'en')
        if language not in ['en', 'ru', 'he']:
            language = 'en'

        try:
            doc = LegalDocument.objects.get(
                document_type='terms',
                language_code=language,
                is_active=True
            )
            return Response({
                'content': doc.content,
                'version': doc.version,
                'effective_date': doc.effective_date,
                'document_type': 'terms',
                'language': doc.language_code
            })
        except LegalDocument.DoesNotExist:
            # Fallback to English if translation not found
            try:
                doc = LegalDocument.objects.get(
                    document_type='terms',
                    language_code='en',
                    is_active=True
                )
                return Response({
                    'content': doc.content,
                    'version': doc.version,
                    'effective_date': doc.effective_date,
                    'document_type': 'terms',
                    'language': 'en',
                    'fallback': True  # Indicate fallback to English
                })
            except LegalDocument.DoesNotExist:
                return Response(
                    {'error': 'Terms of Service not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def privacy(self, request):
        """
        Get Privacy Policy.

        GET /api/legal/privacy/?lang=en|ru|he
        """
        language = request.GET.get('lang', 'en')
        if language not in ['en', 'ru', 'he']:
            language = 'en'

        try:
            doc = LegalDocument.objects.get(
                document_type='privacy',
                language_code=language,
                is_active=True
            )
            return Response({
                'content': doc.content,
                'version': doc.version,
                'effective_date': doc.effective_date,
                'document_type': 'privacy',
                'language': doc.language_code
            })
        except LegalDocument.DoesNotExist:
            # Fallback to English
            try:
                doc = LegalDocument.objects.get(
                    document_type='privacy',
                    language_code='en',
                    is_active=True
                )
                return Response({
                    'content': doc.content,
                    'version': doc.version,
                    'effective_date': doc.effective_date,
                    'document_type': 'privacy',
                    'language': 'en',
                    'fallback': True
                })
            except LegalDocument.DoesNotExist:
                return Response(
                    {'error': 'Privacy Policy not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def cookies(self, request):
        """
        Get Cookie Policy.

        GET /api/legal/cookies/?lang=en|ru|he
        """
        language = request.GET.get('lang', 'en')
        if language not in ['en', 'ru', 'he']:
            language = 'en'

        try:
            doc = LegalDocument.objects.get(
                document_type='cookies',
                language_code=language,
                is_active=True
            )
            return Response({
                'content': doc.content,
                'version': doc.version,
                'effective_date': doc.effective_date,
                'document_type': 'cookies',
                'language': doc.language_code
            })
        except LegalDocument.DoesNotExist:
            # Fallback to English
            try:
                doc = LegalDocument.objects.get(
                    document_type='cookies',
                    language_code='en',
                    is_active=True
                )
                return Response({
                    'content': doc.content,
                    'version': doc.version,
                    'effective_date': doc.effective_date,
                    'document_type': 'cookies',
                    'language': 'en',
                    'fallback': True
                })
            except LegalDocument.DoesNotExist:
                return Response(
                    {'error': 'Cookie Policy not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def copyright(self, request):
        """
        Get Copyright Notice.

        GET /api/legal/copyright/
        """
        try:
            doc = LegalDocument.objects.get(
                document_type='copyright',
                language_code='en',
                is_active=True)
            return Response({
                'content': doc.content,
                'version': doc.version,
                'effective_date': doc.effective_date,
                'document_type': 'copyright'
            })
        except LegalDocument.DoesNotExist:
            return Response(
                {'error': 'Copyright Notice not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def rcip(self, request):
        """
        Get RCIP License.

        GET /api/legal/rcip/
        """
        try:
            doc = LegalDocument.objects.get(
                document_type='rcip',
                language_code='en',
                is_active=True)
            return Response({
                'content': doc.content,
                'version': doc.version,
                'effective_date': doc.effective_date,
                'document_type': 'rcip'
            })
        except LegalDocument.DoesNotExist:
            return Response(
                {'error': 'RCIP License not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def accept(self, request):
        """
        Record user acceptance of legal documents.

        POST /api/legal/accept/

        Called during registration or when user accepts updated policies.
        """
        user = request.user

        # Get client information for audit trail
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Get consent method (default: registration)
        consent_method = request.data.get('consent_method', 'registration')

        # Create acceptance record
        acceptance = LegalAcceptance.objects.create(
            user=user,
            terms_version='2.0',
            privacy_version='2.0',
            cookie_version='2.0',
            ip_address=ip_address,
            user_agent=user_agent,
            consent_method=consent_method
        )

        serializer = LegalAcceptanceSerializer(acceptance)

        return Response({
            'success': True,
            'message': 'Legal acceptance recorded',
            'acceptance': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def cookie_consent(self, request):
        """
        Save cookie consent preferences.

        POST /api/legal/cookie_consent/

        Body:
        {
            "consent_type": "all" | "essential" | "custom" | "rejected",
            "functional": true/false (for custom),
            "analytics": true/false (for custom),
            "performance": true/false (for custom)
        }
        """
        serializer = CookieConsentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        consent_data = serializer.validated_data
        consent_type = consent_data['consent_type']

        # Get or create session
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key

        # Get client information
        ip_address = get_client_ip(request)
        gpc_signal = detect_gpc_signal(request)

        # If GPC signal detected, force reject non-essential cookies
        if gpc_signal:
            consent_type = 'rejected'
            consent_data['functional'] = False
            consent_data['analytics'] = False
            consent_data['performance'] = False

        # Determine if user is authenticated
        user = request.user if request.user.is_authenticated else None

        # Update or create consent record
        if user:
            # For authenticated users, store by user
            consent, created = CookieConsent.objects.update_or_create(
                user=user,
                defaults={
                    'session_id': session_id,
                    'consent_type': consent_type,
                    'essential_cookies': True,  # Always true
                    'functional_cookies': consent_data.get('functional', False),
                    'analytics_cookies': consent_data.get('analytics', False),
                    'performance_cookies': consent_data.get('performance', False),
                    'gpc_signal_detected': gpc_signal,
                    'ip_address': ip_address,
                }
            )
        else:
            # For anonymous users, store by session
            consent, created = CookieConsent.objects.update_or_create(
                session_id=session_id,
                defaults={
                    'consent_type': consent_type,
                    'essential_cookies': True,
                    'functional_cookies': consent_data.get('functional', False),
                    'analytics_cookies': consent_data.get('analytics', False),
                    'performance_cookies': consent_data.get('performance', False),
                    'gpc_signal_detected': gpc_signal,
                    'ip_address': ip_address,
                }
            )

        # Return consent settings
        return Response({
            'success': True,
            'consent_type': consent.consent_type,
            'settings': {
                'essential': consent.essential_cookies,
                'functional': consent.functional_cookies,
                'analytics': consent.analytics_cookies,
                'performance': consent.performance_cookies,
            },
            'gpc_honored': gpc_signal,
            'created': created
        })

    @method_decorator(csrf_exempt)
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def get_cookie_consent(self, request):
        """
        Get current cookie consent settings.

        GET /api/legal/get_cookie_consent/
        """
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        session_id = request.session.session_key

        try:
            # Try to find consent by user first (if authenticated)
            if request.user.is_authenticated:
                consent = CookieConsent.objects.get(user=request.user)
            # Then try session ID
            elif session_id:
                consent = CookieConsent.objects.get(session_id=session_id)
            else:
                # No consent found
                return Response({
                    'has_consent': False,
                    'gpc_detected': detect_gpc_signal(request)
                })

            return Response({
                'has_consent': True,
                'consent_type': consent.consent_type,
                'settings': {
                    'essential': consent.essential_cookies,
                    'functional': consent.functional_cookies,
                    'analytics': consent.analytics_cookies,
                    'performance': consent.performance_cookies,
                },
                'consented_at': consent.consented_at,
                'updated_at': consent.updated_at
            })
        except CookieConsent.DoesNotExist:
            return Response({
                'has_consent': False,
                'gpc_detected': detect_gpc_signal(request)
            })


class PrivacyViewSet(viewsets.ViewSet):
    """
    API endpoints for user privacy rights (GDPR/CCPA compliance).

    - Data export (Article 20)
    - Account deletion (Article 17)
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def export_data(self, request):
        """
        Request data export (GDPR Article 20 - Right to Data Portability).

        POST /api/privacy/export_data/

        Creates an export request and generates JSON file with all user data.
        """
        user = request.user
        export_format = request.data.get('format', 'json')

        # Check if there's a pending request
        pending = DataExportRequest.objects.filter(
            user=user,
            status__in=['pending', 'processing']
        ).first()

        if pending:
            return Response({
                'error': 'You already have a pending export request',
                'request_id': pending.id,
                'status': pending.status
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create export request
        export_request = DataExportRequest.objects.create(
            user=user,
            export_format=export_format
        )

        # TODO: Trigger async task to generate export file
        # For now, return request ID

        return Response({
            'success': True,
            'message': 'Data export requested. You will be notified when ready.',
            'request_id': export_request.id,
            'estimated_time': '5-10 minutes'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'])
    def request_deletion(self, request):
        """
        Request account deletion (GDPR Article 17 - Right to Erasure).

        POST /api/privacy/request_deletion/

        Body:
        {
            "reason": "optional reason for leaving"
        }

        Starts 30-day grace period before permanent deletion.
        """
        user = request.user
        reason = request.data.get('reason', '')

        # Check if there's already a pending deletion
        pending = AccountDeletionRequest.objects.filter(
            user=user,
            status='pending'
        ).first()

        if pending:
            return Response({
                'error': 'You already have a pending deletion request',
                'grace_period_ends': pending.grace_period_ends,
                'days_remaining': (pending.grace_period_ends - timezone.now()).days
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create deletion request with 30-day grace period
        grace_period_ends = timezone.now() + timedelta(days=30)

        deletion_request = AccountDeletionRequest.objects.create(
            user=user,
            reason=reason,
            grace_period_ends=grace_period_ends
        )

        return Response({
            'success': True,
            'message': 'Account deletion requested. You have 30 days to cancel.',
            'request_id': deletion_request.id,
            'grace_period_ends': grace_period_ends,
            'days_until_deletion': 30
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def cancel_deletion(self, request):
        """
        Cancel pending account deletion.

        POST /api/privacy/cancel_deletion/
        """
        user = request.user

        # Find pending deletion request
        deletion_request = AccountDeletionRequest.objects.filter(
            user=user,
            status='pending'
        ).first()

        if not deletion_request:
            return Response({
                'error': 'No pending deletion request found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Cancel the request
        deletion_request.status = 'cancelled'
        deletion_request.cancelled_at = timezone.now()
        deletion_request.save()

        return Response({
            'success': True,
            'message': 'Account deletion cancelled successfully'
        })
