"""
Ingredient Mapper Service - Maps text to ingredient_key from IML
Supports: parsing, exact match, fuzzy match, aliases, AI fallback
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from django.db.models import Q
from django.conf import settings
from .models import IngredientCache, IngredientTranslation


@dataclass
class MatchResult:
    """Result of ingredient matching"""
    ingredient_key: Optional[str]
    confidence: float  # 0.0 - 1.0
    display_name: str
    matched_translation: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_type: Optional[str] = None
    original_text: Optional[str] = None


class IngredientMapper:
    """Service for mapping text to ingredient_key with confidence scoring"""

    # Unit type mapping
    UNIT_TYPES = {
        'weight': ['g', 'kg', 'mg', 'oz', 'lb', 'pound', 'gram', 'kilogram'],
        'volume': ['ml', 'l', 'dl', 'cup', 'gallon', 'fl oz', 'pint', 'quart', 'liter', 'milliliter'],
        'cooking': ['tsp', 'tbsp', 'teaspoon', 'tablespoon', 'pinch', 'dash'],
        'count': ['pcs', 'pieces', 'piece', 'unit', 'units', 'cloves', 'clove', 'leaves', 'stalks']
    }

    # Unit aliases for normalization
    UNIT_ALIASES = {
        'teaspoon': 'tsp', 'teaspoons': 'tsp',
        'tablespoon': 'tbsp', 'tablespoons': 'tbsp',
        'pieces': 'pcs', 'piece': 'pcs',
        'gram': 'g', 'grams': 'g', 'грамм': 'g', 'гр': 'g',
        'kilogram': 'kg', 'kilograms': 'kg', 'килограмм': 'kg', 'кг': 'kg',
        'liter': 'L', 'liters': 'L', 'litre': 'L', 'литр': 'L', 'л': 'L',
        'milliliter': 'ml', 'milliliters': 'ml', 'миллилитр': 'ml', 'мл': 'ml',
        'ounce': 'oz', 'ounces': 'oz',
        'pound': 'lb', 'pounds': 'lb', 'фунт': 'lb',
        'unit': 'pcs', 'units': 'pcs',
        'יחידות': 'pcs', 'יחידה': 'pcs',
        'כוס': 'cup', 'כפית': 'tsp', 'כף': 'tbsp'
    }

    def __init__(self):
        self.groq_client = None
        try:
            from groq import Groq
            groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
            if groq_api_key:
                self.groq_client = Groq(api_key=groq_api_key)
        except ImportError:
            pass

    def map(self, text: str, language: str = 'en', user_unit_system: str = 'metric') -> MatchResult:
        """
        Map text to ingredient_key with confidence

        Args:
            text: User input (e.g., "500g помідори", "2 cups flour")
            language: User's language (en, ru, he)
            user_unit_system: User's unit preference (metric, imperial)

        Returns:
            MatchResult with ingredient_key, confidence, and parsed data
        """
        # Step 1: Parse text (extract quantity, unit, name)
        quantity, unit, ingredient_name = self._parse_text(text)

        # Step 2: Normalize unit
        normalized_unit, unit_type = self._normalize_unit(
            unit) if unit else (None, None)

        # Step 3: Find ingredient match
        match = self._find_ingredient_match(ingredient_name, language)

        if match:
            return MatchResult(
                ingredient_key=match['key'],
                confidence=match['confidence'],
                display_name=match['display_name'],
                matched_translation=match.get('matched_translation'),
                quantity=quantity,
                unit=normalized_unit,
                unit_type=unit_type,
                original_text=text
            )

        # Step 4: No match - return with low confidence
        return MatchResult(
            ingredient_key=None,
            confidence=0.0,
            display_name=ingredient_name or text,
            quantity=quantity,
            unit=normalized_unit,
            unit_type=unit_type,
            original_text=text
        )

    def _parse_text(self, text: str) -> Tuple[Optional[float], Optional[str], str]:
        """
        Parse text to extract quantity, unit, and ingredient name

        Examples:
            "500g помідори" → (500, 'g', 'помідори')
            "2 cups flour" → (2, 'cups', 'flour')
            "tomatoes" → (None, None, 'tomatoes')

        Returns:
            (quantity, unit, ingredient_name)
        """
        text = text.strip()

        # Pattern: <number> <unit> <name>
        # Supports: 500g, 2.5 kg, 1 cup, etc.
        pattern = r'^(\d+\.?\d*)\s*([a-zA-Zа-яА-Яא-ת]+)?\s+(.+)$'
        match = re.match(pattern, text)

        if match:
            quantity_str, unit, name = match.groups()
            quantity = float(quantity_str) if quantity_str else None
            return (quantity, unit, name.strip())

        # Pattern: <number> <name> (no unit)
        pattern = r'^(\d+\.?\d*)\s+(.+)$'
        match = re.match(pattern, text)

        if match:
            quantity_str, name = match.groups()
            quantity = float(quantity_str) if quantity_str else None
            return (quantity, None, name.strip())

        # No quantity/unit found - return whole text as ingredient name
        return (None, None, text)

    def _normalize_unit(self, unit: str) -> Tuple[str, str]:
        """
        Normalize unit and determine unit type

        Args:
            unit: Raw unit text (e.g., "teaspoons", "грамм", "כוס")

        Returns:
            (normalized_unit, unit_type)
        """
        if not unit:
            return (None, None)

        unit_lower = unit.lower().strip()

        # Check aliases first
        if unit_lower in self.UNIT_ALIASES:
            normalized = self.UNIT_ALIASES[unit_lower]
        else:
            normalized = unit_lower

        # Determine unit type
        for unit_type, units in self.UNIT_TYPES.items():
            if normalized in units or unit_lower in units:
                return (normalized, unit_type)

        # Unknown unit - default to 'weight' for metric-like, 'count' otherwise
        if normalized in ['g', 'kg', 'mg', 'oz', 'lb']:
            return (normalized, 'weight')
        elif normalized in ['ml', 'l', 'dl']:
            return (normalized, 'volume')
        else:
            return (normalized, 'count')

    def _find_ingredient_match(self, name: str, language: str) -> Optional[Dict]:
        """
        Find ingredient match using multiple strategies

        Strategies (in order):
        1. Exact match (1.0 confidence)
        2. Case-insensitive match (0.95 confidence)
        3. Alias match (0.90 confidence)
        4. Fuzzy match (0.70-0.89 confidence)
        5. Cross-language match (0.85 confidence)
        6. AI fallback (varies)

        Returns:
            {
                'key': ingredient_key,
                'confidence': 0.0-1.0,
                'display_name': name in user's language,
                'matched_translation': original matched text
            }
        """
        if not name:
            return None

        # Strategy 1: Exact match (case-sensitive)
        result = self._exact_match(name, language)
        if result:
            return result

        # Strategy 2: Case-insensitive match
        result = self._case_insensitive_match(name, language)
        if result:
            return result

        # Strategy 3: Alias match
        result = self._alias_match(name, language)
        if result:
            return result

        # Strategy 4: Fuzzy match (Levenshtein-like)
        result = self._fuzzy_match(name, language)
        if result:
            return result

        # Strategy 5: Cross-language match
        result = self._cross_language_match(name, language)
        if result:
            return result

        # Strategy 6: AI fallback (if available) - DISABLED for now due to rate limits
        # if self.groq_client:
        #     result = self._ai_match(name, language)
        #     if result:
        #         return result

        # Strategy 7: Synthetic key (ALWAYS succeeds)
        # Create a normalized key from the ingredient name
        # This allows translation to work even if not in IML database
        synthetic_key = self._create_synthetic_key(name)
        return {
            'key': synthetic_key,
            'confidence': 0.5,  # Medium confidence
            'display_name': name,  # Store as string, will be dict after translation
            'matched_translation': name
        }

    def _create_synthetic_key(self, name: str) -> str:
        """
        Create a synthetic ingredient_key from the name
        Format: synthetic_{normalized_name}
        """
        import re
        # Normalize: lowercase, remove special chars, replace spaces with underscores
        normalized = re.sub(r'[^a-z0-9\s]', '', name.lower())
        normalized = re.sub(r'\s+', '_', normalized.strip())
        return f"synthetic_{normalized}"

    def _get_all_translations(self, ingredient) -> Dict[str, str]:
        """
        Get all language translations for an ingredient

        Returns:
            {'en': 'tomato', 'ru': 'помидор', 'he': 'עגבנייה'}
        """
        translations = {}
        for trans in ingredient.translations.all():
            translations[trans.language] = trans.name
        return translations

    def _exact_match(self, name: str, language: str) -> Optional[Dict]:
        """Exact match (case-sensitive)"""
        translation = IngredientTranslation.objects.filter(
            language=language,
            name=name
        ).select_related('ingredient').first()

        if translation:
            # Get ALL language translations for this ingredient
            all_translations = self._get_all_translations(
                translation.ingredient)

            return {
                'key': translation.ingredient.ingredient_key,
                'confidence': 1.0,
                'display_name': all_translations,  # Dict with en, ru, he
                'matched_translation': name
            }
        return None

    def _case_insensitive_match(self, name: str, language: str) -> Optional[Dict]:
        """Case-insensitive match"""
        translation = IngredientTranslation.objects.filter(
            language=language,
            name__iexact=name
        ).select_related('ingredient').first()

        if translation:
            all_translations = self._get_all_translations(
                translation.ingredient)

            return {
                'key': translation.ingredient.ingredient_key,
                'confidence': 0.95,
                'display_name': all_translations,
                'matched_translation': name
            }
        return None

    def _alias_match(self, name: str, language: str) -> Optional[Dict]:
        """Match against aliases"""
        # Django JSONField contains lookup for arrays
        translations = IngredientTranslation.objects.filter(
            language=language,
            aliases__icontains=name.lower()
        ).select_related('ingredient')

        for translation in translations:
            # Verify exact alias match (case-insensitive)
            if any(alias.lower() == name.lower() for alias in translation.aliases):
                all_translations = self._get_all_translations(
                    translation.ingredient)

                return {
                    'key': translation.ingredient.ingredient_key,
                    'confidence': 0.90,
                    'display_name': all_translations,
                    'matched_translation': name
                }
        return None

    def _fuzzy_match(self, name: str, language: str, threshold: float = 0.70) -> Optional[Dict]:
        """
        Fuzzy match using simple similarity
        (In production, use python-Levenshtein for better performance)
        """
        from difflib import SequenceMatcher

        name_lower = name.lower()

        # Get candidates from database
        translations = IngredientTranslation.objects.filter(
            language=language
        ).select_related('ingredient')[:1000]  # Limit for performance

        best_match = None
        best_score = threshold

        for translation in translations:
            # Calculate similarity
            score = SequenceMatcher(
                None, name_lower, translation.name.lower()).ratio()

            if score > best_score:
                best_score = score
                best_match = translation

        if best_match:
            all_translations = self._get_all_translations(
                best_match.ingredient)

            return {
                'key': best_match.ingredient.ingredient_key,
                'confidence': round(best_score, 2),
                'display_name': all_translations,
                'matched_translation': name
            }

        return None

    def _cross_language_match(self, name: str, language: str) -> Optional[Dict]:
        """Match in other languages (user typed in wrong language)"""
        other_languages = ['en', 'ru', 'he']
        other_languages.remove(language)

        for lang in other_languages:
            translation = IngredientTranslation.objects.filter(
                language=lang,
                name__iexact=name
            ).select_related('ingredient').first()

            if translation:
                all_translations = self._get_all_translations(
                    translation.ingredient)

                return {
                    'key': translation.ingredient.ingredient_key,
                    'confidence': 0.85,
                    'display_name': all_translations,
                    'matched_translation': name
                }

        return None

    def _ai_match(self, name: str, language: str) -> Optional[Dict]:
        """AI fallback using Groq (last resort)"""
        if not self.groq_client:
            return None

        try:
            # Get sample ingredients from DB for AI to match against
            sample_translations = IngredientTranslation.objects.filter(
                language=language
            ).select_related('ingredient')[:50]

            ingredient_list = '\n'.join([
                f"- {t.name} (key: {t.ingredient.ingredient_key})"
                for t in sample_translations
            ])

            prompt = f"""Match the ingredient name to the most similar item from the list:

User input: "{name}"
Language: {language}

Available ingredients:
{ingredient_list}

Return ONLY the ingredient_key of the best match, or "NO_MATCH" if none are similar.
Be strict - only match if very similar."""

            completion = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an ingredient matching expert. Return only the ingredient_key or NO_MATCH."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )

            response = completion.choices[0].message.content.strip()

            if response and response != "NO_MATCH":
                # Verify the key exists
                ingredient = IngredientCache.objects.filter(
                    ingredient_key=response).first()
                if ingredient:
                    translation = IngredientTranslation.objects.filter(
                        ingredient=ingredient,
                        language=language
                    ).first()

                    return {
                        'key': response,
                        'confidence': 0.75,  # AI confidence
                        'display_name': translation.name if translation else name,
                        'matched_translation': name
                    }

        except Exception as e:
            print(f"[AI MATCH ERROR] {e}")
            return None

        return None

    def batch_map(self, items: List[str], language: str = 'en') -> List[MatchResult]:
        """
        Map multiple items at once (more efficient)

        Args:
            items: List of text items to map
            language: User's language

        Returns:
            List of MatchResults
        """
        results = []
        for item in items:
            result = self.map(item, language)
            results.append(result)

        return results
