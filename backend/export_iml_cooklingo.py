"""
Export IML and CookLingo data from SQLite to JSON for PostgreSQL import
"""
import os
import django
import json

# Set up Django environment for SQLite
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
os.environ['USE_POSTGRES'] = 'False'  # Use SQLite
os.environ['SECRET_KEY'] = 'temp'
os.environ['DEBUG'] = 'True'

django.setup()

from apps.core.models import (
    IngredientCache, IngredientTranslation,
    CookingTermCache, CookingTermTranslation
)


def export_iml_data():
    """Export IML ingredients and translations"""
    print("\n" + "="*80)
    print("[EXPORT] Exporting IML Data from SQLite")
    print("="*80 + "\n")
    
    data = {
        'ingredients': [],
        'ingredient_translations': []
    }
    
    try:
        # Export ingredients
        ingredients = IngredientCache.objects.all()
        total = ingredients.count()
        print(f"[INFO] Found {total} ingredients")
        
        for i, ing in enumerate(ingredients, 1):
            if i % 100 == 0:
                print(f"[PROGRESS] Exported {i}/{total} ingredients...")
            
            data['ingredients'].append({
                'id': ing.id,
                'ingredient_key': ing.ingredient_key,
                'category': ing.category,
                'source': ing.source,
                'common_units': ing.common_units,
                'unit_conversions': ing.unit_conversions,
                'shelf_life': ing.shelf_life,
                'storage_recommendations': ing.storage_recommendations,
                'nutrition_per_100g': ing.nutrition_per_100g,
                'metadata': ing.metadata,
                'typical_amount_min': ing.typical_amount_min,
                'typical_amount_max': ing.typical_amount_max,
            })
        
        # Export ingredient translations
        translations = IngredientTranslation.objects.all()
        total_trans = translations.count()
        print(f"[INFO] Found {total_trans} ingredient translations")
        
        for i, trans in enumerate(translations, 1):
            if i % 100 == 0:
                print(f"[PROGRESS] Exported {i}/{total_trans} translations...")
            
            data['ingredient_translations'].append({
                'ingredient_id': trans.ingredient_id,
                'language': trans.language,
                'name': trans.name,
                'description': trans.description,
                'aliases': trans.aliases,
                'storage_tips': trans.storage_tips,
            })
        
        # Save to JSON
        output_file = 'data/iml_export.json'
        os.makedirs('data', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=True, indent=2)  # Use ensure_ascii=True to escape all non-ASCII
        
        print(f"\n[SUCCESS] Exported IML data to: {output_file}")
        print(f"[INFO] Ingredients: {len(data['ingredients'])}")
        print(f"[INFO] Translations: {len(data['ingredient_translations'])}")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] IML export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_cooklingo_data():
    """Export CookLingo cooking terms and translations"""
    print("\n" + "="*80)
    print("[EXPORT] Exporting CookLingo Data from SQLite")
    print("="*80 + "\n")
    
    data = {
        'cooking_terms': [],
        'cooking_term_translations': []
    }
    
    try:
        # Export cooking terms
        terms = CookingTermCache.objects.all()
        total = terms.count()
        print(f"[INFO] Found {total} cooking terms")
        
        for i, term in enumerate(terms, 1):
            if i % 100 == 0:
                print(f"[PROGRESS] Exported {i}/{total} cooking terms...")
            
            data['cooking_terms'].append({
                'id': term.id,
                'term_english': term.term_english,
                'term_english_normalized': term.term_english_normalized,
                'term_type': term.term_type,
                'category': term.category,
                'definition': term.definition,
                'usage_frequency': term.usage_frequency,
                'difficulty_level': term.difficulty_level,
                'confidence_score': term.confidence_score,
                'verified': term.verified,
            })
        
        # Export cooking term translations
        translations = CookingTermTranslation.objects.all()
        total_trans = translations.count()
        print(f"[INFO] Found {total_trans} cooking term translations")
        
        for i, trans in enumerate(translations, 1):
            if i % 100 == 0:
                print(f"[PROGRESS] Exported {i}/{total_trans} translations...")
            
            data['cooking_term_translations'].append({
                'term_id': trans.term_id,
                'language_code': trans.language_code,
                'translation': trans.translation,
                'verification_status': trans.verification_status,
                'alternative_translations': trans.alternative_translations,
                'cultural_notes': trans.cultural_notes,
                'source': trans.source,
                'confidence_score': trans.confidence_score,
            })
        
        # Save to JSON
        output_file = 'data/cooklingo_export.json'
        os.makedirs('data', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=True, indent=2)  # Use ensure_ascii=True to escape all non-ASCII
        
        print(f"\n[SUCCESS] Exported CookLingo data to: {output_file}")
        print(f"[INFO] Cooking Terms: {len(data['cooking_terms'])}")
        print(f"[INFO] Translations: {len(data['cooking_term_translations'])}")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] CookLingo export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "="*80)
    print("Starting IML and CookLingo Data Export")
    print("="*80)
    
    iml_success = export_iml_data()
    cooklingo_success = export_cooklingo_data()
    
    print("\n" + "="*80)
    if iml_success and cooklingo_success:
        print("ALL EXPORTS SUCCESSFUL!")
    else:
        print("SOME EXPORTS FAILED!")
        if not iml_success:
            print("  - IML export failed")
        if not cooklingo_success:
            print("  - CookLingo export failed")
    print("="*80 + "\n")

