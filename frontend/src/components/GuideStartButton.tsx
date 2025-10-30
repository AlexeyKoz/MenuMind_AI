import React from 'react';
import { useTranslation } from 'react-i18next';
import { HelpCircle } from 'lucide-react';
import { useUserGuide } from '../contexts/UserGuideContext';

interface GuideStartButtonProps {
    page: string;
    className?: string;
}

/**
 * A button to manually restart the guide for a specific page
 * Useful in settings or help sections
 */
export const GuideStartButton: React.FC<GuideStartButtonProps> = ({ page, className = '' }) => {
    const { t } = useTranslation();
    const { startGuide, resetGuide } = useUserGuide();

    const handleClick = () => {
        resetGuide(page);
        startGuide(page);
    };

    return (
        <button
            onClick={handleClick}
            className={`flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition ${className}`}
        >
            <HelpCircle className="w-5 h-5" />
            {t('guide.startTour')}
        </button>
    );
};

