import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { CollaborationProvider } from './contexts/CollaborationContext';
import Navigation from './components/Navigation';
import { Dashboard, ShoppingList, NutritionTracker, Recipes, Login, Inventory, SettingsPage, CanonicalRecipesPage } from './pages';
import Registration from './pages/Registration';
import ArchivePage from './pages/ArchivePage';
import './App.css';

const AppContent: React.FC = () => {
    // Parse URL on mount to determine initial page
    const getInitialPage = () => {
        const path = window.location.pathname.replace('/', '');
        const validPages = ['dashboard', 'shopping', 'nutrition', 'recipes', 'discover', 'inventory', 'archive', 'settings'];
        const initialPage = validPages.includes(path) ? path : 'shopping';
        console.log(`🎯 App initializing - URL: ${window.location.href}, Path: ${path}, Initial Page: ${initialPage}`);
        return initialPage;
    };

    const [currentPage, setCurrentPage] = useState(getInitialPage());
    const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
    const { user, loading } = useAuth();

    // Update URL when page changes
    useEffect(() => {
        if (user && currentPage) {
            const newUrl = `/${currentPage}${window.location.search}`;
            window.history.pushState({ page: currentPage }, '', newUrl);
        }
    }, [currentPage, user]);

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
            <>
                {authMode === 'login' ? (
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
                <Toaster position="top-right" />
            </>
        );
    }

    return (
        <CollaborationProvider>
            <div className="min-h-screen bg-gray-100">
                <Navigation currentPage={currentPage} setCurrentPage={setCurrentPage} />
                <CurrentPageComponent />
                <Toaster position="top-right" />
            </div>
        </CollaborationProvider>
    );
};

const App: React.FC = () => {
    return (
        <AuthProvider>
            <AppContent />
        </AuthProvider>
    );
};

export default App;