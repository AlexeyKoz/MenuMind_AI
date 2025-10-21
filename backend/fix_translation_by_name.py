import re
from django.utils import timezone
from apps.core.cooking_terms_service import CookingTermsTranslationService
from apps.core.models import IngredientCache
from apps.recipes.models import CanonicalRecipe, RecipeTranslation
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
django.setup()


recipe_id = '643f87d9-d51e-4cfb-be63-bdcee55edc14'
target_language = 'he'

recipe = CanonicalRecipe.objects.get(id=recipe_id)
cooking_terms_service = CookingTermsTranslationService()

# Delete existing bad translation
RecipeTranslation.objects.filter(
    canonical_recipe=recipe, language=target_language).delete()

# Create new translation
translation = RecipeTranslation.objects.create(
    canonical_recipe=recipe,
    language=target_language,
    status='in_progress'
)

# Translate ingredients BY NAME (fallback for old recipes without ingredient_keys)
translated_ingredients = []
for ing in recipe.base_ingredients:
    translated_ing = ing.copy()
    ing_name = ing.get('name', '').lower().strip()

    # Try to find by ingredient_key first
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
        # Fallback: Try to match by name
        # Normalize name: remove dashes, hyphens
        normalized_name = re.sub(r'[-\s]+', '_', ing_name)

        try:
            # Try exact match first
            ingredient_obj = IngredientCache.objects.filter(
                ingredient_key=normalized_name
            ).first()

            if not ingredient_obj:
                # Try contains match
                ingredient_obj = IngredientCache.objects.filter(
                    ingredient_key__icontains=ing_name.split()[
                        0] if ing_name else ''
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

# Translate steps
translated_steps = []
for step in recipe.base_steps:
    translated_step = step.copy()

    if step.get('text'):
        translated_step['text'] = cooking_terms_service.translate_text(
            step['text'],
            target_language
        )

    translated_steps.append(translated_step)

# Save translation
translation.name = recipe.name
translation.description = recipe.description
translation.base_ingredients = translated_ingredients
translation.base_steps = translated_steps
translation.status = 'completed'
translation.completed_at = timezone.now()
translation.save()

with open('translation_final.txt', 'w', encoding='utf-8') as f:
    f.write(f"Translation created!\n")
    f.write(f"Ingredients: {len(translated_ingredients)}\n\n")
    for i, ing in enumerate(translated_ingredients[:5]):
        f.write(f"{i+1}. {ing['name']}\n")

print("Translation created! Check translation_final.txt and refresh browser")
