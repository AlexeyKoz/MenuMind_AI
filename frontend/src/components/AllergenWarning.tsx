import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface AllergenWarningProps {
    allergens: string[];
    userAllergies?: string[];
    className?: string;
}

const ALLERGEN_LABELS: Record<string, string> = {
    'dairy': 'Dairy',
    'eggs': 'Eggs',
    'fish': 'Fish',
    'shellfish': 'Shellfish',
    'tree_nuts': 'Tree Nuts',
    'peanuts': 'Peanuts',
    'wheat': 'Wheat',
    'gluten': 'Gluten',
    'soy': 'Soy',
    'sesame': 'Sesame'
};

const AllergenWarning: React.FC<AllergenWarningProps> = ({
    allergens,
    userAllergies = [],
    className = ''
}) => {
    if (!allergens || allergens.length === 0) {
        return null;
    }

    // Check for dangerous allergens (matches user's allergies)
    const dangerousAllergens = allergens.filter(a =>
        userAllergies.some(ua => ua.toLowerCase() === a.toLowerCase() ||
            ua.toLowerCase().includes(a.toLowerCase()) ||
            a.toLowerCase().includes(ua.toLowerCase()))
    );

    const isDangerous = dangerousAllergens.length > 0;

    return (
        <div className={`rounded-lg p-3 ${isDangerous ? 'bg-red-50 border border-red-200' : 'bg-yellow-50 border border-yellow-200'} ${className}`}>
            <div className="flex items-start gap-2">
                <AlertTriangle
                    className={`flex-shrink-0 mt-0.5 ${isDangerous ? 'text-red-600' : 'text-yellow-600'}`}
                    size={20}
                />
                <div className="flex-1">
                    {isDangerous && (
                        <div className="mb-2">
                            <p className="font-semibold text-red-800 text-sm mb-1">
                                ⚠️ Contains allergens you're allergic to!
                            </p>
                            <div className="flex flex-wrap gap-1">
                                {dangerousAllergens.map(allergen => (
                                    <span
                                        key={allergen}
                                        className="inline-block px-2 py-0.5 bg-red-100 text-red-800 text-xs font-medium rounded border border-red-300"
                                    >
                                        {ALLERGEN_LABELS[allergen] || allergen}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    <p className={`text-xs ${isDangerous ? 'text-red-700' : 'text-yellow-800'} font-medium mb-1`}>
                        {isDangerous ? 'Other allergens in this recipe:' : 'Contains allergens:'}
                    </p>
                    <div className="flex flex-wrap gap-1">
                        {allergens.filter(a => !dangerousAllergens.includes(a)).map(allergen => (
                            <span
                                key={allergen}
                                className={`inline-block px-2 py-0.5 ${isDangerous ? 'bg-yellow-100 text-yellow-800 border-yellow-300' : 'bg-yellow-100 text-yellow-800 border-yellow-300'} text-xs rounded border`}
                            >
                                {ALLERGEN_LABELS[allergen] || allergen}
                            </span>
                        ))}
                        {allergens.length === dangerousAllergens.length && (
                            <span className="text-xs text-gray-500 italic">
                                (All allergens match your profile)
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AllergenWarning;

