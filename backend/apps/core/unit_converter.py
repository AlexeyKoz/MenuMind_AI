"""
Unit Converter Service - Converts units between metric/imperial systems
Handles: weight, volume, temperature conversions
"""
from typing import Dict, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass


@dataclass
class ConversionResult:
    """Result of unit conversion"""
    value: float
    unit: str
    unit_type: str
    original_value: float
    original_unit: str
    conversion_applied: bool


class UnitConverter:
    """Service for converting units based on user preferences"""

    # Conversion constants (precise values)
    CONVERSIONS = {
        # Weight conversions
        'kg_to_lb': 2.20462,
        'lb_to_kg': 0.453592,
        'g_to_oz': 0.035274,
        'oz_to_g': 28.3495,
        'kg_to_g': 1000,
        'g_to_kg': 0.001,
        'lb_to_oz': 16,
        'oz_to_lb': 0.0625,

        # Volume conversions
        'l_to_gallon': 0.264172,
        'gallon_to_l': 3.78541,
        'ml_to_fl_oz': 0.033814,
        'fl_oz_to_ml': 29.5735,
        'l_to_ml': 1000,
        'ml_to_l': 0.001,
        'gallon_to_fl_oz': 128,
        'fl_oz_to_gallon': 0.0078125,

        # Cooking conversions (to ml)
        'cup_to_ml': 240,
        'ml_to_cup': 0.00416667,
        'tbsp_to_ml': 15,
        'ml_to_tbsp': 0.0666667,
        'tsp_to_ml': 5,
        'ml_to_tsp': 0.2,

        # Temperature
        'c_to_f': lambda c: (c * 9/5) + 32,
        'f_to_c': lambda f: (f - 32) * 5/9,
    }

    # Unit categories
    UNIT_TYPES = {
        'weight': {
            'metric': ['g', 'kg', 'mg'],
            'imperial': ['oz', 'lb'],
            'base_metric': 'g',
            'base_imperial': 'oz'
        },
        'volume': {
            'metric': ['ml', 'l', 'dl'],
            'imperial': ['fl oz', 'gallon', 'cup', 'pint', 'quart'],
            'base_metric': 'ml',
            'base_imperial': 'fl oz'
        },
        'cooking': {
            'universal': ['tsp', 'tbsp', 'cup', 'pinch', 'dash'],
            'no_conversion': True
        },
        'count': {
            'universal': ['pcs', 'pieces', 'cloves', 'leaves', 'stalks'],
            'no_conversion': True
        },
        'temperature': {
            'metric': ['c', 'celsius'],
            'imperial': ['f', 'fahrenheit']
        }
    }

    # Precision for rounding
    PRECISION = 2

    def __init__(self):
        pass

    def convert(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        precision: Optional[int] = None
    ) -> ConversionResult:
        """
        Convert value from one unit to another

        Args:
            value: Quantity to convert
            from_unit: Source unit (e.g., 'kg', 'g', 'oz')
            to_unit: Target unit
            precision: Decimal places (default: 2)

        Returns:
            ConversionResult with converted value
        """
        precision = precision or self.PRECISION

        # Normalize units
        from_unit = from_unit.lower().strip()
        to_unit = to_unit.lower().strip()

        # Same unit - no conversion
        if from_unit == to_unit:
            return ConversionResult(
                value=round(value, precision),
                unit=to_unit,
                unit_type=self._get_unit_type(to_unit),
                original_value=value,
                original_unit=from_unit,
                conversion_applied=False
            )

        # Get conversion key
        conversion_key = f"{from_unit}_to_{to_unit}"

        if conversion_key in self.CONVERSIONS:
            # Direct conversion available
            converter = self.CONVERSIONS[conversion_key]
            if callable(converter):
                converted = converter(value)
            else:
                converted = value * converter

            return ConversionResult(
                value=round(converted, precision),
                unit=to_unit,
                unit_type=self._get_unit_type(to_unit),
                original_value=value,
                original_unit=from_unit,
                conversion_applied=True
            )

        # Try two-step conversion (e.g., kg → g → oz)
        converted = self._two_step_conversion(value, from_unit, to_unit)
        if converted is not None:
            return ConversionResult(
                value=round(converted, precision),
                unit=to_unit,
                unit_type=self._get_unit_type(to_unit),
                original_value=value,
                original_unit=from_unit,
                conversion_applied=True
            )

        # No conversion available - return original
        return ConversionResult(
            value=round(value, precision),
            unit=from_unit,
            unit_type=self._get_unit_type(from_unit),
            original_value=value,
            original_unit=from_unit,
            conversion_applied=False
        )

    def _two_step_conversion(
        self,
        value: float,
        from_unit: str,
        to_unit: str
    ) -> Optional[float]:
        """
        Attempt two-step conversion (e.g., kg → g → oz)
        """
        # Weight conversions
        if from_unit == 'kg' and to_unit == 'oz':
            # kg → g → oz
            grams = value * self.CONVERSIONS['kg_to_g']
            return grams * self.CONVERSIONS['g_to_oz']

        if from_unit == 'oz' and to_unit == 'kg':
            # oz → g → kg
            grams = value * self.CONVERSIONS['oz_to_g']
            return grams * self.CONVERSIONS['g_to_kg']

        if from_unit == 'kg' and to_unit == 'lb':
            # Direct conversion exists, but fallback
            return value * self.CONVERSIONS['kg_to_lb']

        if from_unit == 'lb' and to_unit == 'g':
            # lb → kg → g
            kg = value * self.CONVERSIONS['lb_to_kg']
            return kg * self.CONVERSIONS['kg_to_g']

        if from_unit == 'g' and to_unit == 'lb':
            # g → oz → lb
            oz = value * self.CONVERSIONS['g_to_oz']
            return oz * self.CONVERSIONS['oz_to_lb']

        if from_unit == 'lb' and to_unit == 'oz':
            # Direct conversion
            return value * self.CONVERSIONS['lb_to_oz']

        if from_unit == 'oz' and to_unit == 'lb':
            # Direct conversion
            return value * self.CONVERSIONS['oz_to_lb']

        if from_unit == 'g' and to_unit == 'kg':
            # Direct conversion
            return value * self.CONVERSIONS['g_to_kg']

        if from_unit == 'kg' and to_unit == 'g':
            # Direct conversion
            return value * self.CONVERSIONS['kg_to_g']

        # Volume conversions
        if from_unit == 'l' and to_unit == 'fl oz':
            # l → ml → fl oz
            ml = value * self.CONVERSIONS['l_to_ml']
            return ml * self.CONVERSIONS['ml_to_fl_oz']

        if from_unit == 'fl oz' and to_unit == 'l':
            # fl oz → ml → l
            ml = value * self.CONVERSIONS['fl_oz_to_ml']
            return ml * self.CONVERSIONS['ml_to_l']

        if from_unit == 'gallon' and to_unit == 'ml':
            # gallon → l → ml
            liters = value * self.CONVERSIONS['gallon_to_l']
            return liters * self.CONVERSIONS['l_to_ml']

        if from_unit == 'ml' and to_unit == 'gallon':
            # ml → l → gallon
            liters = value * self.CONVERSIONS['ml_to_l']
            return liters * self.CONVERSIONS['l_to_gallon']

        # Cup conversions
        if from_unit == 'cup' and to_unit in ['ml', 'l', 'fl oz']:
            ml = value * self.CONVERSIONS['cup_to_ml']
            if to_unit == 'ml':
                return ml
            elif to_unit == 'l':
                return ml * self.CONVERSIONS['ml_to_l']
            elif to_unit == 'fl oz':
                return ml * self.CONVERSIONS['ml_to_fl_oz']

        if to_unit == 'cup' and from_unit in ['ml', 'l', 'fl oz']:
            if from_unit == 'ml':
                return value * self.CONVERSIONS['ml_to_cup']
            elif from_unit == 'l':
                ml = value * self.CONVERSIONS['l_to_ml']
                return ml * self.CONVERSIONS['ml_to_cup']
            elif from_unit == 'fl oz':
                ml = value * self.CONVERSIONS['fl_oz_to_ml']
                return ml * self.CONVERSIONS['ml_to_cup']

        return None

    def convert_to_user_preference(
        self,
        value: float,
        current_unit: str,
        user_unit_system: str = 'metric',
        precision: Optional[int] = None
    ) -> ConversionResult:
        """
        Convert to user's preferred unit system

        Args:
            value: Quantity
            current_unit: Current unit
            user_unit_system: 'metric' or 'imperial'
            precision: Decimal places

        Returns:
            ConversionResult in user's preferred system
        """
        unit_type = self._get_unit_type(current_unit)

        # Don't convert cooking units or count units (universal)
        if unit_type in ['cooking', 'count']:
            return ConversionResult(
                value=round(value, precision or self.PRECISION),
                unit=current_unit,
                unit_type=unit_type,
                original_value=value,
                original_unit=current_unit,
                conversion_applied=False
            )

        # Determine target unit based on user preference
        target_unit = self._get_preferred_unit(current_unit, user_unit_system)

        if target_unit == current_unit:
            # Already in preferred system
            return ConversionResult(
                value=round(value, precision or self.PRECISION),
                unit=current_unit,
                unit_type=unit_type,
                original_value=value,
                original_unit=current_unit,
                conversion_applied=False
            )

        # Convert to preferred unit
        return self.convert(value, current_unit, target_unit, precision)

    def _get_unit_type(self, unit: str) -> str:
        """Determine unit type (weight, volume, cooking, count, temperature)"""
        unit = unit.lower().strip()

        for unit_type, config in self.UNIT_TYPES.items():
            if 'universal' in config and unit in config['universal']:
                return unit_type
            if 'metric' in config and unit in config['metric']:
                return unit_type
            if 'imperial' in config and unit in config['imperial']:
                return unit_type

        # Default to weight for unknown units
        return 'weight'

    def _get_preferred_unit(self, current_unit: str, user_unit_system: str) -> str:
        """
        Get preferred unit based on user's unit system

        Logic:
        - If current unit matches user system → keep current
        - If current unit doesn't match → convert to base unit of user system
        """
        unit_type = self._get_unit_type(current_unit)
        config = self.UNIT_TYPES.get(unit_type, {})

        # Universal units - don't convert
        if config.get('no_conversion'):
            return current_unit

        current_unit_lower = current_unit.lower()

        # Check if current unit is already in user's system
        user_units = config.get(user_unit_system, [])
        if current_unit_lower in user_units:
            return current_unit

        # Convert to base unit of user's system
        base_key = f'base_{user_unit_system}'
        return config.get(base_key, current_unit)

    def get_conversion_alternatives(
        self,
        value: float,
        unit: str
    ) -> Dict[str, float]:
        """
        Get alternative representations in different units

        Example:
            500g → {
                'kg': 0.5,
                'oz': 17.64,
                'lb': 1.10,
                'display_metric': '500g',
                'display_imperial': '1.1 lb'
            }

        Returns:
            Dict with alternative units
        """
        unit_type = self._get_unit_type(unit)
        config = self.UNIT_TYPES.get(unit_type, {})

        alternatives = {}

        # Don't provide alternatives for universal units
        if config.get('no_conversion'):
            return {
                'original': f"{value}{unit}",
                'alternatives': []
            }

        # Convert to all common units in same type
        if unit_type == 'weight':
            alternatives['g'] = self.convert(value, unit, 'g').value
            alternatives['kg'] = self.convert(value, unit, 'kg').value
            alternatives['oz'] = self.convert(value, unit, 'oz').value
            alternatives['lb'] = self.convert(value, unit, 'lb').value

            # Display strings
            alternatives['display_metric'] = self._format_display(
                alternatives['kg'], 'kg') if alternatives['kg'] >= 1 else self._format_display(alternatives['g'], 'g')
            alternatives['display_imperial'] = self._format_display(
                alternatives['lb'], 'lb') if alternatives['lb'] >= 1 else self._format_display(alternatives['oz'], 'oz')

        elif unit_type == 'volume':
            alternatives['ml'] = self.convert(value, unit, 'ml').value
            alternatives['l'] = self.convert(value, unit, 'l').value
            alternatives['fl oz'] = self.convert(value, unit, 'fl oz').value
            alternatives['cup'] = self.convert(value, unit, 'cup').value

            # Display strings
            alternatives['display_metric'] = self._format_display(
                alternatives['l'], 'L') if alternatives['l'] >= 1 else self._format_display(alternatives['ml'], 'ml')
            alternatives['display_imperial'] = self._format_display(
                alternatives['cup'], 'cup') if alternatives['cup'] >= 1 else self._format_display(alternatives['fl oz'], 'fl oz')

        return alternatives

    def _format_display(self, value: float, unit: str) -> str:
        """Format value and unit for display"""
        # Round to appropriate precision
        if value >= 100:
            formatted = f"{int(round(value))}"
        elif value >= 10:
            formatted = f"{round(value, 1)}"
        else:
            formatted = f"{round(value, 2)}"

        return f"{formatted}{unit}"

    def normalize_unit(self, unit: str) -> str:
        """
        Normalize unit aliases

        Examples:
            'teaspoon' → 'tsp'
            'kilogram' → 'kg'
            'pieces' → 'pcs'
        """
        unit_aliases = {
            'teaspoon': 'tsp', 'teaspoons': 'tsp',
            'tablespoon': 'tbsp', 'tablespoons': 'tbsp',
            'pieces': 'pcs', 'piece': 'pcs',
            'gram': 'g', 'grams': 'g', 'грамм': 'g', 'гр': 'g',
            'kilogram': 'kg', 'kilograms': 'kg', 'килограмм': 'kg', 'кг': 'kg',
            'liter': 'l', 'liters': 'l', 'litre': 'l', 'литр': 'l', 'л': 'l',
            'milliliter': 'ml', 'milliliters': 'ml', 'миллилитр': 'ml', 'мл': 'ml',
            'ounce': 'oz', 'ounces': 'oz',
            'pound': 'lb', 'pounds': 'lb', 'фунт': 'lb',
            'unit': 'pcs', 'units': 'pcs',
        }

        unit_lower = unit.lower().strip()
        return unit_aliases.get(unit_lower, unit_lower)
