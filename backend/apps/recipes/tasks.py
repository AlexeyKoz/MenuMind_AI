"""
Celery background tasks for recipe system

Tasks:
1. update_canonical_recipe_statistics - Recalculate statistics for a recipe
2. batch_update_recipe_statistics - Update statistics for all recipes (periodic)
3. cleanup_expired_builder_sessions - Remove old builder sessions from cache
4. generate_recipe_thumbnails - Generate thumbnail images (future enhancement)
"""

from celery import shared_task
from django.db.models import Avg, Count
from django.core.cache import cache
from apps.recipes.models import (
    CanonicalRecipe,
    RecipeLike,
    RecipeRating,
    RecipeReview
)
from apps.recipes.cache import RecipeCache
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def update_canonical_recipe_statistics(self, recipe_id: str):
    """
    Update denormalized statistics for a canonical recipe

    This task recalculates:
    - total_saves (from RecipeLike count)
    - total_ratings (from RecipeRating count)
    - average_rating (from RecipeRating average)
    - total_reviews (from RecipeReview count)
    - total_cooked (from Recipe fork count where has_cooked=True)
    """
    try:
        recipe = CanonicalRecipe.objects.get(id=recipe_id)

        # Calculate statistics
        total_likes = RecipeLike.objects.filter(
            canonical_recipe=recipe).count()

        rating_stats = RecipeRating.objects.filter(
            canonical_recipe=recipe
        ).aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )

        total_reviews = RecipeReview.objects.filter(
            canonical_recipe=recipe,
            is_approved=True
        ).count()

        # Update recipe
        recipe.total_saves = total_likes
        recipe.total_ratings = rating_stats['count'] or 0
        recipe.average_rating = rating_stats['avg_rating'] or 0.0
        recipe.total_reviews = total_reviews

        recipe.save(update_fields=[
            'total_saves',
            'total_ratings',
            'average_rating',
            'total_reviews'
        ])

        # Invalidate caches
        RecipeCache.invalidate_all_for_recipe(recipe_id)

        logger.info(f"Updated statistics for recipe {recipe_id}: "
                    f"saves={total_likes}, ratings={recipe.total_ratings}, "
                    f"avg_rating={recipe.average_rating:.2f}, reviews={total_reviews}")

        return {
            'recipe_id': recipe_id,
            'total_saves': total_likes,
            'total_ratings': recipe.total_ratings,
            'average_rating': float(recipe.average_rating),
            'total_reviews': total_reviews
        }

    except CanonicalRecipe.DoesNotExist:
        logger.error(f"Recipe {recipe_id} not found")
        return None
    except Exception as exc:
        logger.error(
            f"Error updating statistics for recipe {recipe_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def batch_update_recipe_statistics():
    """
    Update statistics for all canonical recipes (periodic task)

    Run this task hourly or daily depending on traffic
    """
    recipes = CanonicalRecipe.objects.filter(is_published=True)

    updated_count = 0
    error_count = 0

    for recipe in recipes:
        try:
            # Queue individual update tasks
            update_canonical_recipe_statistics.delay(str(recipe.id))
            updated_count += 1
        except Exception as exc:
            logger.error(
                f"Error queuing statistics update for recipe {recipe.id}: {exc}")
            error_count += 1

    logger.info(
        f"Batch statistics update: {updated_count} queued, {error_count} errors")

    return {
        'queued': updated_count,
        'errors': error_count
    }


@shared_task
def cleanup_expired_builder_sessions():
    """
    Clean up expired recipe builder sessions from cache

    Builder sessions have 1-hour TTL, but this task ensures cleanup
    Run this task every 4 hours
    """
    # Note: This is a placeholder as Redis automatically expires keys
    # In production, you might want to log session statistics

    logger.info("Builder session cleanup completed")
    return {'status': 'ok'}


@shared_task
def recalculate_recipe_hash(recipe_id: str):
    """
    Recalculate recipe hash for deduplication

    Useful if hash algorithm changes or data needs revalidation
    """
    try:
        from apps.recipes.models import Recipe

        recipe = Recipe.objects.get(id=recipe_id)

        # Only recalculate for non-fork recipes
        if not recipe.is_fork:
            old_hash = recipe.recipe_hash
            # Recipe.save() will recalculate hash
            recipe.save()

            logger.info(
                f"Recalculated hash for recipe {recipe_id}: {old_hash} -> {recipe.recipe_hash}")

            return {
                'recipe_id': recipe_id,
                'old_hash': old_hash,
                'new_hash': recipe.recipe_hash
            }

        return {'recipe_id': recipe_id, 'skipped': 'is_fork'}

    except Recipe.DoesNotExist:
        logger.error(f"Recipe {recipe_id} not found")
        return None


@shared_task
def detect_duplicate_canonical_recipes():
    """
    Detect potential duplicate canonical recipes

    Run periodically to identify recipes that might be duplicates
    despite different hashes
    """
    from django.db.models import Count

    # Find recipes with similar names
    duplicates = []

    recipes = CanonicalRecipe.objects.values('name').annotate(
        count=Count('id')
    ).filter(count__gt=1)

    for item in recipes:
        similar_recipes = CanonicalRecipe.objects.filter(
            name__iexact=item['name']
        ).values('id', 'name', 'recipe_hash')

        duplicates.append({
            'name': item['name'],
            'count': item['count'],
            'recipes': list(similar_recipes)
        })

    if duplicates:
        logger.warning(
            f"Found {len(duplicates)} potential duplicate recipe groups")

    return duplicates


@shared_task
def archive_old_reviews():
    """
    Archive or cleanup very old, unhelpful reviews

    Run monthly to keep database size manageable
    """
    from datetime import timedelta
    from django.utils import timezone

    # Example: Archive reviews older than 2 years with 0 helpful votes
    cutoff_date = timezone.now() - timedelta(days=730)

    old_reviews = RecipeReview.objects.filter(
        created_at__lt=cutoff_date,
        helpful_count=0,
        is_approved=True
    )

    count = old_reviews.count()

    # Option 1: Mark as archived (add is_archived field to model)
    # old_reviews.update(is_archived=True)

    # Option 2: Delete (be careful!)
    # old_reviews.delete()

    logger.info(f"Found {count} old reviews to archive")

    return {'count': count}


@shared_task
def warm_cache_for_popular_recipes():
    """
    Warm up cache for most popular recipes

    Run this after cache clears or server restarts
    """
    from apps.recipes.serializers import CanonicalRecipeSerializer

    # Get top 100 most popular recipes
    popular_recipes = CanonicalRecipe.objects.filter(
        is_published=True
    ).order_by('-total_saves')[:100]

    warmed_count = 0

    for recipe in popular_recipes:
        try:
            # Serialize and cache
            serialized = CanonicalRecipeSerializer(recipe).data
            RecipeCache.set_canonical_detail(str(recipe.id), serialized)

            # Cache statistics
            stats = {
                'total_saves': recipe.total_saves,
                'total_cooked': recipe.total_cooked,
                'average_rating': float(recipe.average_rating),
                'total_ratings': recipe.total_ratings,
                'total_reviews': recipe.total_reviews
            }
            RecipeCache.set_recipe_stats(str(recipe.id), stats)

            warmed_count += 1
        except Exception as exc:
            logger.error(f"Error warming cache for recipe {recipe.id}: {exc}")

    logger.info(f"Warmed cache for {warmed_count} popular recipes")

    return {'warmed': warmed_count}


# Periodic task schedule configuration
# Add to settings.py or celery.py:
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'update-recipe-statistics-hourly': {
        'task': 'apps.recipes.tasks.batch_update_recipe_statistics',
        'schedule': crontab(minute=0, hour='*/1'),  # Every hour
    },
    'cleanup-builder-sessions': {
        'task': 'apps.recipes.tasks.cleanup_expired_builder_sessions',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
    },
    'detect-duplicates-daily': {
        'task': 'apps.recipes.tasks.detect_duplicate_canonical_recipes',
        'schedule': crontab(minute=0, hour=3),  # 3 AM daily
    },
    'archive-old-reviews-monthly': {
        'task': 'apps.recipes.tasks.archive_old_reviews',
        'schedule': crontab(minute=0, hour=2, day_of_month=1),  # 1st of month at 2 AM
    },
    'warm-cache-morning': {
        'task': 'apps.recipes.tasks.warm_cache_for_popular_recipes',
        'schedule': crontab(minute=0, hour=6),  # 6 AM daily
    },
}
"""


@shared_task(bind=True, max_retries=3)
def translate_recipe_to_language(self, recipe_id: str, target_language: str):
    """
    Translate a recipe to a target language using IML and CookLingo databases

    Args:
        recipe_id: UUID of the CanonicalRecipe
        target_language: Language code ('ru', 'he', etc.)

    Returns:
        Dict with translation status and data
    """
    from apps.recipes.models import CanonicalRecipe, RecipeTranslation
    from apps.core.translation_service import TranslationService
    from apps.core.cooking_terms_service import CookingTermsTranslationService
    from django.utils import timezone

    try:
        logger.info(
            f"[TRANSLATION] Starting translation of recipe {recipe_id} to {target_language}")

        # Get recipe
        recipe = CanonicalRecipe.objects.get(id=recipe_id)

        # Get or create translation record
        translation, created = RecipeTranslation.objects.get_or_create(
            canonical_recipe=recipe,
            language=target_language,
            defaults={'status': 'in_progress'}
        )

        if not created and translation.status == 'completed':
            logger.info(
                f"[TRANSLATION] Translation already completed for {recipe_id} ({target_language})")
            return {
                'recipe_id': recipe_id,
                'language': target_language,
                'status': 'already_completed'
            }

        # Update status
        translation.status = 'in_progress'
        translation.save()

        # Initialize services
        translation_service = TranslationService()
        cooking_terms_service = CookingTermsTranslationService()

        # Translate recipe name
        translated_name = recipe.name  # For now, keep English - can enhance later

        # Translate ingredients (using IML database)
        translated_ingredients = []
        for ing in recipe.base_ingredients:
            translated_ing = ing.copy()

            # Translate ingredient name using IML
            if ing.get('ingredient_key'):
                from apps.core.models import IngredientCache
                try:
                    ingredient = IngredientCache.objects.get(
                        ingredient_key=ing['ingredient_key'])
                    translations_dict = {}
                    for trans in ingredient.translations.all():
                        translations_dict[trans.language] = trans.name

                    if target_language in translations_dict:
                        translated_ing['name'] = translations_dict[target_language]
                except IngredientCache.DoesNotExist:
                    pass  # Keep original name

            translated_ingredients.append(translated_ing)

        # Translate cooking steps (using CookLingo database)
        translated_steps = []
        for step in recipe.base_steps:
            translated_step = step.copy()

            # Translate cooking terms in step text
            if step.get('text'):
                translated_step['text'] = cooking_terms_service.translate_text(
                    step['text'],
                    target_language
                )

            translated_steps.append(translated_step)

        # Save translation
        translation.name = translated_name
        translation.description = recipe.description
        translation.base_ingredients = translated_ingredients
        translation.base_steps = translated_steps
        translation.status = 'completed'
        translation.completed_at = timezone.now()
        translation.save()

        logger.info(
            f"[TRANSLATION] ✅ Completed translation of recipe {recipe_id} to {target_language}")

        return {
            'recipe_id': recipe_id,
            'language': target_language,
            'status': 'completed',
            'ingredients_count': len(translated_ingredients),
            'steps_count': len(translated_steps)
        }

    except CanonicalRecipe.DoesNotExist:
        logger.error(f"[TRANSLATION] Recipe {recipe_id} not found")
        return {'recipe_id': recipe_id, 'status': 'failed', 'error': 'Recipe not found'}

    except Exception as exc:
        logger.error(
            f"[TRANSLATION] Error translating recipe {recipe_id} to {target_language}: {exc}")

        # Update translation status
        try:
            translation.status = 'failed'
            translation.error_message = str(exc)
            translation.save()
        except:
            pass

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def translate_recipe_to_all_languages(recipe_id: str, priority_language: str = None):
    """
    Translate a recipe to all supported languages

    Args:
        recipe_id: UUID of the CanonicalRecipe
        priority_language: Language to translate first (synchronously if needed)

    Returns:
        Dict with translation task IDs
    """
    from apps.recipes.models import RecipeTranslation

    # Excluding 'en' as it's the base language
    SUPPORTED_LANGUAGES = ['ru', 'he']

    logger.info(f"[TRANSLATION] Queuing translations for recipe {recipe_id}")

    task_ids = {}

    # If priority language is specified and not English, translate it first
    if priority_language and priority_language != 'en' and priority_language in SUPPORTED_LANGUAGES:
        task = translate_recipe_to_language.apply_async(
            args=[recipe_id, priority_language],
            priority=9  # High priority
        )
        task_ids[priority_language] = task.id
        SUPPORTED_LANGUAGES.remove(priority_language)

    # Queue other languages in background
    for lang in SUPPORTED_LANGUAGES:
        task = translate_recipe_to_language.apply_async(
            args=[recipe_id, lang],
            priority=5  # Normal priority
        )
        task_ids[lang] = task.id

    logger.info(
        f"[TRANSLATION] Queued {len(task_ids)} translation tasks for recipe {recipe_id}")

    return {
        'recipe_id': recipe_id,
        'task_ids': task_ids,
        'total_languages': len(task_ids)
    }
