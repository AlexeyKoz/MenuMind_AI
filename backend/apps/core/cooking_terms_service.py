"""
Cooking Terms Translation Service
Uses CookLingo database to translate cooking terminology in recipes
"""
from typing import Dict, List, Optional, Set
import re
from django.core.cache import cache
from apps.core.models import CookingTermCache, CookingTermTranslation


class CookingTermsTranslationService:
    """Service to translate cooking terms in recipes using CookLingo database"""

    def __init__(self):
        self._term_index = None
        self._load_term_index()

    def _load_term_index(self):
        """Load cooking terms into memory for fast lookups"""
        cache_key = 'cooking_terms_index'
        self._term_index = cache.get(cache_key)

        if not self._term_index:
            print("[COOKLINGO] Loading cooking terms index...")
            self._term_index = {}

            # Load all terms with their translations
            terms = CookingTermCache.objects.prefetch_related(
                'translations').all()

            for term in terms:
                # Index by English term (normalized)
                normalized = term.term_english_normalized or term.term_english.lower()

                # Get all translations
                translations = {
                    'en': term.term_english,
                    'ru': None,
                    'he': None,
                    'category': term.category,
                    'confidence': term.confidence_score
                }

                for trans in term.translations.all():
                    translations[trans.language_code] = trans.translation

                self._term_index[normalized] = translations

            # Cache for 1 hour
            cache.set(cache_key, self._term_index, 3600)
            print(f"[COOKLINGO] Loaded {len(self._term_index)} cooking terms")

    def translate_text(self, text: str, target_language: str) -> str:
        """
        Translate cooking terms in a text to target language

        Args:
            text: Text containing cooking terms (e.g., recipe step)
            target_language: Target language code (ru, he)

        Returns:
            Text with cooking terms translated
        """
        if not text or target_language == 'en':
            return text

        if not self._term_index:
            self._load_term_index()

        # Find and replace cooking terms
        translated_text = text
        terms_found = 0

        # Sort terms by length (longest first) to avoid partial replacements
        sorted_terms = sorted(
            self._term_index.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )

        for normalized_term, translations in sorted_terms:
            english_term = translations['en']
            target_translation = translations.get(target_language)

            if not target_translation:
                continue

            # Try to find the term in the text (case-insensitive, whole word)
            pattern = r'\b' + re.escape(english_term) + r'\b'

            # Check if term exists before replacing
            if re.search(pattern, translated_text, flags=re.IGNORECASE):
                terms_found += 1

                # Replace with case preservation
                def replace_func(match):
                    original = match.group(0)
                    # Preserve capitalization
                    if original[0].isupper():
                        return target_translation.capitalize()
                    return target_translation

                translated_text = re.sub(
                    pattern,
                    replace_func,
                    translated_text,
                    flags=re.IGNORECASE
                )

        # Log if terms were found and translated
        if terms_found > 0:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(
                f"[COOKLINGO] Translated {terms_found} cooking terms in text")

        return translated_text

    def translate_steps(self, steps: List[Dict], target_language: str) -> List[Dict]:
        """
        Translate cooking terms in recipe steps

        Args:
            steps: List of recipe steps (each with 'text' field)
            target_language: Target language code (ru, he)

        Returns:
            Steps with translated cooking terms
        """
        if target_language == 'en' or not steps:
            return steps

        translated_steps = []
        for step in steps:
            translated_step = step.copy()

            if 'text' in step:
                translated_step['text'] = self.translate_text(
                    step['text'],
                    target_language
                )
            elif 'instruction' in step:
                translated_step['instruction'] = self.translate_text(
                    step['instruction'],
                    target_language
                )

            translated_steps.append(translated_step)

        return translated_steps

    def translate_ingredients(self, ingredients: List[Dict], target_language: str) -> List[Dict]:
        """
        Translate cooking terms in ingredient names

        Args:
            ingredients: List of ingredients (each with 'name' field)
            target_language: Target language code (ru, he)

        Returns:
            Ingredients with translated names
        """
        if target_language == 'en' or not ingredients:
            return ingredients

        translated_ingredients = []
        for ingredient in ingredients:
            translated_ingredient = ingredient.copy()

            if 'name' in ingredient:
                translated_ingredient['name'] = self.translate_text(
                    ingredient['name'],
                    target_language
                )

            translated_ingredients.append(translated_ingredient)

        return translated_ingredients

    def get_term_translation(self, term: str, target_language: str) -> Optional[str]:
        """
        Get translation for a specific cooking term

        Args:
            term: English cooking term
            target_language: Target language code (ru, he)

        Returns:
            Translated term or None if not found
        """
        if not self._term_index:
            self._load_term_index()

        normalized = term.lower().strip()

        if normalized in self._term_index:
            return self._term_index[normalized].get(target_language)

        return None

    def find_cooking_terms(self, text: str) -> Set[str]:
        """
        Find all cooking terms present in a text

        Args:
            text: Text to search

        Returns:
            Set of cooking terms found
        """
        if not self._term_index:
            self._load_term_index()

        found_terms = set()
        text_lower = text.lower()

        for normalized_term, translations in self._term_index.items():
            english_term = translations['en']

            # Check if term appears as whole word
            pattern = r'\b' + re.escape(english_term.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_terms.add(english_term)

        return found_terms

    def get_stats(self) -> Dict:
        """Get statistics about cooking terms database"""
        if not self._term_index:
            self._load_term_index()

        total_terms = len(self._term_index)

        ru_count = sum(1 for t in self._term_index.values() if t.get('ru'))
        he_count = sum(1 for t in self._term_index.values() if t.get('he'))

        categories = {}
        for term_data in self._term_index.values():
            cat = term_data.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1

        return {
            'total_terms': total_terms,
            'ru_translations': ru_count,
            'he_translations': he_count,
            'categories': categories
        }

    def refresh_index(self):
        """Force refresh of the term index"""
        cache.delete('cooking_terms_index')
        self._term_index = None
        self._load_term_index()
