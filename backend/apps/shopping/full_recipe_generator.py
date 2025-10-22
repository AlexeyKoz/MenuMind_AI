"""
Full Recipe Generator - Sprint 7 Phase 4
Converts recipe briefs to complete RCIP 2.0 recipes with full instructions
"""
from typing import Dict, List, Optional
import json
from apps.shopping.inventory_services import InventoryRecipeGenerator


class FullRecipeGenerator:
    """
    Generate complete recipe with detailed cooking steps from a brief

    Uses Gemini/Groq to expand brief into full recipe
    """

    def __init__(self):
        # Reuse the inventory recipe generator for AI access
        self.ai_generator = InventoryRecipeGenerator()

    def generate_full_recipe(
        self,
        brief: Dict,
        language: str = 'en',
        user_preferences: Dict = None
    ) -> Optional[Dict]:
        """
        Convert recipe brief to full recipe with detailed steps

        Args:
            brief: Recipe brief from inventory generation
            language: Target language
            user_preferences: User preferences (unit_system, etc.)

        Returns:
            Complete recipe in RCIP 2.0 format
        """
        if user_preferences is None:
            user_preferences = {'unit_system': 'metric'}

        print(
            f"[FULL RECIPE] Generating complete recipe for '{brief['name']}' in {language}")
        print(f"[FULL RECIPE] User preferences: {user_preferences}")

        # Build prompt for full recipe generation
        prompt = self._build_full_recipe_prompt(
            brief, language, user_preferences)

        # Try Gemini first
        full_recipe_data = None
        ai_provider = None

        if self.ai_generator.gemini_client:
            print("[FULL RECIPE] Trying Gemini...")
            full_recipe_data = self._generate_with_gemini(prompt)
            if full_recipe_data:
                ai_provider = 'gemini'
                print(f"[FULL RECIPE] ✅ Gemini generated full recipe")

        # Fallback to Groq
        if not full_recipe_data and self.ai_generator.groq_client:
            print("[FULL RECIPE] Gemini failed, trying Groq...")
            full_recipe_data = self._generate_with_groq(prompt)
            if full_recipe_data:
                ai_provider = 'groq'
                print(f"[FULL RECIPE] ✅ Groq generated full recipe")

        if not full_recipe_data:
            print("[FULL RECIPE] ❌ Both AIs failed")
            return None

        # VALIDATE OUTPUT before converting to RCIP
        if not self._validate_recipe_output(full_recipe_data, language, user_preferences):
            print("[FULL RECIPE] ❌ Validation failed - recipe rejected")
            return None

        # Convert to RCIP 2.0 format
        rcip_recipe = self._convert_to_rcip(brief, full_recipe_data, language)
        rcip_recipe['ai_provider'] = ai_provider

        return rcip_recipe

    def _build_full_recipe_prompt(self, brief: Dict, language: str) -> str:
        """Build prompt for full recipe generation"""

        # Language-specific prompts
        PROMPTS = {
            'en': f"""You are a professional chef. Expand this recipe brief into a complete, detailed recipe.

Recipe Brief:
- Name: {brief['name']}
- Ingredients: {', '.join([f"{ing['name']} ({ing['quantity']} {ing['unit']})" for ing in brief.get('ingredients_from_inventory', [])])}
- Missing ingredients: {', '.join(brief.get('missing_ingredients', []))}
- Cooking time: {brief.get('cooking_time', 'N/A')}
- Difficulty: {brief.get('difficulty', 'N/A')}

Provide a complete recipe with:
1. Detailed cooking steps (numbered, clear instructions)
2. Specific techniques (dice, sauté, simmer, etc.)
3. Timing for each step
4. Temperature details where relevant
5. Tips for best results

Return ONLY valid JSON:
{{
    "description": "Detailed recipe description (2-3 sentences)",
    "prep_time": "preparation time in minutes",
    "cook_time": "cooking time in minutes",
    "steps": [
        {{
            "step_number": 1,
            "instruction": "Detailed instruction with technique",
            "timing": "5 min" or null,
            "temperature": "180C" or null,
            "techniques": ["dice", "sauté"]
        }}
    ],
    "tips": ["tip 1", "tip 2"]
}}""",

            'he': f"""אתה שף מקצועי. הרחב את תקציר המתכון הזה למתכון מפורט ומלא.

תקציר מתכון:
- שם: {brief['name']}
- מרכיבים: {', '.join([f"{ing['name']} ({ing['quantity']} {ing['unit']})" for ing in brief.get('ingredients_from_inventory', [])])}
- מרכיבים חסרים: {', '.join(brief.get('missing_ingredients', []))}
- זמן בישול: {brief.get('cooking_time', 'לא זמין')}
- רמת קושי: {brief.get('difficulty', 'לא זמין')}

ספק מתכון מלא עם:
1. שלבי בישול מפורטים (ממוספרים, הוראות ברורות)
2. טכניקות ספציפיות (קיצוץ, טיגון, הרתחה וכו')
3. תזמון לכל שלב
4. פרטי טמפרטורה במידת הצורך
5. טיפים לתוצאות מיטביות

החזר רק JSON תקין:
{{
    "description": "תיאור מפורט של המתכון",
    "prep_time": "זמן הכנה בדקות",
    "cook_time": "זמן בישול בדקות",
    "steps": [
        {{
            "step_number": 1,
            "instruction": "הוראה מפורטת עם טכניקה",
            "timing": "5 דקות" או null,
            "temperature": "180 מעלות" או null,
            "techniques": ["קיצוץ", "טיגון"]
        }}
    ],
    "tips": ["טיפ 1", "טיפ 2"]
}}""",

            'ru': f"""Вы профессиональный повар. Разверните этот краткий рецепт в полный, подробный рецепт.

═══════════════════════════════════════════════════════════════
🚨 КРИТИЧЕСКИ ВАЖНО - ТОЛЬКО РУССКИЙ ЯЗЫК 🚨
═══════════════════════════════════════════════════════════════

ВЫ ДОЛЖНЫ вывести ВСЁ ТОЛЬКО на РУССКОМ языке.

❌ ЗАПРЕЩЕНО:
- Английские слова: "Place", "Mix", "cooked", "rice", "vinegar", etc.
- Смешанный язык: "Place приготовленный rice" ❌
- Частичные переводы: "Mix полностью fried" ❌

✅ ТРЕБУЕТСЯ:
- ВЕСЬ текст должен быть на русском языке: "Поместите приготовленный рис" ✅
- Если ингредиенты указаны на английском, ПЕРЕВЕДИТЕ их на русский
- Каждое слово должно быть узнаваемым русским словом

ПРОВЕРКА ПЕРЕД ОТВЕТОМ:
1. ✓ Все названия ингредиентов на русском
2. ✓ Все инструкции шагов на русском
3. ✓ Нет английских слов
4. ✓ Нет смешанного языка
5. ✓ Нет непереведенных терминов

═══════════════════════════════════════════════════════════════

Краткий рецепт:
- Название: {brief['name']}
- Ингредиенты: {', '.join([f"{ing['name']} ({ing['quantity']} {ing['unit']})" for ing in brief.get('ingredients_from_inventory', [])])}
- Недостающие ингредиенты: {', '.join(brief.get('missing_ingredients', []))}
- Время приготовления: {brief.get('cooking_time', 'Н/Д')}
- Сложность: {brief.get('difficulty', 'Н/Д')}

Предоставьте полный рецепт с:
1. Подробные шаги приготовления (пронумерованные, четкие инструкции НА РУССКОМ)
2. Конкретные техники (нарезка, обжаривание, тушение и т.д. - ТОЛЬКО ПО-РУССКИ)
3. Время для каждого шага
4. Температурные детали где необходимо
5. Советы для лучших результатов

ВАЖНО: Все инструкции должны быть ПОЛНОСТЬЮ на русском языке!

Верните только валидный JSON:
{{
    "description": "Подробное описание рецепта (ТОЛЬКО НА РУССКОМ)",
    "prep_time": "время подготовки в минутах",
    "cook_time": "время приготовления в минутах",
    "steps": [
        {{
            "step_number": 1,
            "instruction": "Подробная инструкция с техникой (ТОЛЬКО НА РУССКОМ - без английских слов!)",
            "timing": "5 мин" или null,
            "temperature": "180C" или null,
            "techniques": ["нарезка", "обжаривание"]
        }}
    ],
    "tips": ["совет 1", "совет 2"]
}}

НАПОМИНАНИЕ: ВСЕ инструкции должны быть ПОЛНОСТЬЮ НА РУССКОМ ЯЗЫКЕ. Ни одного английского слова!"""
        }

        return PROMPTS.get(language, PROMPTS['en'])

    def _generate_with_gemini(self, prompt: str) -> Optional[Dict]:
        """Generate with Gemini (with retry logic)"""
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                print(
                    f"[FULL RECIPE] Gemini attempt {attempt + 1}/{max_retries}")

                response = self.ai_generator.gemini_client.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.5,
                        'max_output_tokens': 3000,
                    },
                    request_options={'timeout': 30}
                )

                result = self._parse_json_response(response.text)
                if result:
                    return result

            except Exception as e:
                print(
                    f"[FULL RECIPE] Gemini error (attempt {attempt + 1}): {e}")

                if 'quota' in str(e).lower() or '429' in str(e):
                    print(f"[FULL RECIPE] Quota hit - not retrying")
                    return None

                if attempt < max_retries - 1:
                    import time
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"[FULL RECIPE] Waiting {wait_time}s...")
                    time.sleep(wait_time)

        return None

    def _generate_with_groq(self, prompt: str) -> Optional[Dict]:
        """Generate with Groq"""
        try:
            # Determine system message based on language in prompt
            system_content = "You are a professional chef. Return ONLY valid JSON."
            if "ТОЛЬКО РУССКИЙ ЯЗЫК" in prompt or "КРИТИЧЕСКИ ВАЖНО" in prompt:
                system_content = "Вы профессиональный повар. Возвращайте ТОЛЬКО валидный JSON. ВСЕ инструкции должны быть ПОЛНОСТЬЮ на русском языке."
            elif "עברית בלבד" in prompt or "שף מקצועי" in prompt:
                system_content = "אתה שף מקצועי. החזר רק JSON תקין בעברית."

            completion = self.ai_generator.groq_client.chat.completions.create(
                model=self.ai_generator.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=3000
            )

            return self._parse_json_response(completion.choices[0].message.content)
        except Exception as e:
            print(f"[FULL RECIPE] Groq error: {e}")
            return None

    def _parse_json_response(self, response_text: str) -> Optional[Dict]:
        """Parse JSON from AI response"""
        try:
            # Remove markdown code blocks
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())

            return None
        except Exception as e:
            print(f"[FULL RECIPE] JSON parse error: {e}")
            return None

    def _convert_to_rcip(
        self,
        brief: Dict,
        full_recipe_data: Dict,
        language: str
    ) -> Dict:
        """
        Convert brief + full recipe data to RCIP 2.0 format
        """
        from apps.core.utils.temperature_utils import parse_temperature_text

        # Build ingredients list
        ingredients = []

        # Add inventory ingredients
        for ing in brief.get('ingredients_from_inventory', []):
            ingredients.append({
                'iml_key': ing['name'].lower().replace(' ', '-'),
                'amount': ing.get('quantity', 1),
                'unit': ing.get('unit', 'unit'),
                'from_inventory': True
            })

        # Add missing ingredients
        for ing_name in brief.get('missing_ingredients', []):
            ingredients.append({
                'iml_key': ing_name.lower().replace(' ', '-'),
                'amount': 1,
                'unit': 'unit',
                'from_inventory': False
            })

        # Build steps with structured temperature data
        steps = []
        for step_data in full_recipe_data.get('steps', []):
            step = {
                'step_number': step_data.get('step_number', len(steps) + 1),
                'instruction': step_data.get('instruction', ''),
                'timing': step_data.get('timing'),
                'cooklingo_keys': step_data.get('techniques', [])
            }

            # Handle temperature - normalize to structured format
            temp = step_data.get('temperature')
            if temp:
                if isinstance(temp, dict) and 'value' in temp and 'unit' in temp:
                    # Already structured
                    step['temperature'] = temp
                elif isinstance(temp, str):
                    # Parse from string like "180C" or "350F"
                    parsed_temp = parse_temperature_text(temp)
                    if parsed_temp:
                        step['temperature'] = parsed_temp
                    else:
                        step['temperature'] = None
                else:
                    step['temperature'] = None
            else:
                step['temperature'] = None

            steps.append(step)

        # Build RCIP 2.0 structure
        rcip = {
            'metadata': {
                'title': brief['name'],
                'description': full_recipe_data.get('description', brief.get('reasoning', '')),
                'source_language': language,
                'servings': brief.get('servings', 2),
                'prep_time': full_recipe_data.get('prep_time', 'unknown'),
                'cook_time': full_recipe_data.get('cook_time', brief.get('cooking_time', 'unknown')),
                'difficulty': brief.get('difficulty', 'easy'),
                'tags': ['inventory-generated'],
                'nutrition': brief.get('nutrition', {})
            },
            'structure': {
                'ingredients': ingredients,
                'steps': steps
            },
            'tips': full_recipe_data.get('tips', [])
        }

        return rcip


# Singleton
_full_recipe_generator = None


def get_full_recipe_generator() -> FullRecipeGenerator:
    """Get singleton instance"""
    global _full_recipe_generator
    if _full_recipe_generator is None:
        _full_recipe_generator = FullRecipeGenerator()
    return _full_recipe_generator
