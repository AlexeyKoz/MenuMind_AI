import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

interface GuideStep {
    id: string;
    page: string;
    elementId?: string;
    position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
    translationKey: string;
    order: number;
}

interface UserGuideContextType {
    currentStep: GuideStep | null;
    isGuideActive: boolean;
    isInitialized: boolean;  // Add this so pages can wait for initialization
    startGuide: (page: string) => void;
    nextStep: () => void;
    skipGuide: () => void;
    resetGuide: (page: string) => void;
    hasSeenGuide: (page: string) => boolean;
}

const UserGuideContext = createContext<UserGuideContextType | undefined>(undefined);

// Define all guide steps for different pages
const GUIDE_STEPS: GuideStep[] = [
    // Shopping List Guide
    {
        id: 'shopping-welcome',
        page: 'shopping',
        position: 'center',
        translationKey: 'guide.shopping.welcome',
        order: 0
    },
    {
        id: 'shopping-create-list',
        page: 'shopping',
        elementId: 'create-list-button',
        position: 'bottom',
        translationKey: 'guide.shopping.createList',
        order: 1
    },
    {
        id: 'shopping-ai-add',
        page: 'shopping',
        elementId: 'ai-add-section',
        position: 'bottom',
        translationKey: 'guide.shopping.aiAdd',
        order: 2
    },
    {
        id: 'shopping-manual-add',
        page: 'shopping',
        elementId: 'manual-add-input',
        position: 'bottom',
        translationKey: 'guide.shopping.manualAdd',
        order: 3
    },
    {
        id: 'shopping-collaborators',
        page: 'shopping',
        elementId: 'collaborators-button',
        position: 'left',
        translationKey: 'guide.shopping.collaborators',
        order: 4
    },
    {
        id: 'shopping-send-inventory',
        page: 'shopping',
        elementId: 'send-inventory-button',
        position: 'top',
        translationKey: 'guide.shopping.sendInventory',
        order: 5
    },
    {
        id: 'shopping-complete',
        page: 'shopping',
        position: 'center',
        translationKey: 'guide.shopping.complete',
        order: 6
    },
    
    // Inventory Guide
    {
        id: 'inventory-welcome',
        page: 'inventory',
        position: 'center',
        translationKey: 'guide.inventory.welcome',
        order: 0
    },
    {
        id: 'inventory-add-item',
        page: 'inventory',
        elementId: 'add-item-button',
        position: 'bottom',
        translationKey: 'guide.inventory.addItem',
        order: 1
    },
    {
        id: 'inventory-locations',
        page: 'inventory',
        elementId: 'location-tabs',
        position: 'bottom',
        translationKey: 'guide.inventory.locations',
        order: 2
    },
    {
        id: 'inventory-expiring',
        page: 'inventory',
        elementId: 'expiring-items-section',
        position: 'bottom',
        translationKey: 'guide.inventory.expiring',
        order: 3
    },
    {
        id: 'inventory-recipes',
        page: 'inventory',
        elementId: 'get-recipes-button',
        position: 'top',
        translationKey: 'guide.inventory.recipes',
        order: 4
    },
    {
        id: 'inventory-complete',
        page: 'inventory',
        position: 'center',
        translationKey: 'guide.inventory.complete',
        order: 5
    },
    
    // Discover Recipes Guide
    {
        id: 'discover-welcome',
        page: 'discover',
        position: 'center',
        translationKey: 'guide.discover.welcome',
        order: 0
    },
    {
        id: 'discover-ai-search',
        page: 'discover',
        elementId: 'ai-recipe-search',
        position: 'bottom',
        translationKey: 'guide.discover.aiSearch',
        order: 1
    },
    {
        id: 'discover-filters',
        page: 'discover',
        elementId: 'recipe-filters',
        position: 'bottom',
        translationKey: 'guide.discover.filters',
        order: 2
    },
    {
        id: 'discover-like-rate',
        page: 'discover',
        elementId: 'recipe-cards-section',
        position: 'top',
        translationKey: 'guide.discover.likeRate',
        order: 3
    },
    {
        id: 'discover-create',
        page: 'discover',
        elementId: 'create-recipe-button',
        position: 'left',
        translationKey: 'guide.discover.create',
        order: 4
    },
    {
        id: 'discover-complete',
        page: 'discover',
        position: 'center',
        translationKey: 'guide.discover.complete',
        order: 5
    },
    
    // My Recipes Guide
    {
        id: 'recipes-welcome',
        page: 'recipes',
        position: 'center',
        translationKey: 'guide.recipes.welcome',
        order: 0
    },
    {
        id: 'recipes-upload',
        page: 'recipes',
        elementId: 'upload-rcip-button',
        position: 'bottom',
        translationKey: 'guide.recipes.upload',
        order: 1
    },
    {
        id: 'recipes-filters',
        page: 'recipes',
        elementId: 'recipes-filter-section',
        position: 'bottom',
        translationKey: 'guide.recipes.filters',
        order: 2
    },
    {
        id: 'recipes-view-detail',
        page: 'recipes',
        elementId: 'recipe-collection',
        position: 'top',
        translationKey: 'guide.recipes.viewDetail',
        order: 3
    },
    {
        id: 'recipes-archive',
        page: 'recipes',
        position: 'center',
        translationKey: 'guide.recipes.archive',
        order: 4
    },
    {
        id: 'recipes-complete',
        page: 'recipes',
        position: 'center',
        translationKey: 'guide.recipes.complete',
        order: 5
    },
    
    // Nutrition Coach Guide
    {
        id: 'nutrition-welcome',
        page: 'nutrition',
        position: 'center',
        translationKey: 'guide.nutrition.welcome',
        order: 0
    },
    {
        id: 'nutrition-goals',
        page: 'nutrition',
        elementId: 'nutrition-goals-section',
        position: 'bottom',
        translationKey: 'guide.nutrition.goals',
        order: 1
    },
    {
        id: 'nutrition-add-entry',
        page: 'nutrition',
        elementId: 'add-entry-button',
        position: 'bottom',
        translationKey: 'guide.nutrition.addEntry',
        order: 2
    },
    {
        id: 'nutrition-ai-coach',
        page: 'nutrition',
        elementId: 'ai-coach-section',
        position: 'top',
        translationKey: 'guide.nutrition.aiCoach',
        order: 3
    },
    {
        id: 'nutrition-settings',
        page: 'nutrition',
        elementId: 'nutrition-settings-link',
        position: 'left',
        translationKey: 'guide.nutrition.settings',
        order: 4
    },
    {
        id: 'nutrition-complete',
        page: 'nutrition',
        position: 'center',
        translationKey: 'guide.nutrition.complete',
        order: 5
    },
    
    // Dashboard Guide
    {
        id: 'dashboard-welcome',
        page: 'dashboard',
        position: 'center',
        translationKey: 'guide.dashboard.welcome',
        order: 0
    },
    {
        id: 'dashboard-overview',
        page: 'dashboard',
        elementId: 'dashboard-overview',
        position: 'bottom',
        translationKey: 'guide.dashboard.overview',
        order: 1
    },
    {
        id: 'dashboard-insights',
        page: 'dashboard',
        elementId: 'ai-insights-section',
        position: 'bottom',
        translationKey: 'guide.dashboard.insights',
        order: 2
    },
    {
        id: 'dashboard-shopping',
        page: 'dashboard',
        elementId: 'shopping-insights',
        position: 'top',
        translationKey: 'guide.dashboard.shopping',
        order: 3
    },
    {
        id: 'dashboard-inventory',
        page: 'dashboard',
        elementId: 'inventory-alerts',
        position: 'top',
        translationKey: 'guide.dashboard.inventory',
        order: 4
    },
    {
        id: 'dashboard-complete',
        page: 'dashboard',
        position: 'center',
        translationKey: 'guide.dashboard.complete',
        order: 5
    }
];

export const UserGuideProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [currentStep, setCurrentStep] = useState<GuideStep | null>(null);
    const [isGuideActive, setIsGuideActive] = useState(false);
    const [completedGuides, setCompletedGuides] = useState<Set<string>>(new Set());
    const [isInitialized, setIsInitialized] = useState(false);

    // Load completed guides from backend (or fallback to localStorage)
    useEffect(() => {
        const loadCompletedGuides = async () => {
            console.log('🔍 [GUIDE DEBUG] Starting to load completed guides...');
            
            try {
                // Check if user is authenticated
                const token = localStorage.getItem('access_token');
                console.log('🔍 [GUIDE DEBUG] Token present:', !!token);
                
                if (!token) {
                    console.log('🔍 [GUIDE DEBUG] No token - using localStorage');
                    // Not authenticated, use localStorage
                    const stored = localStorage.getItem('menumine-completed-guides');
                    if (stored) {
                        const guides = JSON.parse(stored);
                        console.log('🔍 [GUIDE DEBUG] Loaded from localStorage:', guides);
                        setCompletedGuides(new Set(guides));
                    }
                    setIsInitialized(true);
                    return;
                }

                // Fetch user data including has_seen_guides
                console.log('🔍 [GUIDE DEBUG] Fetching from API...');
                // Direct URL to backend (bypass proxy)
                const response = await axios.get('http://localhost:8000/api/users/profile/user_settings/', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                console.log('🔍 [GUIDE DEBUG] API Response status:', response.status);
                console.log('🔍 [GUIDE DEBUG] API Response has_seen_guides:', response.data.has_seen_guides);

                const hasSeenGuides = response.data.has_seen_guides || [];
                setCompletedGuides(new Set(hasSeenGuides));
                
                // Also sync to localStorage for offline access
                localStorage.setItem('menumine-completed-guides', JSON.stringify(hasSeenGuides));
                
                console.log('✅ [GUIDE DEBUG] Successfully loaded guides from backend:', hasSeenGuides);
            } catch (error) {
                console.error('❌ [GUIDE DEBUG] Failed to load from backend:', error);
                // Fallback to localStorage
                const stored = localStorage.getItem('menumine-completed-guides');
                if (stored) {
                    try {
                        const guides = JSON.parse(stored);
                        console.log('🔍 [GUIDE DEBUG] Fallback to localStorage:', guides);
                        setCompletedGuides(new Set(guides));
                    } catch (e) {
                        console.error('❌ [GUIDE DEBUG] Failed to parse localStorage:', e);
                    }
                }
            } finally {
                console.log('🔍 [GUIDE DEBUG] Initialization complete');
                setIsInitialized(true);
            }
        };

        loadCompletedGuides();
    }, []);

    const hasSeenGuide = (page: string): boolean => {
        return completedGuides.has(page);
    };

    const startGuide = (page: string) => {
        console.log('🔍 [GUIDE DEBUG] startGuide called for page:', page);
        console.log('🔍 [GUIDE DEBUG] isInitialized:', isInitialized);
        console.log('🔍 [GUIDE DEBUG] completedGuides:', Array.from(completedGuides));
        
        // Wait for initialization before checking
        if (!isInitialized) {
            console.log('⏳ [GUIDE DEBUG] Not initialized yet, waiting...');
            return;
        }

        if (hasSeenGuide(page)) {
            console.log('✅ [GUIDE DEBUG] Guide already completed for:', page);
            return;
        }

        const pageSteps = GUIDE_STEPS.filter(step => step.page === page).sort((a, b) => a.order - b.order);
        
        if (pageSteps.length > 0) {
            console.log('🚀 [GUIDE DEBUG] Starting guide for', page, 'with', pageSteps.length, 'steps');
            setCurrentStep(pageSteps[0]);
            setIsGuideActive(true);
        }
    };

    const nextStep = () => {
        if (!currentStep) return;

        const pageSteps = GUIDE_STEPS
            .filter(step => step.page === currentStep.page)
            .sort((a, b) => a.order - b.order);

        const currentIndex = pageSteps.findIndex(step => step.id === currentStep.id);
        
        if (currentIndex < pageSteps.length - 1) {
            setCurrentStep(pageSteps[currentIndex + 1]);
        } else {
            // Guide completed
            completeGuide(currentStep.page);
        }
    };

    const skipGuide = () => {
        if (currentStep) {
            completeGuide(currentStep.page);
        }
    };

    const completeGuide = async (page: string) => {
        const newCompleted = new Set(completedGuides);
        newCompleted.add(page);
        setCompletedGuides(newCompleted);
        
        // Save to localStorage for immediate persistence
        localStorage.setItem('menumine-completed-guides', JSON.stringify([...newCompleted]));
        
        setCurrentStep(null);
        setIsGuideActive(false);
        console.log(`✅ Guide completed for ${page}`);

        // Sync to backend
        try {
            const token = localStorage.getItem('access_token');
            if (token) {
                // Direct URL to backend (bypass proxy issues)
                await axios.post('http://localhost:8000/api/users/profile/mark-guide-seen/', 
                    { page },
                    {
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        }
                    }
                );
                console.log(`✅ [GUIDE] Guide completion synced to backend for ${page}`);
            }
        } catch (error) {
            console.error('[GUIDE] Failed to sync guide completion to backend:', error);
            // Not critical - localStorage is already updated
        }
    };

    const resetGuide = async (page: string) => {
        const newCompleted = new Set(completedGuides);
        newCompleted.delete(page);
        setCompletedGuides(newCompleted);
        
        // Update localStorage
        localStorage.setItem('menumine-completed-guides', JSON.stringify([...newCompleted]));
        console.log(`🔄 Guide reset for ${page}`);

        // Sync to backend - reset by re-syncing the full list
        try {
            const token = localStorage.getItem('access_token');
            if (token) {
                // We'll need to handle reset separately or just don't sync here
                // For now, just update localStorage
                console.log(`🔄 Guide reset locally for ${page}`);
            }
        } catch (error) {
            console.error('Failed to reset guide on backend:', error);
        }
    };

    return (
        <UserGuideContext.Provider
            value={{
                currentStep,
                isGuideActive,
                isInitialized,
                startGuide,
                nextStep,
                skipGuide,
                resetGuide,
                hasSeenGuide
            }}
        >
            {children}
        </UserGuideContext.Provider>
    );
};

export const useUserGuide = (): UserGuideContextType => {
    const context = useContext(UserGuideContext);
    if (!context) {
        throw new Error('useUserGuide must be used within UserGuideProvider');
    }
    return context;
};

