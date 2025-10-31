import React, { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';
import { toast } from 'react-hot-toast';

const LanguageSwitcher: React.FC = () => {
    const { i18n } = useTranslation();
    const { user, token } = useAuth();

    const languages = [
        { code: 'en', label: 'English', flag: '🇬🇧' },
        { code: 'ru', label: 'Русский', flag: '🇷🇺' },
        { code: 'he', label: 'עברית', flag: '🇮🇱' }
    ];

    // Load user's saved language on mount
    useEffect(() => {
        if (user?.preferred_language && i18n.language !== user.preferred_language) {
            i18n.changeLanguage(user.preferred_language);
            console.log(`🌍 Language set to: ${user.preferred_language}`);
        }
    }, [user?.preferred_language, i18n]);

    const handleLanguageChange = async (langCode: string) => {
        try {
            // Change language in i18n
            await i18n.changeLanguage(langCode);
            console.log(`🌍 Language changed to: ${langCode}`);

            // Save to backend if user is logged in
            if (token) {
                const api = new ApiService(token);
                await api.updateUserPreferences({ preferred_language: langCode as 'en' | 'ru' | 'he' });
                toast.success(`Language changed to ${langCode.toUpperCase()}`);
            }
        } catch (error: any) {
            console.error('Failed to save language preference:', error);
            toast.error('Failed to save language preference');
        }
    };

    return (
        <select
            value={i18n.language}
            onChange={(e) => handleLanguageChange(e.target.value)}
            className="bg-gray-50 border border-gray-300 rounded-md px-3 py-2 text-sm text-gray-700 font-medium hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 cursor-pointer transition-all"
            aria-label="Select language"
            style={{ minWidth: '120px' }}
        >
            {languages.map((lang) => (
                <option key={lang.code} value={lang.code} className="bg-white text-gray-800">
                    {lang.flag} {lang.label}
                </option>
            ))}
        </select>
    );
};

export default LanguageSwitcher;