#!/usr/bin/env python
"""
Export canonical recipes from SQLite database
"""
import os
import sys
import json

# Setup Django with SQLite
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
os.environ['USE_POSTGRES'] = 'False'  # Use SQLite
os.environ['SECRET_KEY'] = 'temp'
os.environ['DEBUG'] = 'True'

import django
django.setup()

from apps.recipes.models import CanonicalRecipe

def export_recipes():
    """Export canonical recipes to JSON"""
    print("\n" + "="*80)
    print("[EXPORT] Exporting Canonical Recipes from SQLite")
    print("="*80 + "\n")
    
    recipes_data = []
    
    try:
        recipes = CanonicalRecipe.objects.all()
        total = recipes.count()
        
        print(f"[INFO] Found {total} canonical recipes")
        print("[INFO] Exporting recipes...")
        print()
        
        for i, recipe in enumerate(recipes, 1):
            if i % 10 == 0:
                print(f"[PROGRESS] Exported {i}/{total} recipes...")
            
            recipe_data = {
                'name': recipe.name,
                'description': recipe.description or '',
                'source_type': recipe.source_type,
                'ai_source_url': recipe.ai_source_url or '',
                'base_ingredients': recipe.base_ingredients,
                'base_steps': recipe.base_steps,
                'cuisine': recipe.cuisine or '',
                'difficulty': recipe.difficulty,
                'diet_labels': recipe.diet_labels,
                'allergens': recipe.allergens,
                'prep_time_minutes': recipe.prep_time_minutes,
                'cook_time_minutes': recipe.cook_time_minutes,
                'total_time_minutes': recipe.total_time_minutes,
                'servings': recipe.servings,
                'recipe_hash': recipe.recipe_hash,
                'is_published': recipe.is_published,
                'is_featured': recipe.is_featured,
                'title_translations': recipe.title_translations,
                'description_translations': recipe.description_translations,
                'steps_translations': recipe.steps_translations,
                'nutrition_per_serving': recipe.nutrition_per_serving,
                'original_language': recipe.original_language
            }
            
            recipes_data.append(recipe_data)
        
        # Save to JSON
        output_file = 'data/canonical_recipes_export.json'
        os.makedirs('data', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(recipes_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[SUCCESS] Exported {len(recipes_data)} recipes to: {output_file}")
        print(f"[INFO] Total ingredients: {sum(len(r.get('base_ingredients', [])) for r in recipes_data)}")
        print(f"[INFO] Total steps: {sum(len(r.get('base_steps', [])) for r in recipes_data)}")
        
        print("\n" + "="*80)
        print("[SUCCESS] Export complete!")
        print("="*80 + "\n")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = export_recipes()
    sys.exit(0 if success else 1)

