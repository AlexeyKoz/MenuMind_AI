"""
Nutrition Calculator Service - Calculates recipe nutrition from IML data
NO AI CALLS - uses cached nutrition_per_100g from IML
"""
from typing import Dict, List, Optional
from decimal import Decimal
from .models import IngredientCache


class NutritionCalculator:
    """Calculate recipe nutrition from IML ingredient data"""

    # Nutrients we track
    NUTRIENTS = [
        'calories',
        'protein',      # grams
        'fat',          # grams
        'carbohydrates',  # grams (also check 'carbs')
        'fiber',        # grams
        'sugar',        # grams
        'sodium',       # mg
        'potassium',    # mg
        'vitamin_c',    # mg
        'calcium',      # mg
        'iron',         # mg
    ]

    def __init__(self):
        pass

    def calculate_recipe_nutrition(
        self,
        ingredients: List[Dict],
        servings: int = 4
    ) -> Dict:
        """
        Calculate nutrition for entire recipe

        Args:
            ingredients: List of ingredients with structure:
                [
                    {
                        "ingredient_key": "beet-red",
                        "quantity": 500,
                        "unit": "g"
                    },
                    {
                        "ingredient_key": "beef-with-bone",
                        "quantity": 700,
                        "unit": "g"
                    }
                ]
            servings: Number of servings (default: 4)

        Returns:
            {
                "per_serving": {
                    "calories": 380,
                    "protein": 26,
                    "fat": 15,
                    ...
                },
                "total": {
                    "calories": 1520,
                    "protein": 104,
                    ...
                },
                "coverage": 0.95,  # 95% of ingredients have nutrition data
                "missing_ingredients": ["ingredient-key-without-data"]
            }
        """
        if not ingredients or servings <= 0:
            return self._empty_nutrition()

        # Accumulate totals
        totals = {nutrient: 0.0 for nutrient in self.NUTRIENTS}
        ingredients_with_data = 0
        missing_ingredients = []

        for ingredient in ingredients:
            ingredient_key = ingredient.get('ingredient_key')
            quantity = ingredient.get('quantity', 0)
            unit = ingredient.get('unit', 'g')

            if not ingredient_key:
                continue

            # Get nutrition from IML
            nutrition_data = self.get_ingredient_nutrition(ingredient_key)

            if nutrition_data:
                # Calculate for this ingredient's quantity
                ingredient_nutrition = self._calculate_for_quantity(
                    nutrition_data,
                    quantity,
                    unit
                )

                if ingredient_nutrition:
                    ingredients_with_data += 1
                    # Add to totals
                    for nutrient in self.NUTRIENTS:
                        totals[nutrient] += ingredient_nutrition.get(
                            nutrient, 0)
                else:
                    missing_ingredients.append(ingredient_key)
            else:
                missing_ingredients.append(ingredient_key)

        # Calculate coverage
        coverage = ingredients_with_data / \
            len(ingredients) if ingredients else 0

        # Calculate per serving
        per_serving = {
            nutrient: round(totals[nutrient] / servings, 2)
            for nutrient in self.NUTRIENTS
        }

        # Round totals
        totals_rounded = {
            nutrient: round(totals[nutrient], 2)
            for nutrient in self.NUTRIENTS
        }

        return {
            'per_serving': per_serving,
            'total': totals_rounded,
            'coverage': round(coverage, 2),
            'missing_ingredients': missing_ingredients,
            'servings': servings
        }

    def get_ingredient_nutrition(self, ingredient_key: str) -> Optional[Dict]:
        """
        Get nutrition_per_100g from IML cache

        Args:
            ingredient_key: Ingredient key (e.g., "tomatoes-red-ripe")

        Returns:
            nutrition_per_100g dict or None if not found
        """
        try:
            ingredient = IngredientCache.objects.get(
                ingredient_key=ingredient_key)
            nutrition = ingredient.nutrition_per_100g

            if nutrition and isinstance(nutrition, dict):
                return nutrition

            return None
        except IngredientCache.DoesNotExist:
            return None

    def _calculate_for_quantity(
        self,
        nutrition_per_100g: Dict,
        quantity: float,
        unit: str
    ) -> Optional[Dict]:
        """
        Calculate nutrition for specific quantity

        Args:
            nutrition_per_100g: Nutrition data per 100g
            quantity: Amount (e.g., 500)
            unit: Unit (must be weight: g, kg, oz, lb)

        Returns:
            Scaled nutrition dict
        """
        # Convert quantity to grams first
        quantity_in_grams = self._convert_to_grams(quantity, unit)

        if quantity_in_grams is None:
            return None

        # Scale nutrition (per 100g → per quantity)
        multiplier = quantity_in_grams / 100.0

        scaled = {}
        for nutrient in self.NUTRIENTS:
            # Handle both 'carbohydrates' and 'carbs' keys
            value = nutrition_per_100g.get(nutrient)
            if value is None and nutrient == 'carbohydrates':
                value = nutrition_per_100g.get('carbs')

            if value is not None:
                scaled[nutrient] = float(value) * multiplier
            else:
                scaled[nutrient] = 0.0

        return scaled

    def _convert_to_grams(self, quantity: float, unit: str) -> Optional[float]:
        """
        Convert quantity to grams

        Only supports weight units (g, kg, oz, lb)
        Returns None for non-weight units (ml, L, pcs, etc.)
        """
        unit = unit.lower().strip()

        conversions = {
            'g': 1.0,
            'kg': 1000.0,
            'oz': 28.3495,
            'lb': 453.592,
            'mg': 0.001
        }

        if unit in conversions:
            return quantity * conversions[unit]

        # Not a weight unit - can't calculate nutrition
        return None

    def _empty_nutrition(self) -> Dict:
        """Return empty nutrition result"""
        empty = {nutrient: 0.0 for nutrient in self.NUTRIENTS}
        return {
            'per_serving': empty,
            'total': empty,
            'coverage': 0.0,
            'missing_ingredients': [],
            'servings': 0
        }

    def format_nutrition_label(self, nutrition: Dict) -> str:
        """
        Format nutrition data as readable label

        Args:
            nutrition: per_serving dict

        Returns:
            Formatted string (Nutrition Facts style)
        """
        label = "Nutrition Facts (per serving)\n"
        label += "=" * 30 + "\n"
        label += f"Calories: {nutrition.get('calories', 0):.0f}\n"
        label += f"Protein: {nutrition.get('protein', 0):.1f}g\n"
        label += f"Fat: {nutrition.get('fat', 0):.1f}g\n"
        label += f"Carbohydrates: {nutrition.get('carbohydrates', 0):.1f}g\n"
        label += f"  Fiber: {nutrition.get('fiber', 0):.1f}g\n"
        label += f"  Sugar: {nutrition.get('sugar', 0):.1f}g\n"
        label += f"Sodium: {nutrition.get('sodium', 0):.0f}mg\n"

        return label
