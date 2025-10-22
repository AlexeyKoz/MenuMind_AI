from apps.recipes.models import CanonicalRecipe, RecipeTranslation
from django.utils import timezone
import re
import json

# Find Philadelphia Roll
recipe = CanonicalRecipe.objects.filter(
    name__icontains='Philadelphia').order_by('-created_at').first()

if not recipe:
    print("Recipe not found!")
else:
    print("=" * 80)
    print("🔍 PHILADELPHIA ROLL RECIPE - ROOT CAUSE INVESTIGATION")
    print("=" * 80)

    print(f"\n📋 BASIC INFO:")
    print(f"ID: {recipe.id}")
    print(f"Name: {recipe.name}")
    print(f"Created: {recipe.created_at}")
    print(f"Source Type: {recipe.source_type}")
    print(f"AI Provider: {recipe.ai_provider}")

    hours_old = (timezone.now() - recipe.created_at).total_seconds() / 3600
    print(f"Age: {hours_old:.1f} hours old")

    print(f"\n🥘 INGREDIENTS (English base - first 3):")
    for idx, ing in enumerate(recipe.base_ingredients[:3], 1):
        amount = ing.get('amount', ing.get('quantity', 'N/A'))
        unit = ing.get('unit', 'N/A')
        name = ing.get('name', 'N/A')
        print(f"{idx}. {amount} {unit} {name}")
        if unit in ['oz', 'ounce', 'cup', 'cups']:
            print(f"   ⚠️ IMPERIAL UNIT: {unit}")

    print(f"\n📝 STEPS (English base - first 2):")
    for idx, step in enumerate(recipe.base_steps[:2], 1):
        instruction = step.get('instruction', step.get('text', 'N/A'))
        print(f"{idx}. {instruction[:100]}...")

    print(f"\n🌍 TRANSLATIONS:")
    translations = RecipeTranslation.objects.filter(canonical_recipe=recipe)

    for trans in translations:
        print(f"\n  Language: {trans.language} ({trans.status})")
        print(f"  Created: {trans.created_at}")
        print(f"  Name: {trans.name}")

        if trans.language == 'ru':
            print(f"\n  🇷🇺 RUSSIAN TRANSLATION ANALYSIS:")

            # Check ingredients
            print(f"  Ingredients (first 3):")
            for idx, ing in enumerate(trans.base_ingredients[:3], 1):
                amount = ing.get('amount', ing.get('quantity', 'N/A'))
                unit = ing.get('unit', 'N/A')
                name = ing.get('name', ing.get('display_name', {}).get(
                    'ru', 'N/A') if isinstance(ing.get('display_name'), dict) else 'N/A')
                print(f"    {idx}. {amount} {unit} {name}")

                if unit and any(c.isalpha() and ord(c) < 128 for c in unit):
                    print(
                        f"       ⚠️⚠️⚠️ UNIT IN ENGLISH: '{unit}' - NOT TRANSLATED!")

            # Check steps for English words
            print(f"\n  Steps (first 3):")
            for idx, step in enumerate(trans.base_steps[:3], 1):
                instruction = step.get('instruction', step.get('text', 'N/A'))
                print(f"    {idx}. {instruction[:100]}...")

                # Find English words (3+ consecutive Latin letters)
                english_pattern = re.compile(r'\\b[A-Za-z]{3,}\\b')
                english_words = english_pattern.findall(instruction)

                if english_words:
                    print(
                        f"       ⚠️⚠️⚠️ ENGLISH WORDS FOUND: {', '.join(english_words[:7])}")

    print("\n\n" + "=" * 80)
    print("🎯 ROOT CAUSE ANALYSIS")
    print("=" * 80)

    has_english_in_russian = False
    has_untranslated_units = False

    ru_trans = RecipeTranslation.objects.filter(
        canonical_recipe=recipe, language='ru').first()
    if ru_trans:
        # Check for English in Russian steps
        for step in ru_trans.base_steps:
            instruction = step.get('instruction', step.get('text', ''))
            if re.search(r'\\b[A-Za-z]{3,}\\b', instruction):
                has_english_in_russian = True
                break

        # Check for untranslated units
        for ing in ru_trans.base_ingredients:
            unit = ing.get('unit', '')
            if unit and any(c.isalpha() and ord(c) < 128 for c in unit):
                has_untranslated_units = True
                break

    print("\n📊 ISSUES FOUND:")
    if has_english_in_russian:
        print("❌ 1. RUSSIAN TRANSLATIONS CONTAIN ENGLISH WORDS")
        print("   Cause: Translation service is word-by-word, not sentence-level")
        print(
            "   Fix: Must use full AI translation (Gemini/Groq), not CookingTerms service")
    else:
        print("✅ 1. No English words in Russian (Good!)")

    if has_untranslated_units:
        print("❌ 2. UNITS NOT TRANSLATED (oz, cup, etc.)")
        print("   Cause: Unit translation not being applied")
        print("   Fix: Must translate units when serving recipe")
    else:
        print("✅ 2. Units are translated (Good!)")

    print(f"\n⏰ Age: {hours_old:.1f} hours")
    if hours_old > 2:
        print("   ⚠️ This recipe was generated BEFORE recent fixes")
        print("   → Need to generate NEW recipe to test fixes!")

    print("\n" + "=" * 80)
    print("💡 SOLUTION")
    print("=" * 80)
    print("""
The REAL problem is:
1. Recipe is generated in ENGLISH first
2. Then "translated" to Russian using weak translation service
3. Translation service only translates cooking terms, not full sentences
4. This leaves English verbs mixed with Russian nouns

THE FIX THAT WILL ACTUALLY WORK:
→ Generate recipes DIRECTLY in Russian language (don't translate after)
→ Pass target language to AI at generation time
→ AI generates pure Russian from the start
→ No translation layer needed!
""")
