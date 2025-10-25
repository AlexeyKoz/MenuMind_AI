import React from 'react';
import { useTranslation } from 'react-i18next';

const SimpleLanguageSwitcher: React.FC = () => {
    const { i18n } = useTranslation();

    const languages = [
        { code: 'en', label: 'English', flag: '🇬🇧' },
        { code: 'ru', label: 'Русский', flag: '🇷🇺' },
        { code: 'he', label: 'עברית', flag: '🇮🇱' }
    ];

    const handleLanguageChange = async (langCode: string) => {
        console.log(`🌍 Starting language change to: ${langCode}`);

        // Save to localStorage immediately
        localStorage.setItem('i18nextLng', langCode);

        // Change i18n language
        await i18n.changeLanguage(langCode);

        // Update HTML attributes
        document.documentElement.dir = langCode === 'he' ? 'rtl' : 'ltr';
        const googleLangMap: { [key: string]: string } = {
            'en': 'en',
            'ru': 'ru',
            'he': 'iw'
        };
        document.documentElement.lang = googleLangMap[langCode] || 'en';

        console.log(`📝 Language saved to localStorage: ${localStorage.getItem('i18nextLng')}`);

        // Force page reload to update Google button language
        setTimeout(() => {
            console.log(`🔄 Reloading page with language: ${langCode}`);
            window.location.reload();
        }, 100);
    };

    return (
        <select
            value={i18n.language}
            onChange={(e) => handleLanguageChange(e.target.value)}
            className="bg-green-500 bg-opacity-80 backdrop-blur-sm border border-white border-opacity-30 rounded-md px-3 py-2 text-sm text-white font-medium hover:bg-opacity-90 focus:outline-none focus:ring-2 focus:ring-white focus:ring-opacity-50 cursor-pointer transition-all"
            aria-label="Select language"
            style={{ minWidth: '120px' }}
        >
            {languages.map((lang) => (
                <option key={lang.code} value={lang.code} className="bg-gray-800 text-white">
                    {lang.flag} {lang.label}
                </option>
            ))}
        </select>
    );
};

export default SimpleLanguageSwitcher;

