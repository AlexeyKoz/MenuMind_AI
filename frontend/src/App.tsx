import React, { useState, useEffect } from 'react';
import { BrowserRouter, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { CollaborationProvider } from './contexts/CollaborationContext';
import Navigation from './components/Navigation';
import EmailVerificationBanner from './components/EmailVerificationBanner';
import { Dashboard, ShoppingList, NutritionTracker, Recipes, Login, Inventory, SettingsPage, CanonicalRecipesPage } from './pages';
import Registration from './pages/Registration';
import ArchivePage from './pages/ArchivePage';
import VerifyEmail from './pages/VerifyEmail';
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
            <Routes>
                <Route
                    path="/verify-email/:key"
                    element={<VerifyEmail />}
                />
                <Route
                    path="/verify-email"
                    element={<VerifyEmail />}
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
        );
    }

    return (
        <CollaborationProvider>
            <div className="min-h-screen bg-gray-100">
                <EmailVerificationBanner />
                <Navigation currentPage={currentPage} setCurrentPage={setCurrentPage} />
                <Routes>
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/shopping" element={<ShoppingList />} />
                    <Route path="/nutrition" element={<NutritionTracker />} />
                    <Route path="/recipes" element={<Recipes />} />
                    <Route path="/discover" element={<CanonicalRecipesPage />} />
                    <Route path="/inventory" element={<Inventory />} />
                    <Route path="/archive" element={<ArchivePage />} />
                    <Route path="/settings" element={<SettingsPage />} />
                    <Route path="/verify-email" element={<VerifyEmail />} />
                    <Route path="/verify-email/:key" element={<VerifyEmail />} />
                    <Route path="/" element={<CurrentPageComponent />} />
                    <Route path="*" element={<CurrentPageComponent />} />
                </Routes>
                <Toaster position="top-right" />
            </div>
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
            </AuthProvider>
        </BrowserRouter>
    );
};

export default App;