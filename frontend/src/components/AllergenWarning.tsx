import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface AllergenWarningProps {
    allergens: string[];
    userAllergies?: string[];
    className?: string;
}

const AllergenWarning: React.FC<AllergenWarningProps> = ({
    allergens,
    userAllergies = [],
    className = ''
}) => {
    const { t } = useTranslation();

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

    // Get translated allergen name
    const getAllergenLabel = (allergen: string): string => {
        return t(`allergens.${allergen}`, allergen);
    };

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
                                ⚠️ {t('allergens.warningYourAllergies')}
                            </p>
                            <div className="flex flex-wrap gap-1">
                                {dangerousAllergens.map(allergen => (
                                    <span
                                        key={allergen}
                                        className="inline-block px-2 py-0.5 bg-red-100 text-red-800 text-xs font-medium rounded border border-red-300"
                                    >
                                        {getAllergenLabel(allergen)}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    <p className={`text-xs ${isDangerous ? 'text-red-700' : 'text-yellow-800'} font-medium mb-1`}>
                        {isDangerous ? t('allergens.otherAllergens') : t('allergens.contains')}
                    </p>
                    <div className="flex flex-wrap gap-1">
                        {allergens.filter(a => !dangerousAllergens.includes(a)).map(allergen => (
                            <span
                                key={allergen}
                                className={`inline-block px-2 py-0.5 ${isDangerous ? 'bg-yellow-100 text-yellow-800 border-yellow-300' : 'bg-yellow-100 text-yellow-800 border-yellow-300'} text-xs rounded border`}
                            >
                                {getAllergenLabel(allergen)}
                            </span>
                        ))}
                        {allergens.length === dangerousAllergens.length && (
                            <span className="text-xs text-gray-500 italic">
                                ({t('allergens.allMatch')})
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AllergenWarning;

