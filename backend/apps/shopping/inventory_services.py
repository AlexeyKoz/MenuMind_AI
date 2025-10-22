"""
Inventory AI Services - AI-powered categorization and recipe generation
Enhanced with IML integration (IML FIRST, AI fallback)
"""
import os
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from django.conf import settings

# NEW: Import IML services
from apps.core.ingredient_mapper import IngredientMapper
from apps.core.expiration_calculator import ExpirationCalculator
from apps.core.models import IngredientCache


class InventoryCategorizationService:
    """AI service for automatic categorization of shopping items (IML FIRST, AI fallback)"""

    def __init__(self):
        try:
            from groq import Groq
            groq_api_key = os.getenv('GROQ_API_KEY') or getattr(
                settings, 'GROQ_API_KEY', None)
            if groq_api_key:
                self.groq_client = Groq(api_key=groq_api_key)
                self.model = "llama-3.1-8b-instant"
            else:
                print(
                    "[WARNING] GROQ_API_KEY not found. Using fallback categorization.")
                self.groq_client = None
        except ImportError:
            print("[WARNING] Groq not installed. Using fallback categorization.")
            self.groq_client = None

        # NEW: Initialize IML services
        self.ingredient_mapper = IngredientMapper()
        self.expiration_calculator = ExpirationCalculator()

    def categorize_items(self, items: List[Dict]) -> List[Dict]:
        """
        Categorize multiple shopping items with IML/AI

        NEW: Uses IML data FIRST, AI fallback only if needed

        Args:
            items: List of dicts with 'id' and 'name' keys

        Returns:
            List of dicts with categorization suggestions
        """
        results = []

        for item in items:
            try:
                suggestion = self.categorize_single_item(item['name'])
                results.append({
                    'item_id': item['id'],
                    'name': item['name'],
                    'suggested_location': suggestion['location'],
                    'suggested_category': suggestion['category'],
                    'suggested_expiration_days': suggestion['expiration_days'],
                    'suggested_quantity': suggestion['quantity'],
                    'suggested_unit': suggestion['unit'],
                    'confidence': suggestion.get('confidence', 0.85),
                    'ingredient_key': suggestion.get('ingredient_key'),  # NEW
                    # NEW: iml, ai, or default
                    'source': suggestion.get('source', 'iml')
                })
            except Exception as e:
                print(f"[ERROR] Failed to categorize {item['name']}: {e}")
                # Fallback categorization
                results.append(self._fallback_categorization(item))

        return results

    def categorize_single_item(self, item_name: str) -> Dict:
        """
        Categorize a single shopping item with IML/AI

        NEW FLOW:
        1. Try IngredientMapper (IML lookup)
        2. If matched → use IML data (shelf_life, storage, category)
        3. If no match → AI fallback
        4. If AI fails → rule-based fallback

        Args:
            item_name: Name of the shopping item

        Returns:
            Dict with categorization details
        """
        print(f"[CATEGORIZE] Processing: {item_name}")

        # Step 1: Try to match ingredient in IML
        match_result = self.ingredient_mapper.map(item_name, language='en')

        if match_result.ingredient_key and match_result.confidence >= 0.70:
            # Found in IML - use IML data
            print(
                f"   ✅ IML match: {match_result.ingredient_key} ({match_result.confidence})")
            return self._categorize_from_iml(match_result.ingredient_key, item_name)

        # Step 2: No IML match - try AI
        print(f"   ⚠️  No IML match, trying AI...")
        if self.groq_client:
            try:
                return self._ai_categorize(item_name)
            except Exception as e:
                print(f"   [WARNING] AI categorization failed: {e}")

        # Step 3: Fallback to rule-based
        print(f"   ⚠️  Using rule-based fallback")
        return self._fallback_categorization({'name': item_name})

    def _categorize_from_iml(self, ingredient_key: str, item_name: str) -> Dict:
        """
        Categorize using IML data (fast, accurate)

        Args:
            ingredient_key: Matched ingredient key
            item_name: Original item name

        Returns:
            Categorization dict with IML data
        """
        try:
            ingredient = IngredientCache.objects.get(
                ingredient_key=ingredient_key)

            # Get storage location from IML
            location, source = self.expiration_calculator.suggest_storage_location(
                ingredient_key)

            # Get shelf life info
            shelf_life_info = self.expiration_calculator.get_shelf_life_info(
                ingredient_key)

            # Determine expiration days based on recommended location
            expiration_days = 7  # default
            if shelf_life_info:
                expiration_days = shelf_life_info.get(location, 7)

            # Map IML category to shopping category
            category = self._map_iml_category_to_shopping(ingredient.category)

            # Parse quantity/unit from item name (if present)
            quantity, unit = self._parse_quantity_unit(item_name)

            print(
                f"   📦 IML data: {location}, {expiration_days} days, category: {category}")

            return {
                'location': location,
                'category': category,
                'expiration_days': expiration_days,
                'quantity': quantity,
                'unit': unit,
                'confidence': 0.95,  # High confidence from IML
                'ingredient_key': ingredient_key,
                'source': 'iml'
            }

        except IngredientCache.DoesNotExist:
            print(f"   ❌ IML ingredient not found: {ingredient_key}")
            return self._fallback_categorization({'name': item_name})

    def _map_iml_category_to_shopping(self, iml_category: str) -> str:
        """Map IML category to shopping list category"""
        mapping = {
            'vegetables': 'produce',
            'fruits': 'produce',
            'meat': 'meat',
            'poultry': 'meat',
            'fish': 'meat',
            'seafood': 'meat',
            'dairy': 'dairy',
            'cheese': 'dairy',
            'grains': 'pantry',
            'pasta': 'pantry',
            'rice': 'pantry',
            'bread': 'bakery',
            'bakery': 'bakery',
            'frozen': 'frozen',
            'canned': 'pantry',
            'spices': 'pantry',
            'herbs': 'pantry',
            'beverages': 'beverages',
            'drinks': 'beverages',
            'snacks': 'snacks',
            'condiments': 'pantry',
            'oils': 'pantry',
        }

        iml_category_lower = iml_category.lower() if iml_category else ''
        return mapping.get(iml_category_lower, 'other')

    def _ai_categorize(self, item_name: str) -> Dict:
        """Use AI to categorize item"""
        prompt = f"""Analyze this shopping item and categorize it:
Item: "{item_name}"

Determine:
1. Best storage location (fridge/freezer/pantry/counter)
2. Food category (dairy/meat/vegetables/fruits/grains/canned/spices/snacks/beverages/frozen/other)
3. Typical expiration period (in days from purchase)
4. Estimated quantity and unit (parse from item name or use typical amount)

Rules:
- fridge: dairy, fresh meat, vegetables, opened items (3-14 days)
- freezer: frozen foods, meat for long-term storage (30-90 days)
- pantry: dry goods, canned items, grains, spices (90-365 days)
- counter: fruits like bananas, bread, onions (3-7 days)

Return ONLY valid JSON (no markdown, no explanations):
{{
  "location": "fridge|freezer|pantry|counter",
  "category": "dairy|meat|vegetables|fruits|grains|canned|spices|snacks|beverages|frozen|other",
  "expiration_days": <number>,
  "quantity": <number>,
  "unit": "g|kg|ml|L|pieces|units",
  "confidence": <0.0-1.0>
}}"""

        try:
            completion = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a food storage and categorization expert. Return ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=200
            )

            response_text = completion.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            result = json.loads(response_text)

            # Validate and set defaults
            result.setdefault('location', 'pantry')
            result.setdefault('category', 'other')
            result.setdefault('expiration_days', 30)
            result.setdefault('quantity', 1)
            result.setdefault('unit', 'units')
            result.setdefault('confidence', 0.75)  # AI confidence
            result['source'] = 'ai'  # Mark as AI-generated

            print(
                f"   [AI CATEGORIZE] {item_name} → {result['location']}/{result['category']} (expires in {result['expiration_days']} days)")

            return result

        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse AI response: {e}")
            return self._fallback_categorization({'name': item_name})
        except Exception as e:
            print(f"[ERROR] AI categorization error: {e}")
            return self._fallback_categorization({'name': item_name})

    def _fallback_categorization(self, item: Dict) -> Dict:
        """Rule-based fallback categorization (LAST RESORT)"""
        name = item.get('name', '').lower()

        # Parse quantity and unit from name
        quantity, unit = self._parse_quantity_unit(name)

        # Categorize by keywords (improved with IML-like logic)
        if any(word in name for word in ['milk', 'yogurt', 'cheese', 'butter', 'cream', 'sour cream', 'cottage cheese']):
            return {
                'location': 'fridge',
                'category': 'dairy',
                'expiration_days': 7,
                'quantity': quantity,
                'unit': unit,
                'confidence': 0.7,
                'source': 'default'
            }
        elif any(word in name for word in ['chicken', 'beef', 'pork', 'fish', 'meat', 'steak', 'turkey', 'lamb']):
            return {
                'location': 'fridge',
                'category': 'meat',
                'expiration_days': 3,
                'quantity': quantity,
                'unit': unit,
                'confidence': 0.7,
                'source': 'default'
            }
        elif any(word in name for word in ['frozen', 'ice cream', 'popsicle']):
            return {
                'location': 'freezer',
                'category': 'frozen',
                'expiration_days': 90,
                'quantity': quantity,
                'unit': unit,
                'confidence': 0.8,
                'source': 'default'
            }
        elif any(word in name for word in ['tomato', 'lettuce', 'carrot', 'pepper', 'onion', 'vegetable', 'celery', 'cucumber', 'broccoli']):
            return {
                'location': 'fridge',
                'category': 'produce',
                'expiration_days': 7,
                'quantity': quantity,
                'unit': unit,
                'confidence': 0.7,
                'source': 'default'
            }
        elif any(word in name for word in ['apple', 'banana', 'orange', 'fruit', 'berry', 'grape', 'pear']):
            return {
                'location': 'counter',
                'category': 'produce',
                'expiration_days': 5,
                'quantity': quantity,
                'unit': unit,
                'confidence': 0.7,
                'source': 'default'
            }
        elif any(word in name for word in ['rice', 'pasta', 'bread', 'flour', 'grain', 'cereal']):
            return {
                'location': 'pantry',
                'category': 'pantry' if 'bread' not in name else 'bakery',
                'expiration_days': 180 if 'bread' not in name else 7,
                'quantity': quantity,
                'unit': unit,
                'confidence': 0.7,
                'source': 'default'
            }
        elif any(word in name for word in ['can', 'canned', 'tin']):
            return {
                'location': 'pantry',
                'category': 'pantry',
                'expiration_days': 365,
                'quantity': quantity,
                'unit': unit,
                'confidence': 0.8,
                'source': 'default'
            }
        elif any(word in name for word in ['juice', 'soda', 'water', 'drink', 'beverage', 'cola', 'tea', 'coffee']):
            return {
                'location': 'fridge',
                'category': 'beverages',
                'expiration_days': 30,
                'quantity': quantity,
                'unit': unit,
                'confidence': 0.7,
                'source': 'default'
            }
        else:
            # Default
            return {
                'location': 'pantry',
                'category': 'other',
                'expiration_days': 30,
                'quantity': quantity,
                'unit': unit,
                'confidence': 0.5,
                'source': 'default'
            }

    def _parse_quantity_unit(self, name: str) -> tuple:
        """Extract quantity and unit from item name"""
        import re

        # Common patterns: "2kg", "500g", "1L", "3 pieces"
        patterns = [
            r'(\d+\.?\d*)\s*(kg|kilogram|kilo)',
            r'(\d+\.?\d*)\s*(g|gram)',
            r'(\d+\.?\d*)\s*(l|liter|litre)',
            r'(\d+\.?\d*)\s*(ml|milliliter)',
            r'(\d+\.?\d*)\s*(piece|pieces|unit|units)',
        ]

        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                quantity = float(match.group(1))
                unit_raw = match.group(2).lower()

                # Normalize units
                if unit_raw in ['kg', 'kilogram', 'kilo']:
                    return (quantity, 'kg')
                elif unit_raw in ['g', 'gram']:
                    return (quantity, 'g')
                elif unit_raw in ['l', 'liter', 'litre']:
                    return (quantity, 'L')
                elif unit_raw in ['ml', 'milliliter']:
                    return (quantity, 'ml')
                elif unit_raw in ['piece', 'pieces', 'unit', 'units']:
                    return (quantity, 'pieces')

        # Default
        return (1, 'units')


class InventoryRecipeGenerator:
    """
    AI service for generating recipes from inventory

    Sprint 7 Integration:
    - Phase 1: Validation with UniversalValidator
    - Phase 2: Multilingual generation (single language, lazy approach)
    - Uses Gemini PRIMARY, Groq FALLBACK
    """

    def __init__(self):
        # Initialize Gemini (PRIMARY)
        self.gemini_client = None
        try:
            import google.generativeai as genai
            gemini_key = os.getenv('GEMINI_API_KEY') or getattr(
                settings, 'GEMINI_API_KEY', None)
            if gemini_key:
                genai.configure(api_key=gemini_key)
                self.gemini_client = genai.GenerativeModel(
                    'gemini-2.0-flash-lite')
                print("[INVENTORY AI] Initialized Gemini 2.0 Flash Lite (PRIMARY)")
            else:
                print("[WARNING] GEMINI_API_KEY not found. Gemini unavailable.")
        except Exception as e:
            print(f"[WARNING] Gemini initialization failed: {e}")

        # Initialize Groq (FALLBACK)
        self.groq_client = None
        try:
            from groq import Groq
            groq_api_key = os.getenv('GROQ_API_KEY') or getattr(
                settings, 'GROQ_API_KEY', None)
            if groq_api_key:
                self.groq_client = Groq(api_key=groq_api_key)
                self.groq_model = "llama-3.3-70b-versatile"
                print("[INVENTORY AI] Initialized Groq Llama 3.3 70B (FALLBACK)")
            else:
                print("[WARNING] GROQ_API_KEY not found. Groq unavailable.")
        except Exception as e:
            print(f"[WARNING] Groq initialization failed: {e}")

        # Initialize validator (Phase 1)
        try:
            from apps.core.services import get_universal_validator
            self.validator = get_universal_validator()
            print("[INVENTORY AI] Initialized UniversalValidator")
        except Exception as e:
            print(f"[WARNING] Validator initialization failed: {e}")
            self.validator = None

    def generate_recipes(
        self,
        inventory_items: List[Dict],
        user_profile: Dict,
        max_recipes: int = 5,
        prioritize_expiring: bool = True,
        max_missing_ingredients: int = 2,
        target_language: str = 'en'  # Phase 2: Single-language generation
    ) -> List[Dict]:
        """
        Generate recipe suggestions from inventory with validation

        Phase 1: Validates all recipes before returning
        Phase 2: Generates in user's target language only (lazy approach)

        AI Strategy: Gemini PRIMARY, Groq FALLBACK

        Args:
            inventory_items: List of inventory items with name, quantity, expiration_date
            user_profile: User preferences and nutrition goals
            max_recipes: Maximum number of recipes to generate
            prioritize_expiring: Prioritize items expiring soon
            max_missing_ingredients: Max missing ingredients allowed
            target_language: Language for generation ('en', 'he', 'ru')

        Returns:
            List of validated recipe suggestions in target language
        """
        if not self.gemini_client and not self.groq_client:
            print("[ERROR] No AI provider available (Gemini or Groq)")
            return []

        try:
            print(
                f"[INVENTORY AI] Generating {max_recipes} recipes in '{target_language}'")
            print(f"[INVENTORY AI] Inventory items: {len(inventory_items)}")

            # Sort items by expiration if prioritizing
            if prioritize_expiring:
                inventory_items = sorted(
                    inventory_items,
                    key=lambda x: x.get('expiration_date') or '9999-12-31'
                )

            # Build prompt in target language (Phase 2)
            prompt = self._build_prompt(
                inventory_items,
                user_profile,
                max_recipes,
                prioritize_expiring,
                max_missing_ingredients,
                target_language
            )

            # Try Gemini PRIMARY first
            recipe_briefs = None
            ai_provider = None

            if self.gemini_client:
                print("[INVENTORY AI] Trying Gemini (PRIMARY)...")
                recipe_briefs = self._generate_with_gemini(prompt)
                if recipe_briefs:
                    ai_provider = 'gemini'
                    print(
                        f"[INVENTORY AI] ✅ Gemini generated {len(recipe_briefs)} recipes")

            # Fallback to Groq if Gemini failed
            if not recipe_briefs and self.groq_client:
                print("[INVENTORY AI] Gemini failed, trying Groq (FALLBACK)...")
                recipe_briefs = self._generate_with_groq(prompt)
                if recipe_briefs:
                    ai_provider = 'groq'
                    print(
                        f"[INVENTORY AI] ✅ Groq generated {len(recipe_briefs)} recipes")

            if not recipe_briefs:
                print("[ERROR] Both Gemini and Groq failed to generate recipes")
                # Fallback to templates
                return self._generate_fallback_recipes(inventory_items, max_recipes)

            # Phase 1: Validate recipes
            if self.validator:
                validated_recipes = self._validate_recipes(
                    recipe_briefs, ai_provider)
                print(
                    f"[INVENTORY AI] ✅ Validated {len(validated_recipes)}/{len(recipe_briefs)} recipes")
                return validated_recipes[:max_recipes]
            else:
                # No validator available, return unvalidated (mark as unvalidated)
                for recipe in recipe_briefs:
                    recipe['validation'] = {
                        'score': None,
                        'is_valid': None,
                        'validated': False,
                        'reason': 'Validator not available'
                    }
                return recipe_briefs[:max_recipes]

        except Exception as e:
            print(f"[ERROR] Recipe generation error: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to template-based recipes
            return self._generate_fallback_recipes(inventory_items, max_recipes)

    def _build_inventory_summary(self, items: List[Dict]) -> str:
        """Build formatted inventory summary for AI prompt"""
        lines = []
        for item in items:
            expiry_str = ""
            if item.get('expiration_date'):
                exp_date = item['expiration_date']
                if isinstance(exp_date, str):
                    exp_date = datetime.strptime(exp_date, '%Y-%m-%d').date()
                days_left = (exp_date - datetime.now().date()).days
                if days_left <= 3:
                    expiry_str = f" (🔴 EXPIRES IN {days_left} DAYS - URGENT!)"
                elif days_left <= 7:
                    expiry_str = f" (⚠️ expires in {days_left} days)"

            lines.append(
                f"- {item['name']}: {item['quantity']}{item['unit']}{expiry_str}")

        return '\n'.join(lines)

    def _build_user_summary(self, profile: Dict) -> str:
        """Build formatted user profile summary"""
        return f"""- Daily calorie goal: {profile.get('daily_calories_goal', 'Not set')}
- Daily protein goal: {profile.get('daily_protein_goal', 'Not set')}g
- Dietary restrictions: {', '.join(profile.get('dietary_restrictions', [])) or 'None'}
- Allergies: {', '.join(profile.get('allergies', [])) or 'None'}
- Activity level: {profile.get('activity_level', 'moderate')}"""

    def _generate_fallback_recipes(self, inventory_items: List[Dict], max_recipes: int = 5) -> List[Dict]:
        """
        Generate basic fallback recipes when AI fails
        Creates simple recipes based on available ingredients
        """
        print(
            f"[FALLBACK] Generating {max_recipes} fallback recipes from {len(inventory_items)} inventory items")

        recipes = []
        available_items = [
            item for item in inventory_items if item.get('quantity', 0) > 0]

        if len(available_items) < 2:
            print("[FALLBACK] Not enough ingredients for recipes")
            return []

        # Group items by category for better recipe generation
        categories = {}
        for item in available_items:
            category = item.get('category', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)

        # Generate simple recipes based on common combinations
        recipe_templates = [
            {
                'name': 'Simple Salad',
                'categories': ['vegetables', 'fruits'],
                'ingredients_from_inventory': 2,
                'missing_ingredients': ['olive oil', 'salt'],
                'nutrition': {'calories': 150, 'protein': 5, 'carbs': 20, 'fat': 8},
                'difficulty': 'easy',
                'cooking_time': '10 min',
                'reasoning': 'Quick and healthy salad using fresh vegetables'
            },
            {
                'name': 'Pasta with Tomato Sauce',
                'categories': ['grains', 'vegetables'],
                'ingredients_from_inventory': 2,
                'missing_ingredients': ['pasta', 'garlic'],
                'nutrition': {'calories': 400, 'protein': 15, 'carbs': 60, 'fat': 12},
                'difficulty': 'easy',
                'cooking_time': '20 min',
                'reasoning': 'Classic pasta dish using available ingredients'
            },
            {
                'name': 'Chicken Stir Fry',
                'categories': ['meat', 'vegetables'],
                'ingredients_from_inventory': 2,
                'missing_ingredients': ['rice', 'soy sauce'],
                'nutrition': {'calories': 350, 'protein': 30, 'carbs': 25, 'fat': 15},
                'difficulty': 'easy',
                'cooking_time': '15 min',
                'reasoning': 'Quick protein-rich meal with fresh vegetables'
            },
            {
                'name': 'Vegetable Soup',
                'categories': ['vegetables'],
                'ingredients_from_inventory': 3,
                'missing_ingredients': ['broth', 'herbs'],
                'nutrition': {'calories': 120, 'protein': 8, 'carbs': 18, 'fat': 4},
                'difficulty': 'easy',
                'cooking_time': '25 min',
                'reasoning': 'Warm and nourishing soup from fresh vegetables'
            },
            {
                'name': 'Fruit Smoothie',
                'categories': ['fruits', 'dairy'],
                'ingredients_from_inventory': 2,
                'missing_ingredients': ['yogurt', 'honey'],
                'nutrition': {'calories': 200, 'protein': 10, 'carbs': 30, 'fat': 6},
                'difficulty': 'easy',
                'cooking_time': '5 min',
                'reasoning': 'Refreshing and healthy drink from fresh fruits'
            }
        ]

        # Match templates to available categories
        for template in recipe_templates[:max_recipes]:
            template_categories = set(template['categories'])
            available_categories = set(categories.keys())

            # Check if we have ingredients from the required categories
            if template_categories.intersection(available_categories):
                # Create recipe with actual inventory items
                ingredients_from_inventory = []
                for category in template['categories']:
                    if category in categories:
                        # Take up to template['ingredients_from_inventory'] items from this category
                        for item in categories[category][:template['ingredients_from_inventory']]:
                            ingredients_from_inventory.append({
                                'name': item['name'],
                                'quantity': item['quantity'],
                                'unit': item['unit']
                            })

                if ingredients_from_inventory:
                    recipe = {
                        'name': template['name'],
                        'priority': 'normal',
                        'ingredients_from_inventory': ingredients_from_inventory,
                        'missing_ingredients': template['missing_ingredients'],
                        'nutrition': template['nutrition'],
                        'difficulty': template['difficulty'],
                        'cooking_time': template['cooking_time'],
                        'reasoning': template['reasoning']
                    }
                    recipes.append(recipe)

        # If no recipes were generated from templates, create a generic recipe with available items
        if len(recipes) == 0 and len(available_items) >= 2:
            print("[FALLBACK] No category matches found, creating generic recipe")
            ingredients_from_inventory = []
            for item in available_items[:5]:  # Use up to 5 items
                ingredients_from_inventory.append({
                    'name': item['name'],
                    'quantity': item['quantity'],
                    'unit': item['unit']
                })

            generic_recipe = {
                'name': 'Mixed Ingredients Dish',
                'priority': 'normal',
                'ingredients_from_inventory': ingredients_from_inventory,
                'missing_ingredients': ['seasonings', 'cooking oil'],
                'nutrition': {'calories': 300, 'protein': 15, 'carbs': 35, 'fat': 10},
                'difficulty': 'easy',
                'cooking_time': '20 min',
                'reasoning': 'A simple dish using available ingredients from your inventory'
            }
            recipes.append(generic_recipe)

        print(f"[FALLBACK] Generated {len(recipes)} fallback recipes")
        return recipes

    # ==================== SPRINT 7: NEW METHODS ====================

    def _build_prompt(
        self,
        items: List[Dict],
        user_profile: Dict,
        max_recipes: int,
        prioritize_expiring: bool,
        max_missing: int,
        language: str
    ) -> str:
        """
        Build AI prompt in target language (Phase 2: Simplified)

        Items are already in user's language from shopping!
        No translation needed - just format them properly.
        """

        # Build inventory summary
        inventory_summary = self._build_inventory_summary(items)
        user_summary = self._build_user_summary(user_profile)

        # Language-specific system prompts
        SYSTEM_PROMPTS = {
            'en': "You are a professional chef assistant. Generate practical recipe suggestions.",
            'he': "אתה עוזר שף מקצועי. צור הצעות מתכון מעשיות.",
            'ru': "Вы профессиональный помощник шеф-повара. Создайте практические рецепты."
        }

        # Language-specific instructions
        INSTRUCTIONS = {
            'en': f"""Based on the following inventory items, suggest {max_recipes} recipes.

Inventory:
{inventory_summary}

User Profile:
{user_summary}

Requirements:
1. PRIORITIZE ingredients expiring within 3 days (mark priority as "urgent")
2. Maximum {max_missing} missing ingredients per recipe
3. Fit user's nutrition goals
4. Be realistic and achievable

For each recipe, provide:
- name: Recipe name
- priority: "urgent" (uses expiring items), "high" (uses most inventory), or "normal"
- ingredients_from_inventory: List of {{name, quantity, unit}}
- missing_ingredients: List of ingredient names (max {max_missing})
- nutrition: {{calories, protein, carbs, fat}}
- difficulty: "easy", "intermediate", or "advanced"
- cooking_time: e.g., "20 min", "45 min"
- reasoning: Why this recipe

Return ONLY valid JSON array (no markdown):
[{{"name": "...", "priority": "urgent|high|normal", ...}}]""",

            'he': f"""בהתבסס על מוצרי המלאי הבאים, הצע {max_recipes} מתכונים.

מלאי:
{inventory_summary}

פרופיל משתמש:
{user_summary}

דרישות:
1. תעדוף מרכיבים שפג תוקפם תוך 3 ימים (סמן עדיפות כ-"urgent")
2. מקסימום {max_missing} מרכיבים חסרים למתכון
3. התאם ליעדי התזונה של המשתמש
4. היה ריאלי וישים

לכל מתכון, ספק:
- name: שם המתכון
- priority: "urgent" (משתמש במרכיבים שפג תוקפם), "high" (משתמש ברוב המלאי), או "normal"
- ingredients_from_inventory: רשימה של {{name, quantity, unit}}
- missing_ingredients: רשימת שמות מרכיבים (מקסימום {max_missing})
- nutrition: {{calories, protein, carbs, fat}}
- difficulty: "easy", "intermediate", או "advanced"
- cooking_time: למשל, "20 min", "45 min"
- reasoning: למה המתכון הזה

החזר רק מערך JSON תקין (ללא markdown):
[{{"name": "...", "priority": "urgent|high|normal", ...}}]""",

            'ru': f"""На основе следующих товаров из инвентаря предложите {max_recipes} рецептов.

Инвентарь:
{inventory_summary}

Профиль пользователя:
{user_summary}

Требования:
1. ПРИОРИТЕТ ингредиентам с истекающим сроком в течение 3 дней (отметить приоритет как "urgent")
2. Максимум {max_missing} недостающих ингредиентов на рецепт
3. Соответствовать целям пользователя по питанию
4. Быть реалистичным и достижимым

Для каждого рецепта укажите:
- name: Название рецепта
- priority: "urgent" (использует ингредиенты с истекающим сроком), "high" (использует большинство инвентаря), или "normal"
- ingredients_from_inventory: Список {{name, quantity, unit}}
- missing_ingredients: Список названий ингредиентов (максимум {max_missing})
- nutrition: {{calories, protein, carbs, fat}}
- difficulty: "easy", "intermediate", или "advanced"
- cooking_time: например, "20 min", "45 min"
- reasoning: Почему этот рецепт

Верните только валидный JSON массив (без markdown):
[{{"name": "...", "priority": "urgent|high|normal", ...}}]"""
        }

        system_prompt = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS['en'])
        instruction = INSTRUCTIONS.get(language, INSTRUCTIONS['en'])

        return f"{system_prompt}\n\n{instruction}"

    def _generate_with_gemini(self, prompt: str) -> Optional[List[Dict]]:
        """Generate recipes using Gemini (PRIMARY) with retry logic"""
        max_retries = 3
        retry_delay = 1  # Start with 1 second

        for attempt in range(max_retries):
            try:
                print(
                    f"[INVENTORY AI] Gemini attempt {attempt + 1}/{max_retries}")

                response = self.gemini_client.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.7,
                        'max_output_tokens': 2000,
                    },
                    request_options={'timeout': 30}  # 30 second timeout
                )

                response_text = response.text.strip()
                recipes = self._parse_json_response(response_text)

                if recipes:
                    return recipes
                else:
                    print(
                        f"[INVENTORY AI] Gemini returned invalid JSON, retrying...")

            except Exception as e:
                error_str = str(e)
                print(
                    f"[INVENTORY AI] Gemini error (attempt {attempt + 1}): {e}")

                # Check if it's a retryable error
                if 'quota' in error_str.lower() or '429' in error_str:
                    print(f"[INVENTORY AI] Quota/rate limit hit - not retrying")
                    return None

                if attempt < max_retries - 1:
                    # Exponential backoff
                    import time
                    wait_time = retry_delay * (2 ** attempt)
                    print(
                        f"[INVENTORY AI] Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"[INVENTORY AI] All {max_retries} attempts failed")
                    return None

        return None

    def _generate_with_groq(self, prompt: str) -> Optional[List[Dict]]:
        """Generate recipes using Groq (FALLBACK)"""
        try:
            completion = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional chef and nutritionist. Return ONLY valid JSON array."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )

            response_text = completion.choices[0].message.content.strip()
            return self._parse_json_response(response_text)

        except Exception as e:
            print(f"[INVENTORY AI] Groq error: {e}")
            return None

    def _parse_json_response(self, response_text: str) -> Optional[List[Dict]]:
        """Parse JSON response from AI (handles markdown code blocks)"""
        try:
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            recipes = json.loads(response_text)

            if not isinstance(recipes, list):
                print(f"[INVENTORY AI] ERROR: Response is not a list")
                return None

            return recipes

        except json.JSONDecodeError as e:
            print(f"[INVENTORY AI] JSON parse error: {e}")
            print(f"[INVENTORY AI] Response was: {response_text[:500]}")
            return None

    def _validate_recipes(self, recipe_briefs: List[Dict], ai_provider: str) -> List[Dict]:
        """
        Validate recipe briefs using UniversalValidator (Phase 1)

        Returns only valid recipes with validation scores

        NOTE: Recipe briefs use a lower validation threshold (30%) because they are
        lightweight suggestions without full RCIP 2.0 structure. Full recipes (Phase 4)
        will use the standard 75% threshold.
        """
        validated_recipes = []
        validation_stats = {
            'generated': len(recipe_briefs),
            'validated': 0,
            'failed': 0,
            'issues': []
        }

        for brief in recipe_briefs:
            # Convert brief to RCIP 2.0 format for validation
            rcip_recipe = self._convert_brief_to_rcip(brief)

            # Validate using UniversalValidator
            try:
                validation_result = self.validator.validate_recipe(rcip_recipe)

                if validation_result.overall_score >= 30:  # Lower threshold for briefs
                    # Add validation metadata to brief
                    brief['validation'] = {
                        'score': validation_result.overall_score,
                        'is_valid': True,
                        'validated_at': validation_result.execution_time_ms,
                        'ai_provider': ai_provider,
                        'brief_mode': True  # Indicates lower threshold used
                    }
                    validated_recipes.append(brief)
                    validation_stats['validated'] += 1
                else:
                    # Log failure but don't show to user
                    validation_stats['failed'] += 1
                    validation_stats['issues'].append({
                        'recipe_name': brief['name'],
                        'score': validation_result.overall_score,
                        'issues': [
                            {
                                'layer': issue.layer,
                                'level': issue.level,
                                'field': issue.field,
                                'message': issue.message
                            }
                            for issue in validation_result.issues
                        ]
                    })
                    print(
                        f"[INVENTORY AI] ❌ Recipe '{brief['name']}' failed validation (score: {validation_result.overall_score})")

            except Exception as e:
                print(
                    f"[INVENTORY AI] Validation error for '{brief['name']}': {e}")
                validation_stats['failed'] += 1

        # Log validation statistics
        print(
            f"[INVENTORY AI] Validation stats: {validation_stats['validated']} passed, {validation_stats['failed']} failed")

        # Sort by validation score (best first)
        validated_recipes.sort(
            key=lambda r: r['validation']['score'], reverse=True)

        return validated_recipes

    def _convert_brief_to_rcip(self, brief: Dict) -> Dict:
        """
        Convert recipe brief to RCIP 2.0 format for validation

        Brief structure (from AI):
        {
            "name": "Quick Tomato Pasta",
            "ingredients_from_inventory": [...],
            "missing_ingredients": [...],
            "cooking_time": "20 min",
            "difficulty": "easy",
            "nutrition": {...}
        }

        RCIP 2.0 structure (for validator):
        {
            "metadata": {...},
            "structure": {
                "ingredients": [...],
                "steps": [...]
            }
        }
        """
        # Combine all ingredients
        all_ingredients = []

        # Add inventory ingredients
        for ing in brief.get('ingredients_from_inventory', []):
            all_ingredients.append({
                'iml_key': self._normalize_ingredient_name(ing['name']),
                'amount': ing.get('quantity', 1),
                'unit': ing.get('unit', 'unit'),
                'from_inventory': True
            })

        # Add missing ingredients
        for ing_name in brief.get('missing_ingredients', []):
            all_ingredients.append({
                'iml_key': self._normalize_ingredient_name(ing_name),
                'amount': 1,
                'unit': 'unit',
                'from_inventory': False
            })

        # Build RCIP structure
        rcip = {
            'metadata': {
                'title': brief['name'],
                'source_language': 'en',  # Will be set by API endpoint
                'servings': brief.get('servings', 2),
                'cooking_time': brief.get('cooking_time', 'unknown'),
                'difficulty': brief.get('difficulty', 'easy'),
                'tags': ['inventory-generated'],
                'nutrition': brief.get('nutrition', {})
            },
            'structure': {
                'ingredients': all_ingredients,
                'steps': self._generate_placeholder_steps(brief)
            }
        }

        return rcip

    def _normalize_ingredient_name(self, name: str) -> str:
        """Convert ingredient name to IML key format"""
        return name.lower().strip().replace(' ', '-')

    def _generate_placeholder_steps(self, brief: Dict) -> List[Dict]:
        """
        Generate minimal placeholder steps for validation

        NOTE: Full steps will be generated when user clicks "Create Recipe"
        For validation, we just need basic structure
        """
        return [
            {
                'step_number': 1,
                'instruction': f"Prepare ingredients for {brief['name']}",
                'cooklingo_keys': []
            },
            {
                'step_number': 2,
                'instruction': "Cook according to recipe",
                'cooklingo_keys': []
            },
            {
                'step_number': 3,
                'instruction': "Serve and enjoy",
                'cooklingo_keys': []
            }
        ]
