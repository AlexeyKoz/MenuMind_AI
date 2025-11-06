from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task
def reset_daily_quotas():
    """
    Reset daily AI quotas for all users.
    Scheduled to run daily at midnight (see settings.py CELERY_BEAT_SCHEDULE).
    """
    updated = User.objects.all().update(
        recipe_generations_today=0,
        translations_today=0,
        nutrition_logs_today=0,
        url_scrapes_today=0,
        ai_requests_today=0,
        ai_requests_reset_at=timezone.now() + timedelta(days=1)
    )
    return f"Reset quotas for {updated} users"

