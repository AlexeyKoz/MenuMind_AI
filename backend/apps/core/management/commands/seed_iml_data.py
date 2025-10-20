"""
Management command to seed sample IML ingredient data
Usage: python manage.py seed_iml_data
"""
from django.core.management.base import BaseCommand
from apps.core.models import IngredientCache, IngredientTranslation
from django.utils import timezone


class Command(BaseCommand):
    help = 'Seed sample IML ingredient data for testing'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('Seeding IML Ingredient Data'))
        self.stdout.write('='*70 + '\n')

        # Sample ingredients data
        ingredients_data = [
            {
                'ingredient_key': 'tomatoes-red-ripe',
                'category': 'vegetables',
                'source': 'usda',
                'common_units': {'weight': ['g', 'kg'], 'volume': ['ml', 'L'], 'count': ['pcs']},
                'unit_conversions': {'1_pcs': '150g', '1_cup': '180g'},
                'shelf_life': {'room_temperature': 2, 'refrigerator': 7, 'freezer': 180},
                'storage_recommendations': {'recommended': 'refrigerator', 'temperature_range': '4-10°C'},
                'nutrition_per_100g': {
                    'calories': 18,
                    'protein': 0.9,
                    'fat': 0.2,
                    'carbohydrates': 3.9,
                    'fiber': 1.2,
                    'sugar': 2.6
                },
                'translations': {
                    'en': {'name': 'Tomato', 'description': 'Fresh ripe tomato', 'aliases': ['tomato', 'red tomato']},
                    'ru': {'name': 'Помидор', 'description': 'Свежий спелый помидор', 'aliases': ['помидор', 'томат']},
                    'he': {'name': 'עגבנייה', 'description': 'עגבנייה בשלה טרייה', 'aliases': ['עגבנייה']}
                }
            },
            {
                'ingredient_key': 'onions-yellow',
                'category': 'vegetables',
                'source': 'usda',
                'common_units': {'weight': ['g', 'kg'], 'count': ['pcs']},
                'unit_conversions': {'1_pcs': '110g', '1_cup_chopped': '160g'},
                'shelf_life': {'room_temperature': 14, 'refrigerator': 30, 'freezer': 180},
                'storage_recommendations': {'recommended': 'room_temperature', 'temperature_range': '15-20°C'},
                'nutrition_per_100g': {
                    'calories': 40,
                    'protein': 1.1,
                    'fat': 0.1,
                    'carbohydrates': 9.3,
                    'fiber': 1.7,
                    'sugar': 4.2
                },
                'translations': {
                    'en': {'name': 'Onion', 'description': 'Yellow onion', 'aliases': ['onion', 'yellow onion']},
                    'ru': {'name': 'Лук', 'description': 'Желтый лук', 'aliases': ['лук', 'репчатый лук']},
                    'he': {'name': 'בצל', 'description': 'בצל צהוב', 'aliases': ['בצל']}
                }
            },
            {
                'ingredient_key': 'chicken-breast',
                'category': 'meat',
                'source': 'usda',
                'common_units': {'weight': ['g', 'kg']},
                'unit_conversions': {'1_breast': '200g'},
                'shelf_life': {'refrigerator': 2, 'freezer': 270},
                'storage_recommendations': {'recommended': 'freezer', 'temperature_range': '-18°C'},
                'nutrition_per_100g': {
                    'calories': 165,
                    'protein': 31.0,
                    'fat': 3.6,
                    'carbohydrates': 0,
                    'fiber': 0,
                    'sugar': 0
                },
                'translations': {
                    'en': {'name': 'Chicken Breast', 'description': 'Skinless chicken breast', 'aliases': ['chicken', 'chicken breast', 'breast']},
                    'ru': {'name': 'Куриная грудка', 'description': 'Куриная грудка без кожи', 'aliases': ['курица', 'куриная грудка', 'грудка']},
                    'he': {'name': 'חזה עוף', 'description': 'חזה עוף ללא עור', 'aliases': ['עוף', 'חזה עוף']}
                }
            },
            {
                'ingredient_key': 'rice-white-long',
                'category': 'grains',
                'source': 'usda',
                'common_units': {'weight': ['g', 'kg'], 'volume': ['cups']},
                'unit_conversions': {'1_cup': '185g'},
                'shelf_life': {'room_temperature': 730, 'refrigerator': 1095},
                'storage_recommendations': {'recommended': 'room_temperature', 'temperature_range': '15-20°C'},
                'nutrition_per_100g': {
                    'calories': 130,
                    'protein': 2.7,
                    'fat': 0.3,
                    'carbohydrates': 28.2,
                    'fiber': 0.4,
                    'sugar': 0.1
                },
                'translations': {
                    'en': {'name': 'White Rice', 'description': 'Long grain white rice', 'aliases': ['rice', 'white rice']},
                    'ru': {'name': 'Белый рис', 'description': 'Длиннозерный белый рис', 'aliases': ['рис', 'белый рис']},
                    'he': {'name': 'אורז לבן', 'description': 'אורז לבן גרעין ארוך', 'aliases': ['אורז', 'אורז לבן']}
                }
            },
            {
                'ingredient_key': 'milk-whole',
                'category': 'dairy',
                'source': 'usda',
                'common_units': {'volume': ['ml', 'L', 'cups']},
                'unit_conversions': {'1_cup': '244ml', '1_L': '1000ml'},
                'shelf_life': {'refrigerator': 7, 'freezer': 90},
                'storage_recommendations': {'recommended': 'refrigerator', 'temperature_range': '2-4°C'},
                'nutrition_per_100g': {
                    'calories': 61,
                    'protein': 3.2,
                    'fat': 3.3,
                    'carbohydrates': 4.8,
                    'fiber': 0,
                    'sugar': 5.1
                },
                'translations': {
                    'en': {'name': 'Milk', 'description': 'Whole milk', 'aliases': ['milk', 'whole milk']},
                    'ru': {'name': 'Молоко', 'description': 'Цельное молоко', 'aliases': ['молоко']},
                    'he': {'name': 'חלב', 'description': 'חלב מלא', 'aliases': ['חלב']}
                }
            },
            {
                'ingredient_key': 'eggs-chicken',
                'category': 'dairy',
                'source': 'usda',
                'common_units': {'count': ['pcs']},
                'unit_conversions': {'1_pcs': '50g', '1_dozen': '600g'},
                'shelf_life': {'refrigerator': 28, 'freezer': 270},
                'storage_recommendations': {'recommended': 'refrigerator', 'temperature_range': '2-4°C'},
                'nutrition_per_100g': {
                    'calories': 143,
                    'protein': 12.6,
                    'fat': 9.5,
                    'carbohydrates': 0.7,
                    'fiber': 0,
                    'sugar': 0.4
                },
                'translations': {
                    'en': {'name': 'Egg', 'description': 'Chicken egg', 'aliases': ['egg', 'eggs']},
                    'ru': {'name': 'Яйцо', 'description': 'Куриное яйцо', 'aliases': ['яйцо', 'яйца']},
                    'he': {'name': 'ביצה', 'description': 'ביצת עוף', 'aliases': ['ביצה', 'ביצים']}
                }
            },
            {
                'ingredient_key': 'potato-russet',
                'category': 'vegetables',
                'source': 'usda',
                'common_units': {'weight': ['g', 'kg'], 'count': ['pcs']},
                'unit_conversions': {'1_pcs': '200g'},
                'shelf_life': {'room_temperature': 14, 'refrigerator': 30},
                'storage_recommendations': {'recommended': 'room_temperature', 'temperature_range': '7-10°C'},
                'nutrition_per_100g': {
                    'calories': 77,
                    'protein': 2.0,
                    'fat': 0.1,
                    'carbohydrates': 17.5,
                    'fiber': 2.1,
                    'sugar': 0.8
                },
                'translations': {
                    'en': {'name': 'Potato', 'description': 'Russet potato', 'aliases': ['potato', 'russet potato']},
                    'ru': {'name': 'Картофель', 'description': 'Картофель', 'aliases': ['картофель', 'картошка']},
                    'he': {'name': 'תפוח אדמה', 'description': 'תפוח אדמה', 'aliases': ['תפוח אדמה']}
                }
            },
            {
                'ingredient_key': 'carrots-raw',
                'category': 'vegetables',
                'source': 'usda',
                'common_units': {'weight': ['g', 'kg'], 'count': ['pcs']},
                'unit_conversions': {'1_pcs': '61g', '1_cup_chopped': '128g'},
                'shelf_life': {'refrigerator': 21, 'freezer': 270},
                'storage_recommendations': {'recommended': 'refrigerator', 'temperature_range': '0-4°C'},
                'nutrition_per_100g': {
                    'calories': 41,
                    'protein': 0.9,
                    'fat': 0.2,
                    'carbohydrates': 9.6,
                    'fiber': 2.8,
                    'sugar': 4.7
                },
                'translations': {
                    'en': {'name': 'Carrot', 'description': 'Fresh raw carrot', 'aliases': ['carrot', 'carrots']},
                    'ru': {'name': 'Морковь', 'description': 'Свежая морковь', 'aliases': ['морковь', 'морковка']},
                    'he': {'name': 'גזר', 'description': 'גזר טרי', 'aliases': ['גזר']}
                }
            }
        ]

        created_count = 0
        updated_count = 0

        for data in ingredients_data:
            # Create or update ingredient
            ingredient, created = IngredientCache.objects.update_or_create(
                ingredient_key=data['ingredient_key'],
                defaults={
                    'category': data['category'],
                    'source': data['source'],
                    'common_units': data['common_units'],
                    'unit_conversions': data['unit_conversions'],
                    'shelf_life': data['shelf_life'],
                    'storage_recommendations': data['storage_recommendations'],
                    'nutrition_per_100g': data['nutrition_per_100g'],
                    'metadata': data
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'  [+] Created: {data["ingredient_key"]}')
            else:
                updated_count += 1
                self.stdout.write(f'  [~] Updated: {data["ingredient_key"]}')

            # Create translations
            for lang, trans_data in data['translations'].items():
                translation, trans_created = IngredientTranslation.objects.update_or_create(
                    ingredient=ingredient,
                    language=lang,
                    defaults={
                        'name': trans_data['name'],
                        'description': trans_data.get('description', ''),
                        'aliases': trans_data.get('aliases', []),
                        'storage_tips': ''
                    }
                )

        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS(
            f'Created: {created_count} ingredients'))
        self.stdout.write(self.style.SUCCESS(
            f'Updated: {updated_count} ingredients'))
        self.stdout.write(self.style.SUCCESS(
            f'Total translations: {created_count * 3 + updated_count * 3}'))
        self.stdout.write('='*70 + '\n')
        self.stdout.write(self.style.SUCCESS(
            '[OK] IML data seeded successfully!'))
        self.stdout.write(
            '\nYou can now view the ingredients at: http://localhost:8000/admin/core/ingredientcache/\n')


