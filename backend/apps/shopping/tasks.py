"""
Celery tasks for shopping list background processing
"""

from celery import shared_task
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def complete_shopping_list_recipe(
    self,
    recipe_hash: str,
    scraped_data: dict,
    recipe_name: str,
    user_id: int,
    shopping_list_id: int,
    user_language: str
):
    """
    PHASE 2: Complete full recipe processing in background

    This runs AFTER ingredients are already added to shopping list.

    Steps:
    1. Check if canonical recipe already created (race condition)
    2. Extract full recipe (steps, times, metadata)
    3. Enrich with IML (nutrition calculation)
    4. Translate to REMAINING languages (not user's language - already done)
    5. Create CanonicalRecipe
    6. Link to shopping list
    7. Send WebSocket notification to user

    Args:
        recipe_hash: Recipe hash for deduplication
        scraped_data: {'url': str, 'text': str} from Firecrawl
        recipe_name: Recipe name (English)
        user_id: User who requested
        shopping_list_id: Shopping list to link to
        user_language: User's language (already translated, skip in Phase 2)
    """
    logger.info(
        f"[BACKGROUND RECIPE] Starting Phase 2 for recipe: {recipe_name}")
    logger.info(f"[BACKGROUND RECIPE] User language (skip): {user_language}")

    try:
        # Import here to avoid circular imports
        from apps.recipes.models import CanonicalRecipe
        from apps.recipes.services import RecipeAgentService
        from apps.shopping.models import ShoppingList

        # STEP 1: Check if canonical recipe already exists (deduplication)
        try:
            canonical = CanonicalRecipe.objects.get(recipe_hash=recipe_hash)
            logger.info(
                f"[BACKGROUND RECIPE] Recipe already exists: {canonical.name} (ID: {canonical.id})")

            logger.info(
                f"[BACKGROUND RECIPE] ✅ Recipe already created")
            return {
                'status': 'linked_existing',
                'canonical_recipe_id': str(canonical.id),
                'recipe_name': canonical.name
            }

        except CanonicalRecipe.DoesNotExist:
            logger.info(
                "[BACKGROUND RECIPE] Recipe doesn't exist yet, creating...")

        # STEP 2: Use RecipeAgentService to process full recipe
        # We'll use the existing _convert_to_rcip method
        agent = RecipeAgentService()
        user = User.objects.get(id=user_id)

        user_preferences = {
            'dietary_restrictions': user.dietary_restrictions,
            'allergies': user.allergies,
            'language': user_language,
            'unit_system': 'metric' if getattr(user, 'weight_unit', 'kg') == 'kg' else 'imperial'
        }

        logger.info(
            "[BACKGROUND RECIPE] Converting scraped data to RCIP format...")

        # Convert to RCIP (includes IML enrichment, step extraction, etc.)
        rcip_recipe = async_to_sync(agent._convert_to_rcip)(
            scraped_data,
            recipe_name,
            user_preferences
        )

        if not rcip_recipe:
            logger.error("[BACKGROUND RECIPE] ❌ RCIP conversion failed")
            raise Exception("Failed to convert recipe to RCIP format")

        logger.info(f"[BACKGROUND RECIPE] ✅ RCIP conversion complete")
        logger.info(
            f"[BACKGROUND RECIPE] Recipe: {rcip_recipe['meta']['name']}")
        logger.info(
            f"[BACKGROUND RECIPE] Ingredients: {len(rcip_recipe.get('base_ingredients', []))}")
        logger.info(
            f"[BACKGROUND RECIPE] Steps: {len(rcip_recipe.get('base_steps', []))}")

        # STEP 3: Translate to REMAINING languages (exclude user's language)
        all_languages = ['en', 'ru', 'he']
        remaining_languages = [
            lang for lang in all_languages if lang != user_language]

        logger.info(
            f"[BACKGROUND RECIPE] Translating to remaining languages: {remaining_languages}")

        for lang in remaining_languages:
            try:
                logger.info(f"[BACKGROUND RECIPE] Translating to {lang}...")
                rcip_recipe = async_to_sync(
                    agent._translate_recipe)(rcip_recipe, lang)
                logger.info(f"[BACKGROUND RECIPE] ✅ Translated to {lang}")
            except Exception as e:
                logger.warning(
                    f"[BACKGROUND RECIPE] ⚠️ Translation to {lang} failed: {e}")

        # STEP 4: Create CanonicalRecipe
        logger.info("[BACKGROUND RECIPE] Creating CanonicalRecipe...")

        canonical = async_to_sync(agent._create_canonical_recipe)(
            rcip_recipe,
            source_type='ai_generated',  # Same as discovery agent - AI extracted from web
            original_creator=user
        )

        logger.info(
            f"[BACKGROUND RECIPE] ✅ Created CanonicalRecipe: {canonical.name} (ID: {canonical.id})")

        # STEP 5: Create user fork
        logger.info("[BACKGROUND RECIPE] Creating user fork...")

        user_recipe = async_to_sync(agent._create_user_fork)(
            canonical,
            user,
            user_modifications={}
        )

        logger.info(
            f"[BACKGROUND RECIPE] ✅ Created user fork (ID: {user_recipe.id})")

        # STEP 6: Shopping list linked via WebSocket notification
        shopping_list = ShoppingList.objects.get(id=shopping_list_id)

        logger.info(f"[BACKGROUND RECIPE] ✅ Recipe created successfully")

        # STEP 7: Send WebSocket notification
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync as sync

            channel_layer = get_channel_layer()
            group_name = f"shopping_list_{shopping_list_id}"

            sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'recipe_completed',
                    'data': {
                        'canonical_recipe_id': str(canonical.id),
                        'recipe_name': canonical.name,
                        'user_recipe_id': str(user_recipe.id),
                        'message': f"Full recipe ready: {canonical.name}"
                    }
                }
            )

            logger.info(f"[BACKGROUND RECIPE] ✅ Sent WebSocket notification")
        except Exception as ws_error:
            logger.warning(
                f"[BACKGROUND RECIPE] WebSocket notification failed: {ws_error}")

        return {
            'status': 'created',
            'canonical_recipe_id': str(canonical.id),
            'user_recipe_id': str(user_recipe.id),
            'recipe_name': canonical.name
        }

    except Exception as e:
        logger.error(f"[BACKGROUND RECIPE] ❌ Task failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(
                f"[BACKGROUND RECIPE] Retrying... (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)

        return {
            'status': 'failed',
            'error': str(e)
        }
