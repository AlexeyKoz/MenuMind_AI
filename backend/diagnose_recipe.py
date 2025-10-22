from apps.recipes.models import CanonicalRecipe, RecipeTranslation
from django.utils import timezone

# Find the Philadelphia roll recipe
recipe = CanonicalRecipe.objects.filter(
    name__icontains='Филадельфия').order_by('-created_at').first()

if recipe:
    print("=" * 80)
    print("RECIPE DETAILS")
    print("=" * 80)
    print(f"ID: {recipe.id}")
    print(f"Name: {recipe.name}")
    print(f"Created: {recipe.created_at}")
    print(f"Source Type: {recipe.source_type}")
    print(f"Source Language: {recipe.source_language}")
    print(f"Generated with AI: {recipe.ai_provider}")

    print("\n" + "=" * 80)
    print("INGREDIENTS (First 3)")
    print("=" * 80)
    for idx, ing in enumerate(recipe.base_ingredients[:3], 1):
        print(f"{idx}. Amount: {ing.get('amount', ing.get('quantity', 'N/A'))}, Unit: {ing.get('unit', 'N/A')}, Name: {ing.get('name', 'N/A')}")

    print("\n" + "=" * 80)
    print("STEPS (First 3)")
    print("=" * 80)
    for idx, step in enumerate(recipe.base_steps[:3], 1):
        instruction = step.get('instruction', step.get('text', 'N/A'))
        print(f"{idx}. {instruction[:100]}...")

    print("\n" + "=" * 80)
    print("TRANSLATIONS")
    print("=" * 80)
    translations = RecipeTranslation.objects.filter(canonical_recipe=recipe)
    for trans in translations:
        print(f"\nLanguage: {trans.language}")
        print(f"Status: {trans.status}")
        print(f"Created: {trans.created_at}")
        if trans.base_ingredients:
            print(
                f"First ingredient unit: {trans.base_ingredients[0].get('unit', 'N/A') if trans.base_ingredients else 'N/A'}")
        if trans.base_steps:
            first_step = trans.base_steps[0].get('instruction', trans.base_steps[0].get(
                'text', 'N/A')) if trans.base_steps else 'N/A'
            print(f"First step (first 100 chars): {first_step[:100]}...")

    print("\n" + "=" * 80)
    print("ROOT CAUSE ANALYSIS")
    print("=" * 80)

    # Check if this is inventory-generated
    if recipe.source_type == 'ai_inventory':
        print("✓ Recipe source: AI Inventory Generator")
        print("  This recipe was generated from user's inventory items")
    elif recipe.source_type == 'user_created':
        print("✓ Recipe source: User Created (Recipe Builder)")
    elif recipe.source_type == 'ai_discovered':
        print("✓ Recipe source: AI Web Scraper")

    # Check creation date
    hours_old = (timezone.now() - recipe.created_at).total_seconds() / 3600
    print(f"✓ Recipe age: {hours_old:.1f} hours old")
    if hours_old > 2:
        print("  ⚠️ WARNING: This recipe is OLD - generated before recent fixes!")
        print("  → Solution: Generate a NEW recipe to test fixes")

    # Check language
    if recipe.source_language != 'ru':
        print(f"✓ Source language: {recipe.source_language}")
        print("  ⚠️ WARNING: Recipe was generated in English, then translated!")
        print("  → This is why we have mixed English/Russian")
        print("  → Solution: Generate recipes DIRECTLY in Russian")

else:
    print("Recipe not found!")
