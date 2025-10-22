import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import openai
# Deprecated - TODO: Remove if OpenAI is not being used
# from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from django.core.cache import cache

from config.ai_config import AIConfig
from config.nutrition_config import NutritionConfig
from config.external_services import MockStoreServices

# Initialize OpenAI
openai.api_key = AIConfig.OPENAI_API_KEY

# Pydantic models for structured output


class ParsedShoppingItem(BaseModel):
    """Structured shopping item from natural language"""
    name: str = Field(description="Item name")
    quantity: float = Field(description="Quantity needed")
    unit: str = Field(description="Unit of measurement")
    category: str = Field(description="Item category")
    notes: Optional[str] = Field(description="Additional notes")


class RecipeSuggestion(BaseModel):
    """Structured recipe suggestion"""
    name: str = Field(description="Recipe name")
    ingredients_needed: List[str] = Field(description="Required ingredients")
    missing_ingredients: List[str] = Field(
        description="Ingredients not in inventory")
    prep_time_minutes: int = Field(description="Preparation time")
    difficulty: str = Field(description="Difficulty level")
    nutrition_per_serving: Dict[str, float] = Field(
        description="Nutrition information")
    instructions: List[str] = Field(description="Cooking instructions")


class NutritionAdvice(BaseModel):
    """Structured nutrition coaching advice"""
    current_status: str = Field(description="Current nutrition status")
    recommendations: List[str] = Field(
        description="Actionable recommendations")
    meal_suggestions: List[str] = Field(description="Suggested meals")
    macro_adjustments: Dict[str, str] = Field(
        description="Macro nutrient adjustments needed")


class AIOrchestrator:
    """Main AI orchestration service"""

    def __init__(self):
        try:
            self.llm = ChatOpenAI(
                temperature=AIConfig.OPENAI_TEMPERATURE,
                model=AIConfig.OPENAI_MODEL,  # Changed from model_name to model
                api_key=AIConfig.OPENAI_API_KEY  # Changed from openai_api_key to api_key
            )
        except Exception as e:
            print(f"[ERROR] Failed to initialize ChatOpenAI: {e}")
            # Fallback: try with minimal parameters
            try:
                self.llm = ChatOpenAI(
                    model=AIConfig.OPENAI_MODEL,
                    api_key=AIConfig.OPENAI_API_KEY
                )
            except Exception as e2:
                print(f"[ERROR] Fallback initialization also failed: {e2}")
                self.llm = None
        self.shopping_assistant = ShoppingAssistant(self.llm)
        self.recipe_assistant = RecipeAssistant(self.llm)
        self.nutrition_coach = NutritionCoach(self.llm)
        self.store_services = MockStoreServices()

    async def process_natural_language(self, text: str, context: Dict) -> Dict:
        """Route natural language to appropriate agent"""
        # Note: We don't return error here, we let fallback processing happen
        # The individual assistants have their own fallback logic

        intent = await self._detect_intent(text)

        if intent == 'shopping':
            return await self.shopping_assistant.process(text, context)
        elif intent == 'recipe':
            return await self.recipe_assistant.process(text, context)
        elif intent == 'nutrition':
            return await self.nutrition_coach.process(text, context)
        else:
            return {
                'success': False,
                'message': 'Could not understand the request. Please try again.'
            }

    async def _detect_intent(self, text: str) -> str:
        """Detect user intent from natural language"""
        if self.llm is None:
            # Fallback: simple keyword matching
            text_lower = text.lower()
            if any(word in text_lower for word in ['buy', 'shopping', 'list', 'store', 'purchase', 'get']):
                return 'shopping'
            elif any(word in text_lower for word in ['recipe', 'cook', 'meal', 'dish', 'food', 'make']):
                return 'recipe'
            elif any(word in text_lower for word in ['calories', 'nutrition', 'protein', 'carbs', 'health', 'diet']):
                return 'nutrition'
            return 'shopping'  # Default to shopping

        prompt = f"""
        Classify the following text into one of these categories:
        - shopping (adding items, creating lists, store orders)
        - recipe (meal ideas, cooking, ingredients)
        - nutrition (calories, macros, health goals)
        
        Text: {text}
        
        Return only the category name.
        """

        response = await self.llm.apredict(prompt)
        return response.strip().lower()

    async def generate_nutrition_insights(self, user_id: int) -> List[Dict]:
        """Generate nutrition insights for user"""
        # In production, fetch from database
        # Here we'll return mock insights
        return await self.nutrition_coach.generate_insights(user_id)

    async def coordinate_partner_goals(self, couple_id: int) -> Dict:
        """Coordinate nutrition goals between partners"""
        # Mock implementation
        return {
            'shared_goals': {
                'weekly_calories': 14000,
                'protein_target': 700,
                'meal_sync': True
            },
            'recommendations': [
                'Consider meal prepping together on Sundays',
                'Your protein intake is 20% below target',
                'Great job on vegetable consumption!'
            ]
        }


class ShoppingAssistant:
    """AI agent for shopping list management"""

    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=ParsedShoppingItem)

    async def process(self, text: str, context: Dict) -> Dict:
        """Process shopping-related requests"""

        if self.llm is None:
            # Fallback: basic text parsing
            return await self._fallback_process(text, context)

        # Check for simple add intent
        if any(word in text.lower() for word in ['add', 'buy', 'need', 'get']):
            items = await self.parse_shopping_items(text, context)
            return {
                'success': True,
                'action': 'add_items',
                'items': items,
                'message': f'Added {len(items)} items to your list'
            }

        # Check for nutrition-aware suggestions
        if 'suggest' in text.lower() or 'recommend' in text.lower():
            suggestions = await self.generate_suggestions(context)
            return {
                'success': True,
                'action': 'suggestions',
                'items': suggestions,
                'message': 'Here are some suggestions based on your nutrition goals'
            }

        return {
            'success': False,
            'message': 'Could not process shopping request'
        }

    async def _fallback_process(self, text: str, context: Dict) -> Dict:
        """Fallback processing without AI"""
        import re

        # Simple pattern matching for items
        items = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to extract quantity and item name
            # Pattern: "number unit item" or "item"
            match = re.search(r'(\d+\.?\d*)\s*(\w+)?\s+(.+)', line)
            if match:
                quantity = float(match.group(1))
                unit = match.group(2) or 'unit'
                name = match.group(3)
            else:
                quantity = 1
                unit = 'unit'
                name = line

            items.append({
                'name': name.strip(),
                'quantity': quantity,
                'unit': unit,
                'category': 'other',
                'notes': 'Added via basic parsing (AI unavailable)'
            })

        if not items:
            # If no items parsed, treat whole text as one item
            items.append({
                'name': text.strip(),
                'quantity': 1,
                'unit': 'unit',
                'category': 'other',
                'notes': 'Added via basic parsing (AI unavailable)'
            })

        return {
            'success': True,
            'action': 'add_items',
            'items': items,
            'message': f'Added {len(items)} item(s) using basic parsing (AI unavailable)'
        }

    async def parse_shopping_items(self, text: str, context: Dict) -> List[Dict]:
        """Parse natural language into structured shopping items"""

        if self.llm is None:
            result = await self._fallback_process(text, context)
            return result.get('items', [])

        prompt = ChatPromptTemplate.from_messages([
            ("system", AIConfig.SHOPPING_ASSISTANT_PROMPT),
            ("human", """
            Parse this shopping request into structured items:
            "{text}"
            
            Context:
            - Current inventory: {inventory}
            - User preferences: {preferences}
            
            Return a list of items with name, quantity, unit, category, and notes.
            Categories: produce, dairy, meat, bakery, frozen, pantry, beverages, snacks, household, other
            """)
        ])

        # Format the prompt
        formatted = prompt.format_messages(
            text=text,
            inventory=context.get('inventory', []),
            preferences=context.get('preferences', {}),
            partner_context=context.get('partner_context', {})
        )

        # Get response from LLM
        response = await self.llm.apredict_messages(formatted)

        # Parse into structured items
        try:
            # Simple parsing for MVP
            items = []
            lines = response.content.split('\n')
            for line in lines:
                if line.strip():
                    # Basic parsing logic
                    parts = line.split(',')
                    if len(parts) >= 2:
                        items.append({
                            'name': parts[0].strip(),
                            'quantity': 1,
                            'unit': 'unit',
                            'category': 'other',
                            'notes': ''
                        })

            return items if items else [
                {'name': text, 'quantity': 1, 'unit': 'unit',
                    'category': 'other', 'notes': ''}
            ]
        except Exception as e:
            print(f"Error parsing items: {e}")
            return [{
                'name': text,
                'quantity': 1,
                'unit': 'unit',
                'category': 'other',
                'notes': ''
            }]

    async def generate_suggestions(self, context: Dict) -> List[Dict]:
        """Generate shopping suggestions based on nutrition goals"""

        suggestions = []

        # Check protein goals
        if context.get('protein_deficit', 0) > 20:
            suggestions.extend([
                {'name': 'Chicken breast', 'quantity': 500,
                    'unit': 'g', 'category': 'meat'},
                {'name': 'Greek yogurt', 'quantity': 3,
                    'unit': 'cups', 'category': 'dairy'},
                {'name': 'Eggs', 'quantity': 12,
                    'unit': 'units', 'category': 'dairy'}
            ])

        # Check for low inventory items
        if context.get('low_stock_items'):
            for item in context['low_stock_items']:
                suggestions.append({
                    'name': item['name'],
                    'quantity': item['suggested_quantity'],
                    'unit': item['unit'],
                    'category': item['category']
                })

        return suggestions


class RecipeAssistant:
    """AI agent for recipe generation and meal planning"""

    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=RecipeSuggestion)

    async def process(self, text: str, context: Dict) -> Dict:
        """Process recipe-related requests"""

        if 'what can i make' in text.lower() or 'recipe' in text.lower():
            recipes = await self.generate_recipes(
                context.get('available_ingredients', []),
                context.get('dietary_restrictions', []),
                context.get('nutrition_goals', {})
            )
            return {
                'success': True,
                'action': 'show_recipes',
                'recipes': recipes,
                'message': f'Found {len(recipes)} recipes you can make'
            }

        return {
            'success': False,
            'message': 'Could not process recipe request'
        }

    async def generate_recipes(
        self,
        ingredients: List[str],
        restrictions: List[str],
        nutrition_goals: Dict
    ) -> List[Dict]:
        """Generate recipes based on available ingredients"""

        prompt = f"""
        Generate 3 recipes using these ingredients: {ingredients}
        Dietary restrictions: {restrictions}
        Nutrition goals: {nutrition_goals}
        
        For each recipe provide:
        - Name
        - Required ingredients
        - Prep time
        - Difficulty (easy/medium/hard)
        - Nutrition per serving
        - Brief instructions
        """

        response = await self.llm.apredict(prompt)

        # Parse response into structured recipes
        recipes = []

        # Mock recipes for MVP
        if 'chicken' in str(ingredients).lower():
            recipes.append({
                'name': 'Grilled Chicken Salad',
                'ingredients_needed': ['chicken breast', 'lettuce', 'tomatoes', 'olive oil'],
                'missing_ingredients': [],
                'prep_time_minutes': 20,
                'difficulty': 'easy',
                'nutrition_per_serving': {
                    'calories': 350,
                    'protein': 40,
                    'carbs': 15,
                    'fat': 15
                },
                'instructions': [
                    'Season chicken with salt and pepper',
                    'Grill for 6-7 minutes per side',
                    'Prepare salad greens',
                    'Slice chicken and serve over salad'
                ]
            })

        recipes.append({
            'name': 'Mediterranean Bowl',
            'ingredients_needed': ['rice', 'cucumber', 'tomatoes', 'feta', 'olive oil'],
            'missing_ingredients': ['feta'],
            'prep_time_minutes': 30,
            'difficulty': 'easy',
            'nutrition_per_serving': {
                'calories': 450,
                'protein': 15,
                'carbs': 65,
                'fat': 18
            },
            'instructions': [
                'Cook rice according to package',
                'Dice vegetables',
                'Mix with olive oil and lemon',
                'Top with feta cheese'
            ]
        })

        return recipes


class NutritionCoach:
    """AI agent for nutrition coaching and tracking"""

    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=NutritionAdvice)

    async def process(self, text: str, context: Dict) -> Dict:
        """Process nutrition-related requests"""

        if 'calorie' in text.lower() or 'macro' in text.lower():
            analysis = await self.analyze_nutrition(text, context)
            return {
                'success': True,
                'action': 'nutrition_analysis',
                'data': analysis,
                'message': 'Here\'s your nutrition analysis'
            }

        if 'advice' in text.lower() or 'help' in text.lower():
            advice = await self.generate_advice(context)
            return {
                'success': True,
                'action': 'coaching_advice',
                'advice': advice,
                'message': 'Here\'s your personalized nutrition advice'
            }

        return {
            'success': False,
            'message': 'Could not process nutrition request'
        }

    async def analyze_nutrition(self, text: str, context: Dict) -> Dict:
        """Analyze nutrition from food description"""

        # Extract food items from text
        prompt = f"""
        Extract food items and quantities from this text: "{text}"
        
        Calculate approximate nutrition (calories, protein, carbs, fat) for each item.
        Return total nutrition values.
        """

        response = await self.llm.apredict(prompt)

        # Mock nutrition data
        return {
            'foods_detected': ['chicken salad 200g'],
            'total_nutrition': {
                'calories': 350,
                'protein': 40,
                'carbs': 15,
                'fat': 15
            },
            'meal_type': 'lunch',
            'quality_score': 8.5
        }

    async def generate_advice(self, context: Dict) -> Dict:
        """Generate personalized nutrition advice"""

        current_stats = context.get('current_stats', {})
        goals = context.get('goals', {})
        recent_meals = context.get('recent_meals', [])

        prompt = f"""
        Generate nutrition coaching advice:
        Current stats: {current_stats}
        Goals: {goals}
        Recent meals: {recent_meals}
        
        Provide:
        - Current status assessment
        - 3 specific recommendations
        - 2 meal suggestions
        - Macro adjustments needed
        """

        response = await self.llm.apredict(prompt)

        # Return structured advice
        return {
            'current_status': 'You\'re 200 calories below your daily target',
            'recommendations': [
                'Add a protein-rich snack in the afternoon',
                'Increase water intake to 8 glasses per day',
                'Consider meal prepping on Sundays'
            ],
            'meal_suggestions': [
                'Greek yogurt with berries and granola (300 cal, 20g protein)',
                'Grilled salmon with quinoa and vegetables (450 cal, 35g protein)'
            ],
            'macro_adjustments': {
                'protein': '+20g',
                'carbs': 'on target',
                'fat': '-10g'
            }
        }

    async def generate_insights(self, user_id: int) -> List[Dict]:
        """Generate weekly nutrition insights"""

        # Mock insights
        return [
            {
                'type': 'achievement',
                'title': 'Protein Goal Met!',
                'description': 'You hit your protein target 5 days this week',
                'icon': 'trophy'
            },
            {
                'type': 'suggestion',
                'title': 'Morning Nutrition',
                'description': 'Try adding protein to breakfast for better satiety',
                'icon': 'lightbulb'
            },
            {
                'type': 'warning',
                'title': 'Hydration Alert',
                'description': 'Water intake is 30% below recommended',
                'icon': 'water'
            }
        ]
