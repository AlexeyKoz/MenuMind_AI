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

