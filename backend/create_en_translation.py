import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
django.setup()

from apps.recipes.models import CanonicalRecipe, RecipeTranslation
from apps.recipes.tasks import translate_recipe_to_language

r = CanonicalRecipe.objects.latest('created_at')
print(f'Recipe: {r.name}')
print(f'ID: {r.id}')
print(f'Original language: {r.original_language}')

# Create English translation
print(f'\nCreating English translation...')
translate_recipe_to_language(str(r.id), 'en')

# Check result
en_trans = RecipeTranslation.objects.filter(canonical_recipe=r, language='en').first()
if en_trans:
    print(f'SUCCESS: {en_trans.name}')
else:
    print('FAILED!')

