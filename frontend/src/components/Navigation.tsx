import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import LanguageSwitcher from './LanguageSwitcher';
import { Menu, X } from 'lucide-react';

interface NavigationProps {
    currentPage: string;
    setCurrentPage: (page: string) => void;
}

const Navigation: React.FC<NavigationProps> = ({ currentPage, setCurrentPage }) => {
    const { user, logout } = useAuth();
    const { t, i18n } = useTranslation();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    // Update HTML dir attribute for RTL support
    useEffect(() => {
        document.documentElement.dir = i18n.language === 'he' ? 'rtl' : 'ltr';
    }, [i18n.language]);

    // Close mobile menu when clicking outside or on navigation
    useEffect(() => {
        if (isMobileMenuOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
        return () => {
            document.body.style.overflow = '';
        };
    }, [isMobileMenuOpen]);

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

    const handleNavigation = (page: string) => {
        setCurrentPage(page);
        setIsMobileMenuOpen(false);
    };

    const handleLogout = () => {
        setIsMobileMenuOpen(false);
        logout();
    };

    return (
        <>
            <nav className="bg-gradient-to-r from-green-600 to-blue-600 text-white shadow-lg sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4">
                    {/* Desktop & Mobile Header */}
                    <div className="flex justify-between items-center h-16 relative">
                        {/* Logo + Title */}
                        <div className="flex items-center gap-3 z-10">
                            <button
                                onClick={() => handleNavigation('shopping')}
                                className="text-3xl hover:text-green-200 transition cursor-pointer"
                                title={t('nav.shopping')}
                            >
                                🥗
                            </button>
                            {/* Title - Next to logo on desktop, centered on mobile */}
                            <h1 className="hidden md:block text-2xl font-bold text-white drop-shadow-lg whitespace-nowrap">
                                MenuMind AI
                            </h1>
                        </div>

                        {/* Center Title - Mobile Only */}
                        <div className="md:hidden absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 z-0">
                            <h1 className="text-lg font-bold text-white drop-shadow-lg whitespace-nowrap">
                                MenuMind AI
                            </h1>
                        </div>

                        {/* Desktop Navigation - Hidden on Mobile */}
                        <div className="hidden lg:flex items-center space-x-6 z-10">
                            {navItems.map(item => (
                                <button
                                    key={item.id}
                                    onClick={() => handleNavigation(item.id)}
                                    className={`hover:text-green-200 transition flex items-center gap-1 px-3 py-2 rounded ${
                                        currentPage === item.id ? 'bg-white/20 text-green-200 font-bold' : ''
                                    }`}
                                >
                                    <span>{item.icon}</span>
                                    <span className="hidden xl:inline">{t(item.translationKey)}</span>
                                </button>
                            ))}
                        </div>

                        {/* Desktop User Menu - Hidden on Mobile */}
                        <div className="hidden lg:flex items-center space-x-4 z-10">
                            <LanguageSwitcher />
                            <span className="text-sm">👤 {user?.username}</span>
                            {user?.partner && <span className="text-sm">💑 {t('nav.connected')}</span>}
                            <button
                                onClick={handleLogout}
                                className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded transition"
                            >
                                {t('nav.logout')}
                            </button>
                        </div>

                        {/* Mobile Hamburger Button */}
                        <button
                            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                            className="lg:hidden p-2 hover:bg-white/10 rounded transition z-10"
                            aria-label="Toggle menu"
                        >
                            {isMobileMenuOpen ? (
                                <X className="w-6 h-6" />
                            ) : (
                                <Menu className="w-6 h-6" />
                            )}
                        </button>
                    </div>
                </div>
            </nav>

            {/* Mobile Menu Overlay */}
            {isMobileMenuOpen && (
                <>
                    {/* Backdrop */}
                    <div
                        className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                        onClick={() => setIsMobileMenuOpen(false)}
                    />

                    {/* Mobile Menu Panel */}
                    <div className="fixed top-16 left-0 right-0 bottom-0 bg-gradient-to-b from-green-600 to-blue-600 z-40 lg:hidden overflow-y-auto">
                        <div className="p-4 space-y-2">
                            {/* User Info */}
                            <div className="bg-white/10 rounded-lg p-4 mb-4">
                                <div className="flex items-center gap-2 text-white">
                                    <span className="text-2xl">👤</span>
                                    <div>
                                        <div className="font-bold">{user?.username}</div>
                                        {user?.partner && (
                                            <div className="text-sm text-green-200">
                                                💑 {t('nav.connected')}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Navigation Items */}
                            {navItems.map(item => (
                                <button
                                    key={item.id}
                                    onClick={() => handleNavigation(item.id)}
                                    className={`w-full text-left px-4 py-3 rounded-lg transition flex items-center gap-3 text-lg ${
                                        currentPage === item.id
                                            ? 'bg-white text-green-600 font-bold'
                                            : 'text-white hover:bg-white/10'
                                    }`}
                                >
                                    <span className="text-2xl">{item.icon}</span>
                                    <span>{t(item.translationKey)}</span>
                                </button>
                            ))}

                            {/* Language Switcher */}
                            <div className="pt-4 border-t border-white/20">
                                <div className="px-4 py-2 text-white text-sm font-semibold mb-2">
                                    {t('nav.language', 'Language')}
                                </div>
                                <div className="px-4">
                                    <LanguageSwitcher />
                                </div>
                            </div>

                            {/* Logout Button */}
                            <div className="pt-4">
                                <button
                                    onClick={handleLogout}
                                    className="w-full bg-red-500 hover:bg-red-600 text-white px-4 py-3 rounded-lg transition font-bold flex items-center justify-center gap-2"
                                >
                                    <span>🚪</span>
                                    <span>{t('nav.logout')}</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </>
    );
};

export default Navigation;