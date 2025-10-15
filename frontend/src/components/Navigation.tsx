import React, { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import LanguageSwitcher from './LanguageSwitcher';

interface NavigationProps {
    currentPage: string;
    setCurrentPage: (page: string) => void;
}

const Navigation: React.FC<NavigationProps> = ({ currentPage, setCurrentPage }) => {
    const { user, logout } = useAuth();
    const { t, i18n } = useTranslation();

    // Update HTML dir attribute for RTL support
    useEffect(() => {
        document.documentElement.dir = i18n.language === 'he' ? 'rtl' : 'ltr';
    }, [i18n.language]);

    const navItems = [
        { id: 'shopping', translationKey: 'nav.shopping', icon: '🛒' },
        { id: 'dashboard', translationKey: 'nav.dashboard', icon: '📊' },
        { id: 'nutrition', translationKey: 'nav.nutrition', icon: '🥗' },
        { id: 'recipes', translationKey: 'nav.recipes', icon: '👨‍🍳' },
        { id: 'discover', translationKey: 'nav.discover', icon: '🌟' },
        { id: 'inventory', translationKey: 'nav.inventory', icon: '📦' },
        { id: 'archive', translationKey: 'nav.archive', icon: '🗃️' },
        { id: 'settings', translationKey: 'nav.settings', icon: '⚙️' }
    ];

    return (
        <nav className="bg-gradient-to-r from-green-600 to-blue-600 text-white p-4 shadow-lg">
            <div className="max-w-7xl mx-auto flex justify-between items-center">
                <div className="flex items-center space-x-8">
                    <button
                        onClick={() => setCurrentPage('shopping')}
                        className="text-2xl font-bold hover:text-green-200 transition cursor-pointer"
                        title={t('nav.shopping')}
                    >
                        🥗 {t('app.name')}
                    </button>
                    <div className="flex space-x-6">
                        {navItems.map(item => (
                            <button
                                key={item.id}
                                onClick={() => setCurrentPage(item.id)}
                                className={`hover:text-green-200 transition ${currentPage === item.id ? 'text-green-200 font-bold' : ''
                                    }`}
                            >
                                {item.icon} {t(item.translationKey)}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="flex items-center space-x-4">
                    <LanguageSwitcher />
                    <span className="text-sm">👤 {user?.username}</span>
                    {user?.partner && <span className="text-sm">💑 {t('nav.connected')}</span>}
                    <button
                        onClick={logout}
                        className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded transition"
                    >
                        {t('nav.logout')}
                    </button>
                </div>
            </div>
        </nav>
    );
};

export default Navigation;