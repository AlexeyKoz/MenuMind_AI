"""
Unit Translation and Conversion Utilities
Handles translation of measurement units across languages
"""
from typing import Dict, Optional


# Unit translation mappings
UNIT_TRANSLATIONS = {
    'en': {
        # English units
        'cup': 'cup',
        'cups': 'cups',
        'tablespoon': 'tablespoon',
        'tablespoons': 'tablespoons',
        'teaspoon': 'teaspoon',
        'teaspoons': 'teaspoons',
        'gram': 'gram',
        'grams': 'grams',
        'g': 'g',
        'kilogram': 'kilogram',
        'kilograms': 'kilograms',
        'kg': 'kg',
        'liter': 'liter',
        'liters': 'liters',
        'l': 'l',
        'milliliter': 'milliliter',
        'milliliters': 'milliliters',
        'ml': 'ml',
        'ounce': 'ounce',
        'ounces': 'ounces',
        'oz': 'oz',
        'pound': 'pound',
        'pounds': 'pounds',
        'lb': 'lb',
        'unit': 'unit',
        'piece': 'piece',
        'pieces': 'pieces',
        'pinch': 'pinch',
        'dash': 'dash',
        'tbsp': 'tbsp',
        'tsp': 'tsp',
        'as': 'unit',  # Fallback
    },
    'ru': {
        # Russian units
        'cup': 'чашка',
        'cups': 'чашки',
        'tablespoon': 'столовая ложка',
        'tablespoons': 'столовые ложки',
        'teaspoon': 'чайная ложка',
        'teaspoons': 'чайные ложки',
        'gram': 'грамм',
        'grams': 'граммов',
        'g': 'г',
        'kilogram': 'килограмм',
        'kilograms': 'килограммов',
        'kg': 'кг',
        'liter': 'литр',
        'liters': 'литров',
        'l': 'л',
        'milliliter': 'миллилитр',
        'milliliters': 'миллилитров',
        'ml': 'мл',
        'ounce': 'унция',
        'ounces': 'унций',
        'oz': 'унц',
        'pound': 'фунт',
        'pounds': 'фунтов',
        'lb': 'фнт',
        'unit': 'шт',
        'piece': 'штука',
        'pieces': 'штуки',
        'pinch': 'щепотка',
        'dash': 'капля',
        'tbsp': 'ст.л.',
        'tsp': 'ч.л.',
        'as': 'шт',  # Map 'as' to 'шт' (штука)
    },
    'he': {
        # Hebrew units
        'cup': 'כוס',
        'cups': 'כוסות',
        'tablespoon': 'כף',
        'tablespoons': 'כפות',
        'teaspoon': 'כפית',
        'teaspoons': 'כפיות',
        'gram': 'גרם',
        'grams': 'גרם',
        'g': 'ג׳',
        'kilogram': 'קילוגרם',
        'kilograms': 'קילוגרם',
        'kg': 'ק״ג',
        'liter': 'ליטר',
        'liters': 'ליטר',
        'l': 'ל׳',
        'milliliter': 'מיליליטר',
        'milliliters': 'מיליליטר',
        'ml': 'מ״ל',
        'ounce': 'אונקיה',
        'ounces': 'אונקיות',
        'oz': 'oz',
        'pound': 'פאונד',
        'pounds': 'פאונד',
        'lb': 'lb',
        'unit': 'יח׳',
        'piece': 'יחידה',
        'pieces': 'יחידות',
        'pinch': 'קורט',
        'dash': 'טיפה',
        'tbsp': 'כף',
        'tsp': 'כפית',
        'as': 'יח׳',  # Map 'as' to 'יח׳' (יחידה)
    }
}


def translate_unit(unit: str, target_language: str) -> str:
    """
    Translate a measurement unit to target language

    Args:
        unit: Unit string to translate (e.g., 'cup', 'tablespoon', 'as')
        target_language: Target language code ('en', 'ru', 'he')

    Returns:
        Translated unit string
    """
    if not unit:
        return ''

    # Normalize unit
    unit_lower = unit.lower().strip()

    # If target language is English, try to normalize common units
    if target_language == 'en':
        return UNIT_TRANSLATIONS['en'].get(unit_lower, unit)

    # Get translation from dictionary
    translations = UNIT_TRANSLATIONS.get(target_language, {})
    translated = translations.get(unit_lower)

    if translated:
        return translated

    # Fallback: try to find in English mapping first
    english_normalized = UNIT_TRANSLATIONS['en'].get(unit_lower)
    if english_normalized and english_normalized != unit_lower:
        # Try again with normalized English unit
        translated = translations.get(english_normalized)
        if translated:
            return translated

    # No translation found, return original
    return unit


def get_unit_abbreviations(language: str) -> Dict[str, str]:
    """
    Get common unit abbreviations for a language

    Args:
        language: Language code ('en', 'ru', 'he')

    Returns:
        Dict mapping full names to abbreviations
    """
    abbreviations = {
        'en': {
            'tablespoon': 'tbsp',
            'tablespoons': 'tbsp',
            'teaspoon': 'tsp',
            'teaspoons': 'tsp',
            'gram': 'g',
            'grams': 'g',
            'kilogram': 'kg',
            'kilograms': 'kg',
            'milliliter': 'ml',
            'milliliters': 'ml',
            'liter': 'l',
            'liters': 'l',
        },
        'ru': {
            'столовая ложка': 'ст.л.',
            'столовые ложки': 'ст.л.',
            'чайная ложка': 'ч.л.',
            'чайные ложки': 'ч.л.',
            'грамм': 'г',
            'граммов': 'г',
            'килограмм': 'кг',
            'килограммов': 'кг',
            'миллилитр': 'мл',
            'миллилитров': 'мл',
            'литр': 'л',
            'литров': 'л',
        },
        'he': {
            'כף': 'כף',
            'כפות': 'כף',
            'כפית': 'כפית',
            'כפיות': 'כפית',
            'גרם': 'ג׳',
            'קילוגרם': 'ק״ג',
            'מיליליטר': 'מ״ל',
            'ליטר': 'ל׳',
        }
    }

    return abbreviations.get(language, {})
