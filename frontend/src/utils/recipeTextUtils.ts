/**
 * Convert temperatures in recipe text based on user preference
 * Handles both "350°F" and "350 degrees Fahrenheit" formats
 */

import { convertTemperature, Temperature } from './temperatureUtils';

export const convertTemperaturesInText = (
    text: string,
    targetUnit: 'celsius' | 'fahrenheit'
): string => {
    if (!text) return text;

    // Pattern 1: "350°F" or "175°C"
    const pattern1 = /(\d+\.?\d*)\s*°\s*([FC])/gi;

    // Pattern 2: "350 degrees Fahrenheit" or "175 degrees Celsius"
    const pattern2 = /(\d+\.?\d*)\s*degrees?\s*(Fahrenheit|Celsius|F|C)/gi;

    let result = text;

    // Replace pattern 1
    result = result.replace(pattern1, (match, value, unit) => {
        const numValue = parseFloat(value);
        const sourceUnit: 'fahrenheit' | 'celsius' = unit.toUpperCase() === 'F' ? 'fahrenheit' : 'celsius';

        if (sourceUnit === targetUnit) {
            // Already in target unit, just standardize format
            return `${Math.round(numValue)}°${unit.toUpperCase()}`;
        }

        // Convert to target unit
        const temp: Temperature = { value: numValue, unit: sourceUnit };
        const converted = convertTemperature(temp, targetUnit);
        const symbol = targetUnit === 'fahrenheit' ? '°F' : '°C';

        return `${Math.round(converted.value)}${symbol}`;
    });

    // Replace pattern 2
    result = result.replace(pattern2, (match, value, unitText) => {
        const numValue = parseFloat(value);
        const unitLower = unitText.toLowerCase();
        const sourceUnit: 'fahrenheit' | 'celsius' = (unitLower === 'fahrenheit' || unitLower === 'f') ? 'fahrenheit' : 'celsius';

        if (sourceUnit === targetUnit) {
            // Already in target unit
            const unitName = targetUnit === 'fahrenheit' ? 'Fahrenheit' : 'Celsius';
            return `${Math.round(numValue)} degrees ${unitName}`;
        }

        // Convert to target unit
        const temp: Temperature = { value: numValue, unit: sourceUnit };
        const converted = convertTemperature(temp, targetUnit);
        const unitName = targetUnit === 'fahrenheit' ? 'Fahrenheit' : 'Celsius';

        return `${Math.round(converted.value)} degrees ${unitName}`;
    });

    return result;
};

/**
 * Get user's preferred temperature unit
 * Defaults to Celsius for metric countries, Fahrenheit for US
 */
export const getUserTemperatureUnit = (user: any): 'celsius' | 'fahrenheit' => {
    // Use user's explicit preference if set
    if (user?.temperature_unit) {
        return user.temperature_unit;
    }

    // Use language as a proxy for location
    const lang = user?.preferred_language || 'en';

    // US uses Fahrenheit, most other countries use Celsius
    if (lang === 'en') {
        return 'fahrenheit';  // Assume US English
    }

    return 'celsius';  // Russian, Hebrew, and most other languages use Celsius
};

