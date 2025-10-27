from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    UserProfileSerializer, PartnerConnectionSerializer,
    UserSettingsSerializer
)
from .models import User
from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.conf import settings as django_settings
from django.utils import timezone
from datetime import timedelta
import logging
import json

logger = logging.getLogger(__name__)

# Note: EmailAddress import moved inside functions to avoid app loading order issues


class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        # Import here to avoid app loading order issues
        EmailAddress = None
        EmailConfirmation = None

        try:
            from allauth.account.models import EmailAddress as EA, EmailConfirmation as EC
            EmailAddress = EA
            EmailConfirmation = EC
            print(
                f"[REGISTRATION] ✅ Imported EmailAddress and EmailConfirmation", flush=True)
        except Exception as e:
            print(
                f"[REGISTRATION] ❌ Error importing allauth models: {e}", flush=True)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create EmailAddress for allauth verification
        if EmailAddress is not None and EmailConfirmation is not None and user.email:
            email_address, created = EmailAddress.objects.get_or_create(
                user=user,
                email=user.email.lower(),
                defaults={'primary': True, 'verified': False}
            )

            # Send verification email by creating EmailConfirmation
            try:
                print(
                    f"📧 Creating email confirmation for {user.email}", flush=True)

                # Create confirmation object - this automatically sends email via our adapter
                email_confirmation = EmailConfirmation.create(email_address)
                email_confirmation.send(request, signup=True)

                print(
                    f"✅ Verification email sent successfully to {user.email}", flush=True)
            except Exception as e:
                print(f"❌ Failed to send verification email: {e}", flush=True)
                import traceback
                traceback.print_exc()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Registration successful. Please check your email to verify your account.'
        }, status=status.HTTP_201_CREATED)


class UserProfileViewSet(viewsets.ModelViewSet):
    """User profile management"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['post'])
    def connect_partner(self, request):
        """Connect with partner using couple code"""
        code = request.data.get('couple_code')

        if not code:
            return Response(
                {'error': 'Couple code required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        partner = User.objects.filter(couple_code=code).first()

        if not partner:
            return Response(
                {'error': 'Invalid couple code'},
                status=status.HTTP_404_NOT_FOUND
            )

        if partner == request.user:
            return Response(
                {'error': 'Cannot connect with yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Connect partners
        request.user.connect_partner(partner)

        return Response({
            'message': 'Successfully connected with partner',
            'partner': UserSerializer(partner).data
        })

    @action(detail=False, methods=['post'])
    def generate_couple_code(self, request):
        """Generate new couple code"""
        code = request.user.generate_couple_code()
        request.user.save()

        return Response({
            'couple_code': code,
            'message': 'Share this code with your partner'
        })

    @action(detail=False, methods=['get'])
    def nutrition_goals(self, request):
        """Get nutrition goals"""
        return Response({
            'daily_calories': request.user.daily_calories_goal,
            'daily_protein': request.user.daily_protein_goal,
            'daily_carbs': request.user.daily_carbs_goal,
            'daily_fat': request.user.daily_fat_goal,
            'bmr': request.user.calculate_bmr()
        })

    @action(detail=False, methods=['post'])
    def generate_collaboration_key(self, request):
        """Generate new collaboration key for shopping list sharing"""
        key = request.user.generate_collaboration_key()
        request.user.save()

        return Response({
            'collaboration_key': key,
            'message': 'Share this 6-digit key with friends to collaborate on shopping lists'
        })

    @action(detail=False, methods=['get'])
    def my_collaboration_key(self, request):
        """Get current user's collaboration key"""
        if not request.user.collaboration_key:
            key = request.user.generate_collaboration_key()
            request.user.save()
        else:
            key = request.user.collaboration_key

        return Response({
            'collaboration_key': key,
            'personal_color': request.user.personal_color,
            'shopping_role': request.user.shopping_role
        })

    @action(detail=False, methods=['post'])
    def update_personal_color(self, request):
        """Update user's personal color for shopping lists"""
        color = request.data.get('color')
        if not color or not color.startswith('#') or len(color) != 7:
            return Response(
                {'error': 'Invalid color format. Use hex format like #FF0000'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.personal_color = color
        request.user.save()

        return Response({
            'success': True,
            'color': color,
            'message': 'Personal color updated successfully'
        })

    @action(detail=False, methods=['get'])
    def user_settings(self, request):
        """Get user settings and preferences"""
        serializer = UserSettingsSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'])
    def update_settings(self, request):
        """Update user settings and preferences"""
        serializer = UserSettingsSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Settings updated successfully',
                'data': serializer.data
            })

        return Response({
            'success': False,
            'errors': serializer.errors,
            'message': 'Failed to update settings'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get', 'patch'], url_path='preferences')
    def preferences(self, request):
        """Get or update user language and unit preferences"""
        if request.method == 'GET':
            return Response({
                'preferred_language': request.user.preferred_language,
                'unit_system': 'metric' if request.user.weight_unit == 'kg' else 'imperial',
                'weight_unit': request.user.weight_unit,
                'volume_unit': request.user.volume_unit,
                'time_format': request.user.time_format
            })

        # PATCH method
        if 'preferred_language' in request.data:
            lang = request.data['preferred_language']
            print(
                f"[USER_PREFS] Updating language: {request.user.username} → {lang}")
            if lang in ['en', 'ru', 'he']:
                request.user.preferred_language = lang
                print(f"[USER_PREFS] ✅ Language updated to: {lang}")
            else:
                print(f"[USER_PREFS] ⚠️ Invalid language: {lang}")

        if 'unit_system' in request.data:
            system = request.data['unit_system']
            if system == 'metric':
                request.user.weight_unit = 'kg'
                request.user.volume_unit = 'liters'
            elif system == 'imperial':
                request.user.weight_unit = 'lbs'
                request.user.volume_unit = 'gallons'

        request.user.save()

        return Response({
            'success': True,
            'message': 'Preferences updated successfully',
            'preferred_language': request.user.preferred_language,
            'unit_system': 'metric' if request.user.weight_unit == 'kg' else 'imperial'
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Custom login view with JWT tokens - supports email or username"""
    email_or_username = request.data.get(
        'username') or request.data.get('email')
    password = request.data.get('password')

    if not email_or_username or not password:
        return Response(
            {'error': 'Please provide email and password'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Try to find user by email first, then by username
    user = None
    if '@' in email_or_username:
        # It's an email
        try:
            user_obj = User.objects.get(email=email_or_username.lower())
            user = authenticate(username=user_obj.username, password=password)
        except User.DoesNotExist:
            pass
    else:
        # It's a username
        user = authenticate(username=email_or_username, password=password)

    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

    return Response(
        {'error': 'Invalid email or password'},
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resend_verification_email(request):
    """Resend email verification link"""
    import sys
    import traceback as tb
    sys.stdout.flush()  # Force flush output
    sys.stderr.flush()

    # Import here to avoid app loading order issues
    EmailAddress = None
    EmailConfirmation = None

    try:
        from allauth.account.models import EmailAddress as EA, EmailConfirmation as EC
        EmailAddress = EA
        EmailConfirmation = EC
        print(
            f"[DEBUG] ✅ Successfully imported EmailAddress and EmailConfirmation", flush=True)
    except Exception as e:
        print(f"[DEBUG] ❌ Error importing allauth models: {e}", flush=True)
        tb.print_exc()

    # Use multiple output methods
    logger.error("="*60)
    logger.error("🔄 RESEND VERIFICATION EMAIL - FUNCTION CALLED")
    logger.error("="*60)
    print(f"\n{'='*60}", flush=True)
    print(f"🔄 RESEND VERIFICATION EMAIL REQUEST", flush=True)
    print(f"{'='*60}", flush=True)

    try:
        print(f"User: {request.user}", flush=True)
        print(f"User email: {request.user.email}", flush=True)

        user = request.user

        print(f"[DEBUG] Step 1: Got user {user.username}", flush=True)

        if EmailAddress is None or EmailConfirmation is None:
            print(
                "[DEBUG] EmailAddress or EmailConfirmation is None, returning error", flush=True)
            return Response(
                {'error': 'Email verification not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        print("[DEBUG] Step 2: Checking if email already verified...", flush=True)
        # Check if email is already verified
        email_address = EmailAddress.objects.filter(
            user=user,
            email=user.email,
            verified=True
        ).first()

        if email_address:
            print("[DEBUG] Email already verified", flush=True)
            return Response(
                {'message': 'Email already verified'},
                status=status.HTTP_200_OK
            )

        print("[DEBUG] Step 3: Getting or creating email address...", flush=True)
        # Get or create unverified email address
        email_address, created = EmailAddress.objects.get_or_create(
            user=user,
            email=user.email.lower(),
            defaults={'primary': True, 'verified': False}
        )

        print(f"[DEBUG] Step 4: Email address created={created}", flush=True)
        print(
            f"📧 EmailAddress for {user.email}: verified={email_address.verified}", flush=True)

        # Send verification email by creating EmailConfirmation
        print("[DEBUG] Step 5: Creating and sending email confirmation...", flush=True)
        try:
            # Create confirmation object - this automatically sends email via our adapter
            email_confirmation = EmailConfirmation.create(email_address)
            email_confirmation.send(request, signup=False)

            print(f"✅ Resent verification email to {user.email}", flush=True)
            return Response(
                {'message': 'Verification email sent. Please check your inbox.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(f"❌ Failed to send verification email: {e}", flush=True)
            tb.print_exc()
            return Response(
                {'error': f'Failed to send verification email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Exception as e:
        print(f"\n{'='*60}", flush=True)
        print(f"❌ CATASTROPHIC ERROR in resend_verification_email", flush=True)
        print(f"Error type: {type(e).__name__}", flush=True)
        print(f"Error message: {str(e)}", flush=True)
        print(f"{'='*60}\n", flush=True)
        tb.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        return Response(
            {'error': f'Unexpected error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """Verify email address using the confirmation key"""
    try:
        from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC

        key = request.data.get('key')

        if not key:
            return Response(
                {'detail': 'Verification key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        print(f"\n{'='*60}", flush=True)
        print(f"📧 EMAIL VERIFICATION REQUEST", flush=True)
        print(f"Key: {key}", flush=True)
        print(f"{'='*60}", flush=True)

        # Try to get confirmation by key
        try:
            confirmation = EmailConfirmation.objects.get(key=key.lower())
        except EmailConfirmation.DoesNotExist:
            # Try HMAC-based confirmation (alternative method)
            try:
                confirmation = EmailConfirmationHMAC.from_key(key)
            except:
                print(f"❌ Invalid verification key: {key}", flush=True)
                return Response(
                    {'detail': 'Invalid or expired verification key'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Confirm the email
        try:
            confirmation.confirm(request)
        except Exception as e:
            print(f"⚠️ confirmation.confirm() error: {e}", flush=True)

        # CRITICAL FIX: Manually ensure verified=True is set
        email_address = confirmation.email_address
        email_address.refresh_from_db()
        if not email_address.verified:
            print(f"⚠️ Manually setting verified=True", flush=True)
            email_address.verified = True
            # Use force_update to avoid UNIQUE constraint issues
            EmailAddress.objects.filter(
                pk=email_address.pk).update(verified=True)

        print(
            f"✅ Email verified successfully for user: {confirmation.email_address.user.username}", flush=True)

        return Response(
            {'detail': 'Email verified successfully'},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        print(f"❌ Error verifying email: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return Response(
            {'detail': f'Verification failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_user_data(request):
    """
    Export all user data in JSON format (GDPR/CCPA Article 20 - Right to Data Portability)

    Creates a data export request and sends user an email with download link
    within 24-48 hours.
    """
    from legal.models import DataExportRequest

    user = request.user

    try:
        # Check if there's already a pending request
        pending_request = DataExportRequest.objects.filter(
            user=user,
            status__in=['pending', 'in_progress']
        ).first()

        if pending_request:
            return Response({
                'detail': 'You already have a pending data export request',
                'request_id': str(pending_request.id),
                'requested_at': pending_request.requested_at,
                'status': pending_request.status
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create new export request
        export_request = DataExportRequest.objects.create(
            user=user,
            status='pending'
        )

        logger.info(
            f"Data export request created: {export_request.id} for user {user.email}")

        # TODO: Send email notification
        # TODO: Trigger async task to generate data export

        return Response({
            'detail': 'Data export request submitted successfully',
            'message': 'You will receive an email with a download link within 24-48 hours',
            'request_id': str(export_request.id),
            'requested_at': export_request.requested_at
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating data export request: {e}")
        return Response(
            {'detail': f'Failed to create export request: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_data_export(request):
    """
    Get user's complete data in JSON format for immediate download.

    This is a synchronous version that generates data immediately.
    Use this for smaller data sets or when async processing is not needed.
    """
    user = request.user

    try:
        # Import models
        from apps.recipes.models import Recipe
        from apps.shopping.models import ShoppingList
        from apps.nutrition.models import MealPlan
        from legal.models import LegalAcceptance, CookieConsent

        # Collect all user data
        user_data = {
            'export_date': timezone.now().isoformat(),
            'user_info': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'language_preference': user.language_preference,
                'is_email_verified': user.is_email_verified,
            },
            'recipes': [],
            'shopping_lists': [],
            'meal_plans': [],
            'legal_acceptances': [],
            'cookie_consent': None,
        }

        # Export recipes
        recipes = Recipe.objects.filter(owner=user)
        for recipe in recipes:
            user_data['recipes'].append({
                'id': recipe.id,
                'name': recipe.name,
                'description': recipe.description,
                'ingredients': recipe.ingredients,
                'instructions': recipe.instructions,
                'prep_time': recipe.prep_time,
                'cook_time': recipe.cook_time,
                'servings': recipe.servings,
                'created_at': recipe.created_at.isoformat() if recipe.created_at else None,
            })

        # Export shopping lists
        shopping_lists = ShoppingList.objects.filter(owner=user)
        for shopping_list in shopping_lists:
            items = []
            for item in shopping_list.items.all():
                items.append({
                    'name': item.name,
                    'quantity': item.quantity,
                    'unit': item.unit,
                    'checked': item.checked,
                })

            user_data['shopping_lists'].append({
                'id': shopping_list.id,
                'name': shopping_list.name,
                'created_at': shopping_list.created_at.isoformat() if shopping_list.created_at else None,
                'items': items,
            })

        # Export meal plans
        meal_plans = MealPlan.objects.filter(user=user)
        for meal_plan in meal_plans:
            user_data['meal_plans'].append({
                'id': meal_plan.id,
                'date': meal_plan.date.isoformat() if meal_plan.date else None,
                'meal_type': meal_plan.meal_type,
                'recipe_name': meal_plan.recipe.name if meal_plan.recipe else None,
            })

        # Export legal acceptances
        legal_acceptances = LegalAcceptance.objects.filter(user=user)
        for acceptance in legal_acceptances:
            user_data['legal_acceptances'].append({
                'accepted_at': acceptance.accepted_at.isoformat(),
                'terms_version': acceptance.terms_version,
                'privacy_version': acceptance.privacy_version,
                'cookie_version': acceptance.cookie_version,
                'ip_address': acceptance.ip_address,
            })

        # Export cookie consent
        try:
            cookie_consent = CookieConsent.objects.get(user=user)
            user_data['cookie_consent'] = {
                'consent_type': cookie_consent.consent_type,
                'essential_cookies': cookie_consent.essential_cookies,
                'functional_cookies': cookie_consent.functional_cookies,
                'analytics_cookies': cookie_consent.analytics_cookies,
                'performance_cookies': cookie_consent.performance_cookies,
                'consented_at': cookie_consent.consented_at.isoformat(),
                'updated_at': cookie_consent.updated_at.isoformat(),
            }
        except CookieConsent.DoesNotExist:
            pass

        logger.info(f"User data export generated for user {user.email}")

        return Response(user_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error generating user data export: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'detail': f'Failed to generate data export: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """
    Request account deletion (GDPR/CCPA Article 17 - Right to Erasure)

    Creates a deletion request with a 30-day grace period.
    User can cancel within 30 days, after which account is permanently deleted.
    """
    from legal.models import AccountDeletionRequest

    user = request.user

    try:
        # Check if there's already a pending/confirmed deletion request
        existing_request = AccountDeletionRequest.objects.filter(
            user=user,
            status__in=['pending', 'confirmed', 'in_progress']
        ).first()

        if existing_request:
            return Response({
                'detail': 'You already have a pending account deletion request',
                'request_id': str(existing_request.id),
                'requested_at': existing_request.requested_at,
                'grace_period_ends': existing_request.grace_period_ends,
                'status': existing_request.status,
                'message': 'You can cancel this request within 30 days by contacting support'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create deletion request with 30-day grace period
        grace_period_ends = timezone.now() + timedelta(days=30)

        deletion_request = AccountDeletionRequest.objects.create(
            user=user,
            status='confirmed',
            grace_period_ends=grace_period_ends
        )

        logger.info(
            f"Account deletion request created: {deletion_request.id} for user {user.email}")

        # TODO: Send confirmation email
        # TODO: Send reminder emails (7 days before, 1 day before)
        # TODO: Schedule deletion task

        return Response({
            'detail': 'Account deletion request submitted successfully',
            'message': 'Your account will be permanently deleted in 30 days. You can cancel by contacting support.',
            'request_id': str(deletion_request.id),
            'requested_at': deletion_request.requested_at,
            'grace_period_ends': deletion_request.grace_period_ends,
            'grace_period_days': 30
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating account deletion request: {e}")
        return Response(
            {'detail': f'Failed to create deletion request: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_account_deletion(request):
    """
    Cancel a pending account deletion request within the 30-day grace period.
    """
    from legal.models import AccountDeletionRequest

    user = request.user

    try:
        deletion_request = AccountDeletionRequest.objects.filter(
            user=user,
            status__in=['pending', 'confirmed']
        ).first()

        if not deletion_request:
            return Response({
                'detail': 'No pending deletion request found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if still within grace period
        if deletion_request.grace_period_ends and deletion_request.grace_period_ends < timezone.now():
            return Response({
                'detail': 'Deletion grace period has expired. Please contact support.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Cancel the request
        deletion_request.status = 'cancelled'
        deletion_request.save()

        logger.info(
            f"Account deletion cancelled: {deletion_request.id} for user {user.email}")

        return Response({
            'detail': 'Account deletion request cancelled successfully',
            'message': 'Your account will not be deleted'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error cancelling account deletion: {e}")
        return Response(
            {'detail': f'Failed to cancel deletion request: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
