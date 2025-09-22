import os
from typing import Dict, Any


class AIConfig:
    """AI configuration management for MenuMind AI"""

    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'sk-proj-...')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4')
    OPENAI_TEMPERATURE = float(os.environ.get('OPENAI_TEMPERATURE', '0.7'))

    # AI Features Toggle
    AI_FEATURES_ENABLED = os.environ.get(
        'AI_FEATURES_ENABLED', 'True') == 'True'
    NUTRITION_AI_ENABLED = os.environ.get(
        'NUTRITION_AI_ENABLED', 'True') == 'True'
    MOCK_MODE = os.environ.get('MOCK_MODE', 'True') == 'True'

    # Rate Limiting
    MAX_AI_REQUESTS_PER_DAY = int(
        os.environ.get('MAX_AI_REQUESTS_PER_DAY', '100'))
    MAX_AI_REQUESTS_PER_MINUTE = int(
        os.environ.get('MAX_AI_REQUESTS_PER_MINUTE', '10'))

    # Prompt Templates
    SHOPPING_ASSISTANT_PROMPT = """You are a helpful shopping assistant for a family food management app.
    Parse natural language shopping requests and return structured data.
    Consider nutrition goals and dietary restrictions.
    Current inventory: {inventory}
    User preferences: {preferences}
    Partner context: {partner_context}
    """

    RECIPE_ASSISTANT_PROMPT = """You are a recipe assistant optimizing for nutrition and available ingredients.
    Available ingredients: {ingredients}
    Dietary restrictions: {restrictions}
    Nutrition goals: {goals}
    Generate recipes that match these constraints.
    """

    NUTRITION_COACH_PROMPT = """You are a nutrition coach helping users achieve their health goals.
    Current stats: {current_stats}
    Goals: {goals}
    Recent meals: {recent_meals}
    Provide actionable coaching advice.
    """

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Return all configuration as dictionary"""
        return {
            'openai_key': cls.OPENAI_API_KEY,
            'model': cls.OPENAI_MODEL,
            'temperature': cls.OPENAI_TEMPERATURE,
            'features_enabled': cls.AI_FEATURES_ENABLED,
            'mock_mode': cls.MOCK_MODE
        }
