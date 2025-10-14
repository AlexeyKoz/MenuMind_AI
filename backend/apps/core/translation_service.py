"""
Translation Service - Translates recipe content using Groq AI
Supports: EN, RU, HE
"""
from typing import Dict, List, Optional
from django.conf import settings


class TranslationService:
    """Service for translating recipe content to multiple languages"""

    SUPPORTED_LANGUAGES = ['en', 'ru', 'he']

    def __init__(self):
        self.groq_client = None
        try:
            from groq import Groq
            groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
            if groq_api_key:
                self.groq_client = Groq(api_key=groq_api_key)
                self.model = "llama-3.1-8b-instant"
        except ImportError:
            pass

    def translate_recipe(
        self,
        content: Dict,
        from_language: str,
        to_languages: Optional[List[str]] = None
    ) -> Dict:
        """
        Translate recipe content to multiple languages

        Args:
            content: Recipe content with keys:
                - title: str
                - description: str
                - steps: List[Dict] with 'instruction' key
            from_language: Source language (en, ru, he)
            to_languages: Target languages (default: all except source)

        Returns:
            {
                'title_translations': {en: "...", ru: "...", he: "..."},
                'description_translations': {en: "...", ru: "...", he: "..."},
                'steps_translations': {
                    en: [{step_number: 1, instruction: "..."}, ...],
                    ru: [{step_number: 1, instruction: "..."}, ...],
                    he: [{step_number: 1, instruction: "..."}, ...]
                }
            }
        """
        if not self.groq_client:
            # Fallback: return original in all languages
            return self._fallback_translation(content, from_language)

        if to_languages is None:
            to_languages = [
                lang for lang in self.SUPPORTED_LANGUAGES if lang != from_language]

        result = {
            'title_translations': {from_language: content.get('title', '')},
            'description_translations': {from_language: content.get('description', '')},
            'steps_translations': {from_language: content.get('steps', [])}
        }

        # Translate to each target language
        for target_lang in to_languages:
            try:
                translations = self._translate_to_language(
                    content, from_language, target_lang)

                result['title_translations'][target_lang] = translations['title']
                result['description_translations'][target_lang] = translations['description']
                result['steps_translations'][target_lang] = translations['steps']

            except Exception as e:
                print(
                    f"[TRANSLATION ERROR] {from_language} → {target_lang}: {e}")
                # Fallback: use original
                result['title_translations'][target_lang] = content.get(
                    'title', '')
                result['description_translations'][target_lang] = content.get(
                    'description', '')
                result['steps_translations'][target_lang] = content.get(
                    'steps', [])

        return result

    def _translate_to_language(
        self,
        content: Dict,
        from_lang: str,
        to_lang: str
    ) -> Dict:
        """Translate content to single target language"""

        # Prepare text for translation
        title = content.get('title', '')
        description = content.get('description', '')
        steps = content.get('steps', [])

        # Build translation prompt
        steps_text = '\n'.join([
            f"{i+1}. {step.get('instruction', '')}"
            for i, step in enumerate(steps)
        ])

        language_names = {
            'en': 'English',
            'ru': 'Russian',
            'he': 'Hebrew'
        }

        prompt = f"""Translate this recipe from {language_names[from_lang]} to {language_names[to_lang]}.

IMPORTANT RULES:
1. Keep cooking terms accurate (don't translate measurement units like "tsp", "cup", "g")
2. Keep ingredient names accurate (use proper culinary terms)
3. Maintain the same tone and style
4. For Hebrew: use proper right-to-left format

Recipe Title:
{title}

Description:
{description}

Steps:
{steps_text}

Return in this EXACT JSON format (no markdown, no extra text):
{{
  "title": "translated title",
  "description": "translated description",
  "steps": [
    {{"step_number": 1, "instruction": "translated step 1"}},
    {{"step_number": 2, "instruction": "translated step 2"}}
  ]
}}"""

        try:
            completion = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional recipe translator. Translate accurately while preserving culinary terminology. Return ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )

            response = completion.choices[0].message.content.strip()

            # Clean markdown if present
            if response.startswith('```'):
                response = response.split('```')[1]
                if response.startswith('json'):
                    response = response[4:]
                response = response.strip()

            # Parse JSON
            import json
            translated = json.loads(response)

            # Validate structure
            if 'title' not in translated or 'steps' not in translated:
                raise ValueError("Invalid translation structure")

            # Ensure steps have correct format
            formatted_steps = []
            for i, step in enumerate(translated.get('steps', [])):
                formatted_steps.append({
                    'step_number': i + 1,
                    'instruction': step.get('instruction', '')
                })

            return {
                'title': translated['title'],
                'description': translated.get('description', ''),
                'steps': formatted_steps
            }

        except Exception as e:
            print(f"[TRANSLATION PARSE ERROR] {e}")
            # Return original as fallback
            return {
                'title': content.get('title', ''),
                'description': content.get('description', ''),
                'steps': content.get('steps', [])
            }

    def _fallback_translation(self, content: Dict, language: str) -> Dict:
        """Fallback when no Groq client available"""
        return {
            'title_translations': {language: content.get('title', '')},
            'description_translations': {language: content.get('description', '')},
            'steps_translations': {language: content.get('steps', [])}
        }

    def translate_text(
        self,
        text: str,
        from_language: str,
        to_language: str
    ) -> str:
        """
        Simple text translation (for single strings)

        Args:
            text: Text to translate
            from_language: Source language
            to_language: Target language

        Returns:
            Translated text
        """
        if not self.groq_client or not text:
            return text

        language_names = {
            'en': 'English',
            'ru': 'Russian',
            'he': 'Hebrew'
        }

        prompt = f"""Translate this text from {language_names[from_language]} to {language_names[to_language]}:

"{text}"

Return ONLY the translated text, no explanations."""

        try:
            completion = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system",
                        "content": "You are a translator. Return only the translated text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            return completion.choices[0].message.content.strip()

        except Exception as e:
            print(f"[TEXT TRANSLATION ERROR] {e}")
            return text
