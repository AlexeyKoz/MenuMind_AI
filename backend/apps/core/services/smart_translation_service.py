"""
Smart Translation Service - 3-Phase Translation System

Optimized translation using:
- Layer 1: IML (ingredients) - <1ms
- Layer 2: CookLingo (cooking terms) - <1ms  
- Layer 3: AI (contextual content) - ~2s with Groq primary, Gemini fallback

3-Phase Workflow:
- Phase 1: Immediate (user opens recipe) - ~2-3s
- Phase 2: Background (Celery task) - async
- Phase 3: On-demand (user requests) - ~2-3s

Cost Optimization:
- Groq PRIMARY (higher free quota, faster)
- Gemini FALLBACK (more accurate, limited quota)
- Cache everything in database
- Never re-translate same content
"""
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """Result of a translation operation"""
    success: bool
    translated_content: Dict
    execution_time_ms: float
    ai_provider: str  # 'groq', 'gemini', 'none'
    translation_method: str  # 'iml_cooklingo', 'ai_full', 'hybrid'
    error_message: Optional[str] = None


class SmartTranslationService:
    """
    Smart Translation Service

    3-Layer approach:
    1. IML for ingredients (<1ms)
    2. CookLingo for cooking terms (<1ms)
    3. AI for contextual content (~2s, Groq primary)

    Performance: ~2-3s total for complete recipe translation
    """

    def __init__(self):
        self._iml_service = None
        self._cooklingo_service = None
        self._groq_client = None
        self._gemini_client = None
        self._stats = {
            'total_translations': 0,
            'groq_success': 0,
            'gemini_fallback': 0,
            'avg_time_ms': 0
        }

    def _ensure_services_loaded(self):
        """Lazy load services"""
        if not self._iml_service:
            from apps.core.services import get_iml_service
            self._iml_service = get_iml_service()

        if not self._cooklingo_service:
            from apps.core.services import get_cooklingo_service
            self._cooklingo_service = get_cooklingo_service()

    def translate_recipe(
        self,
        recipe_data: Dict,
        target_lang: str,
        phase: str = 'immediate'
    ) -> TranslationResult:
        """
        Translate a complete recipe to target language

        Args:
            recipe_data: Recipe in RCIP 2.0 format (canonical structure)
            target_lang: Target language code ('en', 'he', 'ru')
            phase: Translation phase ('immediate', 'background', 'on_demand')

        Returns:
            TranslationResult with translated content

        Performance: ~2-3s for complete recipe
        """
        start_time = time.time()
        self._ensure_services_loaded()

        logger.info(
            f"[TRANSLATION] Starting {phase} translation to {target_lang}")

        try:
            # Extract canonical data
            canonical = recipe_data.get('canonical', {})
            metadata = canonical.get('metadata', {})
            structure = canonical.get('structure', {})

            # Layer 1 + 2: Fast translation (ingredients + terms)
            ingredients_text = self._translate_ingredients(
                structure.get('ingredients', []),
                target_lang
            )

            # Layer 3: AI translation (contextual content)
            title = metadata.get('title', 'Untitled Recipe')
            description = metadata.get('description', '')
            steps = structure.get('steps', [])

            # Try Gemini first (PRIMARY)
            ai_result = self._translate_with_gemini(
                title=title,
                description=description,
                steps=steps,
                target_lang=target_lang
            )

            ai_provider = 'gemini'

            # Fallback to Groq if Gemini fails
            if not ai_result:
                logger.warning(
                    "[TRANSLATION] Gemini failed, trying Groq fallback...")
                ai_result = self._translate_with_groq(
                    title=title,
                    description=description,
                    steps=steps,
                    target_lang=target_lang
                )
                ai_provider = 'groq'

            if not ai_result:
                raise Exception("Both Gemini and Groq translation failed")

            # Combine results
            translated_content = {
                'title': ai_result.get('title', title),
                'description': ai_result.get('description', description),
                'ingredients_text': ingredients_text,
                'steps_text': ai_result.get('steps_text', []),
                'tags': ai_result.get('tags', [])
            }

            execution_time = (time.time() - start_time) * 1000

            # Update stats
            self._update_stats(ai_provider, execution_time)

            logger.info(
                f"[TRANSLATION] ✅ Complete: {execution_time:.2f}ms using {ai_provider}")

            return TranslationResult(
                success=True,
                translated_content=translated_content,
                execution_time_ms=execution_time,
                ai_provider=ai_provider,
                translation_method='hybrid'
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"[TRANSLATION] ❌ Failed: {e}")

            return TranslationResult(
                success=False,
                translated_content={},
                execution_time_ms=execution_time,
                ai_provider='none',
                translation_method='failed',
                error_message=str(e)
            )

    def _translate_ingredients(
        self,
        ingredients: List[Dict],
        target_lang: str
    ) -> Dict[str, str]:
        """
        Layer 1: Translate ingredients using IML service

        Performance: <1ms for typical recipe (10-30 ingredients)
        """
        ingredients_text = {}

        for ingredient in ingredients:
            iml_key = ingredient.get('iml_key')
            if iml_key:
                translation = self._iml_service.translate_ingredient(
                    iml_key, target_lang)
                if translation:
                    # Build full ingredient text
                    amount = ingredient.get('amount', '')
                    unit = ingredient.get('unit', '')
                    processing = ingredient.get('processing', '')

                    parts = []
                    if amount:
                        parts.append(str(amount))
                    if unit:
                        parts.append(unit)
                    parts.append(translation)
                    if processing:
                        parts.append(f"({processing})")

                    ingredients_text[iml_key] = ' '.join(parts)
                else:
                    ingredients_text[iml_key] = iml_key  # Fallback to key

        return ingredients_text

    def _translate_with_groq(
        self,
        title: str,
        description: str,
        steps: List[Dict],
        target_lang: str
    ) -> Optional[Dict]:
        """
        Layer 3: Translate contextual content with Groq (FALLBACK)

        Performance: ~1.5-2s
        """
        try:
            from groq import Groq
            from django.conf import settings

            if not self._groq_client:
                self._groq_client = Groq(api_key=settings.GROQ_API_KEY)

            # Build prompt
            steps_text = '\n'.join([
                f"{idx + 1}. {step.get('instruction', '')}"
                for idx, step in enumerate(steps)
            ])

            lang_names = {'en': 'English', 'he': 'Hebrew', 'ru': 'Russian'}
            target_lang_name = lang_names.get(target_lang, target_lang)

            prompt = f"""Translate this recipe to {target_lang_name}. Keep it natural and cooking-appropriate.

Title: {title}
Description: {description}

Steps:
{steps_text}

Respond in JSON format:
{{
    "title": "translated title",
    "description": "translated description",
    "steps_text": ["step 1 translated", "step 2 translated", ...],
    "tags": ["tag1", "tag2"]
}}

Only translate the text, maintain the structure. Be concise."""

            response = self._groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000,
            )

            result_text = response.choices[0].message.content

            # Parse JSON
            import json
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                data = json.loads(json_match.group())
                return data

            return None

        except Exception as e:
            logger.warning(f"[TRANSLATION] Groq error: {e}")
            return None

    def _translate_with_gemini(
        self,
        title: str,
        description: str,
        steps: List[Dict],
        target_lang: str
    ) -> Optional[Dict]:
        """
        Layer 3: Translate contextual content with Gemini (PRIMARY)

        Performance: ~2-2.5s
        """
        try:
            import google.generativeai as genai
            from django.conf import settings

            if not self._gemini_client:
                # Try GEMINI_API_KEY first, then GOOGLE_API_KEY for backwards compatibility
                api_key = getattr(settings, 'GEMINI_API_KEY', None) or getattr(
                    settings, 'GOOGLE_API_KEY', None)
                if not api_key:
                    logger.warning("[TRANSLATION] No Gemini API key found")
                    return None
                genai.configure(api_key=api_key)
                self._gemini_client = genai.GenerativeModel(
                    'gemini-2.0-flash-lite')

            # Build prompt
            steps_text = '\n'.join([
                f"{idx + 1}. {step.get('instruction', '')}"
                for idx, step in enumerate(steps)
            ])

            lang_names = {'en': 'English', 'he': 'Hebrew', 'ru': 'Russian'}
            target_lang_name = lang_names.get(target_lang, target_lang)

            prompt = f"""Translate this recipe to {target_lang_name}. Keep it natural and cooking-appropriate.

Title: {title}
Description: {description}

Steps:
{steps_text}

Respond in JSON format:
{{
    "title": "translated title",
    "description": "translated description",
    "steps_text": ["step 1 translated", "step 2 translated", ...],
    "tags": ["tag1", "tag2"]
}}

Only translate the text, maintain the structure."""

            response = self._gemini_client.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,
                    'max_output_tokens': 2000,
                }
            )

            result_text = response.text

            # Parse JSON
            import json
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                data = json.loads(json_match.group())
                return data

            return None

        except Exception as e:
            logger.warning(f"[TRANSLATION] Gemini error: {e}")
            return None

    def _update_stats(self, ai_provider: str, execution_time_ms: float):
        """Update translation statistics"""
        self._stats['total_translations'] += 1

        if ai_provider == 'groq':
            self._stats['groq_success'] += 1
        elif ai_provider == 'gemini':
            self._stats['gemini_fallback'] += 1

        # Update average time
        total_time = self._stats['avg_time_ms'] * \
            (self._stats['total_translations'] - 1)
        total_time += execution_time_ms
        self._stats['avg_time_ms'] = total_time / \
            self._stats['total_translations']

    def get_stats(self) -> Dict:
        """Get translation statistics"""
        stats = self._stats.copy()
        if stats['total_translations'] > 0:
            stats['groq_success_rate'] = (
                stats['groq_success'] / stats['total_translations']) * 100
            stats['gemini_fallback_rate'] = (
                stats['gemini_fallback'] / stats['total_translations']) * 100
        else:
            stats['groq_success_rate'] = 0
            stats['gemini_fallback_rate'] = 0
        return stats


# Global singleton instance
smart_translation_service = SmartTranslationService()


def get_smart_translation_service() -> SmartTranslationService:
    """
    Get the global Smart Translation Service instance

    Usage:
        from apps.core.services.smart_translation_service import get_smart_translation_service

        translator = get_smart_translation_service()
        result = translator.translate_recipe(recipe_data, 'he', phase='immediate')

        if result.success:
            print(f"Translated in {result.execution_time_ms:.2f}ms using {result.ai_provider}")
        else:
            print(f"Translation failed: {result.error_message}")
    """
    return smart_translation_service
