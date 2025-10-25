# File: backend/apps/analytics/language_utils.py

from typing import Optional
import logging

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = ['en', 'he', 'ru']

LANGUAGE_NAMES = {
    'en': 'English',
    'he': 'Hebrew',
    'ru': 'Russian'
}


def get_user_language(request, user) -> str:
    """
    Detect user's preferred language

    Priority:
    1. Query parameter (?lang=he)
    2. User profile preference (if exists)
    3. Frontend header (X-User-Language)
    4. Accept-Language header
    5. Default: 'en'

    Args:
        request: Django request object
        user: User object

    Returns:
        str: Language code ('en', 'he', or 'ru')
    """
    # 1. Check query parameter
    query_lang = request.GET.get('lang')
    if query_lang and query_lang in SUPPORTED_LANGUAGES:
        logger.debug(f"Language from query param: {query_lang}")
        return query_lang

    # 2. Check user profile preference
    if hasattr(user, 'preferences'):
        try:
            pref_lang = user.preferences.language
            if pref_lang and pref_lang in SUPPORTED_LANGUAGES:
                logger.debug(f"Language from user preferences: {pref_lang}")
                return pref_lang
        except Exception as e:
            logger.warning(f"Error reading user language preference: {e}")

    # 3. Check frontend header
    frontend_lang = request.META.get('HTTP_X_USER_LANGUAGE')
    if frontend_lang and frontend_lang in SUPPORTED_LANGUAGES:
        logger.debug(f"Language from frontend header: {frontend_lang}")
        return frontend_lang

    # 4. Check Accept-Language header
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    if accept_language:
        # Parse "he-IL,he;q=0.9,en;q=0.8" -> "he"
        lang_code = accept_language.split(',')[0].split('-')[0][:2].lower()
        if lang_code in SUPPORTED_LANGUAGES:
            logger.debug(f"Language from Accept-Language: {lang_code}")
            return lang_code

    # 5. Default to English
    logger.debug("Language defaulting to: en")
    return 'en'


def get_language_name(language_code: str) -> str:
    """Get full language name from code"""
    return LANGUAGE_NAMES.get(language_code, 'English')
