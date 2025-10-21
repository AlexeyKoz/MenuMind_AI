import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
django.setup()

from apps.recipes.models import CanonicalRecipe, RecipeTranslation

r = CanonicalRecipe.objects.latest('created_at')
print(f'Canonical recipe name: {r.name}')
print(f'ID: {r.id}')
print(f'Original language: {r.original_language}')

print(f'\nAll translations:')
for t in RecipeTranslation.objects.filter(canonical_recipe=r):
    print(f'\n{t.language} ({t.status}):')
    print(f'  name: {t.name}')
    print(f'  ingredients count: {len(t.base_ingredients) if t.base_ingredients else 0}')
    print(f'  steps count: {len(t.base_steps) if t.base_steps else 0}')

