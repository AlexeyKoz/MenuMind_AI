import React from 'react';
import { useTranslation } from 'react-i18next';

const LanguageSwitcher: React.FC = () => {
    const { i18n } = useTranslation();

    const languages = [
        { code: 'en', label: 'English', flag: '🇬🇧' },
        { code: 'ru', label: 'Русский', flag: '🇷🇺' },
        { code: 'he', label: 'עברית', flag: '🇮🇱' }
    ];

    const changeLanguage = async (langCode: string) => {
        await i18n.changeLanguage(langCode);

        // Update HTML dir attribute for RTL support
        document.documentElement.dir = langCode === 'he' ? 'rtl' : 'ltr';

        // Store preference in localStorage
        localStorage.setItem('preferred_language', langCode);

        // TODO: Update backend UserPreferences
        // await api.patch('/users/profile/preferences/', {
        //     preferred_language: langCode
        // });
    };

    const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];

    return (
        <div className="relative group">
            <button
                className="flex items-center space-x-2 px-3 py-2 rounded-md hover:bg-white hover:bg-opacity-10 transition"
                title="Change Language"
            >
                <span className="text-xl">{currentLanguage.flag}</span>
                <span className="hidden md:inline">{currentLanguage.label}</span>
                <span className="text-xs">▼</span>
            </button>

            {/* Dropdown menu */}
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                {languages.map((lang) => (
                    <button
                        key={lang.code}
                        onClick={() => changeLanguage(lang.code)}
                        className={`w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center space-x-3 ${i18n.language === lang.code ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
                            }`}
                    >
                        <span className="text-xl">{lang.flag}</span>
                        <span className="font-medium">{lang.label}</span>
                        {i18n.language === lang.code && (
                            <span className="ml-auto text-blue-600">✓</span>
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default LanguageSwitcher;
