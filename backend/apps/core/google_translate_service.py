"""
Google Translate API Service with Gemini and Groq fallback
Primary translator for all recipe content with robust error handling
"""
import logging
import time
from typing import Dict, List, Optional
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Debug: Module is being loaded
print("[DEBUG] google_translate_service.py module loaded")
logger.info("[DEBUG] google_translate_service.py module loaded")


class GoogleTranslateService:
    """
    Google Translate API as primary translator with fallback chain:
    1. Google Translate API (primary - fast, reliable)
    2. Gemini Flash 2.5 (fallback if Google fails)
    3. Groq (final fallback if both fail)
    """

    def __init__(self):
        print("[DEBUG] GoogleTranslateService.__init__ called")
        logger.info("[DEBUG] GoogleTranslateService.__init__ called")

        self.google_client = None
        self.gemini_client = None
        self.groq_client = None

        # Initialize Google Translate
        try:
            from google.cloud import translate_v2 as translate
            import os

            # Try service account JSON file first (most reliable)
            json_key_path = os.path.join(os.path.dirname(os.path.dirname(
                os.path.dirname(__file__))), 'gen-lang-client-0598591486-a22cb0b49217.json')

            logger.info(
                f"[GOOGLE_TRANSLATE] Looking for JSON key at: {json_key_path}")
            logger.info(
                f"[GOOGLE_TRANSLATE] File exists: {os.path.exists(json_key_path)}")

            if os.path.exists(json_key_path):
                logger.info(
                    "[GOOGLE_TRANSLATE] Using service account JSON file")
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = json_key_path
                self.google_client = translate.Client()
            else:
                # Try API key from settings
                api_key = getattr(settings, 'GOOGLE_CLOUD_API_KEY', None)
                if api_key:
                    logger.info(
                        "[GOOGLE_TRANSLATE] Using API key authentication")
                    os.environ['GOOGLE_API_KEY'] = api_key
                    self.google_client = translate.Client()
                else:
                    logger.info("[GOOGLE_TRANSLATE] Using default credentials")
                    self.google_client = translate.Client()

            logger.info(
                "[GOOGLE_TRANSLATE] ✅ Initialized Google Translate API")
        except ImportError:
            logger.warning(
                "[GOOGLE_TRANSLATE] ⚠️ google-cloud-translate not installed")
        except Exception as e:
            logger.error(
                f"[GOOGLE_TRANSLATE] ❌ Google Translate init failed: {e}")
            import traceback
            logger.error(traceback.format_exc())

        # Initialize Gemini (fallback)
        try:
            import google.generativeai as genai
            api_key = getattr(settings, 'GEMINI_API_KEY', None)
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_client = genai.GenerativeModel(
                    'gemini-2.0-flash-lite')
                logger.info("[GOOGLE_TRANSLATE] ✅ Gemini fallback ready")
        except Exception as e:
            logger.warning(
                f"[GOOGLE_TRANSLATE] ⚠️ Gemini fallback unavailable: {e}")

        # Initialize Groq (final fallback)
        try:
            from groq import Groq
            api_key = getattr(settings, 'GROQ_API_KEY', None)
            if api_key:
                self.groq_client = Groq(api_key=api_key)
                logger.info("[GOOGLE_TRANSLATE] ✅ Groq fallback ready")
        except Exception as e:
            logger.warning(
                f"[GOOGLE_TRANSLATE] ⚠️ Groq fallback unavailable: {e}")

    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: str = 'en'
    ) -> Optional[str]:
        """
        Translate text using fallback chain: Google → Gemini → Groq

        Args:
            text: Text to translate
            target_language: Target language code (en, ru, he)
            source_language: Source language code (default: en)

        Returns:
            Translated text or None if all methods fail
        """
        if not text or target_language == source_language:
            return text

        # Check cache first
        cache_key = self._get_cache_key(text, target_language, source_language)
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"[GOOGLE_TRANSLATE] 💨 Cache hit")
            return cached

        # Try Google Translate (PRIMARY)
        result = self._translate_with_google(
            text, target_language, source_language)
        if result:
            cache.set(cache_key, result, timeout=60*60*24*7)  # 7 days
            return result

        # Try Gemini (FALLBACK 1)
        logger.warning("[GOOGLE_TRANSLATE] ⚠️ Google failed, trying Gemini...")
        result = self._translate_with_gemini(text, target_language)
        if result:
            cache.set(cache_key, result, timeout=60*60*24*7)
            return result

        # Try Groq (FALLBACK 2)
        logger.warning("[GOOGLE_TRANSLATE] ⚠️ Gemini failed, trying Groq...")
        result = self._translate_with_groq(text, target_language)
        if result:
            cache.set(cache_key, result, timeout=60*60*24*7)
            return result

        logger.error("[GOOGLE_TRANSLATE] ❌ All translation methods failed")
        return None

    def translate_batch(
        self,
        texts: List[str],
        target_language: str,
        source_language: str = 'en'
    ) -> List[str]:
        """
        Translate multiple texts efficiently using batch API

        Args:
            texts: List of texts to translate
            target_language: Target language code
            source_language: Source language code

        Returns:
            List of translated texts (same order as input)
        """
        if not texts or target_language == source_language:
            return texts

        # Filter empty strings
        non_empty_texts = [(i, text) for i, text in enumerate(texts) if text]
        if not non_empty_texts:
            return texts

        indices, valid_texts = zip(*non_empty_texts)

        # Try Google Translate batch (PRIMARY)
        translations = self._translate_batch_with_google(
            valid_texts, target_language, source_language
        )

        if not translations:
            # Fallback to individual translations with Gemini/Groq
            logger.warning(
                "[GOOGLE_TRANSLATE] ⚠️ Batch failed, trying individual translations...")
            translations = [
                self.translate_text(text, target_language,
                                    source_language) or text
                for text in valid_texts
            ]

        # Reconstruct full list with empty strings preserved
        result = list(texts)
        for idx, translation in zip(indices, translations):
            result[idx] = translation

        return result

    def _translate_with_google(
        self,
        text: str,
        target_language: str,
        source_language: str
    ) -> Optional[str]:
        """Translate using Google Translate API"""
        if not self.google_client:
            return None

        try:
            result = self.google_client.translate(
                text,
                target_language=target_language,
                source_language=source_language,
                format_='text'
            )

            translated = result['translatedText']
            logger.info(
                f"[GOOGLE_TRANSLATE] ✅ Success: {text[:50]}... → {translated[:50]}...")
            return translated

        except Exception as e:
            logger.error(f"[GOOGLE_TRANSLATE] ❌ Google error: {e}")
            return None

    def _translate_batch_with_google(
        self,
        texts: List[str],
        target_language: str,
        source_language: str
    ) -> Optional[List[str]]:
        """Translate batch using Google Translate API"""
        if not self.google_client:
            return None

        try:
            results = self.google_client.translate(
                texts,
                target_language=target_language,
                source_language=source_language,
                format_='text'
            )

            translations = [r['translatedText'] for r in results]
            logger.info(
                f"[GOOGLE_TRANSLATE] ✅ Batch success: {len(translations)} texts")
            return translations

        except Exception as e:
            logger.error(f"[GOOGLE_TRANSLATE] ❌ Batch error: {e}")
            return None

    def _translate_with_gemini(self, text: str, target_language: str) -> Optional[str]:
        """Translate using Gemini (fallback)"""
        if not self.gemini_client:
            return None

        language_names = {
            'ru': 'Russian',
            'he': 'Hebrew',
            'en': 'English'
        }

        target_lang_name = language_names.get(target_language, target_language)

        prompt = f"""Translate this text to {target_lang_name}.
Return ONLY the translation, nothing else.

Text: {text}

Translation:"""

        try:
            response = self.gemini_client.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 2000,
                }
            )

            translated = response.text.strip()
            logger.info(f"[GEMINI_FALLBACK] ✅ Success")
            return translated

        except Exception as e:
            logger.error(f"[GEMINI_FALLBACK] ❌ Error: {e}")
            return None

    def _translate_with_groq(self, text: str, target_language: str) -> Optional[str]:
        """Translate using Groq (final fallback)"""
        if not self.groq_client:
            return None

        language_names = {
            'ru': 'Russian',
            'he': 'Hebrew',
            'en': 'English'
        }

        target_lang_name = language_names.get(target_language, target_language)

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator. Translate ONLY to {target_lang_name}. Return only the translation, no explanations."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.1,
                max_tokens=2000
            )

            translated = response.choices[0].message.content.strip()
            logger.info(f"[GROQ_FALLBACK] ✅ Success")
            return translated

        except Exception as e:
            logger.error(f"[GROQ_FALLBACK] ❌ Error: {e}")
            return None

    def _get_cache_key(self, text: str, target_lang: str, source_lang: str) -> str:
        """Generate cache key for translation"""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()[:16]
        return f"gtrans_{source_lang}_{target_lang}_{text_hash}"


# Singleton instance
_google_translate_service = None


def get_google_translate_service() -> GoogleTranslateService:
    """Get or create singleton GoogleTranslateService instance"""
    global _google_translate_service
    if _google_translate_service is None:
        _google_translate_service = GoogleTranslateService()
    return _google_translate_service
