import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

const VerifyEmail: React.FC = () => {
    const { t } = useTranslation();
    const [status, setStatus] = useState<'pending' | 'success' | 'error'>('pending');
    const [errorMessage, setErrorMessage] = useState('');

    useEffect(() => {
        const verifyEmail = async () => {
            const urlParams = new URLSearchParams(window.location.search);
            const keyFromQuery = urlParams.get('key');
            const keyFromPath = window.location.pathname.split('/').pop();
            const verificationKey = keyFromQuery || keyFromPath;

            if (!verificationKey) {
                setStatus('error');
                setErrorMessage(t('auth.verificationKeyMissing'));
                return;
            }

            try {
                const apiUrl = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/?$/, '');
                const res = await fetch(`${apiUrl}/dj-rest-auth/registration/verify-email/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key: verificationKey }),
                });

                if (res.ok) {
                    setStatus('success');
                } else {
                    const data = await res.json().catch(() => ({}));
                    setStatus('error');
                    setErrorMessage(data?.detail || t('auth.verificationFailedMessage'));
                }
            } catch (error) {
                console.error('Verification error:', error);
                setStatus('error');
                setErrorMessage(t('auth.verificationError'));
            }
        };

        verifyEmail();
    }, [t]);

    const handleContinue = () => {
        window.location.href = '/';
    };

    if (status === 'pending') {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
                <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('auth.verifyingEmail')}</h2>
                    <p className="text-gray-600">{t('auth.pleaseWait')}</p>
                </div>
            </div>
        );
    }

    if (status === 'success') {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
                <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('auth.emailVerified')}</h2>
                    <p className="text-gray-600 mb-6">{t('auth.emailVerifiedMessage')}</p>
                    <button
                        onClick={handleContinue}
                        className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                    >
                        {t('auth.continueToApp')}
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
            <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-10 h-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('auth.verificationFailed')}</h2>
                <p className="text-gray-600 mb-6">{errorMessage || t('auth.verificationFailedMessage')}</p>
                <button
                    onClick={handleContinue}
                    className="w-full bg-gray-200 text-gray-700 py-3 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                >
                    {t('auth.backToLogin')}
                </button>
            </div>
        </div>
    );
};

export default VerifyEmail;
