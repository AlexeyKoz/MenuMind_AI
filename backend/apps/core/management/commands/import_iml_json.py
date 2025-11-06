"""
Management command to import IML ingredients from JSON export file
Usage: python manage.py import_iml_json
"""
from django.core.management.base import BaseCommand
from apps.core.models import IngredientCache, IngredientTranslation
import json
import os


class Command(BaseCommand):
    help = 'Import ingredients from IML JSON export file'

    def handle(self, *args, **options):
        # Try multiple possible paths
        possible_paths = [
            'backend/data/iml_export.json',
            'data/iml_export.json',
            '/app/backend/data/iml_export.json',
            '/app/data/iml_export.json',
        ]
        
        json_file = None
        for path in possible_paths:
            if os.path.exists(path):
                json_file = path
                break
        
        if not json_file:
            self.stdout.write(self.style.ERROR(f'File not found. Tried: {possible_paths}'))
            return

        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('IML JSON IMPORT'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

        # Load JSON data
        self.stdout.write('Loading JSON file...')
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        ingredients = data.get('ingredients', [])
        total = len(ingredients)
        
        self.stdout.write(f'Found {total} ingredients in JSON file\n')
        self.stdout.write('[START] Importing ingredients...\n')

        created_count = 0
        updated_count = 0
        error_count = 0

        for idx, ing_data in enumerate(ingredients, 1):
            if idx % 100 == 0:
                self.stdout.write(f'Progress: {idx}/{total} ({(idx/total)*100:.1f}%)')

            try:
                metadata = ing_data.get('metadata', {})
                
                # Get the ingredient key
                ingredient_key = ing_data.get('ingredient_key', '')
                if not ingredient_key:
                    # Try to get from metadata
                    ingredient_key = metadata.get('key', '') or str(metadata.get('id', ''))
                
                if not ingredient_key:
                    error_count += 1
                    continue

                # Create or update IngredientCache
                ingredient, created = IngredientCache.objects.update_or_create(
                    ingredient_key=ingredient_key,
                    defaults={
                        'category': ing_data.get('category', 'other'),
                        'source': ing_data.get('source', 'unknown'),
                        'common_units': ing_data.get('common_units', {}),
                        'unit_conversions': ing_data.get('unit_conversions', {}),
                        'shelf_life': ing_data.get('shelf_life', {}),
                        'storage_recommendations': ing_data.get('storage_recommendations', {}),
                        'nutrition_per_100g': ing_data.get('nutrition_per_100g', {}),
                        'typical_amount_min': ing_data.get('typical_amount_min'),
                        'typical_amount_max': ing_data.get('typical_amount_max'),
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

                # Create translations
                name_en = metadata.get('name_en', '')
                name_ru = metadata.get('name_ru', '')
                name_he = metadata.get('name_he', '')

                if name_en:
                    IngredientTranslation.objects.update_or_create(
                        ingredient=ingredient,
                        language='en',  # Fixed: use 'language' not 'language_code'
                        defaults={'name': name_en}
                    )

                if name_ru:
                    IngredientTranslation.objects.update_or_create(
                        ingredient=ingredient,
                        language='ru',  # Fixed: use 'language' not 'language_code'
                        defaults={'name': name_ru}
                    )

                if name_he:
                    IngredientTranslation.objects.update_or_create(
                        ingredient=ingredient,
                        language='he',  # Fixed: use 'language' not 'language_code'
                        defaults={'name': name_he}
                    )

            except Exception as e:
                error_count += 1
                if error_count <= 10:  # Only show first 10 errors
                    self.stdout.write(self.style.ERROR(f'Error on item {idx}: {str(e)}'))

        # Final summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('[COMPLETE] Import finished!\n'))
        self.stdout.write(f'   Total processed: {total}')
        self.stdout.write(f'   Created: {created_count}')
        self.stdout.write(f'   Updated: {updated_count}')
        self.stdout.write(f'   Errors: {error_count}\n')

        # Show final stats
        total_ingredients = IngredientCache.objects.count()
        total_translations = IngredientTranslation.objects.count()
        trans_en = IngredientTranslation.objects.filter(language='en').count()  # Fixed
        trans_ru = IngredientTranslation.objects.filter(language='ru').count()  # Fixed
        trans_he = IngredientTranslation.objects.filter(language='he').count()  # Fixed

        self.stdout.write('[STATS] Current database state:')
        self.stdout.write(f'   Total ingredients: {total_ingredients}')
        self.stdout.write(f'   Total translations: {total_translations}')
        self.stdout.write(f'     - EN: {trans_en}')
        self.stdout.write(f'     - RU: {trans_ru}')
        self.stdout.write(f'     - HE: {trans_he}\n')
        
        self.stdout.write(self.style.SUCCESS('='*60))

