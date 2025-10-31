"""
RCIP Converter - Recipe Interchange Protocol Converter
Converts raw recipe text into structured RCIP format
"""

import re
from typing import Dict, List, Optional, Tuple
from fractions import Fraction


class RCIPConverter:
    """Converts raw recipe text to RCIP structured format"""

    def __init__(self):
        self.unit_patterns = [
            'cup', 'cups', 'tablespoon', 'tablespoons', 'tbsp', 'teaspoon', 'teaspoons', 'tsp',
            'gram', 'grams', 'g', 'kilogram', 'kilograms', 'kg',
            'milliliter', 'milliliters', 'ml', 'liter', 'liters', 'l',
            'ounce', 'ounces', 'oz', 'pound', 'pounds', 'lb', 'lbs',
            'pinch', 'dash', 'handful', 'piece', 'pieces', 'slice', 'slices',
            'can', 'cans', 'jar', 'jars', 'package', 'packages', 'pkg'
        ]

    def convert(
        self,
        name: str,
        ingredients_text: str,
        steps_text: str,
        source_url: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Convert raw recipe text to RCIP format

        Args:
            name: Recipe name/title
            ingredients_text: Raw ingredients text (one per line)
            steps_text: Raw steps text (one per line)
            source_url: Optional source URL

        Returns:
            Dict with structure:
            {
                'meta': {'name': str, 'source_url': str, ...},
                'ingredients': List[Dict],
                'steps': List[Dict]
            }
        """
        # Parse ingredients
        ingredients = self._parse_ingredients(ingredients_text)

        # Parse steps
        steps = self._parse_steps(steps_text)

        # Build RCIP structure
        rcip_recipe = {
            'meta': {
                'name': name.strip(),
                'source_url': source_url or '',
            },
            'ingredients': ingredients,
            'steps': steps
        }

        return rcip_recipe

    def _parse_ingredients(self, text: str) -> List[Dict]:
        """Parse ingredients text into structured format"""
        if not text:
            return []

        ingredients = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line or len(line) < 2:
                continue

            # Try to parse quantity, unit, and name
            parsed = self._parse_ingredient_line(line)
            if parsed:
                ingredients.append(parsed)

        return ingredients

    def _parse_ingredient_line(self, line: str) -> Optional[Dict]:
        """Parse a single ingredient line"""
        try:
            # Remove common prefixes (numbers, bullets, etc.)
            line = re.sub(r'^[\d\.\)\-\*•]+\s*', '', line).strip()

            if not line:
                return None

            # Try to extract amount (fractions, decimals, ranges)
            amount = None
            unit = None
            name = line

            # Look for numbers at the start
            number_pattern = r'^([\d\s/.\-]+)'
            number_match = re.search(number_pattern, line)

            if number_match:
                amount_str = number_match.group(1).strip()
                try:
                    # Handle fractions like "1/2" or "1 1/2"
                    amount = self._parse_amount(amount_str)
                    # Remove amount from name
                    name = line[number_match.end():].strip()
                except:
                    amount = None

            # Look for unit
            for unit_name in self.unit_patterns:
                pattern = r'\b' + re.escape(unit_name) + r'\b'
                if re.search(pattern, name, re.IGNORECASE):
                    unit = unit_name.lower()
                    # Remove unit from name
                    name = re.sub(pattern, '', name, flags=re.IGNORECASE).strip()
                    break

            # Clean up name
            name = name.strip(' ,.-')

            if not name:
                return None

            return {
                'amount': amount,
                'unit': unit,
                'name': name,
                'original': line
            }

        except Exception as e:
            # If parsing fails, just return the original line as name
            return {
                'amount': None,
                'unit': None,
                'name': line.strip(),
                'original': line
            }

    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float (handles fractions)"""
        try:
            # Handle ranges like "1-2" -> take first number
            if '-' in amount_str and not amount_str.startswith('-'):
                amount_str = amount_str.split('-')[0].strip()

            # Handle fractions like "1/2" or "1 1/2"
            parts = amount_str.split()
            total = 0.0

            for part in parts:
                if '/' in part:
                    # Fraction
                    frac = Fraction(part)
                    total += float(frac)
                else:
                    # Regular number
                    total += float(part)

            return total if total > 0 else None

        except:
            return None

    def _parse_steps(self, text: str) -> List[Dict]:
        """Parse steps text into structured format"""
        if not text:
            return []

        steps = []
        lines = text.split('\n')

        step_number = 1
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue

            # Remove common prefixes (numbers, bullets, etc.)
            clean_line = re.sub(r'^[\d\.\)\-\*•]+\s*', '', line).strip()

            if clean_line:
                steps.append({
                    'order': step_number,
                    'instruction': clean_line,
                    'original': line
                })
                step_number += 1

        return steps


class RecipeAnalyzer:
    """Analyzes recipes and extracts metadata"""

    def __init__(self):
        # Diet label keywords
        self.diet_keywords = {
            'vegetarian': ['vegetarian', 'veggie', 'meatless'],
            'vegan': ['vegan', 'plant-based'],
            'gluten-free': ['gluten-free', 'gluten free', 'gf'],
            'dairy-free': ['dairy-free', 'dairy free', 'lactose-free'],
            'low-carb': ['low-carb', 'low carb', 'keto', 'ketogenic'],
            'paleo': ['paleo', 'caveman'],
            'whole30': ['whole30'],
        }

        # Allergen keywords
        self.allergen_keywords = {
            'dairy': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey'],
            'eggs': ['egg', 'eggs'],
            'fish': ['fish', 'salmon', 'tuna', 'cod', 'halibut'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'shellfish', 'clams', 'mussels'],
            'tree_nuts': ['almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'hazelnut'],
            'peanuts': ['peanut', 'peanuts'],
            'wheat': ['wheat', 'flour', 'bread', 'pasta'],
            'soy': ['soy', 'tofu', 'tempeh', 'edamame'],
        }

        # Time-related keywords
        self.time_keywords = [
            'minute', 'minutes', 'min', 'hour', 'hours', 'hr', 'hrs',
            'second', 'seconds', 'sec', 'day', 'days', 'overnight'
        ]

    def estimate_times(
        self,
        steps: List[Dict],
        ingredients: List[Dict]
    ) -> Dict:
        """
        Estimate prep and cook times based on steps

        Args:
            steps: List of step dictionaries
            ingredients: List of ingredient dictionaries

        Returns:
            Dict with 'prep_time', 'cook_time', 'total_time' (in minutes)
        """
        prep_time = 0
        cook_time = 0

        # Estimate based on number of ingredients (rough heuristic)
        prep_time += len(ingredients) * 2  # 2 minutes per ingredient

        # Estimate based on steps
        for step in steps:
            instruction = step.get('instruction', '').lower()

            # Look for explicit time mentions
            time_match = re.search(
                r'(\d+)\s*(minute|minutes|min|hour|hours|hr)',
                instruction,
                re.IGNORECASE
            )

            if time_match:
                amount = int(time_match.group(1))
                unit = time_match.group(2).lower()

                if 'hour' in unit or unit == 'hr':
                    amount *= 60  # Convert to minutes

                # Determine if prep or cook
                if any(word in instruction for word in ['bake', 'cook', 'simmer', 'boil', 'roast', 'grill', 'fry']):
                    cook_time += amount
                else:
                    prep_time += amount
            else:
                # No explicit time - estimate based on action
                if any(word in instruction for word in ['chop', 'dice', 'slice', 'cut', 'peel', 'mince']):
                    prep_time += 3
                elif any(word in instruction for word in ['mix', 'stir', 'combine', 'blend']):
                    prep_time += 2
                elif any(word in instruction for word in ['bake', 'roast', 'simmer']):
                    cook_time += 30  # Default 30 min for cooking
                elif any(word in instruction for word in ['boil', 'fry', 'sauté']):
                    cook_time += 10  # Default 10 min
                else:
                    prep_time += 2  # Default 2 min per step

        # Minimum times
        prep_time = max(prep_time, 5)
        cook_time = max(cook_time, 0)

        total_time = prep_time + cook_time

        return {
            'prep_time': prep_time,
            'cook_time': cook_time,
            'total_time': total_time
        }

    def detect_diet_labels(self, ingredients: List[Dict]) -> List[str]:
        """
        Detect diet labels from ingredients

        Args:
            ingredients: List of ingredient dictionaries

        Returns:
            List of diet label strings
        """
        labels = []

        # Combine all ingredient names
        all_text = ' '.join([
            ing.get('name', '').lower() + ' ' + ing.get('original', '').lower()
            for ing in ingredients
        ])

        # Check for meat
        has_meat = any(word in all_text for word in ['chicken', 'beef', 'pork', 'lamb', 'turkey', 'meat', 'fish', 'salmon'])

        # Check for animal products
        has_dairy = any(word in all_text for word in ['milk', 'cheese', 'butter', 'cream', 'yogurt'])
        has_eggs = any(word in all_text for word in ['egg', 'eggs'])

        # Determine labels
        if not has_meat:
            labels.append('vegetarian')
            if not has_dairy and not has_eggs:
                labels.append('vegan')

        # Check explicit diet keywords
        for diet_label, keywords in self.diet_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                if diet_label not in labels:
                    labels.append(diet_label)

        return labels

    def detect_allergens(self, ingredients: List[Dict]) -> List[str]:
        """
        Detect allergens from ingredients

        Args:
            ingredients: List of ingredient dictionaries

        Returns:
            List of allergen strings
        """
        allergens = []

        # Combine all ingredient names
        all_text = ' '.join([
            ing.get('name', '').lower() + ' ' + ing.get('original', '').lower()
            for ing in ingredients
        ])

        # Check each allergen
        for allergen, keywords in self.allergen_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                allergens.append(allergen)

        return allergens

    def estimate_difficulty(
        self,
        steps: List[Dict],
        ingredients: List[Dict]
    ) -> str:
        """
        Estimate recipe difficulty

        Args:
            steps: List of step dictionaries
            ingredients: List of ingredient dictionaries

        Returns:
            'easy', 'medium', or 'hard'
        """
        difficulty_score = 0

        # Factor 1: Number of ingredients
        if len(ingredients) > 15:
            difficulty_score += 2
        elif len(ingredients) > 10:
            difficulty_score += 1

        # Factor 2: Number of steps
        if len(steps) > 12:
            difficulty_score += 2
        elif len(steps) > 8:
            difficulty_score += 1

        # Factor 3: Complex techniques
        complex_keywords = [
            'tempering', 'folding', 'caramelize', 'reduce', 'deglaze',
            'julienne', 'brunoise', 'chiffonade', 'blanch', 'poach',
            'braise', 'confit', 'sous vide', 'flambé'
        ]

        all_steps_text = ' '.join([step.get('instruction', '').lower() for step in steps])

        for keyword in complex_keywords:
            if keyword in all_steps_text:
                difficulty_score += 1

        # Determine difficulty
        if difficulty_score <= 2:
            return 'easy'
        elif difficulty_score <= 5:
            return 'medium'
        else:
            return 'hard'



