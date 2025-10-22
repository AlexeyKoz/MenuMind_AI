"""
Temperature Conversion Utilities
Handles conversion between Fahrenheit and Celsius for recipes
"""
from typing import Dict, Optional, Union
import re


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """
    Convert Fahrenheit to Celsius

    Args:
        fahrenheit: Temperature in Fahrenheit

    Returns:
        Temperature in Celsius (rounded to 1 decimal place)
    """
    celsius = (fahrenheit - 32) * 5 / 9
    return round(celsius, 1)


def celsius_to_fahrenheit(celsius: float) -> float:
    """
    Convert Celsius to Fahrenheit

    Args:
        celsius: Temperature in Celsius

    Returns:
        Temperature in Fahrenheit (rounded to 1 decimal place)
    """
    fahrenheit = (celsius * 9 / 5) + 32
    return round(fahrenheit, 1)


def parse_temperature_text(text: str) -> Optional[Dict[str, Union[float, str]]]:
    """
    Parse temperature from text string

    Supports formats like:
    - "350°F"
    - "350 degrees F"
    - "175°C"
    - "175 degrees Celsius"
    - "350F (175C)"

    Args:
        text: Temperature text to parse

    Returns:
        Dict with 'value' and 'unit' keys, or None if no temperature found
    """
    if not text:
        return None

    # Try to find temperature patterns
    # Pattern 1: "350°F" or "350F" or "350 F"
    pattern1 = r'(\d+\.?\d*)\s*°?\s*([FCfc])\b'
    match = re.search(pattern1, text)

    if match:
        value = float(match.group(1))
        unit_char = match.group(2).upper()
        unit = 'fahrenheit' if unit_char == 'F' else 'celsius'
        return {'value': value, 'unit': unit}

    # Pattern 2: "350 degrees Fahrenheit/Celsius"
    pattern2 = r'(\d+\.?\d*)\s*degrees?\s*(fahrenheit|celsius|f|c)'
    match = re.search(pattern2, text.lower())

    if match:
        value = float(match.group(1))
        unit_text = match.group(2).lower()
        if unit_text in ['fahrenheit', 'f']:
            unit = 'fahrenheit'
        else:
            unit = 'celsius'
        return {'value': value, 'unit': unit}

    return None


def convert_temperature(temp: Dict[str, Union[float, str]], target_unit: str) -> Dict[str, Union[float, str]]:
    """
    Convert temperature to target unit

    Args:
        temp: Temperature dict with 'value' and 'unit' keys
        target_unit: Target unit ('fahrenheit' or 'celsius')

    Returns:
        New temperature dict with converted value
    """
    if not temp or 'value' not in temp or 'unit' not in temp:
        return temp

    current_unit = temp['unit'].lower()
    target_unit = target_unit.lower()

    # No conversion needed
    if current_unit == target_unit:
        return temp

    value = float(temp['value'])

    if current_unit == 'fahrenheit' and target_unit == 'celsius':
        converted_value = fahrenheit_to_celsius(value)
    elif current_unit == 'celsius' and target_unit == 'fahrenheit':
        converted_value = celsius_to_fahrenheit(value)
    else:
        # Unknown units, return original
        return temp

    return {
        'value': converted_value,
        'unit': target_unit
    }


def format_temperature(temp: Dict[str, Union[float, str]], language: str = 'en') -> str:
    """
    Format temperature for display

    Args:
        temp: Temperature dict with 'value' and 'unit' keys
        language: Language for formatting ('en', 'ru', 'he')

    Returns:
        Formatted temperature string
    """
    if not temp or 'value' not in temp or 'unit' not in temp:
        return ""

    value = temp['value']
    unit = temp['unit'].lower()

    # Format value (remove .0 if whole number)
    if isinstance(value, float) and value.is_integer():
        value_str = str(int(value))
    else:
        value_str = str(value)

    # Unit symbols
    unit_symbol = '°F' if unit == 'fahrenheit' else '°C'

    # Language-specific formatting
    if language == 'ru':
        return f"{value_str}{unit_symbol}"
    elif language == 'he':
        return f"{value_str}{unit_symbol}"
    else:  # English
        return f"{value_str}{unit_symbol}"


def normalize_temperature_unit(unit: str) -> str:
    """
    Normalize temperature unit string

    Args:
        unit: Unit string (F, f, Fahrenheit, fahrenheit, C, c, Celsius, celsius)

    Returns:
        Normalized unit string ('fahrenheit' or 'celsius')
    """
    unit_lower = unit.lower().strip()

    if unit_lower in ['f', 'fahrenheit', '°f']:
        return 'fahrenheit'
    elif unit_lower in ['c', 'celsius', '°c']:
        return 'celsius'

    return unit_lower
