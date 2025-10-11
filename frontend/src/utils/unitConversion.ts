// Unit conversion utilities based on user preferences

export interface UserPreferences {
    weight_unit: 'kg' | 'lbs';
    volume_unit: 'liters' | 'gallons';
    time_format: '24h' | '12h';
}

// Weight conversion functions
export const gramsToUserWeight = (grams: number, userUnit: 'kg' | 'lbs'): number => {
    if (userUnit === 'lbs') {
        return grams * 0.00220462; // grams to pounds
    }
    return grams / 1000; // grams to kilograms
};

export const userWeightToGrams = (weight: number, userUnit: 'kg' | 'lbs'): number => {
    if (userUnit === 'lbs') {
        return weight / 0.00220462; // pounds to grams
    }
    return weight * 1000; // kilograms to grams
};

// Volume conversion functions
export const millilitersToUserVolume = (ml: number, userUnit: 'liters' | 'gallons'): number => {
    if (userUnit === 'gallons') {
        return ml * 0.000264172; // ml to gallons
    }
    return ml / 1000; // ml to liters
};

export const userVolumeToMilliliters = (volume: number, userUnit: 'liters' | 'gallons'): number => {
    if (userUnit === 'gallons') {
        return volume / 0.000264172; // gallons to ml
    }
    return volume * 1000; // liters to ml
};

// Format weight for display
export const formatWeight = (grams: number, userUnit: 'kg' | 'lbs'): string => {
    const converted = gramsToUserWeight(grams, userUnit);

    if (grams === 0) {
        return `0 ${userUnit === 'kg' ? 'kg' : 'lbs'}`;
    }

    // Show grams/ounces for small quantities
    if (userUnit === 'kg' && grams < 1000) {
        return `${Math.round(grams)}g`;
    } else if (userUnit === 'lbs' && grams < 453.592) { // less than 1 pound
        const ounces = grams * 0.035274;
        return `${Math.round(ounces)}oz`;
    }

    // Show kg/lbs for larger quantities
    if (converted < 0.01) {
        return `0.01 ${userUnit === 'kg' ? 'kg' : 'lbs'}`;
    }

    return `${converted.toFixed(2)} ${userUnit === 'kg' ? 'kg' : 'lbs'}`;
};

// Format volume for display
export const formatVolume = (ml: number, userUnit: 'liters' | 'gallons'): string => {
    const converted = millilitersToUserVolume(ml, userUnit);

    if (ml === 0) {
        return `0 ${userUnit === 'liters' ? 'L' : 'gal'}`;
    }

    // Show ml/fl oz for small quantities
    if (userUnit === 'liters' && ml < 1000) {
        return `${Math.round(ml)}ml`;
    } else if (userUnit === 'gallons' && ml < 3785.41) { // less than 1 gallon
        const flOz = ml * 0.033814;
        return `${Math.round(flOz)}fl oz`;
    }

    // Show liters/gallons for larger quantities
    if (converted < 0.01) {
        return `0.01 ${userUnit === 'liters' ? 'L' : 'gal'}`;
    }

    return `${converted.toFixed(2)} ${userUnit === 'liters' ? 'L' : 'gal'}`;
};

// Get unit abbreviations
export const getWeightUnit = (userUnit: 'kg' | 'lbs'): string => {
    return userUnit === 'kg' ? 'kg' : 'lbs';
};

export const getVolumeUnit = (userUnit: 'liters' | 'gallons'): string => {
    return userUnit === 'liters' ? 'L' : 'gal';
};

// Parse user input back to base units
export const parseWeightInput = (input: string, userUnit: 'kg' | 'lbs'): number => {
    const value = parseFloat(input);
    if (isNaN(value)) return 0;

    // Check if input contains unit indicators
    if (input.includes('g') && !input.includes('kg')) {
        return value; // already in grams
    } else if (input.includes('oz')) {
        return value / 0.035274; // ounces to grams
    } else {
        return userWeightToGrams(value, userUnit); // convert from user unit to grams
    }
};

export const parseVolumeInput = (input: string, userUnit: 'liters' | 'gallons'): number => {
    const value = parseFloat(input);
    if (isNaN(value)) return 0;

    // Check if input contains unit indicators
    if (input.includes('ml')) {
        return value; // already in ml
    } else if (input.includes('fl oz')) {
        return value / 0.033814; // fl oz to ml
    } else {
        return userVolumeToMilliliters(value, userUnit); // convert from user unit to ml
    }
};
