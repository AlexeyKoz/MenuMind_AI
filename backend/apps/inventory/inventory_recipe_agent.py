"""
Inventory Recipe Agent - AI-powered recipe suggestions from user's inventory

This agent provides intelligent recipe suggestions based on what the user has in their inventory.
It uses a multi-stage approach:
1. Generate short recipe briefs (5 at a time, cached for 24h or until inventory changes)
2. Allow user to "generate more" (up to 25 variants total)
3. Generate full recipes only when user selects a brief they like
4. Use deduplication to avoid creating duplicate recipes
5. Support lazy multilingual translation

AI Architecture:
- Primary: Gemini for both brief and full recipe generation
- Fallback: Groq if Gemini fails
- Translation: IML + Google Translate with Gemini fallback, then Groq fallback
"""

import logging
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import google.generativeai as genai
from groq import Groq

logger = logging.getLogger(__name__)


class InventoryRecipeAgent:
    """
    AI agent for generating recipe suggestions from inventory items
    """
    
    def __init__(self):
        """Initialize AI clients"""
        # Initialize Gemini (primary)
        gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-lite')
            logger.info("✅ Gemini initialized as primary AI")
        else:
            self.gemini_model = None
            logger.warning("⚠️ Gemini API key not found")
        
        # Initialize Groq (fallback)
        groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
        if groq_api_key:
            self.groq_client = Groq(api_key=groq_api_key)
            logger.info("✅ Groq initialized as fallback AI")
        else:
            self.groq_client = None
            logger.warning("⚠️ Groq API key not found")
    
    def _get_cache_key(self, user_id: str, inventory_hash: str) -> str:
        """Generate cache key for recipe buffer"""
        return f"inventory_recipes:{user_id}:{inventory_hash}"
    
    def _get_inventory_hash(self, inventory_items: List[Dict]) -> str:
        """
        Generate hash of inventory items to detect changes
        Uses item names and quantities (ignoring small quantity changes)
        """
        # Sort items by name for consistent hashing
        sorted_items = sorted(inventory_items, key=lambda x: x.get('name', ''))
        
        # Create a string representation (name + rounded quantity)
        inventory_str = '_'.join([
            f"{item.get('name', '')}:{int(item.get('quantity', 0))}"
            for item in sorted_items
        ])
        
        # Use simple hash
        import hashlib
        return hashlib.md5(inventory_str.encode()).hexdigest()[:16]
    
    def _call_gemini(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Call Gemini API with retries"""
        if not self.gemini_model:
            logger.warning("[INV AGENT] Gemini not available")
            return None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[INV AGENT] 🤖 Calling Gemini (attempt {attempt + 1}/{max_retries})")
                response = self.gemini_model.generate_content(prompt)
                result = response.text.strip()
                logger.info(f"[INV AGENT] ✅ Gemini returned {len(result)} chars")
                return result
            except Exception as e:
                logger.warning(f"[INV AGENT] ⚠️ Gemini attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return None
        
        return None
    
    def _call_groq(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Call Groq API with retries"""
        if not self.groq_client:
            logger.warning("[INV AGENT] Groq not available")
            return None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[INV AGENT] 🤖 Calling Groq (attempt {attempt + 1}/{max_retries})")
                response = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000
                )
                result = response.choices[0].message.content.strip()
                logger.info(f"[INV AGENT] ✅ Groq returned {len(result)} chars")
                return result
            except Exception as e:
                logger.warning(f"[INV AGENT] ⚠️ Groq attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return None
        
        return None
    
    def _call_ai(self, prompt: str) -> Optional[str]:
        """
        Call AI with fallback chain: Gemini -> Groq
        """
        # Try Gemini first (primary)
        result = self._call_gemini(prompt)
        if result:
            return result
        
        logger.info("[INV AGENT] 🔄 Falling back to Groq")
        
        # Try Groq (fallback)
        result = self._call_groq(prompt)
        if result:
            return result
        
        logger.error("[INV AGENT] ❌ All AI providers failed")
        return None
    
    def generate_recipe_briefs(
        self,
        user_id: str,
        inventory_items: List[Dict],
        count: int = 5,
        offset: int = 0
    ) -> Dict:
        """
        Generate recipe briefs from inventory items
        
        Args:
            user_id: User ID for caching
            inventory_items: List of inventory items with name, quantity, category
            count: Number of recipes to generate (default 5)
            offset: Offset for "generate more" (0, 5, 10, 15, 20)
        
        Returns:
            {
                'briefs': List of recipe briefs,
                'total_generated': Total number of recipes in buffer,
                'can_generate_more': Boolean,
                'cached': Boolean (was this from cache),
                'cache_expires_at': ISO timestamp
            }
        """
        logger.info(f"[INV AGENT] 📋 Generating {count} recipe briefs for user {user_id} (offset: {offset})")
        logger.info(f"[INV AGENT] 📦 Inventory: {len(inventory_items)} items")
        
        # Calculate inventory hash
        inventory_hash = self._get_inventory_hash(inventory_items)
        cache_key = self._get_cache_key(user_id, inventory_hash)
        
        # Check cache
        cached_data = cache.get(cache_key)
        if cached_data and offset < len(cached_data.get('briefs', [])):
            logger.info(f"[INV AGENT] ✅ Found cached recipe buffer")
            
            # Return slice of cached recipes
            all_briefs = cached_data['briefs']
            return {
                'briefs': all_briefs[offset:offset + count],
                'total_generated': len(all_briefs),
                'can_generate_more': len(all_briefs) < 25 and len(all_briefs) == offset,
                'cached': True,
                'cache_expires_at': cached_data.get('expires_at')
            }
        
        # Generate new recipes if not in cache or need more
        if cached_data:
            logger.info(f"[INV AGENT] 🔄 Cache exists but need more recipes")
            existing_briefs = cached_data.get('briefs', [])
        else:
            logger.info(f"[INV AGENT] 🆕 No cache, generating from scratch")
            existing_briefs = []
        
        # Create prompt
        prompt = self._create_brief_prompt(inventory_items, existing_briefs, count)
        
        # Call AI
        response = self._call_ai(prompt)
        if not response:
            logger.error("[INV AGENT] ❌ Failed to generate recipes")
            return {
                'briefs': [],
                'total_generated': 0,
                'can_generate_more': False,
                'cached': False,
                'cache_expires_at': None,
                'error': 'AI service unavailable'
            }
        
        # Parse response
        new_briefs = self._parse_brief_response(response)
        logger.info(f"[INV AGENT] ✅ Parsed {len(new_briefs)} new recipe briefs")
        
        # Combine with existing
        all_briefs = existing_briefs + new_briefs
        
        # Cache for 24 hours
        expires_at = timezone.now() + timedelta(hours=24)
        cache.set(cache_key, {
            'briefs': all_briefs,
            'expires_at': expires_at.isoformat()
        }, timeout=86400)  # 24 hours
        
        logger.info(f"[INV AGENT] 💾 Cached {len(all_briefs)} recipes until {expires_at}")
        
        return {
            'briefs': all_briefs[offset:offset + count],
            'total_generated': len(all_briefs),
            'can_generate_more': len(all_briefs) < 25,
            'cached': False,
            'cache_expires_at': expires_at.isoformat()
        }
    
    def _create_brief_prompt(
        self,
        inventory_items: List[Dict],
        existing_briefs: List[Dict],
        count: int
    ) -> str:
        """Create prompt for recipe brief generation"""
        
        # Format inventory items
        inventory_str = "\n".join([
            f"- {item.get('name', 'Unknown')} ({item.get('quantity', 0)} {item.get('unit', 'units')}) - {item.get('category', 'other')}"
            for item in inventory_items
        ])
        
        # Format existing recipes (to avoid duplicates)
        existing_str = ""
        if existing_briefs:
            existing_str = "\n\nRECIPES ALREADY SUGGESTED (DO NOT REPEAT):\n" + "\n".join([
                f"{i+1}. {brief.get('name', '')}"
                for i, brief in enumerate(existing_briefs)
            ])
        
        prompt = f"""You are a creative chef AI. Generate {count} unique recipe ideas using the available inventory.

AVAILABLE INVENTORY:
{inventory_str}
{existing_str}

Generate {count} NEW and DIFFERENT recipes. For each recipe, provide:
1. Name (creative and appetizing)
2. Brief description (1-2 sentences)
3. Main ingredients needed from inventory (3-5 items)
4. Estimated cook time (in minutes)
5. Difficulty (beginner/intermediate/advanced)
6. Cuisine type (Italian, Asian, Mexican, etc.)

IMPORTANT:
- Use primarily items from the inventory
- Suggest recipes that can be made with what's available
- Be creative and diverse (different cuisines, styles)
- Each recipe should be UNIQUE and DIFFERENT from existing ones
- Think about complementary flavors and techniques

Return as JSON array:
[
  {{
    "name": "Recipe Name",
    "description": "Brief description",
    "main_ingredients": ["ingredient1", "ingredient2", "ingredient3"],
    "cook_time_minutes": 30,
    "difficulty": "intermediate",
    "cuisine": "Italian"
  }},
  ...
]

Return ONLY the JSON array, no other text."""
        
        return prompt
    
    def _parse_brief_response(self, response: str) -> List[Dict]:
        """Parse AI response into recipe briefs"""
        try:
            # Try to find JSON in response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning("[INV AGENT] ⚠️ No JSON array found in response")
                return []
            
            json_str = response[start_idx:end_idx]
            briefs = json.loads(json_str)
            
            # Validate structure
            validated_briefs = []
            for brief in briefs:
                if all(key in brief for key in ['name', 'description', 'main_ingredients']):
                    # Add generated timestamp and ID
                    brief['generated_at'] = timezone.now().isoformat()
                    brief['brief_id'] = f"brief_{timezone.now().timestamp()}_{len(validated_briefs)}"
                    validated_briefs.append(brief)
            
            return validated_briefs
        
        except json.JSONDecodeError as e:
            logger.error(f"[INV AGENT] ❌ Failed to parse JSON: {e}")
            logger.error(f"[INV AGENT] Response was: {response[:500]}")
            return []
    
    def generate_full_recipe(
        self,
        brief: Dict,
        inventory_items: List[Dict],
        target_language: str = 'en'
    ) -> Optional[Dict]:
        """
        Generate full recipe from a brief
        
        Args:
            brief: Recipe brief dictionary
            inventory_items: Available inventory items
            target_language: Target language for recipe (en/ru/he)
        
        Returns:
            Full recipe dictionary or None if failed
        """
        logger.info(f"[INV AGENT] 🍳 Generating full recipe: {brief.get('name')}")
        logger.info(f"[INV AGENT] 🌍 Target language: {target_language}")
        
        # Create prompt for full recipe
        prompt = self._create_full_recipe_prompt(brief, inventory_items)
        
        # Call AI
        response = self._call_ai(prompt)
        if not response:
            logger.error("[INV AGENT] ❌ Failed to generate full recipe")
            return None
        
        # Parse response
        full_recipe = self._parse_full_recipe_response(response, brief)
        
        if full_recipe:
            logger.info(f"[INV AGENT] ✅ Generated full recipe: {full_recipe.get('name')}")
            
            # Translate recipe if target language is not English
            if target_language != 'en':
                logger.info(f"[INV AGENT] 🌍 Translating recipe to {target_language}")
                full_recipe = self._translate_recipe(full_recipe, target_language)
        
        return full_recipe
    
    def _translate_recipe(self, recipe: Dict, target_language: str) -> Dict:
        """
        Translate recipe using multilang translator (IML + Google Translate)
        
        This uses the same translation system as shopping list items and recipes.
        Fallback order: IML -> Google Translate (Gemini) -> Google Translate (Groq)
        """
        try:
            from apps.shopping.multilang_translator import get_multilang_translator
            
            translator = get_multilang_translator()
            
            # Translate recipe name
            recipe_name_translations = translator.translate_text(
                recipe['name'],
                source_language='en',
                target_languages=[target_language]
            )
            
            if recipe_name_translations and target_language in recipe_name_translations:
                recipe['name_translations'] = recipe_name_translations
                recipe['name'] = recipe_name_translations[target_language]
                logger.info(f"[INV AGENT] ✅ Translated recipe name to {target_language}")
            
            # Translate ingredients using IML
            ingredients = recipe.get('ingredients', [])
            if ingredients:
                translated_ingredients = translator.translate_ingredients_batch(
                    ingredients,
                    source_language='en'
                )
                
                # Update ingredients with translations
                for i, ing in enumerate(ingredients):
                    if i < len(translated_ingredients):
                        trans = translated_ingredients[i]
                        ing['name_translations'] = trans.get('name_translations', {})
                        
                        # Set display name to target language
                        if target_language in ing['name_translations']:
                            ing['display_name'] = ing['name_translations'][target_language]
                        else:
                            ing['display_name'] = ing['name']
                
                logger.info(f"[INV AGENT] ✅ Translated {len(ingredients)} ingredients")
            
            # Translate description
            if recipe.get('description'):
                desc_translations = translator.translate_text(
                    recipe['description'],
                    source_language='en',
                    target_languages=[target_language]
                )
                
                if desc_translations and target_language in desc_translations:
                    recipe['description_translations'] = desc_translations
                    recipe['description'] = desc_translations[target_language]
                    logger.info(f"[INV AGENT] ✅ Translated description")
            
            return recipe
        
        except Exception as e:
            logger.warning(f"[INV AGENT] ⚠️ Translation failed: {e}, returning English")
            return recipe
    
    def _create_full_recipe_prompt(self, brief: Dict, inventory_items: List[Dict]) -> str:
        """Create prompt for full recipe generation"""
        
        inventory_str = "\n".join([
            f"- {item.get('name', 'Unknown')} ({item.get('quantity', 0)} {item.get('unit', 'units')})"
            for item in inventory_items
        ])
        
        prompt = f"""You are a professional chef. Create a detailed recipe based on this concept:

RECIPE CONCEPT:
Name: {brief.get('name')}
Description: {brief.get('description')}
Main Ingredients: {', '.join(brief.get('main_ingredients', []))}
Cook Time: {brief.get('cook_time_minutes')} minutes
Difficulty: {brief.get('difficulty')}
Cuisine: {brief.get('cuisine')}

AVAILABLE INVENTORY:
{inventory_str}

Create a complete, detailed recipe with:
1. Full ingredient list with precise amounts
2. Step-by-step cooking instructions
3. Tips and variations
4. Nutritional highlights (if relevant)

Return as JSON:
{{
  "name": "{brief.get('name')}",
  "description": "Expanded description",
  "cuisine": "{brief.get('cuisine')}",
  "difficulty": "{brief.get('difficulty')}",
  "prep_time_minutes": 15,
  "cook_time_minutes": {brief.get('cook_time_minutes', 30)},
  "servings": 4,
  "ingredients": [
    {{
      "name": "ingredient name",
      "amount": 200,
      "unit": "g",
      "notes": "optional notes"
    }}
  ],
  "instructions": [
    "Step 1: Detailed instruction...",
    "Step 2: Detailed instruction..."
  ],
  "tips": ["Tip 1", "Tip 2"],
  "tags": ["tag1", "tag2"]
}}

Return ONLY the JSON object, no other text."""
        
        return prompt
    
    def _parse_full_recipe_response(self, response: str, brief: Dict) -> Optional[Dict]:
        """Parse AI response into full recipe"""
        try:
            # Find JSON in response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning("[INV AGENT] ⚠️ No JSON object found in response")
                return None
            
            json_str = response[start_idx:end_idx]
            recipe = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['name', 'ingredients', 'instructions']
            if not all(key in recipe for key in required_fields):
                logger.warning(f"[INV AGENT] ⚠️ Missing required fields in recipe")
                return None
            
            # Add metadata
            recipe['brief_id'] = brief.get('brief_id')
            recipe['generated_at'] = timezone.now().isoformat()
            recipe['source'] = 'inventory_agent'
            
            return recipe
        
        except json.JSONDecodeError as e:
            logger.error(f"[INV AGENT] ❌ Failed to parse recipe JSON: {e}")
            logger.error(f"[INV AGENT] Response was: {response[:500]}")
            return None
    
    def clear_cache(self, user_id: str, inventory_items: List[Dict]):
        """Clear recipe cache for user (called when inventory changes)"""
        inventory_hash = self._get_inventory_hash(inventory_items)
        cache_key = self._get_cache_key(user_id, inventory_hash)
        cache.delete(cache_key)
        logger.info(f"[INV AGENT] 🗑️ Cleared cache for user {user_id}")


# Singleton instance
_agent_instance = None

def get_inventory_recipe_agent() -> InventoryRecipeAgent:
    """Get singleton instance of inventory recipe agent"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = InventoryRecipeAgent()
    return _agent_instance

