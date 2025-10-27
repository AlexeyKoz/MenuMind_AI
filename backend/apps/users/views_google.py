import logging
import requests
from typing import Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

try:
    from allauth.account.models import EmailAddress
except ImportError:  # pragma: no cover - allauth should be installed
    EmailAddress = None  # type: ignore

from .serializers import UserSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


def _build_unique_username(base: str) -> str:
    """Generate a unique username based on provided base value."""
    candidate = base
    suffix = 1
    while User.objects.filter(username=candidate).exists():
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _ensure_email_verified(user) -> None:
    if not EmailAddress:
        return

    email = user.email
    if not email:
        return

    try:
        # Try to get existing EmailAddress for this user
        email_address = EmailAddress.objects.filter(user=user, email=email).first()
        
        if email_address:
            # Update existing record
            if not email_address.verified:
                email_address.verified = True
                email_address.save(update_fields=['verified'])
            if not email_address.primary:
                email_address.primary = True
                email_address.save(update_fields=['primary'])
        else:
            # Check if email exists for another user (shouldn't happen, but handle it)
            existing = EmailAddress.objects.filter(email=email).first()
            if existing:
                # Email belongs to another user - this is a conflict
                # Update the user reference to current user
                existing.user = user
                existing.verified = True
                existing.primary = True
                existing.save()
            else:
                # Create new EmailAddress
                EmailAddress.objects.create(
                    user=user,
                    email=email,
                    verified=True,
                    primary=True
                )
    except Exception as e:
        # Log but don't fail - Google login should still work
        print(f"⚠️ Warning: Could not update EmailAddress: {e}")
        import traceback
        traceback.print_exc()


@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """Exchange a Google authorization code or ID token for MenuMindAI JWT tokens."""
    print("=" * 80)
    print("🔐 GOOGLE LOGIN ATTEMPT")
    print("=" * 80)
    logger.info("=" * 80)
    logger.info("🔐 GOOGLE LOGIN ATTEMPT")
    logger.info("=" * 80)

    credential = request.data.get('credential')
    code = request.data.get('code')

    print(f"📦 Request data keys: {list(request.data.keys())}")
    print(f"🎫 Has credential: {bool(credential)}")
    print(f"🔑 Has code: {bool(code)}")
    if credential:
        print(f"🎫 Credential preview: {credential[:50]}...")
    logger.info(f"📦 Request data keys: {list(request.data.keys())}")
    logger.info(f"🎫 Has credential: {bool(credential)}")
    logger.info(f"🔑 Has code: {bool(code)}")
    if code:
        logger.info(f"🔑 Code preview: {code[:20]}...")

    if not credential and not code:
        logger.error("❌ No credential or code provided")
        return Response({'error': 'Google credential or code is required'}, status=status.HTTP_400_BAD_REQUEST)

    provider_settings = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
    client_id = provider_settings.get('APP', {}).get('client_id') or None
    client_secret = provider_settings.get('APP', {}).get('secret') or None

    logger.info(f"⚙️ Client ID configured: {bool(client_id)}")
    if client_id:
        logger.info(f"⚙️ Client ID preview: {client_id[:30]}...")
    logger.info(f"⚙️ Client Secret configured: {bool(client_secret)}")

    try:
        # If we received an authorization code, exchange it for tokens
        if code:
            token_endpoint = 'https://oauth2.googleapis.com/token'
            token_data = {
                'code': code,
                'client_id': client_id,
                'redirect_uri': 'postmessage',  # For popup flow
                'grant_type': 'authorization_code',
            }

            # Only add client_secret if it exists (not needed for public clients)
            if client_secret:
                token_data['client_secret'] = client_secret

            logger.info(
                f"Exchanging authorization code for tokens (has_secret: {bool(client_secret)})")
            token_response = requests.post(token_endpoint, data=token_data)

            if not token_response.ok:
                logger.error(
                    f"Token exchange failed: {token_response.status_code} - {token_response.text}")
                token_response.raise_for_status()

            tokens = token_response.json()
            credential = tokens.get('id_token')

            if not credential:
                logger.error(
                    f"No ID token in response. Got: {list(tokens.keys())}")
                raise ValueError('No ID token in response')

            logger.info("Successfully exchanged code for ID token")

        # Verify the ID token
        logger.info(f"Verifying ID token with client_id: {client_id[:20]}...")
        idinfo = id_token.verify_oauth2_token(
            credential, google_requests.Request(), client_id)
    except ValueError as exc:
        logger.error(f"❌ ValueError during token verification: {exc}")
        logger.exception("Full traceback:")
        return Response({'error': f'Invalid Google token: {str(exc)}'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:  # pragma: no cover - unexpected
        logger.error(f"❌ Unexpected error during Google login: {exc}")
        logger.exception('Full traceback:')
        return Response({'error': f'Google login failed: {str(exc)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    email = idinfo.get('email')
    if not email:
        return Response({'error': 'Email not provided by Google'}, status=status.HTTP_400_BAD_REQUEST)

    first_name = idinfo.get('given_name', '')
    last_name = idinfo.get('family_name', '')
    google_sub = idinfo.get('sub', '')

    username_base = email.split('@')[0]
    if google_sub:
        username_base = f"{username_base}_{google_sub[:8]}"

    try:
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': _build_unique_username(username_base),
                    'first_name': first_name,
                    'last_name': last_name,
                },
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=['password'])
            else:
                updated_fields = []
                if not user.first_name and first_name:
                    user.first_name = first_name
                    updated_fields.append('first_name')
                if not user.last_name and last_name:
                    user.last_name = last_name
                    updated_fields.append('last_name')
                if updated_fields:
                    user.save(update_fields=updated_fields)
    except Exception as exc:  # pragma: no cover - unexpected database error
        logger.exception(
            'Failed processing Google login for %s: %s', email, exc)
        return Response({'error': 'Google login failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    _ensure_email_verified(user)

    refresh = RefreshToken.for_user(user)

    logger.info("=" * 80)
    logger.info(f"✅ GOOGLE LOGIN SUCCESS for user: {user.username} ({email})")
    logger.info("=" * 80)

    return Response(
        {
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        },
        status=status.HTTP_200_OK,
    )
