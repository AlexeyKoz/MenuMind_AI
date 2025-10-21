import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
django.setup()

from apps.recipes.models import CanonicalRecipe, RecipeTranslation
from apps.core.smart_translator import SmartTranslationService

r = CanonicalRecipe.objects.latest('created_at')
print(f'Recipe name (Russian): {r.name}')

# Fix English translation
translator = SmartTranslationService()
en_name = translator.translate_recipe_name(r.name, 'en')
print(f'English translation: {en_name}')

# Update the translation
en_trans = RecipeTranslation.objects.filter(canonical_recipe=r, language='en').first()
if en_trans:
    en_trans.name = en_name
    en_trans.save()
    print(f'Updated English translation in DB: {en_trans.name}')

# Fix Hebrew translation too
he_trans = RecipeTranslation.objects.filter(canonical_recipe=r, language='he').first()
if he_trans:
    he_name = translator.translate_recipe_name(r.name, 'he')
    print(f'Hebrew translation: {he_name}')
    he_trans.name = he_name
    he_trans.save()
    print(f'Updated Hebrew translation in DB: {he_trans.name}')

print('\nDone!')

