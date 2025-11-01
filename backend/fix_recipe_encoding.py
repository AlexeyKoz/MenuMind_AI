#!/usr/bin/env python
"""Fix recipes with problematic characters"""

import os
import sys
import django
import re

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')

django.setup()

from apps.recipes.models import Recipe, CanonicalRecipe

def clean_text(text):
    """Remove non-Latin characters from text"""
    if not text:
        return text
    # Keep only ASCII printable characters and common Unicode Latin extended
    cleaned = ''.join(char for char in text if ord(char) < 0x0370 or char.isspace())
    # Clean up multiple spaces
    cleaned = ' '.join(cleaned.split())
    return cleaned

def fix_problematic_recipes():
    """Find and fix recipes with non-Latin characters"""
    print("\n" + "="*80)
    print("[FIX] Finding recipes with non-Latin characters")
    print("="*80)
    
    # Find recipes with characters outside Latin range
    all_recipes = Recipe.objects.all()
    problematic = []
    
    for recipe in all_recipes:
        has_non_latin = False
        try:
            # Try to encode to cp1251 (Windows console encoding)
            recipe.name.encode('cp1251')
            if recipe.description:
                recipe.description.encode('cp1251')
        except (UnicodeEncodeError, UnicodeDecodeError):
            has_non_latin = True
            problematic.append(recipe)
    
    print(f"[INFO] Found {len(problematic)} recipes with non-Latin characters\n")
    
    for idx, recipe in enumerate(problematic):
        print(f"--- Recipe {idx+1}/{len(problematic)} ---")
        print(f"ID: {recipe.id}")
        try:
            print(f"Name: {recipe.name}")
        except:
            print(f"Name: [Cannot display - contains problematic characters]")
        
        # Clean the name
        old_name = recipe.name
        new_name = clean_text(old_name)
        
        if new_name != old_name:
            print(f"Old name length: {len(old_name)} chars")
            print(f"New name: {new_name}")
            print(f"New name length: {len(new_name)} chars")
            
            # Update recipe
            recipe.name = new_name
            if recipe.description:
                recipe.description = clean_text(recipe.description)
            recipe.save()
            print("[OK] Recipe updated")
            
            # Also update canonical recipe if exists
            if recipe.canonical_recipe:
                canon = recipe.canonical_recipe
                canon.name = new_name
                if canon.description:
                    canon.description = clean_text(canon.description)
                canon.save()
                print("[OK] Canonical recipe also updated")
        print()
    
    print("="*80)
    print(f"[OK] Fixed {len(problematic)} recipes")
    print("="*80 + "\n")

if __name__ == '__main__':
    fix_problematic_recipes()

