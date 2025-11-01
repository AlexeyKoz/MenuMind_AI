"""
Import IML and CookLingo data from JSON into PostgreSQL
"""
import os
import django
import json
from django.db import transaction

# Set up Django environment for PostgreSQL
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
os.environ['USE_POSTGRES'] = 'True'  # Use PostgreSQL
os.environ['DB_NAME'] = 'menumine_ai'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'password'
os.environ['DB_HOST'] = 'db'
os.environ['DB_PORT'] = '5432'
os.environ['SECRET_KEY'] = 'temp'
os.environ['DEBUG'] = 'True'

django.setup()

from apps.core.models import (
    IngredientCache, IngredientTranslation,
    CookingTermCache, CookingTermTranslation
)


def import_iml_data():
    """Import IML ingredients and translations"""
    print("\n" + "="*80)
    print("[IMPORT] Importing IML Data into PostgreSQL")
    print("="*80 + "\n")
    
    input_file = 'data/iml_export.json'
    
    if not os.path.exists(input_file):
        print(f"[ERROR] File not found: {input_file}")
        return False
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_ings = len(data['ingredients'])
        total_trans = len(data['ingredient_translations'])
        print(f"[INFO] Found {total_ings} ingredients to import")
        print(f"[INFO] Found {total_trans} translations to import")
        
        imported_ings = 0
        skipped_ings = 0
        imported_trans = 0
        skipped_trans = 0
        errors = []
        
        # Import ingredients
        print("\n[INFO] Importing ingredients...")
        ingredient_id_map = {}  # Map old IDs to new objects
        
        for i, ing_data in enumerate(data['ingredients'], 1):
            if i % 100 == 0:
                print(f"[PROGRESS] Processed {i}/{total_ings} ingredients...")
            
            try:
                with transaction.atomic():
                    # Check if ingredient already exists
                    ing, created = IngredientCache.objects.get_or_create(
                        ingredient_key=ing_data['ingredient_key'],
                        defaults={
                            'category': ing_data.get('category', ''),
                            'source': ing_data.get('source', ''),
                            'common_units': ing_data.get('common_units', {}),
                            'unit_conversions': ing_data.get('unit_conversions', {}),
                            'shelf_life': ing_data.get('shelf_life', {}),
                            'storage_recommendations': ing_data.get('storage_recommendations', {}),
                            'nutrition_per_100g': ing_data.get('nutrition_per_100g', {}),
                            'metadata': ing_data.get('metadata', {}),
                            'typical_amount_min': ing_data.get('typical_amount_min'),
                            'typical_amount_max': ing_data.get('typical_amount_max'),
                        }
                    )
                    
                    ingredient_id_map[ing_data['id']] = ing
                    
                    if created:
                        imported_ings += 1
                    else:
                        skipped_ings += 1
                        
            except Exception as e:
                error_msg = f"Ingredient '{ing_data.get('ingredient_key')}': {str(e)[:100]}"
                errors.append(error_msg)
                if len(errors) <= 5:
                    print(f"\n[WARN] Failed to import {error_msg}")
                continue
        
        # Import ingredient translations
        print(f"\n[INFO] Importing ingredient translations...")
        for i, trans_data in enumerate(data['ingredient_translations'], 1):
            if i % 100 == 0:
                print(f"[PROGRESS] Processed {i}/{total_trans} translations...")
            
            try:
                with transaction.atomic():
                    # Get the ingredient object
                    old_id = trans_data['ingredient_id']
                    if old_id not in ingredient_id_map:
                        continue  # Skip if ingredient wasn't imported
                    
                    ing = ingredient_id_map[old_id]
                    
                    # Check if translation already exists
                    trans, created = IngredientTranslation.objects.get_or_create(
                        ingredient=ing,
                        language=trans_data['language'],
                        defaults={
                            'name': trans_data.get('name', ''),
                            'description': trans_data.get('description', ''),
                            'aliases': trans_data.get('aliases', []),
                            'storage_tips': trans_data.get('storage_tips', ''),
                        }
                    )
                    
                    if created:
                        imported_trans += 1
                    else:
                        skipped_trans += 1
                        
            except Exception as e:
                error_msg = f"Translation: {str(e)[:100]}"
                errors.append(error_msg)
                if len(errors) <= 10:
                    print(f"\n[WARN] Failed to import {error_msg}")
                continue
        
        print(f"\n[SUCCESS] IML import complete!")
        print(f"[INFO] Imported: {imported_ings} ingredients, {imported_trans} translations")
        print(f"[INFO] Skipped (already exist): {skipped_ings} ingredients, {skipped_trans} translations")
        if errors:
            print(f"[INFO] Errors: {len(errors)} items (first 10 shown above)")
        
        # Verify
        total_ings = IngredientCache.objects.count()
        total_trans = IngredientTranslation.objects.count()
        print(f"\n[VERIFY] Database now contains:")
        print(f"  - Ingredients: {total_ings}")
        print(f"  - Ingredient Translations: {total_trans}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] IML import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def import_cooklingo_data():
    """Import CookLingo cooking terms and translations"""
    print("\n" + "="*80)
    print("[IMPORT] Importing CookLingo Data into PostgreSQL")
    print("="*80 + "\n")
    
    input_file = 'data/cooklingo_export.json'
    
    if not os.path.exists(input_file):
        print(f"[ERROR] File not found: {input_file}")
        return False
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_terms = len(data['cooking_terms'])
        total_trans = len(data['cooking_term_translations'])
        print(f"[INFO] Found {total_terms} cooking terms to import")
        print(f"[INFO] Found {total_trans} translations to import")
        
        imported_terms = 0
        skipped_terms = 0
        imported_trans = 0
        skipped_trans = 0
        errors = []
        
        # Import cooking terms
        print("\n[INFO] Importing cooking terms...")
        term_id_map = {}  # Map old IDs to new objects
        
        for i, term_data in enumerate(data['cooking_terms'], 1):
            if i % 100 == 0:
                print(f"[PROGRESS] Processed {i}/{total_terms} cooking terms...")
            
            try:
                with transaction.atomic():
                    # Check if term already exists
                    term, created = CookingTermCache.objects.get_or_create(
                        term_english=term_data['term_english'],
                        defaults={
                            'term_english_normalized': term_data.get('term_english_normalized', ''),
                            'term_type': term_data.get('term_type', ''),
                            'category': term_data.get('category', ''),
                            'definition': term_data.get('definition', ''),
                            'usage_frequency': term_data.get('usage_frequency', ''),
                            'difficulty_level': term_data.get('difficulty_level', ''),
                            'confidence_score': term_data.get('confidence_score', 0),
                            'verified': term_data.get('verified', False),
                        }
                    )
                    
                    term_id_map[term_data['id']] = term
                    
                    if created:
                        imported_terms += 1
                    else:
                        skipped_terms += 1
                        
            except Exception as e:
                error_msg = f"Term '{term_data.get('term_english')}': {str(e)[:100]}"
                errors.append(error_msg)
                if len(errors) <= 5:
                    print(f"\n[WARN] Failed to import {error_msg}")
                continue
        
        # Import cooking term translations
        print(f"\n[INFO] Importing cooking term translations...")
        for i, trans_data in enumerate(data['cooking_term_translations'], 1):
            if i % 100 == 0:
                print(f"[PROGRESS] Processed {i}/{total_trans} translations...")
            
            try:
                with transaction.atomic():
                    # Get the term object
                    old_id = trans_data['term_id']
                    if old_id not in term_id_map:
                        continue  # Skip if term wasn't imported
                    
                    term = term_id_map[old_id]
                    
                    # Check if translation already exists
                    trans, created = CookingTermTranslation.objects.get_or_create(
                        term=term,
                        language_code=trans_data['language_code'],
                        defaults={
                            'translation': trans_data.get('translation', ''),
                            'verification_status': trans_data.get('verification_status', 'unverified'),
                            'alternative_translations': trans_data.get('alternative_translations', []),
                            'cultural_notes': trans_data.get('cultural_notes', ''),
                            'source': trans_data.get('source', ''),
                            'confidence_score': trans_data.get('confidence_score', 0),
                        }
                    )
                    
                    if created:
                        imported_trans += 1
                    else:
                        skipped_trans += 1
                        
            except Exception as e:
                error_msg = f"Translation: {str(e)[:100]}"
                errors.append(error_msg)
                if len(errors) <= 10:
                    print(f"\n[WARN] Failed to import {error_msg}")
                continue
        
        print(f"\n[SUCCESS] CookLingo import complete!")
        print(f"[INFO] Imported: {imported_terms} cooking terms, {imported_trans} translations")
        print(f"[INFO] Skipped (already exist): {skipped_terms} terms, {skipped_trans} translations")
        if errors:
            print(f"[INFO] Errors: {len(errors)} items (first 10 shown above)")
        
        # Verify
        total_terms = CookingTermCache.objects.count()
        total_trans = CookingTermTranslation.objects.count()
        print(f"\n[VERIFY] Database now contains:")
        print(f"  - Cooking Terms: {total_terms}")
        print(f"  - Cooking Term Translations: {total_trans}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] CookLingo import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "="*80)
    print("Starting IML and CookLingo Data Import to PostgreSQL")
    print("="*80)
    
    iml_success = import_iml_data()
    cooklingo_success = import_cooklingo_data()
    
    print("\n" + "="*80)
    if iml_success and cooklingo_success:
        print("ALL IMPORTS SUCCESSFUL!")
    else:
        print("SOME IMPORTS FAILED!")
        if not iml_success:
            print("  - IML import failed")
        if not cooklingo_success:
            print("  - CookLingo import failed")
    print("="*80 + "\n")

