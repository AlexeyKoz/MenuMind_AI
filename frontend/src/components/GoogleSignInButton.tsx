import React, { useState } from 'react';
import { useGoogleOneTapLogin, GoogleLogin } from '@react-oauth/google';
import { useTranslation } from 'react-i18next';

interface GoogleSignInButtonProps {
    onSuccess?: () => void;
    onError?: (error: string) => void;
}

const GoogleSignInButton: React.FC<GoogleSignInButtonProps> = ({ onSuccess, onError }) => {
    const { t, i18n } = useTranslation();
    const [loading, setLoading] = useState(false);
    const [mounted, setMounted] = useState(false);
    const [currentLocale, setCurrentLocale] = useState(i18n.language);

    // Wait for i18n to initialize before rendering button
    React.useEffect(() => {
        const timer = setTimeout(() => {
            setMounted(true);
            setCurrentLocale(i18n.language);
        }, 100); // Small delay to ensure i18n is ready
        return () => clearTimeout(timer);
    }, [i18n.language]);

    // Force re-render when language changes
    React.useEffect(() => {
        if (mounted && i18n.language !== currentLocale) {
            setMounted(false);
            setTimeout(() => {
                setCurrentLocale(i18n.language);
                setMounted(true);
            }, 50); // Unmount and remount with new language
        }
    }, [i18n.language, mounted, currentLocale]);

    const apiUrl = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/?$/, '');

    const handleError = (message: string) => {
        setLoading(false);
        if (onError) {
            onError(message);
        } else {
            alert(message);
        }
    };

    // Map i18n language codes to Google's locale codes
    const getGoogleLocale = () => {
        const localeMap: { [key: string]: string } = {
            'en': 'en',
            'ru': 'ru',
            'he': 'iw'  // Google uses 'iw' for Hebrew
        };
        const locale = localeMap[i18n.language] || 'en';
        console.log(`🌍 Current i18n language: ${i18n.language}, Google locale: ${locale}`);
        return locale;
    };

    const handleGoogleSuccess = async (credentialResponse: any) => {
        setLoading(true);
        try {
            console.log('Google credential response:', credentialResponse);

            // The GoogleLogin component returns the credential directly
            const credential = credentialResponse?.credential;

            if (!credential) {
                throw new Error('No credential received from Google');
            }

            // Send the credential (ID token) to our backend
            const res = await fetch(`${apiUrl}/api/users/auth/google/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ credential }),
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data?.error || t('auth.googleLoginFailed'));
            }

            localStorage.setItem('token', data.access);
            localStorage.setItem('refresh', data.refresh);

            if (onSuccess) {
                onSuccess();
            } else {
                window.location.reload();
            }
        } catch (error: any) {
            console.error('Google login error', error);
            const errorMessage = error?.message || t('auth.googleLoginFailed');
            handleError(errorMessage);
        }
    };

    return (
        <div className="w-full flex items-center justify-center">
            {mounted ? (
                <div className="inline-block">
                    <GoogleLogin
                        key={currentLocale}  // Force re-render when locale changes
                        onSuccess={handleGoogleSuccess}
                        onError={() => {
                            console.error('Google OAuth error');
                            handleError(t('auth.googleLoginFailed'));
                        }}
                        theme="outline"
                        size="large"
                        text="continue_with"
                        locale={getGoogleLocale()}
                    />
                </div>
            ) : (
                <div className="w-full h-12 bg-gray-100 animate-pulse rounded-lg flex items-center justify-center">
                    <span className="text-gray-400 text-sm">Loading...</span>
                </div>
            )}
        </div>
    );
};

export default GoogleSignInButton;
