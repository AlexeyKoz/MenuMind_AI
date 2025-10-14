"""
Expiration Calculator Service - Calculates expiration dates from IML shelf_life
NO AI CALLS - uses cached shelf_life data from IML
"""
from typing import Dict, Optional, Tuple
from datetime import date, timedelta
from .models import IngredientCache


class ExpirationCalculator:
    """Calculate expiration dates from IML shelf_life data"""

    # Storage location mapping
    STORAGE_LOCATIONS = [
        'room_temperature',
        'refrigerator',
        'freezer',
        'counter',  # alias for room_temperature
        'fridge',   # alias for refrigerator
        'pantry'    # alias for room_temperature
    ]

    # Location aliases
    LOCATION_ALIASES = {
        'counter': 'room_temperature',
        'fridge': 'refrigerator',
        'pantry': 'room_temperature',
        'room': 'room_temperature'
    }

    def __init__(self):
        self.groq_client = None
        # AI fallback (optional)
        try:
            from groq import Groq
            from django.conf import settings
            groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
            if groq_api_key:
                self.groq_client = Groq(api_key=groq_api_key)
        except:
            pass

    def calculate_expiration(
        self,
        ingredient_key: str,
        location: str,
        purchase_date: Optional[date] = None
    ) -> Tuple[Optional[date], str]:
        """
        Calculate expiration date from IML shelf_life

        Args:
            ingredient_key: Ingredient key (e.g., "tomatoes-red-ripe")
            location: Storage location (room_temperature, refrigerator, freezer)
            purchase_date: Purchase date (default: today)

        Returns:
            (expiration_date, source)
            source: 'iml', 'ai', or 'default'
        """
        if purchase_date is None:
            purchase_date = date.today()

        # Normalize location
        location = self._normalize_location(location)

        # Try to get shelf_life from IML
        shelf_life_days = self._get_shelf_life_from_iml(
            ingredient_key, location)

        if shelf_life_days is not None:
            expiration_date = purchase_date + timedelta(days=shelf_life_days)
            return (expiration_date, 'iml')

        # Fallback to AI (if available)
        if self.groq_client:
            shelf_life_days = self._get_shelf_life_from_ai(
                ingredient_key, location)
            if shelf_life_days is not None:
                expiration_date = purchase_date + \
                    timedelta(days=shelf_life_days)
                return (expiration_date, 'ai')

        # Default fallback (conservative estimate)
        default_days = self._get_default_shelf_life(location)
        expiration_date = purchase_date + timedelta(days=default_days)
        return (expiration_date, 'default')

    def suggest_storage_location(self, ingredient_key: str) -> Tuple[str, str]:
        """
        Suggest best storage location from IML recommendations

        Args:
            ingredient_key: Ingredient key

        Returns:
            (location, source)
            source: 'iml', 'ai', or 'default'
        """
        try:
            ingredient = IngredientCache.objects.get(
                ingredient_key=ingredient_key)
            storage_recs = ingredient.storage_recommendations

            if storage_recs and isinstance(storage_recs, dict):
                recommended = storage_recs.get('recommended')
                if recommended:
                    return (self._normalize_location(recommended), 'iml')

            # Fallback: guess from shelf_life (longest storage = best location)
            shelf_life = ingredient.shelf_life
            if shelf_life and isinstance(shelf_life, dict):
                # Find location with longest shelf life
                max_days = 0
                best_location = 'refrigerator'

                for loc, days in shelf_life.items():
                    if days and days > max_days:
                        max_days = days
                        best_location = loc

                return (self._normalize_location(best_location), 'iml')

        except IngredientCache.DoesNotExist:
            pass

        # AI fallback (if available)
        if self.groq_client:
            ai_location = self._suggest_storage_from_ai(ingredient_key)
            if ai_location:
                return (ai_location, 'ai')

        # Default: refrigerator (safest)
        return ('refrigerator', 'default')

    def get_shelf_life_info(self, ingredient_key: str) -> Optional[Dict]:
        """
        Get full shelf_life info from IML

        Returns:
            {
                "room_temperature": 2,
                "refrigerator": 7,
                "freezer": 180,
                "recommended": "refrigerator",
                "notes": "..."
            }
        """
        try:
            ingredient = IngredientCache.objects.get(
                ingredient_key=ingredient_key)

            result = {}

            # Shelf life data
            if ingredient.shelf_life and isinstance(ingredient.shelf_life, dict):
                result.update(ingredient.shelf_life)

            # Storage recommendations
            if ingredient.storage_recommendations and isinstance(ingredient.storage_recommendations, dict):
                result['recommended'] = ingredient.storage_recommendations.get(
                    'recommended')
                result['notes'] = ingredient.storage_recommendations.get(
                    'notes', '')

            return result if result else None

        except IngredientCache.DoesNotExist:
            return None

    def _get_shelf_life_from_iml(
        self,
        ingredient_key: str,
        location: str
    ) -> Optional[int]:
        """Get shelf_life days from IML cache"""
        try:
            ingredient = IngredientCache.objects.get(
                ingredient_key=ingredient_key)
            shelf_life = ingredient.shelf_life

            if shelf_life and isinstance(shelf_life, dict):
                days = shelf_life.get(location)
                if days is not None:
                    return int(days)

            return None
        except IngredientCache.DoesNotExist:
            return None

    def _get_shelf_life_from_ai(
        self,
        ingredient_key: str,
        location: str
    ) -> Optional[int]:
        """AI fallback for shelf_life (Groq)"""
        if not self.groq_client:
            return None

        try:
            # Get ingredient name for better AI understanding
            try:
                ingredient = IngredientCache.objects.get(
                    ingredient_key=ingredient_key)
                from .models import IngredientTranslation
                translation = IngredientTranslation.objects.filter(
                    ingredient=ingredient,
                    language='en'
                ).first()
                ingredient_name = translation.name if translation else ingredient_key
            except:
                ingredient_name = ingredient_key

            prompt = f"""What is the typical shelf life for {ingredient_name} when stored in {location}?

Return ONLY a number (days). Examples:
- Fresh tomatoes in refrigerator: 7
- Chicken in freezer: 180
- Bread on counter: 3

Ingredient: {ingredient_name}
Location: {location}
Shelf life (days):"""

            completion = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a food storage expert. Return only the number of days."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )

            response = completion.choices[0].message.content.strip()

            # Extract number
            import re
            match = re.search(r'\d+', response)
            if match:
                return int(match.group())

        except Exception as e:
            print(f"[AI EXPIRATION ERROR] {e}")

        return None

    def _suggest_storage_from_ai(self, ingredient_key: str) -> Optional[str]:
        """AI fallback for storage location suggestion"""
        if not self.groq_client:
            return None

        try:
            prompt = f"""What is the best storage location for: {ingredient_key}?

Return ONLY one word:
- refrigerator
- freezer
- room_temperature

Ingredient: {ingredient_key}
Best location:"""

            completion = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system",
                        "content": "You are a food storage expert. Return only one word."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )

            response = completion.choices[0].message.content.strip().lower()

            if response in ['refrigerator', 'freezer', 'room_temperature']:
                return response

        except Exception as e:
            print(f"[AI STORAGE ERROR] {e}")

        return None

    def _normalize_location(self, location: str) -> str:
        """Normalize storage location"""
        location = location.lower().strip()
        return self.LOCATION_ALIASES.get(location, location)

    def _get_default_shelf_life(self, location: str) -> int:
        """Conservative default shelf life by location"""
        defaults = {
            'room_temperature': 3,
            'refrigerator': 7,
            'freezer': 90
        }
        return defaults.get(location, 7)
