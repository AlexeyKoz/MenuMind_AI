"""
Helpers for resolving shopping-list collaborators by email + collaboration key.
"""
from typing import Optional, Tuple

from apps.users.models import User


def resolve_collaborator_by_email_and_key(
    friend_email: str,
    collaboration_key: str,
) -> Tuple[Optional[User], Optional[dict]]:
    """
    Look up a user by unique email and verify their collaboration key.

    Returns:
        (user, None) on success
        (None, error_dict) on failure — error_dict has message, error_type, status
    """
    email = (friend_email or '').strip().lower()
    key = (collaboration_key or '').strip()

    if not email or '@' not in email:
        return None, {
            'error': 'Invalid email',
            'message': 'Please enter a valid email address.',
            'error_type': 'invalid_email',
            'status': 400,
        }

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return None, {
            'error': 'User not found',
            'message': 'No user found with this email address. Please check the email and try again.',
            'error_type': 'user_not_found',
            'status': 404,
        }

    if not user.collaboration_key or user.collaboration_key != key:
        return None, {
            'error': 'Invalid collaboration key',
            'message': 'The collaboration key does not match this email address. Please verify both and try again.',
            'error_type': 'key_mismatch',
            'status': 400,
        }

    return user, None
