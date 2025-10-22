"""
CookLingo Service - In-Memory Caching for Cooking Terminology

Provides <1ms cooking term lookups by loading all data into memory on startup.

Features:
- Instant term translation (en/he/ru)
- Batch translation support
- Term detection in recipe text
- Category-based filtering (method, texture, equipment)
- Automatic cache warming on startup
"""
import logging
from typing import Dict, List, Optional
from apps.core.models import CookingTermCache, CookingTermTranslation
import re

logger = logging.getLogger(__name__)


class CookLingoService:
    """
    Cooking Terminology Service

    Memory-cached cooking term translation service.
    Loads all terms from PostgreSQL into memory on initialization.

    Performance: <1ms for single lookups, <5ms for batch operations
    """

    def __init__(self):
        self._cache = {}  # {term_english: term_data}
        self._category_index = {}  # {category: [term_english]}
        self._term_patterns = {}  # {lang_term_lower: term_english} for detection
        self._loaded = False

    def initialize(self):
        """
        Load all cooking terms from PostgreSQL into memory
        Call this on Django startup
        """
        if self._loaded:
            logger.info("[CookLingo] Service already initialized, skipping...")
            return

        logger.info(
            "[CookLingo] 🔄 Loading cooking terms from PostgreSQL into memory...")

        # Query all terms with translations
        terms = CookingTermCache.objects.prefetch_related('translations').all()

        if not terms.exists():
            logger.warning(
                "[CookLingo] ⚠️  No cooking terms found in database. Run import to populate.")
            self._loaded = True
            return

        # Build memory cache
        for term in terms:
            term_english = term.term_english

            # Get translations
            translations = {}
            for trans in term.translations.all():
                translations[trans.language_code] = trans.translation

            # Store in main cache
            self._cache[term_english] = {
                'term_english': term_english,
                'term_english_normalized': term.term_english_normalized,
                'translations': translations,
                'category': term.category,
                'term_type': term.term_type,
                'definition': term.definition,
                'confidence_score': term.confidence_score,
                'verified': term.verified,
            }

            # Build category index
            if term.category:
                if term.category not in self._category_index:
                    self._category_index[term.category] = []
                self._category_index[term.category].append(term_english)

            # Build term patterns for text detection
            for lang, translation in translations.items():
                if translation:
                    pattern_key = f"{lang}:{translation.lower().strip()}"
                    self._term_patterns[pattern_key] = term_english

        self._loaded = True

        logger.info(
            f"[CookLingo] ✅ Loaded {len(self._cache)} terms into memory")
        logger.info(f"[CookLingo]    Categories: {len(self._category_index)}")
        logger.info(f"[CookLingo]    Patterns: {len(self._term_patterns)}")

    def reload(self):
        """
        Reload data from PostgreSQL
        Call after admin imports new data
        """
        logger.info("[CookLingo] 🔄 Reloading cooking terms from database...")
        self._cache.clear()
        self._category_index.clear()
        self._term_patterns.clear()
        self._loaded = False
        self.initialize()

    def get_term(self, term_english: str) -> Optional[Dict]:
        """
        Get cooking term data by English term

        Args:
            term_english: English term identifier (e.g., 'dice', 'sauté')

        Returns:
            Dict with translations, category, definition
            None if not found

        Performance: <1ms
        """
        return self._cache.get(term_english)

    def translate_term(self, term_english: str, target_lang: str) -> Optional[str]:
        """
        Get translated cooking term

        Args:
            term_english: English term identifier
            target_lang: Target language code ('en', 'he', 'ru')

        Returns:
            Translated term or None if not found

        Performance: <1ms

        Example:
            >>> cooklingo_service.translate_term('dice', 'he')
            'לחתוך לקוביות'
        """
        term = self.get_term(term_english)
        if term:
            return term['translations'].get(target_lang)
        return None

    def batch_translate(
        self,
        term_keys: List[str],
        target_lang: str
    ) -> Dict[str, str]:
        """
        Translate multiple cooking terms at once

        Args:
            term_keys: List of English term identifiers
            target_lang: Target language code

        Returns:
            Dict of {term_english: translated_term}

        Performance: <5ms for typical recipe steps (10-20 terms)

        Example:
            >>> cooklingo_service.batch_translate(['dice', 'sauté', 'simmer'], 'ru')
            {'dice': 'нарезать кубиками', 'sauté': 'обжарить', ...}
        """
        result = {}
        for key in term_keys:
            translation = self.translate_term(key, target_lang)
            if translation:
                result[key] = translation
        return result

    def detect_terms_in_text(
        self,
        text: str,
        language: str = 'en'
    ) -> List[str]:
        """
        Detect cooking terms in recipe text

        Args:
            text: Recipe step text
            language: Language of the text

        Returns:
            List of detected term_english keys

        Performance: <10ms for typical recipe step

        Example:
            >>> cooklingo_service.detect_terms_in_text(
            ...     "Dice the onions and sauté them until golden brown", 
            ...     'en'
            ... )
            ['dice', 'sauté', 'golden-brown']
        """
        text_lower = text.lower()
        detected = []
        seen_terms = set()

        # Search for each term pattern
        for pattern_key, term_english in self._term_patterns.items():
            lang_prefix, term_text = pattern_key.split(':', 1)

            # Only check patterns for specified language
            if lang_prefix != language:
                continue

            # Use word boundary regex for accurate matching
            pattern = r'\b' + re.escape(term_text) + r'\b'
            if re.search(pattern, text_lower):
                if term_english not in seen_terms:
                    detected.append(term_english)
                    seen_terms.add(term_english)

        return detected

    def get_by_category(self, category: str) -> List[Dict]:
        """
        Get all cooking terms in a category

        Categories:
        - method: dice, chop, sauté, simmer, bake, etc.
        - texture: golden-brown, tender, crispy, etc.
        - temperature: preheat, boiling, simmer, etc.
        - equipment: pot, pan, oven, etc.

        Args:
            category: Category name

        Returns:
            List of term dicts in that category
        """
        term_keys = self._category_index.get(category, [])
        return [self._cache[key] for key in term_keys]

    def get_all_categories(self) -> List[str]:
        """Get list of all available categories"""
        return sorted(list(self._category_index.keys()))

    def search_term(
        self,
        query: str,
        language: str = 'en',
        limit: int = 10
    ) -> List[Dict]:
        """
        Search cooking terms

        Args:
            query: Search query
            language: Language to search in
            limit: Maximum results

        Returns:
            List of matching term dicts

        Performance: <5ms
        """
        query_lower = query.lower().strip()
        results = []
        seen_keys = set()

        for term_english, term_data in self._cache.items():
            term_text = term_data['translations'].get(language, '').lower()

            if query_lower in term_text or query_lower in term_english.lower():
                if term_english not in seen_keys:
                    results.append(term_data)
                    seen_keys.add(term_english)

                    if len(results) >= limit:
                        break

        return results

    def get_stats(self) -> Dict:
        """Get service statistics"""
        return {
            'total_terms': len(self._cache),
            'categories': len(self._category_index),
            'patterns': len(self._term_patterns),
            'loaded': self._loaded,
            'cache_size_kb': self._estimate_cache_size(),
        }

    def _estimate_cache_size(self) -> int:
        """Estimate memory cache size in KB (rough estimate)"""
        import sys
        return sys.getsizeof(self._cache) // 1024

    def is_loaded(self) -> bool:
        """Check if service is initialized"""
        return self._loaded


# Global singleton instance
cooklingo_service = CookLingoService()


def get_cooklingo_service() -> CookLingoService:
    """
    Get the global CookLingo service instance

    Usage:
        from apps.core.services.cooklingo_service import get_cooklingo_service

        cooklingo = get_cooklingo_service()
        translation = cooklingo.translate_term('dice', 'he')
    """
    return cooklingo_service
