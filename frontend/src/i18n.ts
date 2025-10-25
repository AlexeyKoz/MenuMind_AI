import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './locales/en.json';
import ru from './locales/ru.json';
import he from './locales/he.json';

i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
        resources: {
            en: { translation: en },
            ru: { translation: ru },
            he: { translation: he }
        },
        fallbackLng: 'en',
        debug: false,
        interpolation: {
            escapeValue: false
        },
        detection: {
            order: ['localStorage', 'navigator', 'htmlTag'],
            caches: ['localStorage'],
            lookupLocalStorage: 'i18nextLng',
            lookupFromPathIndex: 0,
            lookupFromSubdomainIndex: 0,
            htmlTag: document.documentElement
        }
    });

// Log detected language
console.log(`🌍 i18n initialized with language: ${i18n.language}`);
console.log(`🌍 Browser language: ${navigator.language}`);
console.log(`🌍 localStorage language: ${localStorage.getItem('i18nextLng')}`);

export default i18n;