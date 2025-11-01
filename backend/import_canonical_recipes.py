#!/usr/bin/env python
"""
Import canonical recipes into PostgreSQL database
"""
import os
import sys
import json

# Setup Django with PostgreSQL
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
os.environ['USE_POSTGRES'] = 'True'
os.environ['DB_NAME'] = 'menumine_ai'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'password'
os.environ['DB_HOST'] = 'db'
os.environ['DB_PORT'] = '5432'
os.environ['SECRET_KEY'] = 'temp'
os.environ['DEBUG'] = 'True'

import django
django.setup()

from apps.recipes.models import CanonicalRecipe
from django.db import transaction

def import_recipes():
    """Import canonical recipes from JSON"""
    print("\n" + "="*80)
    print("[IMPORT] Importing Canonical Recipes into PostgreSQL")
    print("="*80 + "\n")
    
    input_file = 'data/canonical_recipes_export.json'
    
    if not os.path.exists(input_file):
        print(f"[ERROR] File not found: {input_file}")
        return False
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            recipes_data = json.load(f)
        
        total = len(recipes_data)
        print(f"[INFO] Found {total} recipes to import")
        print("[INFO] Importing recipes...")
        print()
        
        imported = 0
        skipped = 0
        errors = []
        
        for i, recipe_data in enumerate(recipes_data, 1):
            if i % 10 == 0:
                print(f"[PROGRESS] Processed {i}/{total} recipes...")
            
            try:
                with transaction.atomic():
                    # Check if recipe already exists by hash
                    if CanonicalRecipe.objects.filter(recipe_hash=recipe_data['recipe_hash']).exists():
                        skipped += 1
                        continue
                    
                    # Create recipe
                    recipe = CanonicalRecipe.objects.create(
                        name=recipe_data['name'],
                        description=recipe_data['description'],
                        source_type=recipe_data['source_type'],
                        ai_source_url=recipe_data['ai_source_url'] or None,
                        base_ingredients=recipe_data['base_ingredients'],
                        base_steps=recipe_data['base_steps'],
                        cuisine=recipe_data['cuisine'],
                        difficulty=recipe_data['difficulty'],
                        diet_labels=recipe_data['diet_labels'],
                        allergens=recipe_data['allergens'],
                        prep_time_minutes=recipe_data['prep_time_minutes'],
                        cook_time_minutes=recipe_data['cook_time_minutes'],
                        total_time_minutes=recipe_data['total_time_minutes'],
                        servings=recipe_data['servings'],
                        recipe_hash=recipe_data['recipe_hash'],
                        is_published=recipe_data['is_published'],
                        is_featured=recipe_data['is_featured'],
                        title_translations=recipe_data['title_translations'],
                        description_translations=recipe_data['description_translations'],
                        steps_translations=recipe_data['steps_translations'],
                        nutrition_per_serving=recipe_data['nutrition_per_serving'],
                        original_language=recipe_data['original_language']
                    )
                    
                    imported += 1
                    
            except Exception as e:
                error_msg = f"'{recipe_data['name']}': {str(e)[:100]}"
                errors.append(error_msg)
                if len(errors) <= 5:  # Only print first 5 errors
                    print(f"\n[WARN] Failed to import {error_msg}")
                continue
        
        print(f"\n[SUCCESS] Import complete!")
        print(f"[INFO] Imported: {imported} recipes")
        print(f"[INFO] Skipped (already exist): {skipped} recipes")
        if errors:
            print(f"[INFO] Errors: {len(errors)} recipes (first 5 shown above)")
        
        # Verify
        total_recipes = CanonicalRecipe.objects.count()
        
        print(f"\n[VERIFY] Database now contains:")
        print(f"  - Canonical Recipes: {total_recipes}")
        
        print("\n" + "="*80)
        print("[SUCCESS] Canonical recipes imported!")
        print("="*80 + "\n")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = import_recipes()
    sys.exit(0 if success else 1)

