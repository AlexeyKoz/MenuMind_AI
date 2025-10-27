"""
Celery tasks for GDPR/CCPA compliance operations.

These tasks handle:
- Data export generation
- Account deletion processing
- Scheduled deletion reminders
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
import json

logger = logging.getLogger(__name__)


@shared_task
def generate_user_data_export(user_id, request_id):
    """
    Generate user data export and send email with download link.

    This is an async task that collects all user data and creates
    a downloadable JSON file.
    """
    from django.contrib.auth import get_user_model
    from legal.models import DataExportRequest

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
        export_request = DataExportRequest.objects.get(id=request_id)

        # Update status to in_progress
        export_request.status = 'in_progress'
        export_request.save()

        logger.info(f"Starting data export for user {user.email}")

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

        # Save to file or upload to secure storage
        # For now, we'll store the JSON as a string in the model
        # In production, upload to S3 or similar secure storage

        json_data = json.dumps(user_data, indent=2)

        # Update export request with download URL
        # TODO: Upload to S3 and generate signed URL
        export_request.status = 'completed'
        export_request.completed_at = timezone.now()
        export_request.download_url = f'/api/users/download-export/{request_id}/'
        export_request.save()

        logger.info(f"Data export completed for user {user.email}")

        # TODO: Send email with download link
        # send_data_export_email(user, export_request.download_url)

        return {
            'success': True,
            'user_email': user.email,
            'request_id': str(request_id)
        }

    except Exception as e:
        logger.error(f"Error generating data export: {e}")

        try:
            export_request.status = 'failed'
            export_request.save()
        except:
            pass

        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def process_account_deletion(user_id, deletion_request_id):
    """
    Permanently delete user account and all associated data.

    This task is scheduled to run after the grace period expires.
    """
    from django.contrib.auth import get_user_model
    from legal.models import AccountDeletionRequest

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
        deletion_request = AccountDeletionRequest.objects.get(
            id=deletion_request_id)

        # Double-check grace period has passed
        if deletion_request.grace_period_ends > timezone.now():
            logger.warning(
                f"Attempted to delete user {user.email} before grace period ended")
            return {
                'success': False,
                'error': 'Grace period has not expired'
            }

        # Check if deletion was cancelled
        if deletion_request.status == 'cancelled':
            logger.info(f"Deletion cancelled for user {user.email}")
            return {
                'success': False,
                'error': 'Deletion was cancelled'
            }

        logger.info(f"Starting account deletion for user {user.email}")

        # Update status
        deletion_request.status = 'processing'
        deletion_request.save()

        # Delete user data (Django cascade will handle related objects)
        # This includes:
        # - Recipes
        # - Shopping lists
        # - Meal plans
        # - Legal acceptances
        # - Cookie consent
        # - All other related data

        user_email = user.email
        user.delete()

        # Mark deletion as completed
        deletion_request.status = 'completed'
        deletion_request.completed_at = timezone.now()
        deletion_request.save()

        logger.info(f"Account deletion completed for {user_email}")

        return {
            'success': True,
            'user_email': user_email,
            'deletion_request_id': str(deletion_request_id)
        }

    except Exception as e:
        logger.error(f"Error deleting account: {e}")

        try:
            deletion_request.status = 'failed'
            deletion_request.save()
        except:
            pass

        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def send_deletion_reminder(user_id, deletion_request_id, days_remaining):
    """
    Send reminder email before account deletion.

    Args:
        user_id: User ID
        deletion_request_id: Deletion request ID
        days_remaining: Days until deletion (7 or 1)
    """
    from django.contrib.auth import get_user_model
    from legal.models import AccountDeletionRequest

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
        deletion_request = AccountDeletionRequest.objects.get(
            id=deletion_request_id)

        # Check if deletion was cancelled
        if deletion_request.status == 'cancelled':
            logger.info(
                f"Skipping reminder - deletion cancelled for {user.email}")
            return {'success': True, 'skipped': True}

        logger.info(
            f"Sending {days_remaining}-day deletion reminder to {user.email}")

        # TODO: Send email via Brevo
        # send_deletion_reminder_email(user, days_remaining, deletion_request.grace_period_ends)

        return {
            'success': True,
            'user_email': user.email,
            'days_remaining': days_remaining
        }

    except Exception as e:
        logger.error(f"Error sending deletion reminder: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def check_expired_deletion_requests():
    """
    Periodic task to process expired deletion requests.

    Runs daily to check for deletion requests where grace period has expired.
    """
    from legal.models import AccountDeletionRequest

    logger.info("Checking for expired deletion requests")

    # Find all confirmed deletion requests where grace period has expired
    expired_requests = AccountDeletionRequest.objects.filter(
        status='confirmed',
        grace_period_ends__lte=timezone.now()
    )

    count = 0
    for deletion_request in expired_requests:
        logger.info(
            f"Processing expired deletion request: {deletion_request.id}")

        # Trigger deletion task
        process_account_deletion.delay(
            deletion_request.user.id,
            str(deletion_request.id)
        )
        count += 1

    logger.info(f"Scheduled {count} account deletions")

    return {
        'success': True,
        'count': count
    }
