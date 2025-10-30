import React from 'react';
import { useTranslation } from 'react-i18next';
import { AlertTriangle, AlertCircle } from 'lucide-react';

interface AIWarningBannerProps {
    className?: string;
}

export const AIWarningBanner: React.FC<AIWarningBannerProps> = ({ className = '' }) => {
    const { t } = useTranslation();

    return (
        <div className={`bg-yellow-50 border-l-4 border-yellow-400 p-4 ${className}`}>
            <div className="flex items-center max-w-7xl mx-auto">
                <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
                <p className="ml-3 text-sm text-yellow-800 font-medium">
                    {t('warnings.aiDisclaimer')}
                </p>
            </div>
        </div>
    );
};

interface AllergenWarningBannerProps {
    className?: string;
}

export const AllergenWarningBanner: React.FC<AllergenWarningBannerProps> = ({ className = '' }) => {
    const { t } = useTranslation();

    return (
        <div className={`bg-red-50 border-l-4 border-red-400 p-4 ${className}`}>
            <div className="flex items-start max-w-7xl mx-auto">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="ml-3">
                    <p className="text-sm text-red-800 font-bold">
                        {t('warnings.allergenTitle')}
                    </p>
                    <p className="text-sm text-red-700 mt-1">
                        {t('warnings.allergenMessage')}
                    </p>
                </div>
            </div>
        </div>
    );
};

