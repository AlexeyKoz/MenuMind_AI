"""
RCIP (Recipe Content Interchange Protocol) Converter
Converts raw recipe text to standardized RCIP format
"""
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional


class RCIPConverter:
    """Convert raw recipe text to RCIP format"""

    def __init__(self):
        self.rcip_version = "0.1"

    def convert(
        self,
        name: str,
        ingredients_text: str,
        steps_text: str,
        source_url: str = None,
        author: str = None,
        description: str = None,
        **kwargs
    ) -> Dict:
        """
        Convert recipe components to RCIP format

        Args:
            name: Recipe name
            ingredients_text: Raw text with ingredients list
            steps_text: Raw text with cooking steps
            source_url: Source URL
            author: Recipe author
            description: Recipe description
            **kwargs: Additional metadata

        Returns:
            Dictionary in RCIP format
        """
        # Parse ingredients
        ingredients = self._parse_ingredients(ingredients_text)

        # Parse steps
        steps = self._parse_steps(steps_text)

        # Build RCIP structure
        rcip_recipe = {
            "rcip_version": self.rcip_version,
            "id": f"rcip-{uuid.uuid4()}",
            "meta": {
                "name": name.strip(),
                "description": description or "",
                "author": author or "Unknown",
                "created_date": datetime.now().isoformat(),
                "source_url": source_url,
                "difficulty": kwargs.get('difficulty', 'intermediate'),
                "servings": {
                    "amount": kwargs.get('servings', 4),
                    "unit": "portions",
                    "adjustable": True
                },
                "prep_time_minutes": kwargs.get('prep_time_minutes'),
                "cook_time_minutes": kwargs.get('cook_time_minutes'),
                "total_time_minutes": kwargs.get('total_time_minutes'),
                "keywords": kwargs.get('keywords', []),
                "diet_labels": kwargs.get('diet_labels', []),
                "allergens": kwargs.get('allergens', [])
            },
            "ingredients": ingredients,
            "steps": steps,
            "extensions": {
                "version": 1,
                "times_cooked": 0,
                "parent_recipe_id": None
            }
        }

        return rcip_recipe

    def _parse_ingredients(self, text: str) -> List[Dict]:
        """
        Parse ingredients from raw text

        Expected formats:
        - 200g flour
        - 2 eggs
        - 1 cup sugar
        - 3 tablespoons olive oil
        """
        ingredients = []
        lines = text.strip().split('\n')

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Remove list markers (-, •, *, numbers)
            line = re.sub(r'^[-•*]\s*', '', line)
            line = re.sub(r'^\d+[\.)]\s*', '', line)

            # Try to parse amount and unit
            ingredient = self._parse_ingredient_line(line)
            if ingredient:
                ingredients.append(ingredient)

        return ingredients

    def _parse_ingredient_line(self, line: str) -> Optional[Dict]:
        """Parse a single ingredient line with improved unit detection"""
        # Pattern: number/fraction unit? name
        # Examples: "200g flour", "2 eggs", "1 1/2 cups sugar"

        # Try to match quantity patterns
        patterns = [
            # "200g flour", "2kg sugar", "500ml water"
            r'^(\d+(?:\.\d+)?)\s*([a-z]+)\s+(.+)$',
            # "2 eggs", "3 tomatoes"
            r'^(\d+(?:\.\d+)?)\s+(.+)$',
            # "1/2 cup sugar", "1 1/2 cups flour"
            r'^(\d+(?:\s+\d+)?/\d+)\s+([a-z]+)\s+(.+)$',
            # Just the ingredient name (no quantity)
            r'^([a-zA-Z\s]+)$'
        ]

        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()

                if len(groups) == 3:  # amount, unit, name
                    unit = self._normalize_unit(groups[1].lower())
                    return {
                        "name": groups[2].strip(),
                        "amount": self._parse_amount(groups[0]),
                        "unit": unit,
                        "category": self._guess_category(groups[2])
                    }
                elif len(groups) == 2:  # amount, name (no unit)
                    try:
                        amount = float(groups[0])
                        # Intelligent unit detection based on ingredient name
                        ingredient_name = groups[1].strip().lower()
                        unit = self._infer_unit_from_ingredient(
                            ingredient_name, amount)
                        return {
                            "name": groups[1].strip(),
                            "amount": amount,
                            "unit": unit,
                            "category": self._guess_category(groups[1])
                        }
                    except ValueError:
                        # groups[0] might be unit+name, groups[1] is rest
                        return {
                            "name": f"{groups[0]} {groups[1]}".strip(),
                            "amount": 1,
                            "unit": "as needed",
                            "category": self._guess_category(groups[1])
                        }
                elif len(groups) == 1:  # just name
                    return {
                        "name": groups[0].strip(),
                        "amount": 1,
                        "unit": "as needed",
                        "category": "other"
                    }

        # Fallback: return the whole line as ingredient name
        return {
            "name": line.strip(),
            "amount": 1,
            "unit": "as needed",
            "category": "other"
        }

    def _normalize_unit(self, unit: str) -> str:
        """Normalize unit variations to standard forms"""
        unit_mapping = {
            # Weight units
            'gram': 'g', 'grams': 'g', 'gr': 'g',
            'kilogram': 'kg', 'kilograms': 'kg', 'kilo': 'kg',
            'ounce': 'oz', 'ounces': 'oz',
            'pound': 'lb', 'pounds': 'lb', 'lbs': 'lb',
            # Liquid units
            'milliliter': 'ml', 'milliliters': 'ml', 'millilitre': 'ml', 'millilitres': 'ml',
            'liter': 'l', 'liters': 'l', 'litre': 'l', 'litres': 'l',
            'cup': 'cup', 'cups': 'cup',
            'tablespoon': 'tbsp', 'tablespoons': 'tbsp', 'tbsp': 'tbsp',
            'teaspoon': 'tsp', 'teaspoons': 'tsp', 'tsp': 'tsp',
            # Volume
            'floz': 'fl oz', 'fl.oz': 'fl oz',
            # Count
            'piece': 'pieces', 'pcs': 'pieces', 'pc': 'pieces'
        }

        return unit_mapping.get(unit.lower(), unit)

    def _infer_unit_from_ingredient(self, ingredient_name: str, amount: float) -> str:
        """Intelligently infer unit based on ingredient type and amount"""
        name_lower = ingredient_name.lower()

        # Countable items (eggs, tomatoes, apples, etc.)
        countable_keywords = ['egg', 'apple', 'tomato', 'onion', 'banana', 'potato',
                              'lemon', 'lime', 'orange', 'clove', 'bay leaf', 'leaf']
        if any(keyword in name_lower for keyword in countable_keywords):
            return 'pieces'

        # Liquids (should use ml)
        liquid_keywords = ['water', 'milk', 'oil', 'broth', 'stock', 'juice', 'wine',
                           'cream', 'sauce', 'vinegar', 'soy sauce']
        if any(keyword in name_lower for keyword in liquid_keywords):
            return 'ml'

        # Spices and herbs (typically small amounts in grams)
        spice_keywords = ['salt', 'pepper', 'cinnamon', 'cumin', 'paprika',
                          'oregano', 'basil', 'thyme', 'parsley', 'vanilla']
        if any(keyword in name_lower for keyword in spice_keywords):
            return 'g'

        # Meat, flour, sugar, vegetables (typically use grams)
        solid_keywords = ['flour', 'sugar', 'rice', 'pasta', 'meat', 'chicken',
                          'beef', 'pork', 'fish', 'cheese', 'butter']
        if any(keyword in name_lower for keyword in solid_keywords):
            return 'g'

        # Default: if amount is large (>10), likely grams, if small likely pieces
        return 'g' if amount > 10 else 'pieces'

    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        try:
            # Handle fractions like "1/2" or "1 1/2"
            if '/' in amount_str:
                parts = amount_str.split()
                if len(parts) == 2:  # "1 1/2"
                    whole = float(parts[0])
                    frac = parts[1].split('/')
                    return whole + (float(frac[0]) / float(frac[1]))
                else:  # "1/2"
                    frac = amount_str.split('/')
                    return float(frac[0]) / float(frac[1])
            else:
                return float(amount_str)
        except:
            return 1.0

    def _guess_category(self, ingredient_name: str) -> str:
        """Guess ingredient category from name"""
        name_lower = ingredient_name.lower()

        categories = {
            'vegetables': ['tomato', 'onion', 'garlic', 'carrot', 'potato', 'pepper', 'lettuce', 'spinach', 'celery'],
            'fruits': ['apple', 'banana', 'lemon', 'lime', 'orange', 'berry', 'strawberry'],
            'meat': ['chicken', 'beef', 'pork', 'lamb', 'turkey', 'fish', 'salmon', 'tuna'],
            'dairy': ['milk', 'cream', 'butter', 'cheese', 'yogurt', 'egg'],
            'grains': ['flour', 'rice', 'pasta', 'bread', 'oat', 'wheat'],
            'spices': ['salt', 'pepper', 'cinnamon', 'cumin', 'paprika', 'oregano', 'basil', 'thyme'],
            'oils': ['oil', 'olive oil', 'vegetable oil', 'butter'],
            'liquids': ['water', 'stock', 'broth', 'wine', 'juice']
        }

        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category

        return 'other'

    def _parse_steps(self, text: str) -> List[Dict]:
        """Parse cooking steps from raw text"""
        steps = []
        lines = text.strip().split('\n')
        step_number = 1

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line or len(line) < 10:
                continue

            # Remove step numbers
            line = re.sub(r'^\d+[\.)]\s*', '', line)
            line = re.sub(r'^Step\s+\d+[\.:]\s*',
                          '', line, flags=re.IGNORECASE)

            # Add step
            steps.append({
                "order": step_number,
                "instruction": line.strip(),
                "time_minutes": None,
                "equipment": []
            })

            step_number += 1

        return steps


class RecipeAnalyzer:
    """Analyze recipes for metadata extraction"""

    @staticmethod
    def estimate_times(steps: List[Dict], ingredients: List[Dict]) -> Dict:
        """Estimate prep and cook times from steps and ingredients"""
        # Simple heuristic: more steps and ingredients = more time
        prep_time = min(10 + len(ingredients) * 2, 30)
        cook_time = min(15 + len(steps) * 5, 90)

        return {
            'prep_time_minutes': prep_time,
            'cook_time_minutes': cook_time,
            'total_time_minutes': prep_time + cook_time
        }

    @staticmethod
    def detect_diet_labels(ingredients: List[Dict]) -> List[str]:
        """Detect diet labels from ingredients"""
        labels = set()

        # Check for meat
        meat_keywords = ['chicken', 'beef', 'pork',
                         'lamb', 'fish', 'turkey', 'meat']
        has_meat = any(
            any(keyword in ing['name'].lower() for keyword in meat_keywords)
            for ing in ingredients
        )

        # Check for dairy
        dairy_keywords = ['milk', 'cream', 'cheese', 'butter', 'yogurt']
        has_dairy = any(
            any(keyword in ing['name'].lower() for keyword in dairy_keywords)
            for ing in ingredients
        )

        # Check for eggs
        has_eggs = any('egg' in ing['name'].lower() for ing in ingredients)

        # Determine labels
        if not has_meat:
            labels.add('vegetarian')

        if not has_meat and not has_dairy and not has_eggs:
            labels.add('vegan')

        if not has_dairy:
            labels.add('dairy-free')

        return list(labels)

    @staticmethod
    def detect_allergens(ingredients: List[Dict]) -> List[str]:
        """
        Detect common allergens from ingredients

        Based on major food allergen groups:
        - Dairy (milk, cheese, butter, cream, yogurt)
        - Eggs
        - Fish
        - Shellfish (shrimp, crab, lobster, etc.)
        - Tree nuts (almonds, walnuts, cashews, etc.)
        - Peanuts
        - Wheat/Gluten
        - Soy
        - Sesame
        """
        allergens = set()

        # Allergen keyword mappings
        allergen_keywords = {
            'dairy': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey', 'casein', 'lactose', 'ghee'],
            'eggs': ['egg', 'mayonnaise', 'meringue', 'albumin'],
            'fish': ['fish', 'salmon', 'tuna', 'cod', 'trout', 'bass', 'flounder', 'anchovy', 'sardine', 'halibut'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'crayfish', 'prawn', 'scallop', 'clam', 'mussel', 'oyster', 'squid', 'octopus'],
            'tree_nuts': ['almond', 'walnut', 'cashew', 'pistachio', 'pecan', 'hazelnut', 'macadamia', 'brazil nut', 'pine nut', 'chestnut'],
            'peanuts': ['peanut', 'peanut butter', 'groundnut'],
            'wheat': ['wheat', 'flour', 'bread', 'pasta', 'spaghetti', 'penne', 'macaroni', 'noodle', 'couscous', 'bulgur', 'semolina', 'spelt', 'farro'],
            'gluten': ['wheat', 'barley', 'rye', 'flour', 'bread', 'pasta', 'spaghetti', 'penne', 'macaroni', 'noodle', 'seitan', 'malt'],
            'soy': ['soy', 'tofu', 'tempeh', 'edamame', 'miso', 'soy sauce', 'tamari'],
            'sesame': ['sesame', 'tahini', 'sesame oil', 'sesame seed']
        }

        # Check each ingredient against allergen keywords
        for ing in ingredients:
            ing_name = ing.get('name', '').lower()

            for allergen, keywords in allergen_keywords.items():
                if any(keyword in ing_name for keyword in keywords):
                    allergens.add(allergen)

        # Return sorted list for consistency
        return sorted(list(allergens))

    @staticmethod
    def estimate_difficulty(steps: List[Dict], ingredients: List[Dict]) -> str:
        """Estimate recipe difficulty"""
        complexity_score = len(steps) + len(ingredients)

        if complexity_score < 10:
            return 'beginner'
        elif complexity_score < 20:
            return 'intermediate'
        else:
            return 'advanced'
