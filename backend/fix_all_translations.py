from apps.recipes.models import CanonicalRecipe, RecipeTranslation
from apps.core.models import IngredientCache
from apps.core.cooking_terms_service import CookingTermsTranslationService
from django.utils import timezone
import re
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
django.setup()


recipe_id = '643f87d9-d51e-4cfb-be63-bdcee55edc14'
recipe = CanonicalRecipe.objects.get(id=recipe_id)
cooking_terms_service = CookingTermsTranslationService()


def translate_recipe_to_language(recipe, target_language):
    """Translate recipe to target language"""

    # Delete existing translation
    RecipeTranslation.objects.filter(
        canonical_recipe=recipe, language=target_language).delete()

    # Create new translation
    translation = RecipeTranslation.objects.create(
        canonical_recipe=recipe,
        language=target_language,
        status='in_progress'
    )

    # Translate ingredients BY NAME
    translated_ingredients = []
    for ing in recipe.base_ingredients:
        translated_ing = ing.copy()
        ing_name = ing.get('name', '').lower().strip()

        if ing.get('ingredient_key'):
            try:
                ingredient_obj = IngredientCache.objects.get(
                    ingredient_key=ing['ingredient_key'])
                translations_dict = {}
                for trans in ingredient_obj.translations.all():
                    translations_dict[trans.language] = trans.name

                if target_language in translations_dict:
                    translated_ing['name'] = translations_dict[target_language]
            except IngredientCache.DoesNotExist:
                pass
        else:
            # Fallback: match by name
            normalized_name = re.sub(r'[-\s]+', '_', ing_name)

            try:
                ingredient_obj = IngredientCache.objects.filter(
                    ingredient_key=normalized_name
                ).first()

                if not ingredient_obj and ing_name:
                    ingredient_obj = IngredientCache.objects.filter(
                        ingredient_key__icontains=ing_name.split()[0]
                    ).first()

                if ingredient_obj:
                    translations_dict = {}
                    for trans in ingredient_obj.translations.all():
                        translations_dict[trans.language] = trans.name

                    if target_language in translations_dict:
                        translated_ing['name'] = translations_dict[target_language]
            except:
                pass

        translated_ingredients.append(translated_ing)

    # Translate steps - FIX: Check for both 'text' and 'instruction'
    translated_steps = []
    for step in recipe.base_steps:
        translated_step = step.copy()

        # Get step text from either 'text' or 'instruction'
        step_text = step.get('text') or step.get('instruction')

        if step_text:
            translated_text = cooking_terms_service.translate_text(
                step_text,
                target_language
            )
            # Update both fields to be safe
            if 'text' in translated_step:
                translated_step['text'] = translated_text
            if 'instruction' in translated_step:
                translated_step['instruction'] = translated_text

        translated_steps.append(translated_step)

    # Save translation
    translation.name = recipe.name
    translation.description = recipe.description
    translation.base_ingredients = translated_ingredients
    translation.base_steps = translated_steps
    translation.status = 'completed'
    translation.completed_at = timezone.now()
    translation.save()

    return translated_ingredients, translated_steps


# Create translations for all languages
print("Creating translations for Hebrew and Russian...")
for lang in ['he', 'ru']:
    print(f"\nTranslating to {lang}...")
    ing, steps = translate_recipe_to_language(recipe, lang)
    print(f"  Ingredients: {len(ing)}")
    print(f"  Steps: {len(steps)}")
    if steps and (steps[0].get('text') or steps[0].get('instruction')):
        step_text = steps[0].get('text') or steps[0].get('instruction')
        print(f"  First step preview: {step_text[:60]}...")

print("\nDONE! REFRESH YOUR BROWSER!")
