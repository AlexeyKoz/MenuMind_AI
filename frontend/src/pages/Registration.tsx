import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import SimpleLanguageSwitcher from '../components/SimpleLanguageSwitcher';

interface RegistrationProps {
    onRegistrationSuccess: () => void;
    onSwitchToLogin: () => void;
}

const Registration: React.FC<RegistrationProps> = ({ onRegistrationSuccess, onSwitchToLogin }) => {
    const { t, i18n } = useTranslation();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [error, setError] = useState('');
    const [passwordErrors, setPasswordErrors] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [acceptedLegal, setAcceptedLegal] = useState(false);
    const { register } = useAuth();

    // Update HTML dir attribute for RTL support (Hebrew)
    useEffect(() => {
        document.documentElement.dir = i18n.language === 'he' ? 'rtl' : 'ltr';
    }, [i18n.language]);

    // Validate password in real-time
    useEffect(() => {
        const errors: string[] = [];
        if (password) {
            if (password.length < 8) {
                errors.push(t('auth.passwordMin8'));
            }
            if (!/[A-Z]/.test(password)) {
                errors.push(t('auth.passwordUppercase'));
            }
            if (!/[0-9]/.test(password)) {
                errors.push(t('auth.passwordNumber'));
            }
            try {
                // Check for emojis/special unicode
                new TextEncoder().encode(password).forEach(byte => {
                    if (byte > 127) throw new Error('Non-ASCII');
                });
            } catch {
                errors.push(t('auth.passwordNoEmoji'));
            }
        }
        setPasswordErrors(errors);
    }, [password, t]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        if (passwordErrors.length > 0) {
            setError(t('auth.fixPasswordErrors'));
            setIsLoading(false);
            return;
        }

        if (!acceptedLegal) {
            setError(t('auth.mustAcceptLegal') || 'You must accept the Terms of Service and Privacy Policy to register.');
            setIsLoading(false);
            return;
        }

        const result = await register('', email, password, firstName, lastName, i18n.language);
        setIsLoading(false);

        if (result.success) {
            // Record legal acceptance
            try {
                const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
                const token = localStorage.getItem('token');
                await fetch(`${apiUrl}/api/legal/accept/`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });
            } catch (err) {
                console.error('Failed to record legal acceptance:', err);
            }

            onRegistrationSuccess();
        } else {
            setError(result.error || t('auth.registerError'));
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center">
            <div className="bg-white rounded-lg shadow-xl p-8 w-96 relative">
                {/* Language Switcher */}
                <div className="absolute top-4 right-4">
                    <SimpleLanguageSwitcher />
                </div>

                <h2 className="text-3xl font-bold text-center mb-2 mt-8">{t('auth.welcomeMessage')}</h2>
                <p className="text-center text-gray-600 mb-6">{t('auth.registerSubtitle')}</p>

                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="block text-sm font-medium mb-2">{t('auth.email')}</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder={t('auth.enterEmail')}
                            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                            required
                            disabled={isLoading}
                        />
                    </div>

                    <div className="mb-4">
                        <label className="block text-sm font-medium mb-2">{t('auth.firstName')}</label>
                        <input
                            type="text"
                            value={firstName}
                            onChange={(e) => setFirstName(e.target.value)}
                            placeholder={t('auth.enterFirstName')}
                            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                            required
                            disabled={isLoading}
                        />
                    </div>

                    <div className="mb-4">
                        <label className="block text-sm font-medium mb-2">{t('auth.lastName')}</label>
                        <input
                            type="text"
                            value={lastName}
                            onChange={(e) => setLastName(e.target.value)}
                            placeholder={t('auth.enterLastName')}
                            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                            required
                            disabled={isLoading}
                        />
                    </div>

                    <div className="mb-6">
                        <label className="block text-sm font-medium mb-2">{t('auth.password')}</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder={t('auth.enterPassword')}
                            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                            required
                            disabled={isLoading}
                        />
                        {passwordErrors.length > 0 && password && (
                            <div className="mt-2 text-xs text-amber-600">
                                <p className="font-medium">{t('auth.passwordRequirements')}:</p>
                                <ul className="list-disc list-inside mt-1">
                                    {passwordErrors.map((err, idx) => (
                                        <li key={idx}>{err}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>

                    {/* Legal Acceptance - REQUIRED FOR GDPR/CCPA/Israel Amendment 13 */}
                    <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <label className="flex items-start gap-3 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={acceptedLegal}
                                onChange={(e) => setAcceptedLegal(e.target.checked)}
                                className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                                disabled={isLoading}
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

                    {error && (
                        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={isLoading || passwordErrors.length > 0 || !acceptedLegal}
                    >
                        {isLoading ? t('auth.registering') : t('auth.registerButton')}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <p className="text-sm text-gray-600">
                        {t('auth.hasAccount')}{' '}
                        <button
                            onClick={onSwitchToLogin}
                            className="text-blue-600 hover:text-blue-700 font-medium"
                            disabled={isLoading}
                        >
                            {t('auth.signIn')}
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Registration;
