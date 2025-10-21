import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
django.setup()

from apps.recipes.models import CanonicalRecipe, RecipeTranslation

r = CanonicalRecipe.objects.latest('created_at')

# Write to file to avoid console encoding issues
with open('recipe_names.txt', 'w', encoding='utf-8') as f:
    f.write(f'Canonical recipe name: {r.name}\n')
    f.write(f'ID: {r.id}\n\n')
    
    f.write('Translations:\n')
    for t in RecipeTranslation.objects.filter(canonical_recipe=r):
        f.write(f'\n{t.language}:\n')
        f.write(f'  name: {t.name}\n')

print('Wrote to recipe_names.txt')



