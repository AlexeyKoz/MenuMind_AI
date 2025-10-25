import React, { useState, useEffect } from 'react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import i18n from './i18n';
import App from './App';

const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || '';

const AppWithProviders: React.FC = () => {
    const [locale, setLocale] = useState(() => {
        // Map i18n language to Google locale
        const localeMap: { [key: string]: string } = {
            'en': 'en',
            'ru': 'ru',
            'he': 'iw'
        };
        return localeMap[i18n.language] || 'en';
    });

    useEffect(() => {
        const handleLanguageChange = (lng: string) => {
            const localeMap: { [key: string]: string } = {
                'en': 'en',
                'ru': 'ru',
                'he': 'iw'
            };
            const newLocale = localeMap[lng] || 'en';
            console.log(`🌍 AppWithProviders: Updating Google locale to ${newLocale}`);
            setLocale(newLocale);
        };

        i18n.on('languageChanged', handleLanguageChange);
        return () => {
            i18n.off('languageChanged', handleLanguageChange);
        };
    }, []);

    if (!GOOGLE_CLIENT_ID) {
        console.warn('REACT_APP_GOOGLE_CLIENT_ID is not set');
    }

    return (
        <GoogleOAuthProvider
            clientId={GOOGLE_CLIENT_ID}
            key={locale}  // Force re-render when locale changes
        >
            <App />
        </GoogleOAuthProvider>
    );
};

export default AppWithProviders;
