from functools import wraps
from django.http import JsonResponse
from django.utils import timezone
import time


def email_verified_required(feature_name="this feature"):
    """
    Decorator to require email verification for a view.
    Returns 403 if user's email is not verified.
    
    Works with both function-based views and ViewSet methods.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(self_or_request, *args, **kwargs):
            # Handle both function views and ViewSet methods
            if hasattr(self_or_request, 'request'):
                # It's a ViewSet - first arg is 'self'
                request = self_or_request.request
                self_arg = self_or_request
            else:
                # It's a function view - first arg is 'request'
                request = self_or_request
                self_arg = None
            
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            email_verified = request.user.emailaddress_set.filter(verified=True).exists()
            if not email_verified:
                return JsonResponse({
                    'error': 'Email verification required',
                    'message': f'Please verify your email to use {feature_name}',
                    'verification_required': True
                }, status=403)
            
            # Call original method with correct arguments
            if self_arg:
                return view_func(self_arg, *args, **kwargs)
            else:
                return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def ai_quota_required(request_type='other'):
    """
    Decorator to check and enforce AI quota limits.
    Automatically increments quota on successful requests.
    
    Works with both function-based views and ViewSet methods.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(self_or_request, *args, **kwargs):
            # Handle both function views and ViewSet methods
            if hasattr(self_or_request, 'request'):
                # It's a ViewSet - first arg is 'self'
                request = self_or_request.request
                self_arg = self_or_request
            else:
                # It's a function view - first arg is 'request'
                request = self_or_request
                self_arg = None
            
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            user = request.user
            can_proceed, message = user.check_quota(request_type)
            
            if not can_proceed:
                return JsonResponse({
                    'error': 'Quota exceeded',
                    'message': message,
                    'quota_resets_at': user.ai_requests_reset_at.isoformat()
                }, status=429)
            
            request._ai_request_start = time.time()
            
            # Call original method with correct arguments
            if self_arg:
                response = view_func(self_arg, *args, **kwargs)
            else:
                response = view_func(request, *args, **kwargs)
            
            # Only increment quota if request was successful
            if response.status_code < 400:
                user.increment_quota(request_type)
            
            return response
        return wrapped_view
    return decorator
