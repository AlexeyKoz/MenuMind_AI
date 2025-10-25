from functools import wraps

from rest_framework import status
from rest_framework.response import Response


def verified_email_required(view_func):
    """Require authenticated users to have a verified email via allauth."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user

        if not user or not user.is_authenticated:
            return Response({'detail': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        email_verified = True
        if hasattr(user, 'emailaddress_set'):
            email_verified = user.emailaddress_set.filter(verified=True).exists()

        if not email_verified:
            return Response({'detail': 'Email verification required'}, status=status.HTTP_403_FORBIDDEN)

        return view_func(request, *args, **kwargs)

    return _wrapped
