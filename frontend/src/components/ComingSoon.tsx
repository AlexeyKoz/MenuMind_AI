import React from 'react';
import { useTranslation } from 'react-i18next';

interface ComingSoonProps {
    /** i18n key for the page/feature title (with a sensible English fallback) */
    titleKey?: string;
    /** Plain fallback title if no key is provided / key missing */
    title?: string;
}

/**
 * Temporary placeholder shown on pages that are not fully built yet.
 * The real page code is kept intact behind a feature flag in each page,
 * so re-enabling is just a one-line flag change.
 */
const ComingSoon: React.FC<ComingSoonProps> = ({ titleKey, title }) => {
    const { t } = useTranslation();

    const heading = titleKey
        ? t(titleKey, { defaultValue: title || t('common.comingSoonBadge', 'Coming soon') })
        : (title || t('common.comingSoonBadge', 'Coming soon'));

    return (
        <div className="max-w-3xl mx-auto p-6">
            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-10 text-center">
                <div className="text-6xl mb-4" aria-hidden>🚧</div>
                <h1 className="text-3xl font-bold text-gray-900 mb-3">{heading}</h1>
                <p className="text-lg text-gray-600 mb-2">
                    {t('common.comingSoonTitle', 'This feature will be available soon')}
                </p>
                <p className="text-gray-500">
                    {t('common.comingSoonSubtitle', "We're putting the finishing touches on it. Check back shortly!")}
                </p>
                <div className="mt-6 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-50 text-purple-700 text-sm font-medium">
                    ⏳ {t('common.comingSoonBadge', 'Coming soon')}
                </div>
            </div>
        </div>
    );
};

export default ComingSoon;
