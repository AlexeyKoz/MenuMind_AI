from typing import Dict, List


class NutritionConfig:
    """Nutrition API and calculation configuration"""

    # API Keys
    NUTRITIONIX_APP_ID = 'your-app-id'
    NUTRITIONIX_API_KEY = 'your-api-key'
    USDA_API_KEY = 'your-usda-key'

    # Macro Targets
    DEFAULT_CALORIES_MALE = 2500
    DEFAULT_CALORIES_FEMALE = 2000
    DEFAULT_PROTEIN_RATIO = 0.30  # 30% of calories
    DEFAULT_CARBS_RATIO = 0.40    # 40% of calories
    DEFAULT_FAT_RATIO = 0.30       # 30% of calories

    # Israeli Food Database (Mock)
    ISRAELI_FOODS = {
        'hummus': {'calories': 166, 'protein': 8, 'carbs': 14, 'fat': 10},
        'falafel': {'calories': 333, 'protein': 13, 'carbs': 32, 'fat': 18},
        'shakshuka': {'calories': 185, 'protein': 11, 'carbs': 8, 'fat': 13},
        'sabich': {'calories': 450, 'protein': 18, 'carbs': 45, 'fat': 22},
        'tahini': {'calories': 89, 'protein': 3, 'carbs': 3, 'fat': 8}
    }

    # Micronutrients to Track
    TRACKED_MICRONUTRIENTS = [
        'vitamin_d', 'vitamin_b12', 'iron', 'calcium', 'fiber'
    ]
