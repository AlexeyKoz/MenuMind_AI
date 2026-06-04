import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useUserGuide } from '../contexts/UserGuideContext';
import ApiService from '../services/api';
import toast from 'react-hot-toast';
import {
    Package, Plus, Search, ChefHat, RefreshCw, Edit, Trash2,
    ChevronDown, ChevronUp, AlertTriangle, Clock, X, Save,
    Heart, Download, Users, Eye, ExternalLink, Info
} from 'lucide-react';

// Recipe history storage configuration
const RECIPE_HISTORY_KEY = 'inventory_recipe_history';
const HISTORY_EXPIRATION_HOURS = 24; // Keep for 24 hours

interface InventoryItem {
    id: string;
    name: string;
    quantity: number;
    unit: string;
    category: string;
    location: 'fridge' | 'freezer' | 'pantry' | 'counter';
    expiration_date?: string;
    purchase_date?: string;
    notes?: string;
    expiry_status: 'expired' | 'urgent' | 'warning' | 'ok';
    is_expired: boolean;
    is_expiring_soon: boolean;
    is_low_stock: boolean;
    shopping_list_name?: string;
    created_at: string;
    updated_at: string;
}

interface LocationGroup {
    [key: string]: {
        count: number;
        expiring_count: number;
        items: InventoryItem[];
    };
}

interface RecipeSuggestion {
    name: string;
    description: string;
    main_ingredients: string[];  // NEW AGENT: Simple array of ingredient names
    cook_time_minutes?: number;
    difficulty: string;
    cuisine?: string;
    brief_id?: string;
    generated_at?: string;

    // OLD AGENT fields (for backwards compatibility)
    priority?: 'urgent' | 'high' | 'normal';
    ingredients_from_inventory?: Array<{ name: string; quantity: number; unit: string }>;
    missing_ingredients?: string[];
    nutrition?: { calories: number; protein: number; carbs: number; fat: number };
    cooking_time?: string;
    reasoning?: string;
}

// LocalStorage helper functions for recipe history persistence
const saveRecipeHistoryToStorage = (history: Array<{
    recipes: RecipeSuggestion[];
    inventoryHash: string;
    timestamp: Date;
}>) => {
    try {
        const dataToSave = {
            history: history.map(entry => ({
                ...entry,
                timestamp: entry.timestamp.toISOString() // Convert Date to string for storage
            })),
            savedAt: new Date().toISOString()
        };
        localStorage.setItem(RECIPE_HISTORY_KEY, JSON.stringify(dataToSave));
        console.log('[STORAGE] Saved recipe history:', history.length, 'generations');
    } catch (error) {
        console.error('[STORAGE] Failed to save recipe history:', error);
    }
};

const loadRecipeHistoryFromStorage = (): Array<{
    recipes: RecipeSuggestion[];
    inventoryHash: string;
    timestamp: Date;
}> => {
    try {
        const stored = localStorage.getItem(RECIPE_HISTORY_KEY);
        if (!stored) {
            console.log('[STORAGE] No recipe history found');
            return [];
        }

        const { history, savedAt } = JSON.parse(stored);

        // Check if data is expired (older than HISTORY_EXPIRATION_HOURS)
        const savedDate = new Date(savedAt);
        const now = new Date();
        const hoursElapsed = (now.getTime() - savedDate.getTime()) / (1000 * 60 * 60);

        if (hoursElapsed > HISTORY_EXPIRATION_HOURS) {
            console.log('[STORAGE] Recipe history expired (', Math.round(hoursElapsed), 'hours old). Clearing...');
            localStorage.removeItem(RECIPE_HISTORY_KEY);
            return [];
        }

        // Convert timestamp strings back to Date objects
        const parsedHistory = history.map((entry: any) => ({
            ...entry,
            timestamp: new Date(entry.timestamp)
        }));

        console.log('[STORAGE] Loaded recipe history:', parsedHistory.length, 'generations (saved', Math.round(hoursElapsed), 'hours ago)');
        return parsedHistory;
    } catch (error) {
        console.error('[STORAGE] Failed to load recipe history:', error);
        localStorage.removeItem(RECIPE_HISTORY_KEY);
        return [];
    }
};

const clearRecipeHistoryFromStorage = () => {
    try {
        localStorage.removeItem(RECIPE_HISTORY_KEY);
        console.log('[STORAGE] Cleared recipe history from storage');
    } catch (error) {
        console.error('[STORAGE] Failed to clear recipe history:', error);
    }
};

const Inventory: React.FC = () => {
    const { t } = useTranslation();
    const { token, logout } = useAuth();
    const { startGuide, isInitialized } = useUserGuide();
    const [locationData, setLocationData] = useState<LocationGroup>({});
    const [loading, setLoading] = useState(true);
    const [expandedLocations, setExpandedLocations] = useState<Set<string>>(new Set(['fridge', 'freezer']));
    const [searchQuery, setSearchQuery] = useState('');
    const [showAddModal, setShowAddModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
    const [showRecipesModal, setShowRecipesModal] = useState(false);
    const [recipes, setRecipes] = useState<RecipeSuggestion[]>([]);
    const [generatingRecipes, setGeneratingRecipes] = useState(false);
    const [selectedRecipe, setSelectedRecipe] = useState<any>(null);
    const [showRecipeDetailModal, setShowRecipeDetailModal] = useState(false);
    const [creatingRecipe, setCreatingRecipe] = useState<string | null>(null); // Track which recipe is being created

    // Cache for recipe suggestions to avoid redundant AI calls
    // History of generated recipe lists (max 10 generations) - persisted to localStorage
    const [recipeHistory, setRecipeHistory] = useState<Array<{
        recipes: RecipeSuggestion[];
        inventoryHash: string;
        timestamp: Date;
    }>>(() => loadRecipeHistoryFromStorage()); // Load from localStorage on mount

    const [currentHistoryIndex, setCurrentHistoryIndex] = useState<number>(() => {
        const loaded = loadRecipeHistoryFromStorage();
        return loaded.length > 0 ? loaded.length - 1 : -1; // Start at most recent
    });

    // Initialize with the hash from loaded history if it exists
    const [lastInventoryHash, setLastInventoryHash] = useState<string>(() => {
        const loaded = loadRecipeHistoryFromStorage();
        if (loaded.length > 0) {
            // Use the hash from the most recent cached recipes
            const mostRecentHash = loaded[loaded.length - 1].inventoryHash;
            console.log('[STORAGE] Restored inventory hash from history:', mostRecentHash);
            return mostRecentHash;
        }
        return '';
    });

    // Helper to get current cached recipes
    const cachedRecipes = currentHistoryIndex >= 0 && currentHistoryIndex < recipeHistory.length
        ? recipeHistory[currentHistoryIndex].recipes
        : [];
    const cachedRecipesHash = currentHistoryIndex >= 0 && currentHistoryIndex < recipeHistory.length
        ? recipeHistory[currentHistoryIndex].inventoryHash
        : '';

    // Form states
    const [formData, setFormData] = useState({
        name: '',
        quantity: '',
        unit: 'pieces',
        location: 'pantry' as 'fridge' | 'freezer' | 'pantry' | 'counter',
        category: 'other',
        expiration_date: '',
        notes: ''
    });
    const [submitting, setSubmitting] = useState(false);

    const api = new ApiService(token, logout);

    const generateInventoryHash = useCallback((inventoryData: LocationGroup): string => {
        // Create a simple hash of inventory items to detect changes
        const allItems: InventoryItem[] = [];
        Object.values(inventoryData).forEach(location => {
            allItems.push(...location.items);
        });

        // Sort items by id for consistent hashing
        const sortedItems = allItems.sort((a, b) => a.id.localeCompare(b.id));

        // Create hash string from item names, quantities, and expiration dates
        const hashString = sortedItems.map(item =>
            `${item.name}-${item.quantity}-${item.unit}-${item.expiration_date || ''}`
        ).join('|');

        // Simple hash function (for demo purposes)
        let hash = 0;
        for (let i = 0; i < hashString.length; i++) {
            const char = hashString.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash).toString(36);
    }, []);

    const loadInventory = useCallback(async () => {
        setLoading(true);
        try {
            const data = await api.getInventoryByLocation();
            console.log('[INVENTORY] Loaded inventory:', data);

            // Check if inventory has changed
            const currentHash = generateInventoryHash(data);
            console.log('[INVENTORY] Current hash:', currentHash, '| Last hash:', lastInventoryHash);

            // Only clear history if:
            // 1. We have a previous hash (not first load)
            // 2. The hash has actually changed
            // 3. We have recipe history to clear
            const isFirstLoad = lastInventoryHash === '';
            const hashChanged = currentHash !== lastInventoryHash;

            if (!isFirstLoad && hashChanged && recipeHistory.length > 0) {
                console.log('[INVENTORY] ⚠️ Inventory changed! Clearing recipe history (hash changed from', lastInventoryHash, 'to', currentHash, ')');
                setRecipeHistory([]);
                setCurrentHistoryIndex(-1);
                clearRecipeHistoryFromStorage();
                toast('Inventory updated - recipe suggestions cleared', {
                    icon: 'ℹ️',
                    duration: 3000
                });
            } else if (isFirstLoad && recipeHistory.length > 0) {
                console.log('[INVENTORY] ✅ First load with cached recipes - keeping history');
            } else if (!hashChanged && recipeHistory.length > 0) {
                console.log('[INVENTORY] ✅ Inventory unchanged - keeping recipe history');
            }

            setLastInventoryHash(currentHash);
            setLocationData(data);
        } catch (error: any) {
            console.error('[INVENTORY] Load error:', error);
            toast.error('Failed to load inventory');
        } finally {
            setLoading(false);
        }
    }, [token, lastInventoryHash, recipeHistory.length, generateInventoryHash]);

    useEffect(() => {
        loadInventory();
    }, [loadInventory]);

    // Start user guide on first visit - wait for initialization
    useEffect(() => {
        if (!isInitialized) {
            return; // Wait for guide system to initialize
        }

        // Delay guide start slightly to ensure UI is rendered
        const timer = setTimeout(() => {
            startGuide('inventory');
        }, 1000);

        return () => clearTimeout(timer);
    }, [isInitialized, startGuide]); // Re-run when initialized

    // Show notification if recipes were restored from storage on mount
    useEffect(() => {
        if (recipeHistory.length > 0) {
            const hoursAgo = Math.round((new Date().getTime() - recipeHistory[recipeHistory.length - 1].timestamp.getTime()) / (1000 * 60 * 60));
            const timeText = hoursAgo === 0 ? 'just now' : hoursAgo === 1 ? '1 hour ago' : `${hoursAgo} hours ago`;
            console.log('[STORAGE] ✅ Restored', recipeHistory.length, 'recipe generations from storage (generated', timeText, ')');
            toast.success(`Restored ${recipeHistory.length} recipe list${recipeHistory.length > 1 ? 's' : ''} from earlier! 💾`, { duration: 3000 });
        }
    }, []); // Only run once on mount

    // Save recipe history to localStorage whenever it changes
    useEffect(() => {
        if (recipeHistory.length > 0) {
            saveRecipeHistoryToStorage(recipeHistory);
        }
    }, [recipeHistory]);

    const toggleLocation = (location: string) => {
        const newExpanded = new Set(expandedLocations);
        if (newExpanded.has(location)) {
            newExpanded.delete(location);
        } else {
            newExpanded.add(location);
        }
        setExpandedLocations(newExpanded);
    };

    const handleDelete = async (itemId: string) => {
        if (!window.confirm('Delete this item from inventory?')) return;

        try {
            await api.deleteInventoryItem(itemId);
            toast.success('Item deleted');
            // Clear recipe history when inventory changes
            setRecipeHistory([]);
            setCurrentHistoryIndex(-1);
            clearRecipeHistoryFromStorage();
            await loadInventory();
        } catch (error: any) {
            toast.error('Failed to delete item');
        }
    };

    const handleGenerateRecipes = async (forceRegenerate: boolean = false) => {
        /**
         * NEW AGENT Recipe Generation Flow:
         * 1. Generate 5 recipe briefs at a time
         * 2. Cache briefs for 24 hours or until inventory changes
         * 3. Allow "generate more" up to 5 times (25 total variants)
         * 4. When user clicks a brief, generate full recipe and check for duplicates
         */

        // Calculate current inventory hash
        const currentHash = generateInventoryHash(locationData);
        console.log('[NEW AGENT] Current inventory hash:', currentHash);

        // Check if we have cached recipes for THIS EXACT inventory state
        const isCacheValid = cachedRecipes.length > 0 && cachedRecipesHash === currentHash;

        if (isCacheValid && !forceRegenerate) {
            console.log('[NEW AGENT] Using cached recipes for UNCHANGED inventory');
            setRecipes(cachedRecipes);
            setShowRecipesModal(true);
            toast.success(`Showing ${cachedRecipes.length} recipe ideas from cache! ⚡`);
            return;
        }

        // If cache exists but inventory changed, notify user
        if (cachedRecipes.length > 0 && cachedRecipesHash !== currentHash && !forceRegenerate) {
            console.log('[NEW AGENT] Inventory CHANGED - generating NEW recipes (cache invalidated)');
            toast.success('Inventory changed! Generating fresh recipes... 🔄');
        }

        // Calculate offset for "generate more"
        const currentGeneration = recipeHistory.length;
        const offset = forceRegenerate ? currentGeneration * 5 : 0;

        console.log('[NEW AGENT] Requesting briefs with offset:', offset);

        // Check if we can generate more (max 25 variants = 5 generations)
        if (offset >= 25) {
            toast.error('Maximum recipe variants reached (25). Recipes will refresh after 24 hours or when inventory changes.', { duration: 5000 });
            return;
        }

        setGeneratingRecipes(true);
        try {
            const result = await api.getRecipeBriefsFromInventory({
                offset,
                count: 5
            });

            console.log('[NEW AGENT] ✅ Received briefs:', result);
            console.log('[NEW AGENT] - Total generated:', result.total_generated);
            console.log('[NEW AGENT] - Can generate more:', result.can_generate_more);
            console.log('[NEW AGENT] - Cached:', result.cached);

            // Add to history ONLY if we have actual recipes
            if (result.briefs && result.briefs.length > 0) {
                const newHistoryEntry = {
                    recipes: result.briefs,
                    inventoryHash: currentHash,
                    timestamp: new Date()
                };

                // Keep max 5 generations in history (5 * 5 = 25 recipes)
                const updatedHistory = [...recipeHistory, newHistoryEntry].slice(-5);
                setRecipeHistory(updatedHistory);
                setCurrentHistoryIndex(updatedHistory.length - 1);

                console.log('[NEW AGENT] ✅ Added to history. Total generations:', updatedHistory.length);
            }

            setRecipes(result.briefs || []);
            setShowRecipesModal(true);

            if (result.briefs && result.briefs.length > 0) {
                const message = result.cached
                    ? `Showing ${result.briefs.length} recipes from cache! 💾`
                    : `Generated ${result.briefs.length} new recipe ideas! 🍳`;
                toast.success(message);
            } else {
                toast.error('No recipes generated. Please check your inventory items.', { duration: 4000 });
            }
        } catch (error: any) {
            console.error('[NEW AGENT] ❌ Generation failed:', error);

            // User-friendly error message
            let errorMessage = 'Unable to generate recipes at the moment. Please try again.';
            if (error.message) {
                const msg = error.message.toLowerCase();
                if (msg.includes('throttled')) {
                    errorMessage = 'Rate limit reached. Please wait a moment and try again.';
                } else if (msg.includes('network') || msg.includes('timeout')) {
                    errorMessage = 'Network issue detected. Please check your connection and try again.';
                } else if (msg.includes('no items') || msg.includes('inventory')) {
                    errorMessage = 'Please add items to your inventory first.';
                }
            }

            toast.error(errorMessage, { duration: 6000 });

            // Show cached recipes if available
            if (cachedRecipes.length > 0) {
                console.log('[NEW AGENT] Using cached recipes as fallback');
                setRecipes(cachedRecipes);
                setShowRecipesModal(true);
                toast.success(`Showing ${cachedRecipes.length} recipes from earlier!`);
            } else {
                setRecipes([]);
                setShowRecipesModal(true);
            }
        } finally {
            setGeneratingRecipes(false);
        }
    };

    const handleRecipeClick = async (recipe: RecipeSuggestion) => {
        setCreatingRecipe(recipe.name); // Set the specific recipe being created

        // Helper function for retry with delay
        const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

        const attemptCreateRecipe = async (retryCount: number = 0): Promise<void> => {
            try {
                console.log('[RECIPE CREATE] Starting creation for:', recipe.name);

                // Create the recipe using findRecipe API - it returns the created recipe!
                const createResponse = await api.findRecipe(recipe.name);
                console.log('[RECIPE CREATE] findRecipe response:', createResponse);

                // The API returns: { success, canonical_recipe, user_recipe, created, message }
                if (createResponse.success && createResponse.user_recipe) {
                    console.log('[RECIPE CREATE] ✅ Recipe created successfully!');
                    console.log('[RECIPE CREATE] User recipe ID:', createResponse.user_recipe.id);
                    console.log('[RECIPE CREATE] User recipe name:', createResponse.user_recipe.name);
                    console.log('[RECIPE CREATE] Canonical recipe ID:', createResponse.canonical_recipe?.id);

                    // Use the user_recipe (the fork) which is what shows in "My Recipes"
                    const createdRecipe = createResponse.user_recipe;

                    const statusText = createResponse.created ? 'created' : 'found';
                    toast.success(`Recipe "${createdRecipe.name}" ${statusText} and saved to your library!`);

                    // Close the recipes modal
                    setShowRecipesModal(false);

                    // Navigate to My Recipes page with the recipe ID
                    console.log('[RECIPE CREATE] 🔗 Navigating to My Recipes page with recipe ID:', createdRecipe.id);
                    window.location.href = `/recipes?id=${createdRecipe.id}`;

                } else {
                    console.error('[RECIPE CREATE] ⚠️ Unexpected response format:', createResponse);
                    toast.error('Recipe created but there was an issue displaying it. Check your My Recipes page.');
                    setShowRecipesModal(false);
                }

            } catch (error: any) {
                console.error(`Create recipe error (attempt ${retryCount + 1}):`, error);

                // Check for rate limit error (429)
                if (error.message && error.message.includes('throttled')) {
                    // Extract wait time from error message
                    const match = error.message.match(/(\d+)\s*seconds/);
                    const waitSeconds = match ? parseInt(match[1]) : 0;
                    const waitMinutes = Math.ceil(waitSeconds / 60);

                    console.error(`[RECIPE] ⚠️ Rate limit exceeded. Wait time: ${waitSeconds}s (~${waitMinutes}min)`);

                    const message = waitMinutes > 1
                        ? `Recipe creation limit reached (20/hour). Please wait ${waitMinutes} minutes and try again.`
                        : `Recipe creation limit reached. Please wait a moment and try again.`;

                    toast.error(message, { duration: 8000 });
                    throw error; // Don't retry on rate limit
                }

                // Extract user-friendly error message
                let errorMessage = 'Something went wrong. Please try again.';

                if (error.message) {
                    const msg = error.message.toLowerCase();
                    if (msg.includes('extract') || msg.includes('website') || msg.includes('404')) {
                        errorMessage = 'Unable to find this recipe online. Please try again or try a different recipe.';
                    } else if (msg.includes('network') || msg.includes('timeout')) {
                        errorMessage = 'Network issue detected. Please check your connection and try again.';
                    }
                }

                // Retry logic: Try up to 2 times with increasing delays (but not for rate limits)
                if (retryCount < 2) {
                    const delay = (retryCount + 1) * 1500; // 1.5s, 3s
                    console.log(`[RECIPE] Retrying in ${delay}ms... (attempt ${retryCount + 2}/3)`);
                    toast.loading(`Searching for recipe... Attempt ${retryCount + 2}/3`, { duration: delay });
                    await sleep(delay);
                    return attemptCreateRecipe(retryCount + 1);
                } else {
                    // All retries failed
                    toast.error(errorMessage, { duration: 5000 });
                    throw error;
                }
            }
        };

        try {
            await attemptCreateRecipe();
        } catch (error) {
            // Final catch after all retries failed
            console.error('Create recipe failed after all retries:', error);
        } finally {
            setCreatingRecipe(null); // Clear the creating state
        }
    };

    // Helper functions for recipe actions
    const handleSaveRecipeAction = async (recipe: any) => {
        try {
            await api.saveRecipe(recipe.id);
            toast.success('Recipe saved to your collection!');
            // Update the recipe's saved status
            setSelectedRecipe((prev: any) => prev ? { ...prev, is_saved: true } : null);
        } catch (error: any) {
            console.error('Save error:', error);
            toast.error('Unable to save recipe. Please try again.');
        }
    };

    const handleUnsaveRecipeAction = async (recipe: any) => {
        try {
            await api.unsaveRecipe(recipe.id);
            toast.success('Recipe removed from collection');
            // Update the recipe's saved status
            setSelectedRecipe((prev: any) => prev ? { ...prev, is_saved: false } : null);
        } catch (error: any) {
            console.error('Unsave error:', error);
            toast.error('Unable to remove recipe. Please try again.');
        }
    };

    const handleDownloadRecipeAction = async (recipe: any) => {
        try {
            await api.downloadRCIP(recipe.id, recipe.name);
            toast.success(`Downloaded ${recipe.name}.rcip`);
        } catch (error: any) {
            console.error('Download error:', error);
            toast.error('Unable to download recipe file. Please try again.');
        }
    };

    const resetForm = () => {
        setFormData({
            name: '',
            quantity: '',
            unit: 'pieces',
            location: 'pantry',
            category: 'other',
            expiration_date: '',
            notes: ''
        });
    };

    const handleCreateItem = async () => {
        if (!formData.name.trim()) {
            toast.error('Please enter an item name');
            return;
        }

        if (!formData.quantity || parseFloat(formData.quantity) <= 0) {
            toast.error('Please enter a valid quantity');
            return;
        }

        setSubmitting(true);
        try {
            await api.createInventoryItem({
                name: formData.name.trim(),
                quantity: parseFloat(formData.quantity),
                unit: formData.unit,
                location: formData.location,
                category: formData.category,
                expiration_date: formData.expiration_date || undefined,
                notes: formData.notes.trim() || undefined
            });

            toast.success('Item added to inventory!');
            setShowAddModal(false);
            resetForm();
            // Clear recipe history when inventory changes
            setRecipeHistory([]);
            setCurrentHistoryIndex(-1);
            clearRecipeHistoryFromStorage();
            await loadInventory();
        } catch (error: any) {
            console.error('Create item error:', error);
            toast.error('Failed to add item');
        } finally {
            setSubmitting(false);
        }
    };

    const handleEditItem = async () => {
        if (!editingItem) return;

        if (!formData.name.trim()) {
            toast.error('Please enter an item name');
            return;
        }

        if (!formData.quantity || parseFloat(formData.quantity) <= 0) {
            toast.error('Please enter a valid quantity');
            return;
        }

        setSubmitting(true);
        try {
            await api.updateInventoryItem(editingItem.id, {
                name: formData.name.trim(),
                quantity: parseFloat(formData.quantity),
                unit: formData.unit,
                location: formData.location,
                category: formData.category,
                expiration_date: formData.expiration_date || undefined,
                notes: formData.notes.trim() || undefined
            });

            toast.success('Item updated!');
            setShowEditModal(false);
            setEditingItem(null);
            resetForm();
            // Clear recipe history when inventory changes
            setRecipeHistory([]);
            setCurrentHistoryIndex(-1);
            clearRecipeHistoryFromStorage();
            await loadInventory();
        } catch (error: any) {
            console.error('Update item error:', error);
            toast.error('Failed to update item');
        } finally {
            setSubmitting(false);
        }
    };

    const startEdit = (item: InventoryItem) => {
        setEditingItem(item);
        setFormData({
            name: item.name,
            quantity: item.quantity.toString(),
            unit: item.unit,
            location: item.location,
            category: item.category,
            expiration_date: item.expiration_date || '',
            notes: item.notes || ''
        });
        setShowEditModal(true);
    };

    const handleInputChange = (field: string, value: string) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const getExpiryColor = (status: string) => {
        switch (status) {
            case 'expired':
                return 'text-red-600 bg-red-50 border-red-200';
            case 'urgent':
                return 'text-red-600 bg-red-50 border-red-200';
            case 'warning':
                return 'text-yellow-600 bg-yellow-50 border-yellow-200';
            default:
                return 'text-green-600 bg-green-50 border-green-200';
        }
    };

    const getExpiryLabel = (item: InventoryItem) => {
        if (!item.expiration_date) return '';

        const expiryDate = new Date(item.expiration_date);
        const today = new Date();
        const daysUntilExpiry = Math.floor((expiryDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

        if (daysUntilExpiry < 0) return `🔴 Expired ${Math.abs(daysUntilExpiry)} days ago`;
        if (daysUntilExpiry === 0) return '🔴 Expires today!';
        if (daysUntilExpiry === 1) return '🔴 Expires tomorrow!';
        if (daysUntilExpiry <= 2) return `🔴 Expires in ${daysUntilExpiry} days`;
        if (daysUntilExpiry <= 5) return `🟡 Expires in ${daysUntilExpiry} days`;
        return `🟢 Expires in ${daysUntilExpiry} days`;
    };

    const getLocationIcon = (location: string) => {
        switch (location) {
            case 'freezer':
                return '🧊';
            case 'fridge':
                return '🥶';
            case 'pantry':
                return '📦';
            case 'counter':
                return '🍎';
            default:
                return '📦';
        }
    };

    const getLocationLabel = (location: string) => {
        return t(`inventory.locations.${location}`);
    };

    // Filter items by search query
    const filterItems = (items: InventoryItem[]) => {
        if (!searchQuery) return items;
        const query = searchQuery.toLowerCase();
        return items.filter(item =>
            item.name.toLowerCase().includes(query) ||
            item.category.toLowerCase().includes(query) ||
            item.notes?.toLowerCase().includes(query)
        );
    };

    const totalItems = Object.values(locationData).reduce((sum, loc) => sum + loc.count, 0);
    const totalExpiring = Object.values(locationData).reduce((sum, loc) => sum + loc.expiring_count, 0);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto p-3 sm:p-6">
            {/* Header */}
            <div className="mb-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
                    <div>
                        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
                            <Package className="w-7 h-7 sm:w-8 sm:h-8" />
                            {t('inventory.title')}
                        </h1>
                        <p className="text-gray-600 mt-1">
                            {totalItems} {t('inventory.items')} · {totalExpiring > 0 && (
                                <span className="text-red-600 font-medium" id="expiring-items-section">
                                    ⚠️ {totalExpiring} {t('inventory.expiringSoon')}
                                </span>
                            )}
                        </p>
                    </div>
                    <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 w-full sm:w-auto">
                        <button
                            id="get-recipes-button"
                            onClick={() => handleGenerateRecipes()}
                            disabled={generatingRecipes || totalItems === 0}
                            className="flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 transition disabled:opacity-50 font-medium active:scale-95 w-full sm:w-auto"
                            title={cachedRecipes.length > 0 ? 'Show previous recipe suggestions' : 'Generate recipe suggestions from your inventory'}
                        >
                            <ChefHat className="w-5 h-5" />
                            {generatingRecipes ? t('inventory.generating') : cachedRecipes.length > 0 ? t('inventory.viewRecipes') : t('inventory.getRecipes')}
                        </button>
                        <button
                            id="add-item-button"
                            onClick={() => {
                                resetForm();
                                setShowAddModal(true);
                            }}
                            className="flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition font-medium active:scale-95 w-full sm:w-auto"
                        >
                            <Plus className="w-5 h-5" />
                            {t('inventory.addItem')}
                        </button>
                    </div>
                </div>

                {/* Search */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder={t('inventory.searchPlaceholder')}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                </div>
            </div>

            {/* Location Sections */}
            <div className="space-y-4" id="location-tabs">
                {(['fridge', 'freezer', 'pantry', 'counter'] as const).map(location => {
                    const locData = locationData[location] || { count: 0, expiring_count: 0, items: [] };
                    const filteredItems = filterItems(locData.items);
                    const isExpanded = expandedLocations.has(location);

                    return (
                        <div key={location} className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                            {/* Location Header */}
                            <button
                                onClick={() => toggleLocation(location)}
                                className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition"
                            >
                                <div className="flex items-center gap-3">
                                    <span className="text-3xl">{getLocationIcon(location)}</span>
                                    <div className="text-left">
                                        <h2 className="text-xl font-semibold text-gray-900">
                                            {getLocationLabel(location)}
                                        </h2>
                                        <p className="text-sm text-gray-600">
                                            {locData.count} {t('inventory.items')}
                                            {locData.expiring_count > 0 && (
                                                <span className="ml-2 text-red-600 font-medium">
                                                    ⚠️ {locData.expiring_count} {t('inventory.expiring')}
                                                </span>
                                            )}
                                        </p>
                                    </div>
                                </div>
                                {isExpanded ? (
                                    <ChevronUp className="w-5 h-5 text-gray-400" />
                                ) : (
                                    <ChevronDown className="w-5 h-5 text-gray-400" />
                                )}
                            </button>

                            {/* Location Items */}
                            {isExpanded && (
                                <div className="border-t border-gray-200 p-4">
                                    {filteredItems.length === 0 ? (
                                        <p className="text-center text-gray-500 py-8">
                                            {searchQuery ? t('inventory.noMatchingItems') : t('inventory.noItemsInLocation')}
                                        </p>
                                    ) : (
                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                            {filteredItems.map(item => (
                                                <div
                                                    key={item.id}
                                                    className={`border rounded-lg p-4 ${getExpiryColor(item.expiry_status)}`}
                                                >
                                                    <div className="flex items-start justify-between mb-2">
                                                        <h3 className="font-semibold text-gray-900">{item.name}</h3>
                                                        <div className="flex gap-1">
                                                            <button
                                                                onClick={() => startEdit(item)}
                                                                className="p-1 hover:bg-white/50 rounded transition"
                                                                title={t('inventory.edit')}
                                                            >
                                                                <Edit className="w-4 h-4" />
                                                            </button>
                                                            <button
                                                                onClick={() => handleDelete(item.id)}
                                                                className="p-1 hover:bg-white/50 rounded transition"
                                                                title={t('inventory.delete')}
                                                            >
                                                                <Trash2 className="w-4 h-4" />
                                                            </button>
                                                        </div>
                                                    </div>
                                                    <p className="text-sm font-medium mb-1">
                                                        {item.quantity} {item.unit}
                                                    </p>
                                                    <p className="text-xs text-gray-600 mb-2">
                                                        {item.category}
                                                    </p>
                                                    {item.expiration_date && (
                                                        <p className="text-sm font-medium">
                                                            {getExpiryLabel(item)}
                                                        </p>
                                                    )}
                                                    {item.notes && (
                                                        <p className="text-xs text-gray-600 mt-2 italic">
                                                            {item.notes}
                                                        </p>
                                                    )}
                                                    {item.is_low_stock && (
                                                        <p className="text-xs text-orange-600 mt-2 font-medium">
                                                            ⚠️ {t('inventory.lowStock')}
                                                        </p>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Recipe Suggestions Modal */}
            {showRecipesModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="sticky top-0 bg-white border-b p-6">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                                        <ChefHat className="w-6 h-6" />
                                        Recipe Suggestions
                                    </h2>
                                    {recipeHistory.length > 0 && (
                                        <span className="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full font-medium">
                                            Generation {currentHistoryIndex + 1} of {recipeHistory.length}
                                        </span>
                                    )}
                                </div>
                                <button
                                    onClick={() => setShowRecipesModal(false)}
                                    className="p-2 hover:bg-gray-100 rounded-lg transition"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Important Notice - Always visible at top */}
                            <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 p-4 rounded-lg mb-4">
                                <Info className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                                <div className="flex-1">
                                    <h3 className="font-semibold text-amber-900 mb-1">
                                        💡 Quick Recipe Ideas (Cached for 24 hours)
                                    </h3>
                                    <p className="text-sm text-amber-800">
                                        These are brief recipe ideas based on your current inventory.
                                        They're cached for 24 hours or until your inventory changes.
                                        <strong className="font-semibold"> To create a full recipe, click on any idea below</strong> - the system will
                                        check if the recipe already exists or generate a new one and save it to your "My Recipes" collection.
                                        <br />
                                        <br />
                                        <strong className="font-semibold">💡 Tip:</strong> Don't like these options? Click "Generate More" to get 5 additional ideas (up to 25 total).
                                        If you don't save a recipe you like, it will disappear after 24 hours or when inventory changes!
                                    </p>
                                </div>
                            </div>

                            {/* History Navigation */}
                            {recipeHistory.length > 1 && (
                                <div className="flex items-center justify-between gap-4 bg-gradient-to-r from-indigo-50 to-purple-50 p-4 rounded-lg mb-4">
                                    <button
                                        onClick={() => {
                                            const newIndex = currentHistoryIndex - 1;
                                            setCurrentHistoryIndex(newIndex);
                                            setRecipes(recipeHistory[newIndex].recipes);
                                            toast.success('Showing previous generation');
                                        }}
                                        disabled={currentHistoryIndex <= 0}
                                        className="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-50 transition disabled:opacity-40 disabled:cursor-not-allowed font-medium"
                                    >
                                        <ChevronDown className="w-4 h-4 rotate-90" />
                                        Previous List
                                    </button>

                                    <div className="text-center">
                                        <div className="text-sm text-gray-600">Browse your generated recipe lists</div>
                                        {recipeHistory[currentHistoryIndex]?.timestamp && (
                                            <div className="text-xs text-gray-500 mt-1">
                                                Generated: {new Date(recipeHistory[currentHistoryIndex].timestamp).toLocaleTimeString()}
                                            </div>
                                        )}
                                    </div>

                                    <button
                                        onClick={() => {
                                            const newIndex = currentHistoryIndex + 1;
                                            setCurrentHistoryIndex(newIndex);
                                            setRecipes(recipeHistory[newIndex].recipes);
                                            toast.success('Showing next generation');
                                        }}
                                        disabled={currentHistoryIndex >= recipeHistory.length - 1}
                                        className="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 rounded-lg hover:bg-gray-50 transition disabled:opacity-40 disabled:cursor-not-allowed font-medium"
                                    >
                                        Next List
                                        <ChevronDown className="w-4 h-4 -rotate-90" />
                                    </button>
                                </div>
                            )}
                            {/* Generate New button - only show if we have cached recipes */}
                            {cachedRecipes.length > 0 && (
                                <div className="flex items-center gap-2 bg-blue-50 p-3 rounded-lg">
                                    <div className="flex-1 text-sm text-blue-800">
                                        💡 Not satisfied with these suggestions? Generate fresh recipes from your current inventory.
                                    </div>
                                    <button
                                        onClick={async () => {
                                            setShowRecipesModal(false);
                                            toast.success('Generating fresh recipes!');
                                            // Force regeneration with forceRegenerate flag
                                            await handleGenerateRecipes(true);
                                        }}
                                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-medium whitespace-nowrap"
                                    >
                                        <RefreshCw className="w-4 h-4" />
                                        Generate New
                                    </button>
                                </div>
                            )}
                        </div>

                        <div className="p-6 pt-0 space-y-6">
                            {recipes.length === 0 ? (
                                <p className="text-center text-gray-500 py-8">
                                    No recipes generated. Try adding more items to your inventory.
                                </p>
                            ) : (
                                recipes.map((recipe, index) => (
                                    <div
                                        key={index}
                                        className={`border rounded-lg p-6 ${recipe.priority === 'urgent'
                                            ? 'border-red-300 bg-red-50'
                                            : recipe.priority === 'high'
                                                ? 'border-yellow-300 bg-yellow-50'
                                                : 'border-gray-200 bg-white'
                                            }`}
                                    >
                                        <div className="flex items-start justify-between mb-4">
                                            <div>
                                                <h3 className="text-xl font-bold text-gray-900">
                                                    {recipe.name}
                                                </h3>
                                                {recipe.priority === 'urgent' && (
                                                    <span className="inline-flex items-center gap-1 text-sm text-red-600 font-medium mt-1">
                                                        <AlertTriangle className="w-4 h-4" />
                                                        URGENT: Uses expiring items!
                                                    </span>
                                                )}
                                            </div>
                                            <div className="text-right">
                                                <p className="text-sm text-gray-600 flex items-center gap-1">
                                                    <Clock className="w-4 h-4" />
                                                    {recipe.cooking_time}
                                                </p>
                                                <p className="text-sm text-gray-600 capitalize">
                                                    {recipe.difficulty}
                                                </p>
                                            </div>
                                        </div>

                                        <p className="text-gray-700 mb-4">
                                            {recipe.description}
                                        </p>

                                        <div className="mb-4">
                                            <h4 className="font-semibold text-gray-900 mb-2">
                                                Main Ingredients:
                                            </h4>
                                            <ul className="text-sm text-gray-700 space-y-1">
                                                {(recipe.main_ingredients || []).map((ing, idx) => (
                                                    <li key={idx}>
                                                        ✓ {ing}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>

                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-4 text-sm text-gray-700 bg-gray-50 p-3 rounded-lg flex-1">
                                                <span>⏱️ {recipe.cook_time_minutes || recipe.cooking_time || 'N/A'} min</span>
                                                <span>📊 {recipe.difficulty}</span>
                                                {recipe.cuisine && <span>🌍 {recipe.cuisine}</span>}
                                            </div>
                                            <div className="flex items-center gap-2 ml-4">
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        toast.success('Recipe will be saved to your collection!');
                                                    }}
                                                    className="px-3 py-2 bg-pink-100 text-pink-600 rounded-lg hover:bg-pink-200 transition font-medium flex items-center gap-2"
                                                    title="Like this recipe"
                                                >
                                                    <Heart className="w-4 h-4" />
                                                </button>
                                                <button
                                                    onClick={() => handleRecipeClick(recipe)}
                                                    disabled={creatingRecipe !== null}
                                                    className={`px-4 py-2 bg-indigo-600 text-white rounded-lg transition font-medium flex items-center gap-2 ${creatingRecipe === recipe.name
                                                        ? 'opacity-50 cursor-not-allowed'
                                                        : creatingRecipe !== null
                                                            ? 'cursor-not-allowed'
                                                            : 'hover:bg-indigo-700'
                                                        }`}
                                                >
                                                    <Eye className="w-4 h-4" />
                                                    {creatingRecipe === recipe.name ? 'Creating...' : 'View Recipe'}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Add Item Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl max-w-md w-full">
                        <div className="border-b p-6 flex items-center justify-between">
                            <h2 className="text-xl font-bold text-gray-900">{t('inventory.addNewItem')}</h2>
                            <button
                                onClick={() => setShowAddModal(false)}
                                className="p-2 hover:bg-gray-100 rounded-lg transition"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('inventory.itemName')} *
                                </label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => handleInputChange('name', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder={t('inventory.itemNamePlaceholder')}
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        {t('inventory.quantity')} *
                                    </label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        value={formData.quantity}
                                        onChange={(e) => handleInputChange('quantity', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="1"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        {t('inventory.unit')}
                                    </label>
                                    <select
                                        value={formData.unit}
                                        onChange={(e) => handleInputChange('unit', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="pieces">{t('inventory.units.pieces')}</option>
                                        <option value="g">{t('inventory.units.g')}</option>
                                        <option value="kg">{t('inventory.units.kg')}</option>
                                        <option value="ml">{t('inventory.units.ml')}</option>
                                        <option value="L">{t('inventory.units.L')}</option>
                                        <option value="cups">{t('inventory.units.cups')}</option>
                                        <option value="tbsp">{t('inventory.units.tbsp')}</option>
                                        <option value="tsp">{t('inventory.units.tsp')}</option>
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        {t('inventory.location')}
                                    </label>
                                    <select
                                        value={formData.location}
                                        onChange={(e) => handleInputChange('location', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="pantry">{t('inventory.locations.pantry')}</option>
                                        <option value="fridge">{t('inventory.locations.fridge')}</option>
                                        <option value="freezer">{t('inventory.locations.freezer')}</option>
                                        <option value="counter">{t('inventory.locations.counter')}</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        {t('inventory.category')}
                                    </label>
                                    <select
                                        value={formData.category}
                                        onChange={(e) => handleInputChange('category', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="other">{t('inventory.categories.other')}</option>
                                        <option value="dairy">{t('inventory.categories.dairy')}</option>
                                        <option value="meat">{t('inventory.categories.meat')}</option>
                                        <option value="vegetables">{t('inventory.categories.vegetables')}</option>
                                        <option value="fruits">{t('inventory.categories.fruits')}</option>
                                        <option value="grains">{t('inventory.categories.grains')}</option>
                                        <option value="canned">{t('inventory.categories.canned')}</option>
                                        <option value="spices">{t('inventory.categories.spices')}</option>
                                        <option value="snacks">{t('inventory.categories.snacks')}</option>
                                        <option value="beverages">{t('inventory.categories.beverages')}</option>
                                        <option value="frozen">{t('inventory.categories.frozen')}</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('inventory.expirationDate')}
                                </label>
                                <input
                                    type="date"
                                    value={formData.expiration_date}
                                    onChange={(e) => handleInputChange('expiration_date', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('inventory.notes')}
                                </label>
                                <textarea
                                    value={formData.notes}
                                    onChange={(e) => handleInputChange('notes', e.target.value)}
                                    rows={3}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder={t('inventory.notesPlaceholder')}
                                />
                            </div>

                            <div className="flex gap-3 pt-4">
                                <button
                                    onClick={() => setShowAddModal(false)}
                                    className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
                                >
                                    {t('inventory.cancel')}
                                </button>
                                <button
                                    onClick={handleCreateItem}
                                    disabled={submitting}
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 font-medium"
                                >
                                    {submitting ? t('inventory.adding') : t('inventory.addItem')}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Edit Item Modal */}
            {showEditModal && editingItem && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl max-w-md w-full">
                        <div className="border-b p-6 flex items-center justify-between">
                            <h2 className="text-xl font-bold text-gray-900">{t('inventory.editItem')}</h2>
                            <button
                                onClick={() => setShowEditModal(false)}
                                className="p-2 hover:bg-gray-100 rounded-lg transition"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Item Name *
                                </label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => handleInputChange('name', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        {t('inventory.quantity')} *
                                    </label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        value={formData.quantity}
                                        onChange={(e) => handleInputChange('quantity', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        {t('inventory.unit')}
                                    </label>
                                    <select
                                        value={formData.unit}
                                        onChange={(e) => handleInputChange('unit', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="pieces">{t('inventory.units.pieces')}</option>
                                        <option value="g">{t('inventory.units.g')}</option>
                                        <option value="kg">{t('inventory.units.kg')}</option>
                                        <option value="ml">{t('inventory.units.ml')}</option>
                                        <option value="L">{t('inventory.units.L')}</option>
                                        <option value="cups">{t('inventory.units.cups')}</option>
                                        <option value="tbsp">{t('inventory.units.tbsp')}</option>
                                        <option value="tsp">{t('inventory.units.tsp')}</option>
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        {t('inventory.location')}
                                    </label>
                                    <select
                                        value={formData.location}
                                        onChange={(e) => handleInputChange('location', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="pantry">{t('inventory.locations.pantry')}</option>
                                        <option value="fridge">{t('inventory.locations.fridge')}</option>
                                        <option value="freezer">{t('inventory.locations.freezer')}</option>
                                        <option value="counter">{t('inventory.locations.counter')}</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        {t('inventory.category')}
                                    </label>
                                    <select
                                        value={formData.category}
                                        onChange={(e) => handleInputChange('category', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="other">{t('inventory.categories.other')}</option>
                                        <option value="dairy">{t('inventory.categories.dairy')}</option>
                                        <option value="meat">{t('inventory.categories.meat')}</option>
                                        <option value="vegetables">{t('inventory.categories.vegetables')}</option>
                                        <option value="fruits">{t('inventory.categories.fruits')}</option>
                                        <option value="grains">{t('inventory.categories.grains')}</option>
                                        <option value="canned">{t('inventory.categories.canned')}</option>
                                        <option value="spices">{t('inventory.categories.spices')}</option>
                                        <option value="snacks">{t('inventory.categories.snacks')}</option>
                                        <option value="beverages">{t('inventory.categories.beverages')}</option>
                                        <option value="frozen">{t('inventory.categories.frozen')}</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('inventory.expirationDate')}
                                </label>
                                <input
                                    type="date"
                                    value={formData.expiration_date}
                                    onChange={(e) => handleInputChange('expiration_date', e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('inventory.notes')}
                                </label>
                                <textarea
                                    value={formData.notes}
                                    onChange={(e) => handleInputChange('notes', e.target.value)}
                                    rows={3}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div className="flex gap-3 pt-4">
                                <button
                                    onClick={() => setShowEditModal(false)}
                                    className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
                                >
                                    {t('inventory.cancel')}
                                </button>
                                <button
                                    onClick={handleEditItem}
                                    disabled={submitting}
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 font-medium"
                                >
                                    <Save className="w-4 h-4 mr-2" />
                                    {submitting ? t('inventory.updating') : t('inventory.updateItem')}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Recipe Detail Modal */}
            {showRecipeDetailModal && selectedRecipe && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="sticky top-0 bg-white border-b p-6 flex items-center justify-between">
                            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                                <ChefHat className="w-6 h-6" />
                                {selectedRecipe.name}
                            </h2>
                            <button
                                onClick={() => setShowRecipeDetailModal(false)}
                                className="p-2 hover:bg-gray-100 rounded-lg transition"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="p-6">
                            <div className="grid md:grid-cols-2 gap-6 mb-6">
                                {/* Ingredients */}
                                <div>
                                    <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                                        🥘 Ingredients
                                    </h3>
                                    <div className="space-y-2">
                                        {selectedRecipe.ingredients?.map((ing: any, idx: number) => (
                                            <div key={idx} className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded">
                                                <div className="flex-1">
                                                    <div>
                                                        <span className="font-semibold text-indigo-600">
                                                            {ing.human_amount || `${ing.amount || ''} ${ing.unit || ''}`.trim()}
                                                        </span>
                                                        {' '}
                                                        <span>{ing.name}</span>
                                                    </div>
                                                    {ing.notes && (
                                                        <p className="text-xs text-gray-500 mt-1">{ing.notes}</p>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Instructions */}
                                <div>
                                    <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                                        📝 Instructions
                                    </h3>
                                    <div className="space-y-4">
                                        {selectedRecipe.steps?.map((step: any, idx: number) => (
                                            <div key={idx} className="flex gap-3">
                                                <div className="flex-shrink-0 w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center font-bold">
                                                    {idx + 1}
                                                </div>
                                                <div className="flex-1">
                                                    <p className="text-gray-700">{step.human_text || step.instruction}</p>
                                                    {step.params && (
                                                        <div className="flex gap-2 mt-2">
                                                            {step.params.time_minutes && (
                                                                <span className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded">
                                                                    ⏱️ {step.params.time_minutes}m
                                                                </span>
                                                            )}
                                                            {step.params.temperature_c && (
                                                                <span className="text-xs px-2 py-1 bg-orange-50 text-orange-700 rounded">
                                                                    🌡️ {step.params.temperature_c}°C
                                                                </span>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Recipe Meta */}
                            <div className="bg-gray-50 p-4 rounded-lg mb-6">
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                    {selectedRecipe.total_time_minutes && (
                                        <div className="flex items-center gap-2">
                                            <Clock className="w-4 h-4 text-gray-600" />
                                            <span>{selectedRecipe.total_time_minutes}m total</span>
                                        </div>
                                    )}
                                    {selectedRecipe.servings && (
                                        <div className="flex items-center gap-2">
                                            <Users className="w-4 h-4 text-gray-600" />
                                            <span>{selectedRecipe.servings} servings</span>
                                        </div>
                                    )}
                                    <div className="flex items-center gap-2">
                                        <span className="capitalize">{selectedRecipe.difficulty}</span>
                                    </div>
                                    {selectedRecipe.cuisine && (
                                        <div className="flex items-center gap-2">
                                            <span>{selectedRecipe.cuisine}</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Source URL */}
                            {selectedRecipe.source_url && (
                                <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                                    <div className="flex items-center gap-2">
                                        <ExternalLink className="w-4 h-4 text-gray-600" />
                                        <strong className="text-sm text-gray-700">Source:</strong>
                                        <a
                                            href={selectedRecipe.source_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-indigo-600 hover:underline text-sm"
                                        >
                                            {selectedRecipe.source_url}
                                        </a>
                                    </div>
                                </div>
                            )}

                            {/* Actions */}
                            <div className="flex gap-3 pt-4">
                                <button
                                    onClick={() => {
                                        // Like the recipe (save to my recipes)
                                        if (selectedRecipe.is_saved) {
                                            handleUnsaveRecipeAction(selectedRecipe);
                                        } else {
                                            handleSaveRecipeAction(selectedRecipe);
                                        }
                                    }}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition font-medium ${selectedRecipe.is_saved
                                        ? 'bg-red-600 text-white hover:bg-red-700'
                                        : 'bg-indigo-600 text-white hover:bg-indigo-700'
                                        }`}
                                >
                                    <Heart className={`w-4 h-4 ${selectedRecipe.is_saved ? 'fill-current' : ''}`} />
                                    {selectedRecipe.is_saved ? 'Remove from Collection' : 'Save to My Recipes'}
                                </button>

                                <button
                                    onClick={() => {
                                        // Download RCIP file
                                        handleDownloadRecipeAction(selectedRecipe);
                                    }}
                                    className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                                >
                                    <Download className="w-4 h-4" />
                                    Download .rcip
                                </button>

                                <button
                                    onClick={() => {
                                        setShowRecipeDetailModal(false);
                                        setShowRecipesModal(true);
                                    }}
                                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition font-medium"
                                >
                                    Try Another Recipe
                                </button>

                                <button
                                    onClick={() => setShowRecipeDetailModal(false)}
                                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
                                >
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Inventory;
