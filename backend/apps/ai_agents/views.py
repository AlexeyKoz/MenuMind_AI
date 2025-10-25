from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import async_to_sync

from apps.recipes.services import RecipeAgentService
from .rate_limiter import AIRateLimiter


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_recipes_from_inventory(request):
    """
    Generate recipe suggestions based on user's preferences.

    This endpoint is for the Recipes page AI Generator tab.
    It generates random/popular recipes based on user preferences,
    NOT from inventory.

    For inventory-based recipe generation, use the shopping app endpoint:
    /api/shopping/inventory/generate_recipes/

    Request body (optional):
        - max_recipes: int (default: 3)
        - cuisine: string (optional)
        - difficulty: string (optional)

    Returns:
        - recipes: list of canonical recipes
        - message: success message
    """
    # ⭐ CHECK EMAIL VERIFICATION FIRST
    from allauth.account.models import EmailAddress

    try:
        email_address = EmailAddress.objects.get(
            user=request.user,
            email=request.user.email
        )

        if not email_address.verified:
            return Response({
                'error': 'Email verification required',
                'message': (
                    'Please verify your email address before generating recipes. '
                    'Check your inbox for the verification link we sent you. '
                    'If you didn\'t receive it, you can request a new one from your profile.'
                ),
                'verification_required': True,
                'email': request.user.email,
                'recipes': []
            }, status=status.HTTP_403_FORBIDDEN)

    except EmailAddress.DoesNotExist:
        # Email not registered in allauth (shouldn't happen, but handle gracefully)
        return Response({
            'error': 'Email verification required',
            'message': (
                'Your email address needs to be verified. '
                'Please contact support if you continue to see this message.'
            ),
            'verification_required': True,
            'recipes': []
        }, status=status.HTTP_403_FORBIDDEN)

    # Get options from request
    max_recipes = request.data.get('max_recipes', 3)
    cuisine = request.data.get('cuisine', '')
    difficulty = request.data.get('difficulty', '')

    # ⭐ CHECK RATE LIMIT BEFORE PROCESSING
    allowed, message, limit_type = AIRateLimiter.check_rate_limit(
        request.user, max_recipes)

    if not allowed:
        # Add rate limit headers even to error responses
        headers = AIRateLimiter.get_rate_limit_headers(request.user)

        response = Response({
            'error': message,
            'limit_type': limit_type,
            'recipes': [],
            'rate_limited': True
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Add headers
        for header_name, header_value in headers.items():
            response[header_name] = header_value

        # Add Retry-After header for rate limit errors
        if limit_type == 'minute':
            response['Retry-After'] = '60'
        elif limit_type == 'daily':
            # Calculate seconds until next day
            from datetime import timedelta
            now = timezone.now()
            next_day = (now + timedelta(days=1)).replace(hour=0,
                                                         minute=0, second=0, microsecond=0)
            seconds_until_reset = int((next_day - now).total_seconds())
            response['Retry-After'] = str(seconds_until_reset)

        return response

    # Build query based on user preferences
    queries = [
        "easy pasta recipe",
        "quick chicken dinner",
        "healthy vegetarian meal",
        "simple dessert",
        "30 minute dinner"
    ]

    # Customize based on user dietary restrictions
    user_restrictions = request.user.dietary_restrictions
    if user_restrictions:
        if 'vegetarian' in user_restrictions.lower():
            queries = ["vegetarian pasta",
                       "veggie stir fry", "vegetarian curry"]
        elif 'vegan' in user_restrictions.lower():
            queries = ["vegan pasta", "vegan curry", "vegan bowl"]

    # Limit to requested number
    queries = queries[:max_recipes]

    print(
        f"[AI RECIPES] Generating {len(queries)} recipes for {request.user.username}")

    # Get user preferences
    user_preferences = {
        'dietary_restrictions': request.user.dietary_restrictions,
        'allergies': request.user.allergies,
        'language': getattr(request.user, 'preferred_language', 'en'),
        'unit_system': 'metric' if getattr(request.user, 'weight_unit', 'kg') == 'kg' else 'imperial'
    }

    # Generate multiple recipes
    agent = RecipeAgentService()
    generated_recipes = []

    try:
        # Generate recipes based on different queries
        for i, query in enumerate(queries):
            success, result, message = async_to_sync(agent.process_recipe_query)(
                query,
                request.user,
                user_preferences
            )

            if success:
                generated_recipes.append(result['canonical_recipe'])
                print(
                    f"[AI RECIPES] Generated recipe {i+1}/{len(queries)}: {result['canonical_recipe']['name']}")
            else:
                print(
                    f"[AI RECIPES] Failed to generate recipe {i+1}: {message}")
                # Don't fail the entire request if one recipe fails
                continue

        if not generated_recipes:
            return Response({
                'error': 'Failed to generate recipes. Please try again later.',
                'recipes': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ⭐ LOG SUCCESSFUL REQUEST
        AIRateLimiter.log_request(request.user, len(generated_recipes))

        # Get updated stats
        stats = AIRateLimiter.get_user_stats(request.user)

        # Get rate limit headers
        headers = AIRateLimiter.get_rate_limit_headers(request.user)

        response = Response({
            'success': True,
            'recipes': generated_recipes,
            'message': f'Generated {len(generated_recipes)} recipe(s)',
            'rate_limit_stats': stats
        }, status=status.HTTP_200_OK)

        # Add rate limit headers to response
        for header_name, header_value in headers.items():
            response[header_name] = header_value

        return response

    except Exception as e:
        print(f"[AI RECIPES ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'An error occurred while generating recipes: {str(e)}',
            'recipes': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_assistant(request):
    """
    General AI assistant endpoint for various tasks.
    To be implemented.
    """
    return Response({
        'message': 'AI Assistant endpoint - Coming soon!'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_coaching(request):
    """
    AI nutrition coaching endpoint.
    To be implemented.
    """
    return Response({
        'message': 'AI Coaching endpoint - Coming soon!'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rate_limit_status(request):
    """
    Get current user's rate limit status and usage statistics.

    GET /api/ai_agents/rate-limit-status/

    Returns:
        - Current usage (last minute and today)
        - Remaining quota
        - Limit values
        - Reset times
        - Exemption status
    """
    from django.utils import timezone
    from datetime import timedelta

    stats = AIRateLimiter.get_user_stats(request.user)
    settings = AIRateLimiter.get_settings()

    # Calculate reset times
    now = timezone.now()
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    next_day = (now + timedelta(days=1)).replace(hour=0,
                                                 minute=0, second=0, microsecond=0)

    # Build response
    response_data = {
        'user': request.user.username,
        'plan': 'unlimited' if stats['exempt'] else 'standard',
        'limits': {
            'per_minute': stats['limit_per_minute'],
            'per_day': stats['limit_per_day'],
        },
        'usage': {
            'last_minute': stats['recipes_last_minute'],
            'today': stats['recipes_today'],
        },
        'remaining': {
            'minute': max(0, stats['limit_per_minute'] - stats['recipes_last_minute']) if not stats['exempt'] else 'unlimited',
            'daily': stats.get('remaining_today', 'unlimited'),
        },
        'resets_at': {
            'minute': next_minute.isoformat(),
            'daily': next_day.isoformat(),
        },
        'reset_in_seconds': {
            'minute': int((next_minute - now).total_seconds()),
            'daily': int((next_day - now).total_seconds()),
        },
        'exempt': stats['exempt'],
    }

    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_metrics(request):
    """
    Admin dashboard for rate limiting metrics and analytics.

    GET /api/ai_agents/admin/metrics/

    Requires: Staff/Admin user permissions

    Returns comprehensive metrics including:
    - Overview statistics
    - Usage by endpoint
    - Top users
    - Recent activity
    - Rate limit violations
    """
    from django.db.models import Count, Sum, Avg, Q
    from django.utils import timezone
    from datetime import timedelta
    from .models import AIRateLimitLog, AIRateLimitSettings
    from .rate_limiter import AIRateLimiter

    # Check if user is staff/admin
    if not request.user.is_staff:
        return Response({
            'error': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)

    now = timezone.now()
    today = now.date()
    last_hour = now - timedelta(hours=1)
    last_24h = now - timedelta(hours=24)
    last_7days = now - timedelta(days=7)

    # Overview statistics
    overview = {
        'total_requests_today': AIRateLimitLog.objects.filter(
            timestamp__date=today
        ).count(),
        'total_requests_last_hour': AIRateLimitLog.objects.filter(
            timestamp__gte=last_hour
        ).count(),
        'total_requests_last_24h': AIRateLimitLog.objects.filter(
            timestamp__gte=last_24h
        ).count(),
        'total_requests_last_7days': AIRateLimitLog.objects.filter(
            timestamp__gte=last_7days
        ).count(),
        'unique_users_today': AIRateLimitLog.objects.filter(
            timestamp__date=today
        ).values('user').distinct().count(),
        'unique_users_last_24h': AIRateLimitLog.objects.filter(
            timestamp__gte=last_24h
        ).values('user').distinct().count(),
        'total_recipes_generated_today': AIRateLimitLog.objects.filter(
            timestamp__date=today
        ).aggregate(total=Sum('recipes_generated'))['total'] or 0,
        'total_recipes_generated_last_24h': AIRateLimitLog.objects.filter(
            timestamp__gte=last_24h
        ).aggregate(total=Sum('recipes_generated'))['total'] or 0,
    }

    # Usage by endpoint
    by_endpoint = list(AIRateLimitLog.objects.filter(
        timestamp__gte=last_24h
    ).values('endpoint').annotate(
        request_count=Count('id'),
        total_recipes=Sum('recipes_generated'),
        unique_users=Count('user', distinct=True)
    ).order_by('-request_count'))

    # Top users (last 24h)
    top_users = list(AIRateLimitLog.objects.filter(
        timestamp__gte=last_24h
    ).values('user__username').annotate(
        requests=Count('id'),
        recipes=Sum('recipes_generated')
    ).order_by('-requests')[:20])

    # Hourly breakdown (last 24 hours)
    hourly_stats = []
    for i in range(24):
        hour_start = now - timedelta(hours=i+1)
        hour_end = now - timedelta(hours=i)

        count = AIRateLimitLog.objects.filter(
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        ).count()

        hourly_stats.append({
            'hour': hour_start.strftime('%Y-%m-%d %H:00'),
            'requests': count
        })

    hourly_stats.reverse()  # Show oldest to newest

    # Current rate limit settings
    settings = AIRateLimiter.get_settings()
    current_settings = {
        'max_recipes_per_minute': settings.max_recipes_per_minute,
        'max_recipes_per_day': settings.max_recipes_per_day,
        'exempted_users': settings.get_exempted_users(),
    }

    # Recent activity (last 10 requests)
    recent_activity = []
    recent_logs = AIRateLimitLog.objects.select_related(
        'user').order_by('-timestamp')[:10]
    for log in recent_logs:
        recent_activity.append({
            'user': log.user.username,
            'endpoint': log.endpoint,
            'recipes_generated': log.recipes_generated,
            'timestamp': log.timestamp.isoformat(),
            'time_ago': _time_ago(log.timestamp, now)
        })

    # Compile full response
    metrics = {
        'overview': overview,
        'by_endpoint': by_endpoint,
        'top_users': top_users,
        'hourly_stats': hourly_stats,
        'current_settings': current_settings,
        'recent_activity': recent_activity,
        'generated_at': now.isoformat(),
    }

    return Response(metrics)


def _time_ago(timestamp, now):
    """Helper function to calculate human-readable time ago"""
    diff = now - timestamp
    seconds = diff.total_seconds()

    if seconds < 60:
        return f"{int(seconds)}s ago"
    elif seconds < 3600:
        return f"{int(seconds/60)}m ago"
    elif seconds < 86400:
        return f"{int(seconds/3600)}h ago"
    else:
        return f"{int(seconds/86400)}d ago"
