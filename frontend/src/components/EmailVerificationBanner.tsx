import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';

const EmailVerificationBanner: React.FC = () => {
    const { t } = useTranslation();
    const [dismissed, setDismissed] = useState(false);
    const { user, token } = useAuth();

    const emailVerified = user?.email_verified ?? false;

    // Debug logging
    console.log('🟡 EmailVerificationBanner - user:', user);
    console.log('🟡 EmailVerificationBanner - email_verified:', emailVerified);
    console.log('🟡 EmailVerificationBanner - will show banner:', !dismissed && !emailVerified && !!token && !!user);

    const handleResend = async () => {
        console.log('🔵 Resend button clicked');
        console.log('Token:', token ? 'exists' : 'missing');

        if (!token) {
            console.log('❌ No token, returning');
            alert('You need to be logged in to resend verification email');
            return;
        }

        try {
            const apiUrl = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/?$/, '');
            const url = `${apiUrl}/api/users/auth/resend-verification/`;

            console.log('📤 Sending request to:', url);
            console.log('Authorization header:', `Bearer ${token.substring(0, 20)}...`);

            const res = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
            });

            console.log('📥 Response status:', res.status);

            if (res.ok) {
                const data = await res.json();
                console.log('✅ Success response:', data);
                alert(data.message || t('auth.verificationEmailResent'));
                // Force page reload to refresh user data
                window.location.reload();
            } else {
                const data = await res.json().catch(() => ({}));
                console.log('❌ Error response:', data);
                alert(data?.error || data?.detail || t('auth.resendFailed'));
            }
        } catch (error) {
            console.error('🚨 Resend email error:', error);
            alert(t('auth.resendError'));
        }
    };

    if (dismissed || emailVerified || !token || !user) {
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
