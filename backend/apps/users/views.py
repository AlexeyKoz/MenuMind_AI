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
import logging

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
        send_email_confirmation = None
        
        try:
            from allauth.account.models import EmailAddress as EA
            EmailAddress = EA
            print(f"[REGISTRATION] ✅ Imported EmailAddress: {EmailAddress}", flush=True)
        except Exception as e:
            print(f"[REGISTRATION] ❌ Error EmailAddress: {e}", flush=True)
        
        try:
            from allauth.account.utils import send_email_confirmation as sec
            send_email_confirmation = sec
            print(f"[REGISTRATION] ✅ Imported send_email_confirmation: {send_email_confirmation}", flush=True)
        except Exception as e:
            print(f"[REGISTRATION] ❌ Error send_email_confirmation: {e}", flush=True)
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create EmailAddress for allauth verification
        if EmailAddress is not None and user.email:
            email_address, created = EmailAddress.objects.get_or_create(
                user=user,
                email=user.email.lower(),
                defaults={'primary': True, 'verified': False}
            )

            # Send verification email
            if send_email_confirmation is not None:
                try:
                    print(
                        f"📧 Attempting to send verification email to {user.email}")
                    send_email_confirmation(request, user, signup=True)
                    print(
                        f"✅ Verification email sent successfully to {user.email}")
                except Exception as e:
                    print(f"❌ Failed to send verification email: {e}")
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
    """Custom login view with JWT tokens"""
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

    return Response(
        {'error': 'Invalid credentials'},
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
    send_email_confirmation = None
    
    try:
        from allauth.account.models import EmailAddress as EA
        EmailAddress = EA
        print(f"[DEBUG] ✅ Successfully imported EmailAddress: {EmailAddress}", flush=True)
    except ImportError as e:
        print(f"[DEBUG] ❌ ImportError importing EmailAddress: {e}", flush=True)
    except Exception as e:
        print(f"[DEBUG] ❌ Unexpected error importing EmailAddress: {e}", flush=True)
    
    try:
        from allauth.account.utils import send_email_confirmation as sec
        send_email_confirmation = sec
        print(f"[DEBUG] ✅ Successfully imported send_email_confirmation: {send_email_confirmation}", flush=True)
    except ImportError as e:
        print(f"[DEBUG] ❌ ImportError importing send_email_confirmation: {e}", flush=True)
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"[DEBUG] ❌ Unexpected error importing send_email_confirmation: {e}", flush=True)
        import traceback
        traceback.print_exc()

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
        print(f"[DEBUG] Step 2: Checking EmailAddress import...", flush=True)
        print(f"[DEBUG] EmailAddress is: {EmailAddress}", flush=True)

        if EmailAddress is None:
            print("[DEBUG] EmailAddress is None, returning error", flush=True)
            return Response(
                {'error': 'Email verification not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        print("[DEBUG] Step 3: Checking if email already verified...", flush=True)
        # Check if email is already verified
        email_address = EmailAddress.objects.filter(
            user=user,
            email=user.email,
            verified=True
        ).first()

        print(f"[DEBUG] Step 4: Found email_address: {email_address}", flush=True)

        if email_address:
            print("[DEBUG] Email already verified", flush=True)
            return Response(
                {'message': 'Email already verified'},
                status=status.HTTP_200_OK
            )

        print("[DEBUG] Step 5: Getting or creating email address...", flush=True)
        # Get or create unverified email address
        email_address, created = EmailAddress.objects.get_or_create(
            user=user,
            email=user.email.lower(),
            defaults={'primary': True, 'verified': False}
        )

        print(f"[DEBUG] Step 6: Email address created={created}", flush=True)
        print(
            f"📧 EmailAddress for {user.email}: verified={email_address.verified}")
        
        print(f"[DEBUG] Step 6.5: Checking send_email_confirmation...", flush=True)
        print(f"[DEBUG] send_email_confirmation is: {send_email_confirmation}", flush=True)

        # Send verification email
        if send_email_confirmation is not None:
            print("[DEBUG] Step 7: Sending verification email...", flush=True)
            try:
                # The send_email_confirmation will automatically use:
                # 1. Simple Mailjet (plain HTML) - PRIMARY
                # 2. Mailjet (with templates) - SECONDARY
                # 3. Brevo (if configured) - TERTIARY
                # 4. EmailJS (if configured) - QUATERNARY
                # 5. Django SMTP (fallback) - FINAL
                # This is handled by MultilingualAccountAdapter.send_confirmation_mail
                send_email_confirmation(request, user, signup=False)
                print(f"✅ Resent verification email to {user.email}")
                return Response(
                    {'message': 'Verification email sent. Please check your inbox.'},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                print(f"❌ Failed to send verification email: {e}")
                tb.print_exc()
                return Response(
                    {'error': f'Failed to send verification email: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(
            {'error': 'Email service not available'},
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
