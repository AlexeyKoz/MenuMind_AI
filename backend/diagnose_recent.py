from apps.recipes.models import CanonicalRecipe, RecipeTranslation
from django.utils import timezone
import re

# Search for recent recipes (last 24 hours)
recent_recipes = CanonicalRecipe.objects.filter(
    created_at__gte=timezone.now() - timezone.timedelta(hours=24)
).order_by('-created_at')[:5]

print("=" * 80)
print("RECENT RECIPES (Last 24 hours)")
print("=" * 80)

for recipe in recent_recipes:
    print(f"\nID: {recipe.id}")
    print(f"Name: {recipe.name}")
    print(f"Created: {recipe.created_at}")
    print(f"Source: {recipe.source_type}")
    print(f"Language: {recipe.source_language}")
    print(f"AI: {recipe.ai_provider}")

    if recipe.base_ingredients:
        first_ing = recipe.base_ingredients[0]
        print(
            f"First ingredient: {first_ing.get('amount', first_ing.get('quantity', 'N/A'))} {first_ing.get('unit', 'N/A')} {first_ing.get('name', 'N/A')}")

    if recipe.base_steps:
        first_step = recipe.base_steps[0].get(
            'instruction', recipe.base_steps[0].get('text', 'N/A'))
        print(f"First step: {first_step[:80]}...")

# Now check for any recipe with "roll" or Japanese ingredients
print("\n\n" + "=" * 80)
print("SEARCHING FOR SUSHI/ROLL RECIPES")
print("=" * 80)

roll_recipes = CanonicalRecipe.objects.filter(
    name__icontains='roll'
).order_by('-created_at')[:3]

for recipe in roll_recipes:
    print(f"\nName: {recipe.name}")
    print(f"Created: {recipe.created_at}")
    print(f"Source: {recipe.source_type}, Language: {recipe.source_language}")

    # Check translations
    translations = RecipeTranslation.objects.filter(canonical_recipe=recipe)
    for trans in translations:
        print(f"  - Translation: {trans.language} ({trans.status})")
        if trans.language == 'ru' and trans.base_steps:
            first_step = trans.base_steps[0].get(
                'instruction', trans.base_steps[0].get('text', 'N/A'))
            print(f"    Russian step 1: {first_step[:100]}...")

            # Check for English words in Russian text
            english_pattern = re.compile(r'[A-Za-z]{3,}')
            english_words = english_pattern.findall(first_step)
            if english_words:
                print(f"    ⚠️ FOUND ENGLISH WORDS: {english_words[:5]}")

        if trans.language == 'ru' and trans.base_ingredients:
            first_ing = trans.base_ingredients[0]
            unit = first_ing.get('unit', 'N/A')
            print(f"    Russian ingredient 1 unit: {unit}")
            if unit in ['oz', 'as', 'cup', 'tbsp', 'tsp']:
                print(f"    ⚠️ UNIT NOT TRANSLATED: {unit}")

print("\n\n" + "=" * 80)
print("ROOT CAUSE SUMMARY")
print("=" * 80)
print("""
KEY FINDINGS:
1. Check if recipe.source_language is 'en' but being served to Russian users
   → This means English recipe is being poorly translated
   
2. Check if translations have English words in Russian text
   → Translation service is failing
   
3. Check if ingredients have untranslated units
   → Unit translation not working

SOLUTION NEEDED:
- Generate recipes DIRECTLY in target language (don't generate in English then translate)
- Use full AI translation (not just cooking terms)
- Validate output has NO English before saving
""")
