/**
 * Temperature Conversion Utilities
 * Handles temperature conversion and display for recipes
 */

export interface Temperature {
    value: number;
    unit: 'fahrenheit' | 'celsius';
}

/**
 * Convert Fahrenheit to Celsius
 */
export const fahrenheitToCelsius = (fahrenheit: number): number => {
    return Math.round(((fahrenheit - 32) * 5 / 9) * 10) / 10;
};

/**
 * Convert Celsius to Fahrenheit
 */
export const celsiusToFahrenheit = (celsius: number): number => {
    return Math.round(((celsius * 9 / 5) + 32) * 10) / 10;
};

/**
 * Convert temperature to target unit
 */
export const convertTemperature = (
    temp: Temperature,
    targetUnit: 'fahrenheit' | 'celsius'
): Temperature => {
    if (!temp || !temp.value || !temp.unit) {
        return temp;
    }

    const currentUnit = temp.unit.toLowerCase() as 'fahrenheit' | 'celsius';
    const target = targetUnit.toLowerCase() as 'fahrenheit' | 'celsius';

    // No conversion needed
    if (currentUnit === target) {
        return temp;
    }

    let convertedValue: number;
    if (currentUnit === 'fahrenheit' && target === 'celsius') {
        convertedValue = fahrenheitToCelsius(temp.value);
    } else if (currentUnit === 'celsius' && target === 'fahrenheit') {
        convertedValue = celsiusToFahrenheit(temp.value);
    } else {
        return temp;
    }

    return {
        value: convertedValue,
        unit: target
    };
};

/**
 * Format temperature for display
 */
export const formatTemperature = (
    temp: Temperature | string | null | undefined,
    preferredUnit: 'fahrenheit' | 'celsius' = 'celsius',
    language: string = 'en'
): string => {
    if (!temp) {
        return '';
    }

    // Handle string temperature (legacy format)
    if (typeof temp === 'string') {
        return temp;
    }

    // Handle structured temperature
    if (typeof temp === 'object' && temp.value && temp.unit) {
        // Convert to preferred unit
        const converted = convertTemperature(temp, preferredUnit);

        // Format value (remove .0 if whole number)
        const valueStr = Number.isInteger(converted.value)
            ? converted.value.toString()
            : converted.value.toFixed(1);

        // Unit symbol
        const unitSymbol = converted.unit === 'fahrenheit' ? '°F' : '°C';

        return `${valueStr}${unitSymbol}`;
    }

    return '';
};

/**
 * Parse temperature from text string (legacy support)
 */
export const parseTemperature = (text: string): Temperature | null => {
    if (!text) {
        return null;
    }

    // Try to find temperature patterns
    // Pattern 1: "350°F" or "350F" or "350 F"
    const pattern1 = /(\d+\.?\d*)\s*°?\s*([FCfc])\b/;
    const match1 = text.match(pattern1);

    if (match1) {
        const value = parseFloat(match1[1]);
        const unitChar = match1[2].toUpperCase();
        const unit = unitChar === 'F' ? 'fahrenheit' : 'celsius';
        return { value, unit };
    }

    // Pattern 2: "350 degrees Fahrenheit/Celsius"
    const pattern2 = /(\d+\.?\d*)\s*degrees?\s*(fahrenheit|celsius|f|c)/i;
    const match2 = text.match(pattern2);

    if (match2) {
        const value = parseFloat(match2[1]);
        const unitText = match2[2].toLowerCase();
        const unit = (unitText === 'fahrenheit' || unitText === 'f') ? 'fahrenheit' : 'celsius';
        return { value, unit };
    }

    return null;
};

/**
 * Get user's preferred temperature unit from settings/locale
 */
export const getPreferredTemperatureUnit = (userPreferences?: any): 'fahrenheit' | 'celsius' => {
    // Check user preferences first
    if (userPreferences?.temperatureUnit) {
        return userPreferences.temperatureUnit;
    }

    // Default: use metric (Celsius) for most countries
    // Use Fahrenheit only for US
    const locale = navigator.language || 'en-US';
    if (locale.startsWith('en-US')) {
        return 'fahrenheit';
    }

    return 'celsius';
};

