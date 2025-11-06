import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import GoogleSignInButton from '../components/GoogleSignInButton';
import SimpleLanguageSwitcher from '../components/SimpleLanguageSwitcher';
import logoService, { LogoData } from '../services/logoService';

interface LoginProps {
    onLoginSuccess: () => void;
    onSwitchToRegistration?: () => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess, onSwitchToRegistration }) => {
    const { t, i18n } = useTranslation();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loginLogo, setLoginLogo] = useState<LogoData | null>(null);
    const { login } = useAuth();

    // Load login page logo from API
    useEffect(() => {
        const loadLogo = async () => {
            try {
                const logo = await logoService.getLoginLogo(i18n.language);
                setLoginLogo(logo);
            } catch (error) {
                console.error('[Login] Error loading logo:', error);
            }
        };
        loadLogo();
    }, [i18n.language]);

    // Update HTML dir attribute for RTL support (Hebrew)
    useEffect(() => {
        document.documentElement.dir = i18n.language === 'he' ? 'rtl' : 'ltr';

        // Update HTML lang for Google SDK
        const googleLangMap: { [key: string]: string } = {
            'en': 'en',
            'ru': 'ru',
            'he': 'iw'
        };
        document.documentElement.lang = googleLangMap[i18n.language] || 'en';
    }, [i18n.language]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const result = await login(email, password);
        if (result.success) {
            onLoginSuccess();
        } else {
            setError(result.error || t('auth.loginError'));
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center">
            <div className="bg-white rounded-lg shadow-xl p-8 w-96 relative">
                {/* Language Switcher */}
                <div className="absolute top-4 right-4">
                    <SimpleLanguageSwitcher />
                </div>

                {/* Logo */}
                <div className="flex justify-center mb-8 mt-8">
                    <img 
                        src={loginLogo?.file_url || (i18n.language === 'he' ? '/logo/bishulsheli-logo-compact-he.svg' : '/logo/bishulsheli-logo-compact-en.svg')}
                        alt={loginLogo?.alt_text || (i18n.language === 'he' ? 'בישול שלי' : 'BishulSheli')}
                        className="h-24"
                    />
                </div>

                <p className="text-center text-gray-600 mb-6">{t('auth.loginSubtitle')}</p>
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
                        />
                    </div>
                    {error && (
                        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
                            {error}
                        </div>
                    )}
                    <button
                        type="submit"
                        className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                    >
                        {t('auth.loginButton')}
                    </button>
                </form>

                {/* Divider */}
                <div className="relative my-6">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-gray-300"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                        <span className="px-2 bg-white text-gray-500">{t('common.or')}</span>
                    </div>
                </div>

                {/* Google Sign-In */}
                <GoogleSignInButton
                    onSuccess={onLoginSuccess}
                    onError={(error) => setError(error)}
                />

                {onSwitchToRegistration && (
                    <div className="mt-6 text-center">
                        <p className="text-sm text-gray-600">
                            {t('auth.noAccount')}{' '}
                            <button
                                onClick={onSwitchToRegistration}
                                className="text-green-600 hover:text-green-700 font-medium"
                            >
                                {t('auth.signUp')}
                            </button>
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Login;