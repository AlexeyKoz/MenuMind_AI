import React, { useState, useEffect } from 'react';
import { BrowserRouter, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { CollaborationProvider } from './contexts/CollaborationContext';
import { UserGuideProvider } from './contexts/UserGuideContext';
import Navigation from './components/Navigation';
import EmailVerificationBanner from './components/EmailVerificationBanner';
import CookieConsentBanner from './components/CookieConsentBanner';
import { AIWarningBanner } from './components/WarningBanners';
import { GuideTooltip } from './components/GuideTooltip';
import Footer from './components/Footer';
import { Dashboard, ShoppingList, NutritionTracker, Recipes, Login, Inventory, SettingsPage, CanonicalRecipesPage, WhatsNewPage } from './pages';
import Registration from './pages/Registration';
import ArchivePage from './pages/ArchivePage';
import VerifyEmail from './pages/VerifyEmail';
import About from './pages/About';
import Settings from './pages/Settings';
import PrivacySettings from './pages/PrivacySettings';
import TermsOfService from './pages/TermsOfService';
import PrivacyPolicy from './pages/PrivacyPolicy';
import CookiePolicy from './pages/CookiePolicy';
import CopyrightNotice from './pages/CopyrightNotice';
import RCIPLicense from './pages/RCIPLicense';
import { ShoppingListContainer } from './features/shopping/ShoppingListContainer';
import logoService from './services/logoService';
import './App.css';

const useCurrentPage = (isAuthenticated: boolean) => {
    const location = useLocation();
    const navigate = useNavigate();
    const [currentPage, setCurrentPage] = useState<string>(() => {
        const path = location.pathname.replace('/', '');
        const validPages = ['dashboard', 'shopping', 'nutrition', 'recipes', 'discover', 'inventory', 'archive', 'settings'];
        return validPages.includes(path) ? path : 'shopping';
    });

    useEffect(() => {
        if (!isAuthenticated) {
            return;
        }
        const path = location.pathname.replace('/', '');
        const validPages = ['dashboard', 'shopping', 'nutrition', 'recipes', 'discover', 'inventory', 'archive', 'settings'];
        if (validPages.includes(path) && path !== currentPage) {
            setCurrentPage(path);
        }
    }, [location.pathname, isAuthenticated, currentPage]);

    // Update page title based on current page
    useEffect(() => {
        const pageTitles: { [key: string]: string } = {
            dashboard: 'Dashboard',
            shopping: 'Shopping List',
            nutrition: 'Nutrition Tracker',
            recipes: 'My Recipes',
            discover: 'Discover Recipes',
            inventory: 'Inventory',
            archive: 'Archive',
            settings: 'Settings'
        };

        const pageTitle = pageTitles[currentPage] || 'Shopping List';
        document.title = `${pageTitle} - BishulMe`;
    }, [currentPage]);

    const handleSetPage = (page: string) => {
        setCurrentPage(page);
        navigate(`/${page}${location.search}`);
    };

    return { currentPage, setCurrentPage: handleSetPage };
};

const AppContent: React.FC = () => {
    const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
    const { user, loading } = useAuth();
    const { currentPage, setCurrentPage } = useCurrentPage(Boolean(user));
    const { i18n } = useTranslation();

    // Update favicon when language changes
    useEffect(() => {
        const updateFavicon = async () => {
            try {
                await logoService.updateFavicon(i18n.language);
                console.log('[App] Favicon updated for language:', i18n.language);
            } catch (error) {
                console.error('[App] Error updating favicon:', error);
            }
        };
        updateFavicon();
    }, [i18n.language]);

    // Page component mapping
    const pageComponents: { [key: string]: React.ComponentType } = {
        dashboard: Dashboard,
        shopping: ShoppingList,
        nutrition: NutritionTracker,
        recipes: Recipes,
        discover: CanonicalRecipesPage,
        inventory: Inventory,
        archive: ArchivePage,
        settings: SettingsPage
    };

    const CurrentPageComponent = pageComponents[currentPage] || ShoppingList;

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-2xl">Loading...</div>
            </div>
        );
    }

    if (!user) {
        return (
            <div className="min-h-screen flex flex-col">
                <Routes>
                    {/* Legal Routes - Public */}
                    <Route path="/legal/terms" element={<TermsOfService />} />
                    <Route path="/legal/privacy" element={<PrivacyPolicy />} />
                    <Route path="/legal/cookies" element={<CookiePolicy />} />
                    <Route path="/legal/copyright" element={<CopyrightNotice />} />
                    <Route path="/legal/rcip" element={<RCIPLicense />} />

                    {/* What's New Page - Public */}
                    <Route path="/whats-new" element={<WhatsNewPage />} />

                    <Route
                        path="/verify-email/:key"
                        element={<VerifyEmail />}
                    />
                    <Route
                        path="/verify-email"
                        element={<VerifyEmail />}
                    />
                    <Route
                        path="/about"
                        element={<About />}
                    />
                    <Route
                        path="*"
                        element={authMode === 'login' ? (
                            <Login
                                onLoginSuccess={() => window.location.reload()}
                                onSwitchToRegistration={() => setAuthMode('register')}
                            />
                        ) : (
                            <Registration
                                onRegistrationSuccess={() => window.location.reload()}
                                onSwitchToLogin={() => setAuthMode('login')}
                            />
                        )}
                    />
                </Routes>
                <Footer />
            </div>
        );
    }

    return (
        <CollaborationProvider>
            <UserGuideProvider>
                <div className="min-h-screen bg-gray-100 flex flex-col">
                    <EmailVerificationBanner />
                    <Navigation currentPage={currentPage} setCurrentPage={setCurrentPage} />
                    <AIWarningBanner />
                    <GuideTooltip />
                    <div className="flex-1">
                        <Routes>
                            {/* Legal Routes - Accessible to authenticated users too */}
                            <Route path="/legal/terms" element={<TermsOfService />} />
                            <Route path="/legal/privacy" element={<PrivacyPolicy />} />
                            <Route path="/legal/cookies" element={<CookiePolicy />} />
                            <Route path="/legal/copyright" element={<CopyrightNotice />} />
                            <Route path="/legal/rcip" element={<RCIPLicense />} />

                            {/* Privacy Settings Page */}
                            <Route path="/privacy-settings" element={<PrivacySettings />} />

                            {/* What's New Page */}
                            <Route path="/whats-new" element={<WhatsNewPage />} />

                            <Route path="/dashboard" element={<Dashboard />} />
                            <Route path="/shopping" element={<ShoppingList />} />
                            <Route path="/shopping-mobile" element={<ShoppingListContainer />} />
                            <Route path="/shopping-mobile/:listId" element={<ShoppingListContainer />} />
                            <Route path="/nutrition" element={<NutritionTracker />} />
                            <Route path="/recipes" element={<Recipes />} />
                            <Route path="/discover" element={<CanonicalRecipesPage />} />
                            <Route path="/inventory" element={<Inventory />} />
                            <Route path="/archive" element={<ArchivePage />} />
                            <Route path="/settings" element={<SettingsPage />} />
                            <Route path="/about" element={<About />} />
                            <Route path="/app-settings" element={<Settings />} />
                            <Route path="/verify-email" element={<VerifyEmail />} />
                            <Route path="/verify-email/:key" element={<VerifyEmail />} />
                            <Route path="/" element={<CurrentPageComponent />} />
                            <Route path="*" element={<CurrentPageComponent />} />
                        </Routes>
                    </div>
                    <Footer />
                    <Toaster position="top-right" />
                </div>
            </UserGuideProvider>
        </CollaborationProvider>
    );
};

const App: React.FC = () => {
    return (
        <BrowserRouter
            future={{
                v7_startTransition: true,
                v7_relativeSplatPath: true
            }}
        >
            <AuthProvider>
                <AppContent />
                <CookieConsentBanner />
            </AuthProvider>
        </BrowserRouter>
    );
};

export default App;