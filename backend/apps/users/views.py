from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404

from .models import User
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    UserProfileSerializer, PartnerConnectionSerializer,
    UserSettingsSerializer
)


class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
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
