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
    // Terms-of-use confirmation for new Google users (mirrors manual registration)
    const [showLegalModal, setShowLegalModal] = useState(false);
    const [acceptedLegal, setAcceptedLegal] = useState(false);
    const [pendingAuth, setPendingAuth] = useState<{ access: string; refresh: string } | null>(null);

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

            // New Google users (or anyone who never accepted) must confirm the
            // Terms of Service before they are logged in - same as manual sign-up.
            if (data.requires_legal_acceptance) {
                setPendingAuth({ access: data.access, refresh: data.refresh });
                setAcceptedLegal(false);
                setShowLegalModal(true);
                setLoading(false);
                return;
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

    const completeLogin = (auth: { access: string; refresh: string }) => {
        localStorage.setItem('token', auth.access);
        localStorage.setItem('refresh', auth.refresh);
        if (onSuccess) {
            onSuccess();
        } else {
            window.location.reload();
        }
    };

    const handleAcceptLegal = async () => {
        if (!acceptedLegal || !pendingAuth) {
            return;
        }
        setLoading(true);
        try {
            await fetch(`${apiUrl}/api/legal/accept/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${pendingAuth.access}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ consent_method: 'registration' }),
            });
        } catch (err) {
            console.error('Failed to record legal acceptance:', err);
        }
        const auth = pendingAuth;
        setShowLegalModal(false);
        setPendingAuth(null);
        setLoading(false);
        completeLogin(auth);
    };

    const handleDeclineLegal = () => {
        // User refused the terms: do not log them in, discard pending tokens.
        setShowLegalModal(false);
        setPendingAuth(null);
        setAcceptedLegal(false);
        setLoading(false);
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

            {showLegalModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
                    <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
                        <h3 className="text-xl font-bold mb-2">
                            {t('auth.legalModalTitle') || 'One last step'}
                        </h3>
                        <p className="text-sm text-gray-600 mb-4">
                            {t('auth.legalModalSubtitle') || 'Please review and accept our policies to continue.'}
                        </p>

                        {/* Legal Acceptance - REQUIRED FOR GDPR/CCPA/Israel Amendment 13 */}
                        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <label className="flex items-start gap-3 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={acceptedLegal}
                                    onChange={(e) => setAcceptedLegal(e.target.checked)}
                                    className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                                    disabled={loading}
                                    required
                                />
                                <span className="text-sm text-gray-700 leading-relaxed">
                                    {t('auth.legalAcceptance') || 'I have read and agree to the'}{' '}
                                    <a
                                        href="/legal/terms"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:text-blue-700 font-medium underline"
                                    >
                                        {t('auth.termsOfService') || 'Terms of Service'}
                                    </a>
                                    ,{' '}
                                    <a
                                        href="/legal/privacy"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:text-blue-700 font-medium underline"
                                    >
                                        {t('auth.privacyPolicy') || 'Privacy Policy'}
                                    </a>
                                    , and{' '}
                                    <a
                                        href="/legal/cookies"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:text-blue-700 font-medium underline"
                                    >
                                        {t('auth.cookiePolicy') || 'Cookie Policy'}
                                    </a>
                                    .
                                </span>
                            </label>
                        </div>

                        <div className="flex gap-3">
                            <button
                                type="button"
                                onClick={handleDeclineLegal}
                                disabled={loading}
                                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition disabled:opacity-50"
                            >
                                {t('common.cancel') || 'Cancel'}
                            </button>
                            <button
                                type="button"
                                onClick={handleAcceptLegal}
                                disabled={loading || !acceptedLegal}
                                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {t('auth.continueToApp') || 'Continue'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default GoogleSignInButton;
