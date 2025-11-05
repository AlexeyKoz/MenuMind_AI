import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import LanguageSwitcher from './LanguageSwitcher';
import { Menu, X } from 'lucide-react';

interface NavigationProps {
    currentPage: string;
    setCurrentPage: (page: string) => void;
}

const Navigation: React.FC<NavigationProps> = ({ currentPage, setCurrentPage }) => {
    const { user, logout } = useAuth();
    const { t, i18n } = useTranslation();
    
    // Language-specific logo selection
    const getLogoPath = (type: 'horizontal' | 'mobile') => {
        const isHebrew = i18n.language === 'he';
        const suffix = isHebrew ? 'he' : 'en';
        return `/logo/bishulsheli-logo-${type}-${suffix}.svg`;
    };
    
    const getLogoAlt = () => {
        return i18n.language === 'he' ? 'בישול שלי' : 'BishulSheli';
    };
    const navigate = useNavigate();
    const location = useLocation();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    
    // Check if we're on the What's New page
    const isWhatsNewActive = location.pathname === '/whats-new';

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
        // If navigating away from What's New, go back to the main app
        if (location.pathname === '/whats-new') {
            navigate('/');
        }
    };

    const handleLogout = () => {
        setIsMobileMenuOpen(false);
        logout();
    };

    const handleWhatsNew = () => {
        setIsMobileMenuOpen(false);
        setCurrentPage('whats-new'); // Clear the current page selection
        navigate('/whats-new');
    };

    return (
        <>
            <nav className="bg-white text-gray-800 shadow-md sticky top-0 z-50 border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4">
                    {/* Desktop & Mobile Header */}
                    <div className="flex justify-between items-center h-16 relative">
                        {/* Logo - Desktop */}
                        <div className="hidden lg:flex items-center gap-3 z-10 flex-shrink-0">
                            <button
                                onClick={() => handleNavigation('shopping')}
                                className="flex items-center gap-2 hover:opacity-80 transition"
                            >
                                <img 
                                    src={getLogoPath('horizontal')}
                                    alt={getLogoAlt()}
                                    className="h-10"
                                    onError={(e) => {
                                        console.error('Failed to load horizontal logo');
                                        e.currentTarget.style.display = 'none';
                                    }}
                                />
                            </button>
                        </div>

                        {/* Logo - Mobile (centered) */}
                        <div className="lg:hidden absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 z-0">
                            <button
                                onClick={() => handleNavigation('shopping')}
                                className="hover:opacity-80 transition"
                            >
                                <img 
                                    src={getLogoPath('mobile')}
                                    alt={getLogoAlt()}
                                    className="h-10"
                                    onError={(e) => {
                                        console.error('Failed to load mobile logo');
                                        e.currentTarget.style.display = 'none';
                                    }}
                                />
                            </button>
                        </div>

                        {/* Desktop Navigation - Hidden on Mobile */}
                        <div className="hidden lg:flex items-center space-x-6 z-10">
                            {navItems.map(item => (
                                <button
                                    key={item.id}
                                    onClick={() => handleNavigation(item.id)}
                                    className={`hover:text-blue-600 transition flex items-center gap-1 px-3 py-2 rounded ${
                                        currentPage === item.id && !isWhatsNewActive ? 'bg-blue-50 text-blue-600 font-semibold' : 'text-gray-700'
                                    }`}
                                >
                                    <span>{item.icon}</span>
                                    <span className="hidden xl:inline">{t(item.translationKey)}</span>
                                </button>
                            ))}
                        </div>

                        {/* Desktop User Menu - Hidden on Mobile */}
                        <div className="hidden lg:flex items-center gap-3 z-10">
                            {/* What's New Button - Subtle */}
                            <button
                                onClick={handleWhatsNew}
                                className={`text-sm transition flex items-center gap-1 px-3 py-2 rounded ${
                                    isWhatsNewActive 
                                        ? 'bg-blue-50 text-blue-600 font-semibold' 
                                        : 'text-gray-500 hover:text-blue-600'
                                }`}
                                title={t("What's New")}
                            >
                                <span className="text-xs">✨</span>
                                <span className="hidden xl:inline whitespace-nowrap">{t("What's New")}</span>
                            </button>
                            
                            <div className="h-6 w-px bg-gray-300"></div>
                            
                            <LanguageSwitcher />
                            
                            <div className="h-6 w-px bg-gray-300"></div>
                            
                            <span className="text-sm text-gray-700 whitespace-nowrap">
                                👤 {user?.first_name || user?.username}
                            </span>
                            {user?.partner && <span className="text-sm text-purple-600 whitespace-nowrap">💑 {t('nav.connected')}</span>}
                            
                            <button
                                onClick={handleLogout}
                                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded transition whitespace-nowrap ml-2"
                            >
                                {t('nav.logout')}
                            </button>
                        </div>

                        {/* Mobile Hamburger Button */}
                        <button
                            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                            className="lg:hidden p-2 hover:bg-gray-100 rounded transition z-10 text-gray-700"
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
                    <div className="fixed top-16 left-0 right-0 bottom-0 bg-white z-40 lg:hidden overflow-y-auto">
                        <div className="p-4 space-y-2">
                            {/* User Info */}
                            <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 mb-4 border border-gray-200">
                                <div className="flex items-center gap-2 text-gray-800">
                                    <span className="text-2xl">👤</span>
                                    <div>
                                        <div className="font-bold">
                                            {user?.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : user?.username}
                                        </div>
                                        {user?.email && (
                                            <div className="text-xs text-gray-600">
                                                {user.email}
                                            </div>
                                        )}
                                        {user?.partner && (
                                            <div className="text-sm text-purple-600">
                                                💑 {t('nav.connected')}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* What's New Button - Mobile */}
                            <button
                                onClick={handleWhatsNew}
                                className={`w-full px-4 py-3 rounded-lg transition flex items-center gap-2 text-sm border border-blue-200 mb-2 bg-blue-50 hover:bg-blue-100 text-blue-700 ${
                                    isWhatsNewActive ? 'font-bold' : ''
                                }`}
                            >
                                <span className="text-base">✨</span>
                                <span>{t("What's New")}</span>
                            </button>

                            {/* Navigation Items */}
                            {navItems.map(item => (
                                <button
                                    key={item.id}
                                    onClick={() => handleNavigation(item.id)}
                                    className={`w-full text-left px-4 py-3 rounded-lg transition flex items-center gap-3 text-lg ${
                                        currentPage === item.id && !isWhatsNewActive
                                            ? 'bg-blue-50 text-blue-600 font-bold border border-blue-200'
                                            : 'text-gray-700 hover:bg-gray-100 border border-transparent'
                                    }`}
                                >
                                    <span className="text-2xl">{item.icon}</span>
                                    <span>{t(item.translationKey)}</span>
                                </button>
                            ))}

                            {/* Language Switcher */}
                            <div className="pt-4 border-t border-gray-200">
                                <div className="px-4 py-2 text-gray-700 text-sm font-semibold mb-2">
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