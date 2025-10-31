"""
Celery background tasks for recipe system

Tasks:
1. update_canonical_recipe_statistics - Recalculate statistics for a recipe
2. batch_update_recipe_statistics - Update statistics for all recipes (periodic)
3. cleanup_expired_builder_sessions - Remove old builder sessions from cache
4. generate_recipe_thumbnails - Generate thumbnail images (future enhancement)
"""

from celery import shared_task
from django.db.models import Avg, Count, Q
from django.core.cache import cache
from typing import Optional
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

        # Translate recipe name using SmartTranslationService
        from apps.core.smart_translator import SmartTranslationService
        smart_translator = SmartTranslationService()
        translated_recipe_name = smart_translator.translate_recipe_name(
            recipe.name,
            target_language
        )
        logger.info(
            f"[TRANSLATION] Recipe name: {recipe.name} -> {translated_recipe_name}")

        # Unit translation dictionary
        unit_translations = {
            'ru': {
                'g': 'г', 'kg': 'кг', 'mg': 'мг',
                'ml': 'мл', 'l': 'л',
                'tsp': 'ч.л.', 'tbsp': 'ст.л.', 'cup': 'чашка', 'cups': 'чашки',
                'oz': 'унция', 'lb': 'фунт',
                'pcs': 'шт', 'piece': 'шт', 'pieces': 'шт',
                'cloves': 'зубчика', 'clove': 'зубчик',
                'slice': 'ломтик', 'slices': 'ломтики',
                'pinch': 'щепотка',
                'large': 'крупный', 'medium': 'средний', 'small': 'маленький',
                'egg': 'яйцо', 'eggs': 'яйца'
            },
            'he': {
                'g': 'גרם', 'kg': 'ק"ג', 'mg': 'מ"ג',
                'ml': 'מ"ל', 'l': 'ליטר',
                'tsp': 'כפית', 'tbsp': 'כף', 'cup': 'כוס', 'cups': 'כוסות',
                'oz': 'אונקיה', 'lb': 'ליבר',
                'pcs': 'יח', 'piece': 'יח', 'pieces': 'יח',
                'cloves': 'שיני', 'clove': 'שן',
                'slice': 'פרוסה', 'slices': 'פרוסות',
                'pinch': 'קמצוץ',
                'large': 'גדול', 'medium': 'בינוני', 'small': 'קטן',
                'egg': 'ביצה', 'eggs': 'ביצים'
            }
        }

        # Translate ingredients (using IML database + Gemini fallback)
        translated_ingredients = []
        for ing in recipe.base_ingredients:
            translated_ing = ing.copy()
            translated_name = None

            # Translate unit if available
            if target_language in unit_translations and ing.get('unit'):
                unit = ing.get('unit').lower().strip()
                if unit in unit_translations[target_language]:
                    translated_ing['unit'] = unit_translations[target_language][unit]
                    logger.info(
                        f"[TRANSLATION] Unit: {ing.get('unit')} -> {translated_ing['unit']}")

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
                        translated_name = translations_dict[target_language]
                        logger.info(
                            f"[TRANSLATION] IML: {ing.get('name')} -> {translated_name}")
                except IngredientCache.DoesNotExist:
                    logger.warning(
                        f"[TRANSLATION] Ingredient not in IML: {ing.get('ingredient_key')}")

            # If no translation found in IML, use Gemini fallback
            if not translated_name and ing.get('name'):
                logger.info(
                    f"[TRANSLATION] Using Gemini fallback for ingredient: {ing.get('name')}")
                try:
                    from apps.core.smart_translator import SmartTranslationService
                    smart_translator = SmartTranslationService()

                    # Use the ingredient translation method
                    gemini_translation = smart_translator.translate_ingredients_batch(
                        [ing],
                        target_language
                    )
                    if gemini_translation and len(gemini_translation) > 0:
                        translated_name = gemini_translation[0].get('name')
                        logger.info(
                            f"[TRANSLATION] GEMINI: {ing.get('name')} -> {translated_name}")
                except Exception as e:
                    logger.error(
                        f"[TRANSLATION] Gemini fallback failed: {e}")

            # Apply translation if found
            if translated_name:
                translated_ing['name'] = translated_name
            else:
                logger.warning(
                    f"[TRANSLATION] No translation found for: {ing.get('name')}, keeping English")

            translated_ingredients.append(translated_ing)

        # Translate cooking steps using Google Translate (via SmartTranslationService)
        # NOTE: We skip CookLingo because it does word-by-word translation which causes
        # mixed Latin/Cyrillic characters when encountering untranslated words
        logger.info(
            f"[TRANSLATION] Translating {len(recipe.base_steps)} steps using Google Translate")

        translated_steps = []
        if recipe.base_steps:
            try:
                # Use SmartTranslationService which calls Google Translate
                gemini_steps = smart_translator.translate_cooking_steps_batch(
                    recipe.base_steps,
                    target_language
                )

                if gemini_steps and len(gemini_steps) == len(recipe.base_steps):
                    translated_steps = gemini_steps
                    logger.info(
                        f"[TRANSLATION] ✅ Successfully translated all {len(gemini_steps)} steps")
                else:
                    logger.warning(
                        f"[TRANSLATION] ⚠️ Translation mismatch: expected {len(recipe.base_steps)}, got {len(gemini_steps) if gemini_steps else 0}")
                    translated_steps = recipe.base_steps  # Fallback to original
            except Exception as e:
                logger.error(f"[TRANSLATION] ❌ Step translation failed: {e}")
                translated_steps = recipe.base_steps  # Fallback to original
        else:
            logger.warning(
                f"[TRANSLATION] ⚠️ No base_steps found for recipe {recipe_id}")

        # Save translation
        # FIXED: Use recipe name, not ingredient name!
        translation.name = translated_recipe_name
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


# ============================================================================
# SMART TRANSLATION TASKS (Background, Non-Blocking)
# ============================================================================

@shared_task(bind=True, max_retries=3)
def translate_recipe_name_background(self, recipe_id, target_language, original_name):
    """
    Background task to translate ONLY recipe name (fast, minimal API usage)

    This is called from Discovery page when user switches language.
    - Non-blocking: User doesn't wait
    - Cached: Result saved to DB forever
    - Smart: Only runs once per recipe per language

    API Usage: 1 call per recipe per language (one-time)
    """
    from apps.recipes.models import CanonicalRecipe, RecipeTranslation
    from apps.core.smart_translator import SmartTranslationService
    from django.utils import timezone

    try:
        print(
            f"[TASK] 🚀 Starting NAME translation: {original_name} → {target_language}")

        # Get or create translation record
        translation, created = RecipeTranslation.objects.get_or_create(
            canonical_recipe_id=recipe_id,
            language=target_language,
            defaults={
                'status': 'in_progress',
                'name': '',
                'description': '',
                'base_ingredients': [],
                'base_steps': []
            }
        )

        if not created and translation.name:
            # Already translated
            print(f"[TASK] ✅ Already translated, skipping: {translation.name}")
            return

        # Update status
        translation.status = 'in_progress'
        translation.save()

        # Translate name only
        translator = SmartTranslationService()
        translated_name = translator.translate_recipe_name(
            original_name,
            target_language
        )

        if translated_name and translated_name != original_name:
            translation.name = translated_name
            translation.status = 'completed'  # Name done
            translation.completed_at = timezone.now()
            translation.save()

            print(f"[TASK] ✅ SUCCESS: {original_name} → {translated_name}")
        else:
            # Translation failed
            translation.name = original_name  # Keep original
            translation.status = 'failed'
            translation.error_message = "Translation returned same as original"
            translation.save()

            print(f"[TASK] ⚠️ FAILED: Keeping original name {original_name}")

    except Exception as e:
        print(f"[TASK] ❌ ERROR translating recipe name: {e}")
        import traceback
        traceback.print_exc()

        # Update translation record with error
        try:
            translation = RecipeTranslation.objects.get(
                canonical_recipe_id=recipe_id,
                language=target_language
            )
            translation.status = 'failed'
            translation.error_message = str(e)
            translation.save()
        except:
            pass

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


# ===================================================================
# SPRINT 4: 3-Phase Translation Tasks (Groq Primary, Gemini Fallback)
# ===================================================================

@shared_task(bind=True, max_retries=2)
def translate_recipe_immediate(self, recipe_id: str, target_lang: str):
    """
    PHASE 1: Immediate Translation

    Triggered when user opens a recipe in their language.
    Translates complete recipe in ~2-3s using Groq (primary) or Gemini (fallback).

    Args:
        recipe_id: Recipe UUID
        target_lang: Target language code ('en', 'he', 'ru')

    Returns:
        Dict with translation result
    """
    try:
        from apps.recipes.models import CanonicalRecipe, RecipeTranslation
        from apps.core.services import get_smart_translation_service

        logger.info(
            f"[PHASE 1] Immediate translation: recipe={recipe_id}, lang={target_lang}")

        # Get recipe
        recipe = CanonicalRecipe.objects.get(id=recipe_id)

        # Check if already translated
        existing = RecipeTranslation.objects.filter(
            canonical_recipe=recipe,
            language=target_lang,
            status='completed'
        ).first()

        if existing:
            logger.info(f"[PHASE 1] ✅ Already translated, skipping")
            return {'success': True, 'cached': True}

        # Get or create translation record
        translation, created = RecipeTranslation.objects.get_or_create(
            canonical_recipe=recipe,
            language=target_lang,
            defaults={'status': 'in_progress'}
        )

        if not created:
            translation.status = 'in_progress'
            translation.save(update_fields=['status'])

        # Prepare recipe data
        recipe_data = {
            'canonical': {
                'metadata': {
                    'title': recipe.name,
                    'description': recipe.description or '',
                    'servings': 4,  # Default
                },
                'structure': {
                    'ingredients': recipe.base_ingredients or [],
                    'steps': recipe.base_steps or []
                }
            }
        }

        # Translate
        translator = get_smart_translation_service()
        result = translator.translate_recipe(
            recipe_data, target_lang, phase='immediate')

        if result.success:
            # Save translation
            translation.name = result.translated_content.get(
                'title', recipe.name)
            translation.description = result.translated_content.get(
                'description', '')
            translation.content = result.translated_content
            translation.status = 'completed'
            translation.error_message = None
            translation.save()

            # Queue Phase 2 (background translation to third language)
            third_lang = get_third_language(target_lang)
            if third_lang:
                translate_recipe_background.delay(recipe_id, third_lang)

            logger.info(
                f"[PHASE 1] ✅ Complete: {result.execution_time_ms:.2f}ms using {result.ai_provider}")

            return {
                'success': True,
                'execution_time_ms': result.execution_time_ms,
                'ai_provider': result.ai_provider,
                'cached': False
            }
        else:
            # Mark as failed
            translation.status = 'failed'
            translation.error_message = result.error_message
            translation.save()

            logger.error(f"[PHASE 1] ❌ Failed: {result.error_message}")
            return {'success': False, 'error': result.error_message}

    except Exception as e:
        logger.error(f"[PHASE 1] ❌ Error: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries * 10)


@shared_task(bind=True, max_retries=2)
def translate_recipe_background(self, recipe_id: str, target_lang: str):
    """
    PHASE 2: Background Translation

    Runs asynchronously after Phase 1 completes.
    Translates to popular third language (e.g., if user=ru, translate to he).

    Args:
        recipe_id: Recipe UUID
        target_lang: Target language code

    Returns:
        Dict with translation result
    """
    try:
        from apps.recipes.models import CanonicalRecipe, RecipeTranslation
        from apps.core.services import get_smart_translation_service

        logger.info(
            f"[PHASE 2] Background translation: recipe={recipe_id}, lang={target_lang}")

        # Get recipe
        recipe = CanonicalRecipe.objects.get(id=recipe_id)

        # Check if already translated
        existing = RecipeTranslation.objects.filter(
            canonical_recipe=recipe,
            language=target_lang,
            status='completed'
        ).first()

        if existing:
            logger.info(f"[PHASE 2] ✅ Already translated, skipping")
            return {'success': True, 'cached': True}

        # Get or create translation record
        translation, created = RecipeTranslation.objects.get_or_create(
            canonical_recipe=recipe,
            language=target_lang,
            defaults={'status': 'in_progress'}
        )

        if not created:
            translation.status = 'in_progress'
            translation.save(update_fields=['status'])

        # Prepare recipe data
        recipe_data = {
            'canonical': {
                'metadata': {
                    'title': recipe.name,
                    'description': recipe.description or '',
                },
                'structure': {
                    'ingredients': recipe.base_ingredients or [],
                    'steps': recipe.base_steps or []
                }
            }
        }

        # Translate
        translator = get_smart_translation_service()
        result = translator.translate_recipe(
            recipe_data, target_lang, phase='background')

        if result.success:
            # Save translation
            translation.name = result.translated_content.get(
                'title', recipe.name)
            translation.description = result.translated_content.get(
                'description', '')
            translation.content = result.translated_content
            translation.status = 'completed'
            translation.error_message = None
            translation.save()

            logger.info(
                f"[PHASE 2] ✅ Complete: {result.execution_time_ms:.2f}ms using {result.ai_provider}")

            return {
                'success': True,
                'execution_time_ms': result.execution_time_ms,
                'ai_provider': result.ai_provider
            }
        else:
            # Mark as failed
            translation.status = 'failed'
            translation.error_message = result.error_message
            translation.save()

            logger.error(f"[PHASE 2] ❌ Failed: {result.error_message}")
            return {'success': False, 'error': result.error_message}

    except Exception as e:
        logger.error(f"[PHASE 2] ❌ Error: {e}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries * 10)


@shared_task(bind=True, max_retries=2)
def translate_recipe_on_demand(self, recipe_id: str, target_lang: str):
    """
    PHASE 3: On-Demand Translation

    Triggered when user explicitly requests a language that hasn't been translated yet.
    Same implementation as Phase 1 but triggered differently.

    Args:
        recipe_id: Recipe UUID
        target_lang: Target language code

    Returns:
        Dict with translation result
    """
    # Reuse Phase 1 logic
    return translate_recipe_immediate(recipe_id, target_lang)


def get_third_language(user_lang: str) -> Optional[str]:
    """
    Determine the third language for Phase 2 background translation

    Logic:
    - If user_lang=en, translate to he (Hebrew - primary market)
    - If user_lang=he, translate to ru (Russian - large community)
    - If user_lang=ru, translate to he (Hebrew - local language)

    Args:
        user_lang: User's language code

    Returns:
        Third language code or None
    """
    third_lang_map = {
        'en': 'he',  # English users -> Hebrew (primary market)
        'he': 'ru',  # Hebrew users -> Russian (large community)
        'ru': 'he',  # Russian users -> Hebrew (local language)
    }

    return third_lang_map.get(user_lang)


# ===================================================================
# SPRINT 5: Background Agents (Celery Beat Scheduled Tasks)
# ===================================================================

@shared_task
def hourly_translation_scan():
    """
    BACKGROUND AGENT: Hourly Translation Scan

    Scans for recipes with incomplete translations and queues translation tasks.

    Schedule: Every hour
    Purpose: Ensure all popular recipes are translated to all languages

    Returns:
        Dict with scan results
    """
    from apps.recipes.models import CanonicalRecipe, RecipeTranslation

    logger.info("[AGENT] Starting hourly translation scan...")

    SUPPORTED_LANGUAGES = ['en', 'he', 'ru']
    recipes_queued = 0

    try:
        # Get published recipes
        recipes = CanonicalRecipe.objects.filter(is_published=True)[
            :100]  # Limit to top 100

        for recipe in recipes:
            for lang in SUPPORTED_LANGUAGES:
                # Check if translation exists and is complete
                translation = RecipeTranslation.objects.filter(
                    canonical_recipe=recipe,
                    language=lang,
                    status='completed'
                ).first()

                if not translation:
                    # Queue background translation
                    logger.info(
                        f"[AGENT] Queuing translation: recipe={recipe.id}, lang={lang}")
                    translate_recipe_background.delay(str(recipe.id), lang)
                    recipes_queued += 1

        logger.info(
            f"[AGENT] ✅ Hourly scan complete: {recipes_queued} translations queued")

        return {
            'success': True,
            'recipes_scanned': len(recipes),
            'translations_queued': recipes_queued
        }

    except Exception as e:
        logger.error(f"[AGENT] ❌ Hourly scan failed: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_stale_translations():
    """
    BACKGROUND AGENT: Stale Translation Cleanup

    Removes failed or stuck translation records to prevent queue buildup.

    Schedule: Daily at 3 AM
    Purpose: Clean up failed translations older than 7 days

    Returns:
        Dict with cleanup results
    """
    from apps.recipes.models import RecipeTranslation
    from django.utils import timezone
    from datetime import timedelta

    logger.info("[AGENT] Starting stale translation cleanup...")

    try:
        cutoff_date = timezone.now() - timedelta(days=7)

        # Find stale translations
        stale_translations = RecipeTranslation.objects.filter(
            Q(status='failed') | Q(status='in_progress'),
            updated_at__lt=cutoff_date
        )

        count = stale_translations.count()

        if count > 0:
            # Delete or reset them
            stale_translations.update(
                status='failed', error_message='Cleaned up by agent')
            logger.info(f"[AGENT] ✅ Cleaned up {count} stale translations")
        else:
            logger.info("[AGENT] ✅ No stale translations found")

        return {
            'success': True,
            'cleaned_up': count
        }

    except Exception as e:
        logger.error(f"[AGENT] ❌ Cleanup failed: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def refresh_discovery_cache():
    """
    BACKGROUND AGENT: Discovery Cache Refresh

    Refreshes discovery page cache for all languages.

    Schedule: Every hour
    Purpose: Keep discovery cache fresh with latest translations

    Returns:
        Dict with refresh results
    """
    from apps.core.services import get_discovery_cache_service

    logger.info("[AGENT] Starting discovery cache refresh...")

    SUPPORTED_LANGUAGES = ['en', 'he', 'ru']
    results = {}

    try:
        cache_service = get_discovery_cache_service()

        for lang in SUPPORTED_LANGUAGES:
            try:
                refreshed = cache_service.refresh_all(lang)
                results[lang] = refreshed
                logger.info(
                    f"[AGENT] Refreshed {refreshed} entries for {lang}")
            except Exception as e:
                logger.error(f"[AGENT] Failed to refresh {lang}: {e}")
                results[lang] = 0

        total_refreshed = sum(results.values())
        logger.info(
            f"[AGENT] ✅ Cache refresh complete: {total_refreshed} total entries")

        return {
            'success': True,
            'results': results,
            'total_refreshed': total_refreshed
        }

    except Exception as e:
        logger.error(f"[AGENT] ❌ Cache refresh failed: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_stale_discovery_cache():
    """
    BACKGROUND AGENT: Stale Discovery Cache Cleanup

    Removes old discovery cache entries.

    Schedule: Weekly on Sunday at 4 AM
    Purpose: Clean up entries older than 30 days

    Returns:
        Dict with cleanup results
    """
    from apps.core.services import get_discovery_cache_service

    logger.info("[AGENT] Starting stale discovery cache cleanup...")

    try:
        cache_service = get_discovery_cache_service()
        deleted_count = cache_service.cleanup_stale(days_old=30)

        logger.info(
            f"[AGENT] ✅ Cleaned up {deleted_count} stale cache entries")

        return {
            'success': True,
            'deleted_count': deleted_count
        }

    except Exception as e:
        logger.error(f"[AGENT] ❌ Cache cleanup failed: {e}")
        return {'success': False, 'error': str(e)}


# ===================================================================
# BULK RECIPE GENERATION (Developer Tool)
# ===================================================================

@shared_task(bind=True, max_retries=0)
def process_bulk_recipe_generation(self, job_id: str):
    """
    Process bulk recipe generation job
    
    This task:
    1. Takes a list of recipe names
    2. Searches and scrapes each recipe from the internet
    3. Creates canonical recipes in the database
    4. Tracks progress in real-time
    
    Args:
        job_id: UUID of BulkRecipeGenerationJob
        
    Returns:
        Dict with job results
    """
    from apps.recipes.models import BulkRecipeGenerationJob
    from apps.recipes.services import RecipeAgentService
    from asgiref.sync import async_to_sync
    from django.utils import timezone
    
    logger.info(f"[BULK GENERATION] Starting job {job_id}")
    
    try:
        # Get job
        job = BulkRecipeGenerationJob.objects.get(id=job_id)
        
        # Update status
        job.status = 'in_progress'
        job.started_at = timezone.now()
        job.celery_task_id = self.request.id
        job.save()
        
        # Parse recipe list
        recipe_names = job.get_recipe_names()
        job.total_recipes = len(recipe_names)
        job.save()
        
        logger.info(f"[BULK GENERATION] Processing {job.total_recipes} recipes")
        
        # Initialize agent service
        agent = RecipeAgentService()
        
        # Default user preferences (English, metric)
        user_preferences = {
            'dietary_restrictions': [],
            'allergies': [],
            'language': 'en',
            'unit_system': 'metric'
        }
        
        # Process each recipe
        results = {}
        completed_count = 0
        failed_count = 0
        
        for idx, recipe_name in enumerate(recipe_names, 1):
            logger.info(f"[BULK GENERATION] Processing {idx}/{job.total_recipes}: {recipe_name}")
            
            try:
                # Process recipe query
                success, result, message = async_to_sync(agent.process_recipe_query)(
                    recipe_name,
                    job.created_by,  # Use admin user
                    user_preferences
                )
                
                if success and result.get('canonical_recipe'):
                    # Success
                    canonical_recipe = result['canonical_recipe']
                    recipe_id = canonical_recipe.get('id', '')
                    
                    results[recipe_name] = {
                        'status': 'success',
                        'recipe_id': str(recipe_id),
                        'recipe_name': canonical_recipe.get('name', recipe_name),
                        'message': 'Recipe generated successfully'
                    }
                    completed_count += 1
                    logger.info(f"[BULK GENERATION] ✅ Success: {canonical_recipe.get('name')}")
                    
                    # CREATE DISCOVERY CACHE ENTRIES (so recipe appears in discovery page)
                    try:
                        from apps.recipes.models import CanonicalRecipe, DiscoveryCache
                        
                        recipe_obj = CanonicalRecipe.objects.get(id=recipe_id)
                        
                        # Create cache entry for each supported language
                        for lang in ['en', 'he', 'ru']:
                            cache_entry, created = DiscoveryCache.objects.get_or_create(
                                canonical_recipe=recipe_obj,
                                language=lang,
                                defaults={
                                    'title': recipe_obj.name,
                                    'brief': (recipe_obj.description[:200] if recipe_obj.description else ''),
                                    'image_url': recipe_obj.ai_source_url or '',
                                    'tags': recipe_obj.diet_labels or []
                                }
                            )
                            if created:
                                logger.info(f"[BULK GENERATION] 📋 Created discovery cache entry for {lang}")
                        
                        results[recipe_name]['discovery_cache'] = 'created'
                        logger.info(f"[BULK GENERATION] ✅ Recipe added to discovery page!")
                        
                    except Exception as cache_error:
                        logger.error(f"[BULK GENERATION] ⚠️ Failed to create discovery cache: {cache_error}")
                        results[recipe_name]['discovery_cache_error'] = str(cache_error)
                else:
                    # Failed
                    results[recipe_name] = {
                        'status': 'failed',
                        'error': message or 'Unknown error',
                        'message': f'Failed to generate: {message}'
                    }
                    failed_count += 1
                    logger.warning(f"[BULK GENERATION] ❌ Failed: {recipe_name} - {message}")
                
            except Exception as e:
                # Exception during processing
                error_msg = str(e)
                results[recipe_name] = {
                    'status': 'failed',
                    'error': error_msg,
                    'message': f'Exception: {error_msg}'
                }
                failed_count += 1
                logger.error(f"[BULK GENERATION] ❌ Exception for {recipe_name}: {e}")
            
            # Update progress
            job.completed_recipes = completed_count
            job.failed_recipes = failed_count
            job.results = results
            job.save()
            
            logger.info(f"[BULK GENERATION] Progress: {completed_count + failed_count}/{job.total_recipes}")
        
        # Mark job as completed
        job.completed_at = timezone.now()
        
        if failed_count == 0:
            job.status = 'completed'
        elif completed_count == 0:
            job.status = 'failed'
        else:
            job.status = 'partial'
        
        job.save()
        
        logger.info(f"[BULK GENERATION] ✅ Job {job_id} completed: {completed_count} success, {failed_count} failed")
        
        return {
            'job_id': job_id,
            'status': job.status,
            'total': job.total_recipes,
            'completed': completed_count,
            'failed': failed_count
        }
        
    except BulkRecipeGenerationJob.DoesNotExist:
        logger.error(f"[BULK GENERATION] Job {job_id} not found")
        return {'success': False, 'error': 'Job not found'}
        
    except Exception as e:
        logger.error(f"[BULK GENERATION] ❌ Job {job_id} failed with exception: {e}")
        
        # Update job status
        try:
            job = BulkRecipeGenerationJob.objects.get(id=job_id)
            job.status = 'failed'
            job.completed_at = timezone.now()
            job.results = {
                'error': str(e),
                'message': 'Job failed with exception'
            }
            job.save()
        except:
            pass
        
        return {'success': False, 'error': str(e)}

