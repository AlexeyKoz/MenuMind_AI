"""
Nutrition AI Coach Service

Privacy-first AI coaching that respects user permissions
"""
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.db.models import Sum, Avg
from groq import Groq
import json


class NutritionGoalCalculator:
    """Calculate nutrition goals based on user profile (with permission checks)"""

    @staticmethod
    def calculate_goals(user, settings_obj) -> Dict:
        """
        Calculate optimal nutrition goals based on user profile
        Returns goals and their source (manual, ai_calculated, or fallback)
        """
        # If manual mode or AI coach disabled, use manual goals
        if not settings_obj.ai_coach_enabled or settings_obj.goal_mode == 'manual':
            return {
                "calories": settings_obj.manual_calories_goal or user.daily_calories_goal or 2000,
                "protein": settings_obj.manual_protein_goal or user.daily_protein_goal or 150,
                "carbs": settings_obj.manual_carbs_goal or user.daily_carbs_goal or 200,
                "fat": settings_obj.manual_fat_goal or user.daily_fat_goal or 67,
                "source": "manual"
            }

        # AI calculated mode - requires personal data access
        if settings_obj.goal_mode == 'ai_calculated' and settings_obj.allow_personal_data_access:
            return NutritionGoalCalculator._calculate_ai_goals(user, settings_obj)

        # Fallback to manual
        return {
            "calories": settings_obj.manual_calories_goal or user.daily_calories_goal or 2000,
            "protein": settings_obj.manual_protein_goal or user.daily_protein_goal or 150,
            "carbs": settings_obj.manual_carbs_goal or user.daily_carbs_goal or 200,
            "fat": settings_obj.manual_fat_goal or user.daily_fat_goal or 67,
            "source": "manual_fallback"
        }

    @staticmethod
    def _calculate_ai_goals(user, settings_obj) -> Dict:
        """Calculate goals using AI/scientific formulas"""
        profile = {}

        # Gather permitted data
        if settings_obj.allow_weight_data and user.weight_kg:
            profile["weight_kg"] = float(user.weight_kg)

        if settings_obj.allow_height_data and user.height_cm:
            profile["height_cm"] = user.height_cm

        if settings_obj.allow_age_data and user.birth_date:
            today = date.today()
            age = today.year - user.birth_date.year
            if (today.month, today.day) < (user.birth_date.month, user.birth_date.day):
                age -= 1
            profile["age"] = age

        if settings_obj.allow_gender_data and user.gender:
            profile["gender"] = user.gender

        if settings_obj.allow_activity_level and user.activity_level:
            profile["activity_level"] = user.activity_level

        # Calculate BMR using Mifflin-St Jeor Equation
        if all(k in profile for k in ["weight_kg", "height_cm", "age", "gender"]):
            if profile["gender"] == "male":
                bmr = 10 * profile["weight_kg"] + 6.25 * \
                    profile["height_cm"] - 5 * profile["age"] + 5
            else:
                bmr = 10 * profile["weight_kg"] + 6.25 * \
                    profile["height_cm"] - 5 * profile["age"] - 161

            # Apply activity multiplier
            activity_multipliers = {
                "sedentary": 1.2,
                "light": 1.375,
                "moderate": 1.55,
                "very": 1.725,
                "extra": 1.9
            }
            tdee = bmr * \
                activity_multipliers.get(profile.get(
                    "activity_level", "moderate"), 1.55)

            # Calculate macros
            protein = profile["weight_kg"] * 2  # 2g per kg body weight
            fat = (tdee * 0.25) / 9  # 25% of calories from fat (9 cal/g)
            # Remaining calories from carbs (4 cal/g)
            carbs = (tdee - (protein * 4) - (fat * 9)) / 4

            return {
                "calories": int(tdee),
                "protein": int(protein),
                "carbs": int(carbs),
                "fat": int(fat),
                "source": "ai_calculated",
                "bmr": int(bmr),
                "tdee": int(tdee)
            }

        # Not enough data - fallback to manual
        return {
            "calories": settings_obj.manual_calories_goal or user.daily_calories_goal or 2000,
            "protein": settings_obj.manual_protein_goal or user.daily_protein_goal or 150,
            "carbs": settings_obj.manual_carbs_goal or user.daily_carbs_goal or 200,
            "fat": settings_obj.manual_fat_goal or user.daily_fat_goal or 67,
            "source": "insufficient_data_fallback"
        }


class NutritionCoach:
    """Privacy-respecting AI nutrition coach"""

    def __init__(self):
        """Initialize with Groq client"""
        groq_api_key = os.getenv('GROQ_API_KEY') or getattr(
            settings, 'GROQ_API_KEY', None)
        if not groq_api_key:
            print("[NUTRITION COACH] WARNING: GROQ_API_KEY not found")
            self.client = None
        else:
            self.client = Groq(api_key=groq_api_key)
        self.model = "llama-3.1-8b-instant"

    def generate_daily_suggestion(
        self,
        user,
        nutrition_settings,
        today_summary: Dict,
        meal_type: Optional[str] = None,
        max_calories: Optional[int] = None
    ) -> Dict:
        """
        Generate AI suggestions for remaining meals
        Respects user privacy settings
        """
        if not self.client or not nutrition_settings.ai_coach_enabled:
            return {
                "ai_enabled": False,
                "message": "AI Coach is disabled. Enable it in settings to get personalized suggestions."
            }

        # Build context from permitted data sources
        context = self._build_coaching_context(
            user, nutrition_settings, today_summary)

        # Generate prompt
        prompt = self._build_suggestion_prompt(
            context,
            nutrition_settings.coaching_style,
            meal_type,
            max_calories
        )

        try:
            # Call Groq AI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a {nutrition_settings.coaching_style} nutrition coach. Provide concise, helpful meal suggestions in JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=800
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            # Clean potential markdown code blocks
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            result = json.loads(result_text)

            return {
                "ai_enabled": True,
                "message": result.get("message", ""),
                "suggestions": result.get("suggestions", [])
            }

        except json.JSONDecodeError as e:
            print(f"[NUTRITION COACH] JSON parse error: {e}")
            print(f"[NUTRITION COACH] Raw response: {result_text}")
            return {
                "ai_enabled": True,
                "message": "I'm having trouble formatting suggestions. Try again or check your remaining calories manually.",
                "suggestions": []
            }
        except Exception as e:
            print(f"[NUTRITION COACH] Error: {e}")
            return {
                "ai_enabled": True,
                "message": "I'm temporarily unavailable. Please try again later.",
                "suggestions": []
            }

    def answer_coaching_question(
        self,
        user,
        nutrition_settings,
        question: str,
        today_summary: Dict
    ) -> Dict:
        """
        Answer user's nutrition questions
        Respects privacy settings
        """
        if not self.client or not nutrition_settings.ai_coach_enabled:
            return {
                "advice": "AI Coach is disabled. Enable it in settings to ask questions."
            }

        context = self._build_coaching_context(
            user, nutrition_settings, today_summary)

        prompt = f"""User Question: {question}

Your Current Context:
{context}

Provide a helpful, {nutrition_settings.coaching_style} response. Keep it under 3 sentences.
If relevant, suggest 1-2 specific meal options.

Return JSON:
{{
    "advice": "Your answer here",
    "suggestions": [
        {{
            "name": "Meal name",
            "reason": "Why this helps"
        }}
    ]
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a {nutrition_settings.coaching_style} nutrition coach answering user questions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )

            result_text = response.choices[0].message.content.strip()

            # Clean markdown
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            result = json.loads(result_text)
            return result

        except Exception as e:
            print(f"[NUTRITION COACH] Error answering question: {e}")
            return {
                "advice": "I'm having trouble processing your question. Please try rephrasing it."
            }

    def _build_coaching_context(self, user, nutrition_settings, today_summary: Dict) -> str:
        """Build context string based on permitted data"""
        context_parts = []

        # Goals (always available)
        goals = today_summary.get('goals', {})
        consumed = today_summary.get('consumed', {})
        remaining = today_summary.get('remaining', {})

        context_parts.append(
            f"Goals: {goals.get('calories')}kcal, {goals.get('protein')}g protein")
        context_parts.append(
            f"Consumed: {consumed.get('calories')}kcal, {consumed.get('protein')}g protein")
        context_parts.append(
            f"Remaining: {remaining.get('calories')}kcal, {remaining.get('protein')}g protein")

        # Recipe access
        if nutrition_settings.allow_recipes_access:
            from apps.recipes.models import Recipe
            user_recipes = Recipe.objects.filter(
                created_by=user, is_fork=True)[:5]
            if user_recipes.exists():
                recipe_names = [r.name for r in user_recipes]
                context_parts.append(
                    f"Your available recipes: {', '.join(recipe_names)}")

        # Inventory access
        if nutrition_settings.allow_inventory_access:
            from apps.shopping.models import Inventory
            inventory = Inventory.objects.filter(user=user)[:10]
            if inventory.exists():
                items = [i.name for i in inventory]
                context_parts.append(f"Your inventory: {', '.join(items)}")

        # Personal data
        if nutrition_settings.allow_personal_data_access:
            if nutrition_settings.allow_health_conditions:
                if user.dietary_restrictions:
                    context_parts.append(
                        f"Dietary restrictions: {', '.join(user.dietary_restrictions)}")
                if user.allergies:
                    context_parts.append(
                        f"Allergies: {', '.join(user.allergies)}")

        return "\n".join(context_parts)

    def _build_suggestion_prompt(
        self,
        context: str,
        coaching_style: str,
        meal_type: Optional[str],
        max_calories: Optional[int]
    ) -> str:
        """Build prompt for meal suggestions"""
        style_instructions = {
            "supportive": "Be encouraging, positive, and gentle. Celebrate progress.",
            "strict": "Be direct, disciplined, and firm. Focus on goals and accountability.",
            "balanced": "Mix encouragement with practical advice. Be realistic."
        }

        meal_filter = f"for {meal_type}" if meal_type else "for remaining meals today"
        calorie_limit = f"Stay under {max_calories} kcal." if max_calories else ""

        return f"""You are a {coaching_style} nutrition coach.
{style_instructions.get(coaching_style, '')}

Current Context:
{context}

Task:
1. Provide encouraging feedback on progress (1-2 sentences)
2. Suggest 2-3 meal ideas {meal_filter} {calorie_limit}
3. If user has recipes/inventory, prioritize those
4. Keep response concise

Return JSON:
{{
    "message": "Your coaching message here",
    "suggestions": [
        {{
            "name": "Meal name",
            "source": "recipe|inventory|general",
            "calories": X,
            "protein": Y,
            "reason": "Why this meal fits"
        }}
    ]
}}
"""


class NutritionSummaryService:
    """Service for generating nutrition summaries"""

    @staticmethod
    def get_daily_summary(user, target_date: date, nutrition_settings) -> Dict:
        """Get complete daily nutrition summary"""
        from .models import NutritionEntry

        # Get entries for the day
        entries = NutritionEntry.objects.filter(
            user=user,
            date=target_date
        ).order_by('meal_type', 'time', 'created_at')

        # Calculate consumed totals
        totals = entries.aggregate(
            total_calories=Sum('calories'),
            total_protein=Sum('protein'),
            total_carbs=Sum('carbs'),
            total_fat=Sum('fat')
        )

        consumed = {
            "calories": float(totals['total_calories'] or 0),
            "protein": float(totals['total_protein'] or 0),
            "carbs": float(totals['total_carbs'] or 0),
            "fat": float(totals['total_fat'] or 0)
        }

        # Get goals
        goals = NutritionGoalCalculator.calculate_goals(
            user, nutrition_settings)

        # Calculate remaining
        remaining = {
            "calories": goals['calories'] - consumed['calories'],
            "protein": goals['protein'] - consumed['protein'],
            "carbs": goals.get('carbs', 0) - consumed['carbs'],
            "fat": goals.get('fat', 0) - consumed['fat']
        }

        # Calculate percentages
        percentage = {
            "calories": round((consumed['calories'] / goals['calories'] * 100), 1) if goals['calories'] > 0 else 0,
            "protein": round((consumed['protein'] / goals['protein'] * 100), 1) if goals['protein'] > 0 else 0,
            "carbs": round((consumed['carbs'] / goals.get('carbs', 1) * 100), 1) if goals.get('carbs', 0) > 0 else 0,
            "fat": round((consumed['fat'] / goals.get('fat', 1) * 100), 1) if goals.get('fat', 0) > 0 else 0
        }

        return {
            "date": target_date,
            "goals": goals,
            "consumed": consumed,
            "remaining": remaining,
            "percentage": percentage,
            "meals": entries
        }

    @staticmethod
    def get_weekly_summary(user, week_start: date, nutrition_settings) -> Dict:
        """Get weekly nutrition summary"""
        from .models import NutritionEntry

        week_end = week_start + timedelta(days=6)

        # Get all entries for the week
        entries = NutritionEntry.objects.filter(
            user=user,
            date__gte=week_start,
            date__lte=week_end
        )

        # Weekly totals
        totals = entries.aggregate(
            total_calories=Sum('calories'),
            total_protein=Sum('protein'),
            total_carbs=Sum('carbs'),
            total_fat=Sum('fat')
        )

        # Daily averages
        entry_days = entries.values('date').distinct().count() or 1
        daily_averages = {
            "calories": float(totals['total_calories'] or 0) / entry_days,
            "protein": float(totals['total_protein'] or 0) / entry_days,
            "carbs": float(totals['total_carbs'] or 0) / entry_days,
            "fat": float(totals['total_fat'] or 0) / entry_days
        }

        # Get goals
        goals = NutritionGoalCalculator.calculate_goals(
            user, nutrition_settings)

        # Goal adherence
        goal_adherence = {
            "calories": round((daily_averages['calories'] / goals['calories'] * 100), 1) if goals['calories'] > 0 else 0,
            "protein": round((daily_averages['protein'] / goals['protein'] * 100), 1) if goals['protein'] > 0 else 0
        }

        # Day-by-day breakdown
        days = []
        for i in range(7):
            day_date = week_start + timedelta(days=i)
            day_entries = entries.filter(date=day_date)
            day_totals = day_entries.aggregate(
                calories=Sum('calories'),
                protein=Sum('protein')
            )
            days.append({
                "date": day_date,
                "calories": float(day_totals['calories'] or 0),
                "protein": float(day_totals['protein'] or 0),
                "entry_count": day_entries.count()
            })

        return {
            "week_start": week_start,
            "week_end": week_end,
            "daily_averages": daily_averages,
            "weekly_totals": {
                "calories": float(totals['total_calories'] or 0),
                "protein": float(totals['total_protein'] or 0),
                "carbs": float(totals['total_carbs'] or 0),
                "fat": float(totals['total_fat'] or 0)
            },
            "goal_adherence": goal_adherence,
            "days": days
        }
