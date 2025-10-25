import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

const EmailVerificationBanner: React.FC = () => {
    const { t } = useTranslation();
    const [dismissed, setDismissed] = useState(false);
    const token = localStorage.getItem('token');

    // TODO: Replace with actual verified flag once available in AuthContext
    const emailVerified = true;

    const handleResend = async () => {
        if (!token) {
            return;
        }

        try {
            const apiUrl = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/?$/, '');
            const res = await fetch(`${apiUrl}/dj-rest-auth/registration/resend-email/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (res.ok) {
                alert(t('auth.verificationEmailResent'));
            } else {
                const data = await res.json().catch(() => ({}));
                alert(data?.detail || t('auth.resendFailed'));
            }
        } catch (error) {
            console.error('Resend email error:', error);
            alert(t('auth.resendError'));
        }
    };

    if (dismissed || emailVerified || !token) {
        return null;
    }

    return (
        <div className="bg-yellow-50 border-b border-yellow-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-3 flex-1">
                        <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                            />
                        </svg>
                        <div>
                            <p className="text-sm text-yellow-800 font-medium">{t('auth.verificationRequired')}</p>
                            <p className="text-xs text-yellow-700">{t('auth.checkInboxForVerification')}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleResend}
                            className="text-sm text-yellow-800 hover:text-yellow-900 font-medium underline"
                        >
                            {t('auth.resendEmail')}
                        </button>
                        <button
                            onClick={() => setDismissed(true)}
                            className="text-yellow-600 hover:text-yellow-800 p-1"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default EmailVerificationBanner;
