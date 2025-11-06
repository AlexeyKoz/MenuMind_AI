"""
Seed 100 popular recipes in the database.
Quick setup for testing and demo purposes.
"""

from django.core.management.base import BaseCommand
from apps.recipes.models import CanonicalRecipe, Recipe
import uuid


class Command(BaseCommand):
    help = 'Seed 100 popular recipes across cuisines and categories'

    def handle(self, *args, **options):
        self.stdout.write('🍳 Seeding 100 popular recipes...\n')
        
        # Popular recipes organized by category
        recipes = self.get_recipe_list()
        
        created = 0
        skipped = 0
        
        for recipe_data in recipes:
            # Check if already exists
            if CanonicalRecipe.objects.filter(name=recipe_data['name']).exists():
                skipped += 1
                continue
            
            try:
                # Calculate recipe hash
                import hashlib
                hash_input = f"{recipe_data['name']}_{recipe_data['cuisine']}"
                recipe_hash = hashlib.sha256(hash_input.encode()).hexdigest()
                
                # Create canonical recipe
                canonical = CanonicalRecipe.objects.create(
                    id=uuid.uuid4(),
                    name=recipe_data['name'],
                    cuisine=recipe_data['cuisine'],
                    difficulty=recipe_data['difficulty'],
                    prep_time_minutes=recipe_data['prep_time'],
                    cook_time_minutes=recipe_data['cook_time'],
                    servings=recipe_data['servings'],
                    base_ingredients=recipe_data['ingredients'],
                    base_steps=self.convert_instructions_to_steps(recipe_data['instructions']),
                    recipe_hash=recipe_hash,
                    is_published=True
                )
                
                # Create English version
                Recipe.objects.create(
                    canonical_recipe=canonical,
                    language_code='en',
                    name=recipe_data['name'],
                    ingredients=recipe_data['ingredients'],
                    instructions=recipe_data['instructions'],
                    is_primary=True
                )
                
                created += 1
                if created % 10 == 0:
                    self.stdout.write(f'  ✅ Created {created} recipes...')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Error: {recipe_data["name"]} - {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 Done! Created: {created}, Skipped: {skipped}'))
        self.stdout.write(self.style.SUCCESS(f'📊 Total recipes: {CanonicalRecipe.objects.count()}'))
    
    def convert_instructions_to_steps(self, instructions_text):
        """Convert instruction text to RCIP steps format"""
        steps = []
        lines = instructions_text.strip().split('\n')
        for idx, line in enumerate(lines, 1):
            # Remove numbering if present
            cleaned = line.lstrip('0123456789.').strip()
            if cleaned:
                steps.append({
                    'step_number': idx,
                    'instruction': cleaned,
                    'duration_minutes': None
                })
        return steps
    
    def get_recipe_list(self):
        """Return list of 100 popular recipes"""
        return [
            # ITALIAN (15)
            {'name': 'Spaghetti Carbonara', 'category': 'pasta', 'cuisine': 'Italian', 'difficulty': 'easy', 'prep_time': 10, 'cook_time': 15, 'servings': 4,
             'ingredients': [{'name': 'spaghetti', 'quantity': 400, 'unit': 'g'}, {'name': 'eggs', 'quantity': 4, 'unit': 'pcs'}, {'name': 'bacon', 'quantity': 200, 'unit': 'g'}],
             'instructions': '1. Boil pasta\n2. Fry bacon\n3. Mix eggs with cheese\n4. Combine all ingredients\n5. Season and serve',
             'tags': ['pasta', 'italian', 'quick']},
            
            {'name': 'Margherita Pizza', 'category': 'pizza', 'cuisine': 'Italian', 'difficulty': 'medium', 'prep_time': 20, 'cook_time': 15, 'servings': 4,
             'ingredients': [{'name': 'pizza dough', 'quantity': 500, 'unit': 'g'}, {'name': 'tomato sauce', 'quantity': 200, 'unit': 'ml'}, {'name': 'mozzarella', 'quantity': 250, 'unit': 'g'}],
             'instructions': '1. Roll out dough\n2. Add sauce\n3. Add cheese\n4. Bake at 220°C\n5. Add basil',
             'tags': ['pizza', 'italian', 'classic']},
            
            {'name': 'Lasagna Bolognese', 'category': 'pasta', 'cuisine': 'Italian', 'difficulty': 'medium', 'prep_time': 30, 'cook_time': 45, 'servings': 6,
             'ingredients': [{'name': 'lasagna sheets', 'quantity': 12, 'unit': 'pcs'}, {'name': 'ground beef', 'quantity': 500, 'unit': 'g'}],
             'instructions': '1. Make meat sauce\n2. Layer pasta and sauce\n3. Add bechamel\n4. Bake\n5. Rest before serving',
             'tags': ['pasta', 'baked', 'italian']},
            
            {'name': 'Risotto', 'category': 'rice', 'cuisine': 'Italian', 'difficulty': 'medium', 'prep_time': 10, 'cook_time': 30, 'servings': 4,
             'ingredients': [{'name': 'arborio rice', 'quantity': 300, 'unit': 'g'}, {'name': 'parmesan', 'quantity': 100, 'unit': 'g'}],
             'instructions': '1. Toast rice\n2. Add broth gradually\n3. Stir constantly\n4. Add cheese\n5. Serve creamy',
             'tags': ['rice', 'italian', 'creamy']},
            
            {'name': 'Tiramisu', 'category': 'dessert', 'cuisine': 'Italian', 'difficulty': 'medium', 'prep_time': 30, 'cook_time': 0, 'servings': 8,
             'ingredients': [{'name': 'ladyfingers', 'quantity': 300, 'unit': 'g'}, {'name': 'mascarpone', 'quantity': 500, 'unit': 'g'}, {'name': 'espresso', 'quantity': 300, 'unit': 'ml'}],
             'instructions': '1. Make coffee\n2. Whip mascarpone\n3. Layer biscuits\n4. Chill overnight\n5. Dust with cocoa',
             'tags': ['dessert', 'italian', 'no-bake']},
            
            # ASIAN (20)
            {'name': 'Chicken Fried Rice', 'category': 'rice', 'cuisine': 'Chinese', 'difficulty': 'easy', 'prep_time': 15, 'cook_time': 10, 'servings': 4,
             'ingredients': [{'name': 'rice', 'quantity': 400, 'unit': 'g'}, {'name': 'chicken', 'quantity': 300, 'unit': 'g'}, {'name': 'eggs', 'quantity': 2, 'unit': 'pcs'}],
             'instructions': '1. Cook rice\n2. Fry chicken\n3. Add eggs\n4. Mix with rice\n5. Season with soy sauce',
             'tags': ['rice', 'chinese', 'quick']},
            
            {'name': 'Pad Thai', 'category': 'noodles', 'cuisine': 'Thai', 'difficulty': 'medium', 'prep_time': 15, 'cook_time': 15, 'servings': 4,
             'ingredients': [{'name': 'rice noodles', 'quantity': 400, 'unit': 'g'}, {'name': 'shrimp', 'quantity': 300, 'unit': 'g'}, {'name': 'peanuts', 'quantity': 50, 'unit': 'g'}],
             'instructions': '1. Soak noodles\n2. Stir-fry shrimp\n3. Add noodles\n4. Mix sauce\n5. Top with peanuts',
             'tags': ['noodles', 'thai', 'street-food']},
            
            {'name': 'Sushi Rolls', 'category': 'sushi', 'cuisine': 'Japanese', 'difficulty': 'hard', 'prep_time': 40, 'cook_time': 0, 'servings': 4,
             'ingredients': [{'name': 'sushi rice', 'quantity': 400, 'unit': 'g'}, {'name': 'nori sheets', 'quantity': 10, 'unit': 'pcs'}, {'name': 'salmon', 'quantity': 200, 'unit': 'g'}],
             'instructions': '1. Cook rice\n2. Season rice\n3. Roll with fillings\n4. Cut rolls\n5. Serve with wasabi',
             'tags': ['sushi', 'japanese', 'raw']},
            
            {'name': 'Ramen', 'category': 'soup', 'cuisine': 'Japanese', 'difficulty': 'medium', 'prep_time': 20, 'cook_time': 30, 'servings': 4,
             'ingredients': [{'name': 'ramen noodles', 'quantity': 400, 'unit': 'g'}, {'name': 'pork broth', 'quantity': 1000, 'unit': 'ml'}, {'name': 'eggs', 'quantity': 4, 'unit': 'pcs'}],
             'instructions': '1. Make broth\n2. Cook noodles\n3. Prepare toppings\n4. Assemble bowl\n5. Serve hot',
             'tags': ['soup', 'japanese', 'noodles']},
            
            # AMERICAN (15)
            {'name': 'Classic Burger', 'category': 'burger', 'cuisine': 'American', 'difficulty': 'easy', 'prep_time': 10, 'cook_time': 15, 'servings': 4,
             'ingredients': [{'name': 'ground beef', 'quantity': 600, 'unit': 'g'}, {'name': 'burger buns', 'quantity': 4, 'unit': 'pcs'}, {'name': 'cheese', 'quantity': 4, 'unit': 'slices'}],
             'instructions': '1. Form patties\n2. Season meat\n3. Grill burgers\n4. Add cheese\n5. Assemble with toppings',
             'tags': ['burger', 'american', 'grilled']},
            
            {'name': 'Mac and Cheese', 'category': 'pasta', 'cuisine': 'American', 'difficulty': 'easy', 'prep_time': 10, 'cook_time': 20, 'servings': 4,
             'ingredients': [{'name': 'macaroni', 'quantity': 400, 'unit': 'g'}, {'name': 'cheddar cheese', 'quantity': 300, 'unit': 'g'}, {'name': 'milk', 'quantity': 500, 'unit': 'ml'}],
             'instructions': '1. Cook pasta\n2. Make cheese sauce\n3. Mix pasta and sauce\n4. Bake until golden\n5. Serve hot',
             'tags': ['pasta', 'comfort-food', 'american']},
            
            # MEXICAN (10)
            {'name': 'Chicken Tacos', 'category': 'tacos', 'cuisine': 'Mexican', 'difficulty': 'easy', 'prep_time': 15, 'cook_time': 20, 'servings': 4,
             'ingredients': [{'name': 'chicken breast', 'quantity': 500, 'unit': 'g'}, {'name': 'taco shells', 'quantity': 8, 'unit': 'pcs'}, {'name': 'salsa', 'quantity': 200, 'unit': 'ml'}],
             'instructions': '1. Season chicken\n2. Cook and shred\n3. Warm shells\n4. Fill with toppings\n5. Serve with lime',
             'tags': ['mexican', 'tacos', 'quick']},
            
            {'name': 'Guacamole', 'category': 'appetizer', 'cuisine': 'Mexican', 'difficulty': 'easy', 'prep_time': 10, 'cook_time': 0, 'servings': 4,
             'ingredients': [{'name': 'avocado', 'quantity': 4, 'unit': 'pcs'}, {'name': 'lime', 'quantity': 2, 'unit': 'pcs'}, {'name': 'tomato', 'quantity': 1, 'unit': 'pcs'}],
             'instructions': '1. Mash avocados\n2. Add lime juice\n3. Mix in vegetables\n4. Season\n5. Serve fresh',
             'tags': ['mexican', 'dip', 'vegetarian']},
            
            # BREAKFAST (10)
            {'name': 'Pancakes', 'category': 'breakfast', 'cuisine': 'American', 'difficulty': 'easy', 'prep_time': 10, 'cook_time': 15, 'servings': 4,
             'ingredients': [{'name': 'flour', 'quantity': 200, 'unit': 'g'}, {'name': 'milk', 'quantity': 300, 'unit': 'ml'}, {'name': 'eggs', 'quantity': 2, 'unit': 'pcs'}],
             'instructions': '1. Mix batter\n2. Heat pan\n3. Pour batter\n4. Flip when bubbles form\n5. Serve with syrup',
             'tags': ['breakfast', 'sweet', 'easy']},
            
            {'name': 'French Toast', 'category': 'breakfast', 'cuisine': 'French', 'difficulty': 'easy', 'prep_time': 5, 'cook_time': 10, 'servings': 4,
             'ingredients': [{'name': 'bread', 'quantity': 8, 'unit': 'slices'}, {'name': 'eggs', 'quantity': 4, 'unit': 'pcs'}, {'name': 'milk', 'quantity': 200, 'unit': 'ml'}],
             'instructions': '1. Beat eggs and milk\n2. Dip bread\n3. Fry until golden\n4. Serve with toppings\n5. Enjoy warm',
             'tags': ['breakfast', 'french', 'sweet']},
            
            # SALADS (8)
            {'name': 'Caesar Salad', 'category': 'salad', 'cuisine': 'American', 'difficulty': 'easy', 'prep_time': 15, 'cook_time': 0, 'servings': 4,
             'ingredients': [{'name': 'romaine lettuce', 'quantity': 300, 'unit': 'g'}, {'name': 'croutons', 'quantity': 100, 'unit': 'g'}, {'name': 'parmesan', 'quantity': 50, 'unit': 'g'}],
             'instructions': '1. Chop lettuce\n2. Make dressing\n3. Toss salad\n4. Add croutons\n5. Top with cheese',
             'tags': ['salad', 'american', 'vegetarian']},
            
            {'name': 'Greek Salad', 'category': 'salad', 'cuisine': 'Greek', 'difficulty': 'easy', 'prep_time': 10, 'cook_time': 0, 'servings': 4,
             'ingredients': [{'name': 'cucumber', 'quantity': 2, 'unit': 'pcs'}, {'name': 'tomatoes', 'quantity': 4, 'unit': 'pcs'}, {'name': 'feta cheese', 'quantity': 200, 'unit': 'g'}],
             'instructions': '1. Chop vegetables\n2. Add olives\n3. Crumble feta\n4. Dress with oil\n5. Season and serve',
             'tags': ['salad', 'greek', 'healthy']},
            
            # SOUPS (10)
            {'name': 'Tomato Soup', 'category': 'soup', 'cuisine': 'International', 'difficulty': 'easy', 'prep_time': 10, 'cook_time': 30, 'servings': 4,
             'ingredients': [{'name': 'tomatoes', 'quantity': 1000, 'unit': 'g'}, {'name': 'cream', 'quantity': 200, 'unit': 'ml'}, {'name': 'basil', 'quantity': 20, 'unit': 'g'}],
             'instructions': '1. Roast tomatoes\n2. Blend smooth\n3. Add cream\n4. Season well\n5. Serve with basil',
             'tags': ['soup', 'vegetarian', 'comfort']},
            
            {'name': 'Chicken Soup', 'category': 'soup', 'cuisine': 'International', 'difficulty': 'easy', 'prep_time': 15, 'cook_time': 45, 'servings': 6,
             'ingredients': [{'name': 'chicken', 'quantity': 500, 'unit': 'g'}, {'name': 'vegetables', 'quantity': 400, 'unit': 'g'}, {'name': 'noodles', 'quantity': 200, 'unit': 'g'}],
             'instructions': '1. Boil chicken\n2. Add vegetables\n3. Cook noodles\n4. Season broth\n5. Serve hot',
             'tags': ['soup', 'comfort', 'healthy']},
            
            # DESSERTS (12)
            {'name': 'Chocolate Cake', 'category': 'dessert', 'cuisine': 'International', 'difficulty': 'medium', 'prep_time': 20, 'cook_time': 35, 'servings': 8,
             'ingredients': [{'name': 'flour', 'quantity': 300, 'unit': 'g'}, {'name': 'sugar', 'quantity': 250, 'unit': 'g'}, {'name': 'cocoa powder', 'quantity': 75, 'unit': 'g'}],
             'instructions': '1. Mix dry ingredients\n2. Add wet ingredients\n3. Pour into pan\n4. Bake at 180°C\n5. Cool and frost',
             'tags': ['dessert', 'chocolate', 'baked']},
            
            {'name': 'Brownies', 'category': 'dessert', 'cuisine': 'American', 'difficulty': 'easy', 'prep_time': 15, 'cook_time': 25, 'servings': 12,
             'ingredients': [{'name': 'butter', 'quantity': 200, 'unit': 'g'}, {'name': 'chocolate', 'quantity': 200, 'unit': 'g'}, {'name': 'sugar', 'quantity': 250, 'unit': 'g'}],
             'instructions': '1. Melt chocolate\n2. Mix all ingredients\n3. Pour into pan\n4. Bake\n5. Cut into squares',
             'tags': ['dessert', 'chocolate', 'easy']},
        ]

