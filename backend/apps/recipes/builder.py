"""
Recipe Builder Service - AI-assisted step-by-step recipe creation

USER FLOW:
Step 1: Basic Info → name, cuisine, servings, difficulty
Step 2: Ingredients → AI suggests quantities & units
Step 3: Steps → AI structures cooking instructions
Step 4: Review & Edit → User can review and edit the compiled recipe before saving
Step 5: Finalize → Create canonical recipe (source_type='user_created')
"""
from typing import Dict, List, Optional
import json
import uuid
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
from asgiref.sync import sync_to_async
import os
import asyncio


class RecipeBuilderService:
    """AI-assisted recipe builder with step-by-step guidance"""

    def __init__(self):
        # Try to initialize Groq for AI suggestions
        try:
            from groq import Groq
            groq_api_key = os.getenv('GROQ_API_KEY') or getattr(
                settings, 'GROQ_API_KEY', None)
            if groq_api_key:
                self.groq_client = Groq(api_key=groq_api_key)
                self.model = "llama-3.1-8b-instant"
            else:
                print(
                    "[WARNING] GROQ_API_KEY not found. AI suggestions will be limited.")
                self.groq_client = None
        except ImportError:
            print("[WARNING] Groq not installed. AI suggestions will be limited.")
            self.groq_client = None

    async def create_builder_session(self, user) -> str:
        """
        Create new builder session stored in cache (Redis/in-memory)

        Returns:
            session_id: UUID string for this builder session
        """
        session_id = str(uuid.uuid4())

        session_data = {
            'user_id': str(user.id),
            'username': user.username,
            'step': 'basic_info',
            'data': {},
            'created_at': datetime.now().isoformat()
        }

        # Store session in cache (1 hour expiry)
        await cache.aset(
            f"recipe_builder:{session_id}",
            session_data,
            timeout=3600  # 1 hour
        )

        print(
            f"[BUILDER] Created session: {session_id} for user {user.username}")
        return session_id

    async def process_step(
        self,
        session_id: str,
        step: str,
        user_input: Dict
    ) -> Dict:
        """
        Process a builder step with AI assistance

        Args:
            session_id: Builder session UUID
            step: Current step (basic_info, ingredients, steps, finalize)
            user_input: User's input data for this step

        Returns:
            Response dict with next_step, data, and AI suggestions
        """
        # Retrieve session
        session = await cache.aget(f"recipe_builder:{session_id}")
        if not session:
            raise ValueError(
                "Session expired or invalid. Please start a new builder session.")

        print(f"[BUILDER] Processing step: {step} for session {session_id}")

        # Route to appropriate step processor
        if step == 'basic_info':
            return await self._process_basic_info(session, session_id, user_input)
        elif step == 'ingredients':
            return await self._process_ingredients(session, session_id, user_input)
        elif step == 'steps':
            return await self._process_steps(session, session_id, user_input)
        elif step == 'review':
            return await self._process_review(session, session_id, user_input)
        elif step == 'finalize':
            return await self._process_finalize(session, session_id, user_input)
        else:
            raise ValueError(f"Unknown step: {step}")

    # ============================================================================
    # STEP 1: BASIC INFO
    # ============================================================================

    async def _process_basic_info(self, session: Dict, session_id: str, user_input: Dict) -> Dict:
        """
        Step 1: Process basic recipe information with AI validation and duplicate detection

        User provides:
        - name: Recipe name
        - cuisine: (optional) Italian, Mexican, etc.
        - servings: (optional) Number of servings
        - difficulty: (optional) beginner, intermediate, advanced
        - skip_duplicate_check: (optional) If True, skip duplicate detection

        AI validates and suggests improvements
        """
        name = user_input.get('name', '').strip()
        skip_duplicate_check = user_input.get('skip_duplicate_check', False)

        if not name or len(name) < 3:
            return {
                'success': False,
                'error': 'Recipe name must be at least 3 characters',
                'current_step': 'basic_info'
            }

        # DUPLICATE CHECK - Check early to prevent wasted time
        if not skip_duplicate_check:
            existing_recipe = await self._check_for_duplicates(name)
            if existing_recipe:
                print(
                    f"[BUILDER] ⚠️ Duplicate found in Step 1: {existing_recipe.name} (ID: {existing_recipe.id})")
                return {
                    'success': False,
                    'is_duplicate': True,
                    'existing_recipe': {
                        'id': str(existing_recipe.id),
                        'name': existing_recipe.name,
                        'description': existing_recipe.description,
                        'cuisine': existing_recipe.cuisine,
                        'difficulty': existing_recipe.difficulty,
                        'servings': existing_recipe.servings,
                        'source_type': existing_recipe.source_type,
                        'diet_labels': existing_recipe.diet_labels,
                    },
                    'message': f'A recipe named "{existing_recipe.name}" already exists. Would you like to view it or create your own version?'
                }
        else:
            print(f"[BUILDER] ✅ Skipping duplicate check for: {name}")

        # Get optional fields with defaults
        cuisine = user_input.get('cuisine', '').strip()
        servings = user_input.get('servings', 4)
        difficulty = user_input.get('difficulty', 'intermediate')
        description = user_input.get('description', '').strip()

        # AI validation and suggestions (if available)
        ai_suggestions = []
        validated_data = {
            'name': name,
            'cuisine': cuisine,
            'servings': int(servings),
            'difficulty': difficulty,
            'description': description
        }

        if self.groq_client:
            try:
                ai_response = await self._get_ai_basic_info_suggestions(
                    name, cuisine, servings, difficulty
                )
                validated_data.update(ai_response.get('validated', {}))
                ai_suggestions = ai_response.get('suggestions', [])
            except Exception as e:
                print(f"[BUILDER] AI suggestions failed: {e}")
                # Continue without AI suggestions
        else:
            # Fallback: auto-detect cuisine from name if not provided
            if not cuisine:
                cuisine_keywords = {
                    'italian': ['pasta', 'pizza', 'risotto', 'lasagna', 'carbonara'],
                    'mexican': ['taco', 'burrito', 'quesadilla', 'enchilada', 'salsa'],
                    'chinese': ['stir-fry', 'fried rice', 'noodles', 'dumpling'],
                    'indian': ['curry', 'biryani', 'masala', 'tandoori'],
                    'french': ['ratatouille', 'quiche', 'crepe', 'cassoulet'],
                    'japanese': ['sushi', 'ramen', 'teriyaki', 'tempura'],
                }
                name_lower = name.lower()
                for cuisine_type, keywords in cuisine_keywords.items():
                    if any(keyword in name_lower for keyword in keywords):
                        validated_data['cuisine'] = cuisine_type.title()
                        ai_suggestions.append(
                            f"Detected cuisine: {cuisine_type.title()}")
                        break

        # Update session
        session['data']['basic_info'] = validated_data
        session['step'] = 'ingredients'
        await cache.aset(f"recipe_builder:{session_id}", session, timeout=3600)

        print(f"[BUILDER] Basic info validated: {name}")

        return {
            'success': True,
            'next_step': 'ingredients',
            'current_step': 'basic_info',
            'data': validated_data,
            'ai_suggestions': ai_suggestions,
            'message': f"Recipe '{name}' details saved. Ready for ingredients!"
        }

    async def _get_ai_basic_info_suggestions(
        self,
        name: str,
        cuisine: str,
        servings: int,
        difficulty: str
    ) -> Dict:
        """Get AI suggestions for basic info"""

        prompt = f"""You are a recipe creation assistant. Validate and improve this recipe metadata.

Recipe Name: {name}
Cuisine: {cuisine or 'Not specified'}
Servings: {servings}
Difficulty: {difficulty}

Tasks:
1. If cuisine not specified, suggest based on recipe name
2. Validate servings (typical range 1-12)
3. Validate difficulty matches the dish type
4. Provide 2-3 helpful suggestions

Return JSON only:
{{
    "validated": {{
        "name": "improved name if needed",
        "cuisine": "cuisine name",
        "servings": 4,
        "difficulty": "beginner|intermediate|advanced"
    }},
    "suggestions": ["suggestion 1", "suggestion 2"]
}}"""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=500
            )
        )

        content = response.choices[0].message.content
        # Extract JSON from response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {'validated': {}, 'suggestions': []}

    # ============================================================================
    # STEP 2: INGREDIENTS
    # ============================================================================

    async def _process_ingredients(self, session: Dict, session_id: str, user_input: Dict) -> Dict:
        """
        Step 2: Process ingredients with AI assistance

        User provides:
        - ingredients: List of ingredient strings or objects
          Examples:
          ["2 cups flour", "3 eggs", "salt"]
          OR
          [{"name": "flour", "amount": 2, "unit": "cups"}, ...]

        AI structures, suggests quantities, validates units
        """
        raw_ingredients = user_input.get('ingredients', [])

        if not raw_ingredients:
            return {
                'success': False,
                'error': 'At least one ingredient is required',
                'current_step': 'ingredients'
            }

        # Validate session has basic_info
        if 'basic_info' not in session.get('data', {}):
            return {
                'success': False,
                'error': 'Session expired or invalid. Please start over.',
                'current_step': 'ingredients'
            }

        recipe_name = session['data']['basic_info']['name']
        servings = session['data']['basic_info']['servings']

        # Structure ingredients with AI
        if self.groq_client:
            try:
                structured_ingredients = await self._structure_ingredients_with_ai(
                    recipe_name, raw_ingredients, servings
                )
            except Exception as e:
                print(f"[BUILDER] AI structuring failed: {e}")
                structured_ingredients = self._structure_ingredients_fallback(
                    raw_ingredients)
        else:
            structured_ingredients = self._structure_ingredients_fallback(
                raw_ingredients)

        print(
            f"[BUILDER] Structured {len(structured_ingredients)} ingredients")

        # TRANSLATE INGREDIENTS using IML database (same as Discovery agent)
        # CRITICAL: Do this BEFORE saving to session!
        await self._translate_ingredients(structured_ingredients)

        # Update session with TRANSLATED ingredients
        session['data']['ingredients'] = structured_ingredients
        session['step'] = 'steps'
        await cache.aset(f"recipe_builder:{session_id}", session, timeout=3600)

        return {
            'success': True,
            'next_step': 'steps',
            'current_step': 'ingredients',
            'data': {
                'ingredients': structured_ingredients,
                'total_ingredients': len(structured_ingredients)
            },
            'message': f'Structured {len(structured_ingredients)} ingredients. Ready for cooking steps!'
        }

    async def _structure_ingredients_with_ai(
        self,
        recipe_name: str,
        raw_ingredients: List,
        servings: int
    ) -> List[Dict]:
        """Use AI to structure ingredients with proper quantities and units"""

        prompt = f"""You are structuring ingredients for: "{recipe_name}" (serves {servings})

Raw ingredients:
{json.dumps(raw_ingredients, indent=2)}

CRITICAL MEASUREMENT RULES:
1. ALWAYS provide specific measurements (never "to taste" or vague amounts)
2. For SOLID INGREDIENTS (flour, sugar, meat, vegetables): Use WEIGHT units (g, kg, oz, lb)
3. For LIQUID INGREDIENTS (water, milk, oil, juice, broth): Use VOLUME units (ml, l, cups, fl oz)
4. For COUNTABLE ITEMS (eggs, tomatoes, onions): Use COUNT (2 eggs, 3 tomatoes)
5. For SPICES/HERBS: Use weight (5g salt, 2g pepper) not "pinch" or "dash"
6. If original recipe is vague, estimate reasonable amounts based on servings

PREFERRED UNITS:
- Solids: grams (g) or kilograms (kg)
- Liquids: milliliters (ml) or liters (l)
- Small liquids/spices: ml or g (not tablespoons)
- Countable: pieces

Tasks:
1. Parse each ingredient with SPECIFIC measurements
2. Categorize (vegetables, protein, spices, dairy, grains, liquids, other)
3. Ensure every ingredient has proper amount + unit

Return JSON array only:
[
    {{
        "name": "ingredient name",
        "amount": 300,
        "unit": "g",
        "category": "grains",
        "notes": ""
    }},
    {{
        "name": "milk",
        "amount": 250,
        "unit": "ml",
        "category": "liquids",
        "notes": ""
    }}
]"""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=1500
            )
        )

        content = response.choices[0].message.content

        try:
            # Try to parse JSON directly
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON array in response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            # Fallback
            return self._structure_ingredients_fallback(raw_ingredients)

    def _structure_ingredients_fallback(self, raw_ingredients: List) -> List[Dict]:
        """Fallback ingredient structuring without AI"""
        structured = []

        for ing in raw_ingredients:
            if isinstance(ing, str):
                # Simple string parsing
                parts = ing.split()
                ingredient = {
                    'name': ing,
                    'amount': 1,
                    'unit': 'unit',
                    'category': 'other',
                    'notes': ''
                }

                # Try to extract amount
                if parts and parts[0].replace('.', '').replace('/', '').isdigit():
                    try:
                        # Handle fractions like 1/2
                        ingredient['amount'] = float(eval(parts[0]))
                        ingredient['name'] = ' '.join(parts[1:])
                    except:
                        pass

                structured.append(ingredient)
            elif isinstance(ing, dict):
                # Already structured
                structured.append({
                    'name': ing.get('name', ''),
                    'amount': ing.get('amount', 1),
                    'unit': ing.get('unit', 'unit'),
                    'category': ing.get('category', 'other'),
                    'notes': ing.get('notes', '')
                })

        return structured

    # ============================================================================
    # STEP 3: COOKING STEPS
    # ============================================================================

    async def _process_steps(self, session: Dict, session_id: str, user_input: Dict) -> Dict:
        """
        Step 3: Convert free-form cooking description to structured steps

        User provides:
        - steps_description: Free-form text describing cooking process
          OR
        - steps: List of step strings/objects

        AI structures into clear, numbered steps with time estimates
        """
        steps_description = user_input.get('steps_description', '')
        steps_list = user_input.get('steps', [])

        if not steps_description and not steps_list:
            return {
                'success': False,
                'error': 'Please provide cooking steps or description',
                'current_step': 'steps'
            }

        # Validate session has required data
        if 'basic_info' not in session.get('data', {}):
            return {
                'success': False,
                'error': 'Session expired or invalid. Please start over.',
                'current_step': 'steps'
            }
        if 'ingredients' not in session.get('data', {}):
            return {
                'success': False,
                'error': 'Ingredients not found. Please go back to step 2.',
                'current_step': 'steps'
            }

        recipe_name = session['data']['basic_info']['name']
        ingredients = session['data']['ingredients']

        # Structure steps with AI
        if self.groq_client and steps_description:
            try:
                structured_steps = await self._structure_steps_with_ai(
                    recipe_name, ingredients, steps_description
                )
            except Exception as e:
                print(f"[BUILDER] AI step structuring failed: {e}")
                structured_steps = self._structure_steps_fallback(
                    steps_description or steps_list)
        else:
            structured_steps = self._structure_steps_fallback(
                steps_description or steps_list)

        step_count = len(structured_steps['steps'])
        print(f"[BUILDER] Structured {step_count} cooking steps")

        # NORMALIZE TEMPERATURE DATA in steps
        self._normalize_step_temperatures(structured_steps['steps'])

        # TRANSLATE COOKING STEPS using AI (BEFORE saving to session!)
        await self._translate_cooking_steps(structured_steps['steps'])

        # Update session AFTER translation
        session['data']['steps'] = structured_steps
        session['step'] = 'finalize'
        await cache.aset(f"recipe_builder:{session_id}", session, timeout=3600)

        return {
            'success': True,
            'next_step': 'finalize',
            'current_step': 'steps',
            'data': structured_steps,
            'message': f'Created {step_count} cooking steps! Ready to finalize.'
        }

    async def _structure_steps_with_ai(
        self,
        recipe_name: str,
        ingredients: List[Dict],
        description: str
    ) -> Dict:
        """Use AI to structure cooking steps"""

        ingredient_names = [ing['name'] for ing in ingredients]

        prompt = f"""Structure cooking steps for: "{recipe_name}"

Available ingredients: {', '.join(ingredient_names)}

User's description:
"{description}"

Tasks:
1. Break into clear, numbered steps (5-15 steps typical)
2. Add time estimates where relevant
3. Include temperatures if cooking/baking
4. Reference ingredients from the list

Return JSON only:
{{
    "steps": [
        {{
            "order": 1,
            "instruction": "detailed step",
            "time_minutes": 5,
            "temperature": {{"value": 180, "unit": "celsius"}},
            "tips": ["helpful tip"]
        }}
    ],
    "estimated_prep_time": 15,
    "estimated_cook_time": 30,
    "total_time": 45
}}"""

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=2000
            )
        )

        content = response.choices[0].message.content

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return self._structure_steps_fallback(description)

    def _structure_steps_fallback(self, input_data) -> Dict:
        """Fallback step structuring without AI"""

        if isinstance(input_data, str):
            # Split by newlines or periods
            lines = [line.strip() for line in input_data.replace(
                '. ', '.\n').split('\n') if line.strip()]
            steps = []
            for i, line in enumerate(lines, 1):
                steps.append({
                    'order': i,
                    'instruction': line,
                    'time_minutes': None,
                    'temperature': None,
                    'tips': []
                })
        elif isinstance(input_data, list):
            steps = []
            for i, step in enumerate(input_data, 1):
                if isinstance(step, str):
                    steps.append({
                        'order': i,
                        'instruction': step,
                        'time_minutes': None,
                        'temperature': None,
                        'tips': []
                    })
                elif isinstance(step, dict):
                    steps.append(step)
        else:
            steps = []

        # Estimate total time
        estimated_time = len(steps) * 5  # Rough estimate: 5 min per step

        return {
            'steps': steps,
            'estimated_prep_time': estimated_time // 2,
            'estimated_cook_time': estimated_time // 2,
            'total_time': estimated_time
        }

    # ============================================================================
    # STEP 4: REVIEW & EDIT
    # ============================================================================

    async def _process_review(self, session: Dict, session_id: str, user_input: Dict) -> Dict:
        """
        Step 4: Review compiled recipe and allow edits

        On first call (no save_edits flag):
        - Returns compiled recipe data for user to review/edit

        On second call (with save_edits=True):
        - Saves user's edits back to session
        - Proceeds to finalize step

        User provides:
        - save_edits: (optional) Boolean to save edits
        - edited_data: (optional) Modified recipe data
        """
        save_edits = user_input.get('save_edits', False)

        if save_edits:
            # User has finished editing, save changes back to session
            edited_data = user_input.get('edited_data', {})

            if edited_data:
                # Update session with edited data
                if 'basic_info' in edited_data:
                    session['data']['basic_info'] = edited_data['basic_info']

                if 'ingredients' in edited_data:
                    session['data']['ingredients'] = edited_data['ingredients']

                if 'steps' in edited_data:
                    # Reconstruct steps format
                    session['data']['steps'] = {
                        'steps': edited_data['steps'],
                        'estimated_prep_time': edited_data.get('estimated_times', {}).get('prep_time', 0),
                        'estimated_cook_time': edited_data.get('estimated_times', {}).get('cook_time', 0),
                        'total_time': edited_data.get('estimated_times', {}).get('total_time', 0)
                    }

                # Update session
                session['step'] = 'review_completed'
                await cache.aset(f"recipe_builder:{session_id}", session, timeout=3600)

                print(f"[BUILDER] User edits saved to session")

            return {
                'success': True,
                'next_step': 'finalize',
                'current_step': 'review',
                'message': 'Edits saved! Ready to finalize your recipe.'
            }

        else:
            # First call - compile and return recipe data for review
            basic_info = session['data'].get('basic_info', {})
            ingredients = session['data'].get('ingredients', [])
            steps_data = session['data'].get('steps', {})

            # Auto-detect diet labels for preview
            diet_labels = await self._detect_diet_labels(ingredients)

            # Compile review data
            review_data = {
                'basic_info': basic_info,
                'ingredients': ingredients,
                'steps': steps_data.get('steps', []),
                'diet_labels': diet_labels,
                'estimated_times': {
                    'prep_time': steps_data.get('estimated_prep_time', 0),
                    'cook_time': steps_data.get('estimated_cook_time', 0),
                    'total_time': steps_data.get('total_time', 0)
                }
            }

            # Update session step
            session['step'] = 'review'
            await cache.aset(f"recipe_builder:{session_id}", session, timeout=3600)

            print(
                f"[BUILDER] Compiled recipe data for review: {basic_info.get('name')}")

            return {
                'success': True,
                'next_step': 'review',
                'current_step': 'review',
                'data': review_data,
                'message': 'Review your recipe and make any edits before finalizing!'
            }

    # ============================================================================
    # STEP 5: FINALIZE
    # ============================================================================

    async def _process_finalize(self, session: Dict, session_id: str, user_input: Dict) -> Dict:
        """
        Step 5: Finalize and create canonical recipe

        User provides:
        - is_public: Whether to publish recipe
        - description: (optional) Additional description
        - tags: (optional) Custom tags
        - skip_duplicate_check: (optional) If True, skip duplicate check and create anyway

        Creates CanonicalRecipe with source_type='user_created'
        """
        from .models import CanonicalRecipe, Recipe, UserRecipe
        import hashlib

        # Extract all collected data
        basic_info = session['data']['basic_info']
        ingredients = session['data']['ingredients']
        steps_data = session['data']['steps']

        # Get finalization options
        is_public = user_input.get('is_public', True)
        additional_description = user_input.get('description', '')
        tags = user_input.get('tags', [])
        skip_duplicate_check = user_input.get('skip_duplicate_check', False)

        # DUPLICATE CHECK - Use existing Discovery agent logic
        if not skip_duplicate_check:
            existing_recipe = await self._check_for_duplicates(basic_info['name'])
            if existing_recipe:
                print(
                    f"[BUILDER] ⚠️ Duplicate found: {existing_recipe.name} (ID: {existing_recipe.id})")
                return {
                    'success': False,
                    'is_duplicate': True,
                    'existing_recipe': {
                        'id': str(existing_recipe.id),
                        'name': existing_recipe.name,
                        'description': existing_recipe.description,
                        'cuisine': existing_recipe.cuisine,
                        'difficulty': existing_recipe.difficulty,
                        'servings': existing_recipe.servings,
                        'source_type': existing_recipe.source_type,
                    },
                    'message': f'A recipe named "{existing_recipe.name}" already exists. Would you like to create a personal fork?'
                }

        # Build final description
        description = basic_info.get('description', '')
        if additional_description:
            description = f"{description}\n\n{additional_description}" if description else additional_description

        # Auto-detect diet labels
        diet_labels = await self._detect_diet_labels(ingredients)
        diet_labels.extend(tags)  # Add custom tags
        diet_labels = list(set(diet_labels))  # Remove duplicates

        # Calculate recipe hash
        hash_string = self._calculate_recipe_hash(
            basic_info['name'],
            ingredients
        )

        # Get user from session
        from apps.users.models import User
        user = await sync_to_async(User.objects.get)(id=session['user_id'])

        # Create canonical recipe
        @sync_to_async
        def create_canonical():
            # Check for duplicates
            existing = CanonicalRecipe.objects.filter(
                recipe_hash=hash_string).first()
            if existing:
                print(
                    f"[BUILDER] Recipe with same hash exists: {existing.name}")
                return existing, False

            canonical = CanonicalRecipe.objects.create(
                name=basic_info['name'],
                description=description,
                source_type='user_created',
                original_creator=user,
                base_ingredients=ingredients,
                base_steps=steps_data['steps'],
                cuisine=basic_info.get('cuisine', ''),
                difficulty=basic_info.get('difficulty', 'intermediate'),
                diet_labels=diet_labels,
                prep_time_minutes=steps_data.get('estimated_prep_time'),
                cook_time_minutes=steps_data.get('estimated_cook_time'),
                total_time_minutes=steps_data.get('total_time'),
                servings=basic_info.get('servings', 4),
                is_published=is_public,
                recipe_hash=hash_string
            )
            print(f"[BUILDER] Created canonical recipe: {canonical.name}")
            return canonical, True

        canonical, is_new = await create_canonical()

        # Create user's fork
        @sync_to_async
        def create_user_fork():
            from django.utils import timezone

            fork = Recipe.objects.create(
                canonical_recipe=canonical,
                is_fork=True,
                created_by=user,
                name=canonical.name,
                description=canonical.description,
                ingredients=canonical.base_ingredients,
                steps=canonical.base_steps,
                cuisine=canonical.cuisine,
                difficulty=canonical.difficulty,
                diet_labels=canonical.diet_labels,
                prep_time_minutes=canonical.prep_time_minutes,
                cook_time_minutes=canonical.cook_time_minutes,
                total_time_minutes=canonical.total_time_minutes,
                servings=canonical.servings,
                user_modifications={},
                recipe_hash=None  # NULL for forks - bypasses unique constraint
            )

            # Create UserRecipe entry to make it appear in "My Recipes"
            UserRecipe.objects.create(
                user=user,
                recipe=fork,
                saved_at=timezone.now(),
                is_archived=False,
                times_cooked=0
            )

            # Update canonical statistics
            canonical.total_saves += 1
            canonical.save(update_fields=['total_saves'])

            print(f"[BUILDER] Created fork with UserRecipe entry: {fork.id}")
            return fork

        user_fork = await create_user_fork()

        # Clear session
        await cache.adelete(f"recipe_builder:{session_id}")

        print(f"[BUILDER] Recipe creation complete: {canonical.name}")

        # Serialize for response
        from .serializers import CanonicalRecipeSerializer, RecipeSerializer

        @sync_to_async
        def serialize():
            canonical_data = CanonicalRecipeSerializer(canonical).data
            fork_data = RecipeSerializer(user_fork).data
            return canonical_data, fork_data

        canonical_data, fork_data = await serialize()

        return {
            'success': True,
            'canonical_recipe_id': str(canonical.id),
            'user_recipe_id': str(user_fork.id),
            'canonical_recipe': canonical_data,
            'user_recipe': fork_data,
            'is_new': is_new,
            'message': f"Recipe '{canonical.name}' created successfully!",
            'recipe_summary': {
                'name': canonical.name,
                'source_type': canonical.source_type,
                'total_time': canonical.total_time_minutes,
                'servings': canonical.servings,
                'diet_labels': canonical.diet_labels,
                'is_public': canonical.is_published
            }
        }

    async def _detect_diet_labels(self, ingredients: List[Dict]) -> List[str]:
        """Auto-detect diet labels from ingredients"""

        ingredient_names = [ing['name'].lower() for ing in ingredients]

        # Keywords for different dietary restrictions
        meat_keywords = ['chicken', 'beef', 'pork', 'lamb',
                         'fish', 'turkey', 'meat', 'bacon', 'ham', 'steak']
        dairy_keywords = ['milk', 'cream', 'cheese',
                          'butter', 'yogurt', 'sour cream']
        egg_keywords = ['egg', 'eggs']
        gluten_keywords = ['flour', 'bread', 'pasta', 'wheat', 'barley', 'rye']

        has_meat = any(any(keyword in ing for keyword in meat_keywords)
                       for ing in ingredient_names)
        has_dairy = any(any(keyword in ing for keyword in dairy_keywords)
                        for ing in ingredient_names)
        has_eggs = any(any(keyword in ing for keyword in egg_keywords)
                       for ing in ingredient_names)
        has_gluten = any(any(keyword in ing for keyword in gluten_keywords)
                         for ing in ingredient_names)

        labels = []

        if not has_meat:
            labels.append('vegetarian')

        if not has_meat and not has_dairy and not has_eggs:
            labels.append('vegan')

        if not has_dairy:
            labels.append('dairy-free')

        if not has_gluten:
            labels.append('gluten-free')

        return labels

    async def _translate_ingredients(self, ingredients: List[Dict]):
        """
        Translate ingredients using IML database (same as Discovery agent)
        Modifies ingredients in-place to add translation keys
        """
        def _do_translation():
            """Run translation in sync context"""
            from apps.core.ingredient_mapper import IngredientMapper

            print(
                f"[BUILDER] Translating {len(ingredients)} ingredients using IML...")

            mapper = IngredientMapper()

            for ing in ingredients:
                ingredient_name = ing.get('name', '')
                if not ingredient_name:
                    continue

                # Map to IML ingredient_key using the map() method
                try:
                    result = mapper.map(ingredient_name, language='en')
                    ing['ingredient_key'] = result.ingredient_key

                    # Store display_name for fallback
                    if isinstance(result.display_name, dict):
                        ing['display_name'] = result.display_name
                    else:
                        ing['display_name'] = {'en': result.display_name}

                    print(
                        f"[BUILDER]   ✅ {ingredient_name} → {result.ingredient_key} (confidence: {result.confidence})")
                except Exception as e:
                    print(
                        f"[BUILDER]   ⚠️ {ingredient_name} → fallback (error: {e})")
                    # Create synthetic key for ingredients not in IML
                    synthetic_key = ingredient_name.lower().replace(' ', '_')[
                        :50]
                    ing['ingredient_key'] = f"synthetic_{synthetic_key}"
                    ing['display_name'] = {'en': ingredient_name}

            print(f"[BUILDER] ✅ Ingredient translation complete")

        # Run in thread to avoid async context issues
        await sync_to_async(_do_translation)()

    def _normalize_step_temperatures(self, steps: List[Dict]):
        """
        Normalize temperature data in steps to structured format
        Converts strings like "350F" to {"value": 350, "unit": "fahrenheit"}
        """
        from apps.core.utils.temperature_utils import parse_temperature_text

        print(f"[BUILDER] Normalizing temperatures in {len(steps)} steps...")

        for step in steps:
            temp = step.get('temperature')

            if not temp:
                continue

            # If already structured, ensure it's properly formatted
            if isinstance(temp, dict) and 'value' in temp and 'unit' in temp:
                # Normalize unit name
                unit = temp['unit'].lower()
                if unit in ['f', 'fahrenheit', '°f']:
                    temp['unit'] = 'fahrenheit'
                elif unit in ['c', 'celsius', '°c']:
                    temp['unit'] = 'celsius'
                continue

            # If it's a string, parse it
            if isinstance(temp, str):
                parsed_temp = parse_temperature_text(temp)
                if parsed_temp:
                    step['temperature'] = parsed_temp
                    print(
                        f"[BUILDER]   ✅ Parsed temperature: {temp} → {parsed_temp}")
                else:
                    print(
                        f"[BUILDER]   ⚠️ Could not parse temperature: {temp}")
                    step['temperature'] = None
            else:
                # Unknown format, set to None
                step['temperature'] = None

        print(f"[BUILDER] ✅ Temperature normalization complete")

    async def _translate_cooking_steps(self, steps: List[Dict]):
        """
        Translate cooking steps using Gemini/Groq AI for FULL translation
        Modifies steps in-place to add translations

        CRITICAL: Detects source language and translates from that language
        """
        def _do_translation():
            """Run translation in sync context"""
            print(
                f"[BUILDER] Translating {len(steps)} cooking steps using AI...")

            for step in steps:
                instruction = step.get('instruction', '')
                if not instruction:
                    continue

                try:
                    # Detect source language (simple heuristic)
                    # Check if text contains Cyrillic characters
                    has_cyrillic = any('\u0400' <= char <=
                                       '\u04FF' for char in instruction)
                    # Check if text contains Hebrew characters
                    has_hebrew = any('\u0590' <= char <=
                                     '\u05FF' for char in instruction)

                    if has_cyrillic:
                        source_lang = 'ru'
                        print(
                            f"[BUILDER]   🔍 Step {step.get('order', '?')}: Detected Russian source")
                    elif has_hebrew:
                        source_lang = 'he'
                        print(
                            f"[BUILDER]   🔍 Step {step.get('order', '?')}: Detected Hebrew source")
                    else:
                        source_lang = 'en'
                        print(
                            f"[BUILDER]   🔍 Step {step.get('order', '?')}: Detected English source")

                    # Translate from source language to all target languages
                    # Initialize: set source language, others empty (will be filled by translation)
                    translations = {}
                    # Original stays in source lang
                    translations[source_lang] = instruction

                    if source_lang == 'en':
                        # Source is English, translate to RU and HE using Google Translate
                        from apps.core.google_translate_service import get_google_translate_service
                        google_translate = get_google_translate_service()

                        # Translate to Russian
                        result_ru = google_translate.translate_text(
                            instruction, 'ru', 'en')
                        if result_ru:
                            translations['ru'] = result_ru
                            print(f"[BUILDER]   ✅ RU: {result_ru[:50]}...")
                        else:
                            print(
                                f"[BUILDER]   ❌ RU translation failed, keeping English")
                            translations['ru'] = instruction

                        # Translate to Hebrew
                        result_he = google_translate.translate_text(
                            instruction, 'he', 'en')
                        if result_he:
                            translations['he'] = result_he
                            print(f"[BUILDER]   ✅ HE: {result_he[:50]}...")
                        else:
                            print(
                                f"[BUILDER]   ❌ HE translation failed, keeping English")
                            translations['he'] = instruction

                    elif source_lang == 'ru':
                        # Source is Russian, translate to EN and HE
                        from apps.core.google_translate_service import get_google_translate_service
                        google_translate = get_google_translate_service()

                        result_en = google_translate.translate_text(
                            instruction, 'en', 'ru')
                        if result_en:
                            translations['en'] = result_en
                        else:
                            translations['en'] = instruction

                        result_he = google_translate.translate_text(
                            instruction, 'he', 'ru')
                        if result_he:
                            translations['he'] = result_he
                        else:
                            translations['he'] = instruction

                    elif source_lang == 'he':
                        # Source is Hebrew, translate to EN and RU
                        from apps.core.google_translate_service import get_google_translate_service
                        google_translate = get_google_translate_service()

                        result_en = google_translate.translate_text(
                            instruction, 'en', 'he')
                        if result_en:
                            translations['en'] = result_en
                        else:
                            translations['en'] = instruction

                        result_ru = google_translate.translate_text(
                            instruction, 'ru', 'he')
                        if result_ru:
                            translations['ru'] = result_ru
                        else:
                            translations['ru'] = instruction

                    # Set translations in step
                    step['text_translations'] = translations

                except Exception as e:
                    print(f"[BUILDER]   ⚠️ Translation error: {e}")
                    # Fallback: set all to original
                    step['text_translations'] = {
                        'en': instruction,
                        'ru': instruction,
                        'he': instruction
                    }

            print(f"[BUILDER] ✅ Step translation complete")

        # Run in thread to avoid async context issues
        await sync_to_async(_do_translation)()

    def _translate_with_gemini(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text using Gemini AI (PRIMARY translation method)

        Args:
            text: Text to translate
            source_lang: Source language code (en, ru, he)
            target_lang: Target language code (en, ru, he)

        Returns:
            Translated text or raises exception if translation fails
        """
        try:
            import google.generativeai as genai
            from django.conf import settings

            # Get API key from Django settings
            api_key = getattr(settings, 'GEMINI_API_KEY', None)
            if not api_key:
                raise ValueError("GEMINI_API_KEY not configured in settings")

            # Configure Gemini
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-lite')

            lang_names = {
                'en': 'English',
                'ru': 'Russian',
                'he': 'Hebrew'
            }

            # Special instructions for Russian to prevent mixed-language output
            russian_emphasis = ""
            if target_lang == 'ru':
                russian_emphasis = """
═══════════════════════════════════════════════════════════════
🚨 КРИТИЧЕСКИ ВАЖНО - ТОЛЬКО РУССКИЙ ЯЗЫК 🚨
═══════════════════════════════════════════════════════════════

ВЫ ДОЛЖНЫ вывести ВСЁ ТОЛЬКО на РУССКОМ языке.

❌ ЗАПРЕЩЕНО:
- Английские слова: "Place", "Mix", "Preheat", "Grease", etc.
- Смешанный язык: "Place приготовленный rice" ❌
- Частичные переводы: "Mix полностью fried" ❌

✅ ТРЕБУЕТСЯ:
- ВЕСЬ текст должен быть на русском языке: "Поместите приготовленный рис" ✅
- Каждое слово должно быть узнаваемым русским словом

═══════════════════════════════════════════════════════════════
"""

            prompt = f"""Translate this cooking instruction from {lang_names[source_lang]} to {lang_names[target_lang]}.
{russian_emphasis}
Source text ({lang_names[source_lang]}):
"{text}"

Requirements:
1. Translate ONLY the cooking instruction (preserve meaning and cooking terms)
2. Return ONLY the translated text, nothing else
3. Keep temperatures, measurements, and times exactly as they are
4. Maintain the same tone and style
5. For Hebrew: use proper right-to-left Hebrew script
6. For Russian: EVERY word must be in Russian (no English words allowed!)

Translated text ({lang_names[target_lang]}):"""

            response = model.generate_content(prompt)
            translated = response.text.strip()

            # Remove quotes if Gemini added them
            translated = translated.strip('"').strip("'").strip()

            print(
                f"[BUILDER]   ✅ GEMINI translated {source_lang}→{target_lang}: \"{translated[:50]}...\"")
            return translated

        except Exception as e:
            # Re-raise to trigger Groq fallback
            print(
                f"[BUILDER]   ❌ GEMINI failed ({source_lang}→{target_lang}): {str(e)[:100]}")
            raise

    def _translate_with_groq(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text using Groq as fallback when Gemini fails

        Args:
            text: Text to translate
            source_lang: Source language code (en, ru, he)
            target_lang: Target language code (en, ru, he)

        Returns:
            Translated text or original if translation fails
        """
        if not self.groq_client:
            print(f"[BUILDER] ⚠️ Groq not available, keeping original text")
            return text

        try:
            lang_names = {
                'en': 'English',
                'ru': 'Russian',
                'he': 'Hebrew'
            }

            # Special system message for Russian
            system_message = "You are a professional cooking translator. Return ONLY the translated text."
            if target_lang == 'ru':
                system_message = "Вы профессиональный переводчик рецептов. Возвращайте ТОЛЬКО переведенный текст. ВСЕ слова должны быть ПОЛНОСТЬЮ на русском языке."

            # Special instructions for Russian to prevent mixed-language output
            russian_emphasis = ""
            if target_lang == 'ru':
                russian_emphasis = """

═══════════════════════════════════════════════════════════════
🚨 КРИТИЧЕСКИ ВАЖНО - ТОЛЬКО РУССКИЙ ЯЗЫК 🚨
═══════════════════════════════════════════════════════════════

ВЫ ДОЛЖНЫ вывести ВСЁ ТОЛЬКО на РУССКОМ языке.

❌ ЗАПРЕЩЕНО:
- Английские слова: "Place", "Mix", "Preheat", "Grease", etc.
- Смешанный язык: "Place приготовленный rice" ❌
- Частичные переводы: "Mix полностью fried" ❌

✅ ТРЕБУЕТСЯ:
- ВЕСЬ текст должен быть на русском языке: "Поместите приготовленный рис" ✅
- Каждое слово должно быть узнаваемым русским словом

═══════════════════════════════════════════════════════════════
"""

            prompt = f"""Translate this cooking instruction from {lang_names[source_lang]} to {lang_names[target_lang]}.
{russian_emphasis}
Source text ({lang_names[source_lang]}):
"{text}"

Requirements:
1. Translate ONLY the cooking instruction (preserve meaning and cooking terms)
2. Return ONLY the translated text, nothing else
3. Keep temperatures, measurements, and times exactly as they are
4. Maintain the same tone and style
5. For Hebrew: use proper right-to-left Hebrew script
6. For Russian: EVERY word must be in Russian (no English words allowed!)

Translated text ({lang_names[target_lang]}):"""

            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=300
            )

            translated = response.choices[0].message.content.strip()
            # Remove quotes if Groq added them
            translated = translated.strip('"').strip("'").strip()

            print(
                f"[BUILDER]   ✅ Groq translated {source_lang}→{target_lang}: \"{translated[:50]}...\"")
            return translated

        except Exception as e:
            print(
                f"[BUILDER]   ❌ Groq translation failed: {e}, keeping original")
            return text

    async def _check_for_duplicates(self, recipe_name: str, ingredients: Optional[List[str]] = None):
        """
        Check if recipe with same name exists using AI-powered semantic matching
        Uses RecipeDeduplicationService (Groq + Gemini)
        """
        from apps.core.deduplication_service import get_deduplication_service

        print(f"[BUILDER] Checking for duplicates using AI: '{recipe_name}'")

        dedup_service = get_deduplication_service()
        existing = await dedup_service.find_duplicate(
            recipe_name=recipe_name,
            ingredients=ingredients,
            user_language='en'  # Builder is always in English first
        )

        if existing:
            print(f"[BUILDER] ✅ AI found duplicate: {existing.name}")
        else:
            print(f"[BUILDER] ✅ No duplicates found")

        return existing

    def _calculate_recipe_hash(self, name: str, ingredients: List[Dict]) -> str:
        """Calculate hash for deduplication"""
        import hashlib

        normalized_name = ' '.join(name.lower().split())
        sorted_ingredients = sorted([ing['name'].lower()
                                    for ing in ingredients])
        hash_string = f"{normalized_name}:{','.join(sorted_ingredients)}"

        return hashlib.sha256(hash_string.encode()).hexdigest()
