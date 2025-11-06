import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useCollaboration } from '../contexts/CollaborationContext';
import { useUserGuide } from '../contexts/UserGuideContext';
import ApiService from '../services/api';
import CollaboratorManager from '../components/CollaboratorManager';
import DeleteConfirmationModal from '../components/DeleteConfirmationModal';
import LeaveConfirmationModal from '../components/LeaveConfirmationModal';
import { toast } from 'react-hot-toast';
import { formatWeight, formatVolume, parseWeightInput, parseVolumeInput } from '../utils/unitConversion';
import { getUserFriendlyError } from '../utils/errorHandler';
import { Package, X, Check } from 'lucide-react';
import { LockedFeature } from '../components/LockedFeature';  // NEW: Import LockedFeature

const ShoppingList: React.FC = () => {
    const { t, i18n } = useTranslation();
    const { token, user, logout } = useAuth();
    const { startGuide, isInitialized } = useUserGuide();
    const {
        connectToList,
        disconnect,
        isConnected,
        typingUsers,
        onItemAdded,
        onItemToggled,
        onItemUpdated,
        onItemDeleted,
        onItemsBatchAdded,
        onQuantityTypeChanged,
        onListDeleted,
        onListAccessGranted,
        sendTyping,
        sendCustomMessage,
        wsConnectionId,
        loadCollaborators,
        collaborators
    } = useCollaboration();
    
    // NEW: Check shopping access status
    const [accessStatus, setAccessStatus] = useState<any>(null);
    const [accessLoading, setAccessLoading] = useState(true);
    
    const [lists, setLists] = useState<any[]>([]);
    const [activeList, setActiveList] = useState<any>(null);
    const [items, setItems] = useState<any[]>([]);
    // Track which quantity type is active for each item: 'weight', 'liquid', or 'none'
    const [activeQuantityType, setActiveQuantityType] = useState<Map<string, 'weight' | 'liquid' | 'none'>>(new Map());
    const [newItem, setNewItem] = useState('');
    const [aiInput, setAiInput] = useState('');
    const [loading, setLoading] = useState(false);

    // Load generated recipes from localStorage on mount
    const [generatedRecipes, setGeneratedRecipes] = useState<Array<{
        id: string;
        canonicalId: string;
        name: string;
        query: string;
        timestamp: Date;
        isGenerating?: boolean;
        isNew?: boolean;
    }>>([]);

    // State for AI messages (separate from shopping items)
    const [aiMessages, setAiMessages] = useState<Array<{
        id: string;
        text: string;
        timestamp: Date;
        type: 'info' | 'success' | 'warning';
    }>>([]);

    // Helper function to translate units
    const translateUnit = useCallback((unit: string): string => {
        const unitLower = unit.toLowerCase().trim();

        // Map common unit variations to translation keys
        const unitMapping: { [key: string]: string } = {
            'piece': 'pieces',
            'pieces': 'pieces',
            'unit': 'pieces',
            'units': 'pieces',
            'g': 'g',
            'gram': 'g',
            'grams': 'g',
            'kg': 'kg',
            'kilogram': 'kg',
            'kilograms': 'kg',
            'ml': 'ml',
            'milliliter': 'ml',
            'milliliters': 'ml',
            'l': 'L',
            'liter': 'L',
            'liters': 'L',
            'cup': 'cups',
            'cups': 'cups',
            'tbsp': 'tbsp',
            'tablespoon': 'tbsp',
            'tablespoons': 'tbsp',
            'tsp': 'tsp',
            'teaspoon': 'tsp',
            'teaspoons': 'tsp'
        };

        const mappedKey = unitMapping[unitLower] || unitLower;
        const translatedUnit = t(`inventory.units.${mappedKey}`, { defaultValue: unit });

        return translatedUnit;
    }, [t]);
    const [typingTimeout, setTypingTimeout] = useState<NodeJS.Timeout | null>(null);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [newListName, setNewListName] = useState('');
    const [deleteModal, setDeleteModal] = useState<{
        isOpen: boolean;
        listId: string;
        listName: string;
        countdown: number;
        isDeleting: boolean;
    }>({
        isOpen: false,
        listId: '',
        listName: '',
        countdown: 5,
        isDeleting: false
    });

    const [leaveModal, setLeaveModal] = useState<{
        isOpen: boolean;
        listId: string;
        listName: string;
        countdown: number;
        isLeaving: boolean;
    }>({
        isOpen: false,
        listId: '',
        listName: '',
        countdown: 5,
        isLeaving: false
    });

    // Inventory transfer states
    const [showInventoryModal, setShowInventoryModal] = useState(false);
    const [inventorySuggestions, setInventorySuggestions] = useState<any[]>([]);
    const [showRecipeSuggestions, setShowRecipeSuggestions] = useState(false);
    const [recipeSuggestions, setRecipeSuggestions] = useState<string[]>([]);
    const [failedRecipeQuery, setFailedRecipeQuery] = useState('');
    const [loadingInventory, setLoadingInventory] = useState(false);

    // Create API service with useMemo to prevent recreation on every render
    const api = useMemo(() => {
        console.log('🔧 Creating new API service with token:', token?.substring(0, 20) + '...');
        return new ApiService(token, () => {
            console.log('🔐 Token expired - logging out user');
            toast.error('Your session has expired. Please log in again.');
            logout();
        });
    }, [token, logout]);


    // Load user preferences function
    const loadUserPreferences = useCallback(async () => {
        try {
            const response = await api.get('/users/profile/user_settings/');
            setUserPreferences({
                weight_unit: response.weight_unit || 'kg',
                volume_unit: response.volume_unit || 'liters',
                time_format: response.time_format || '24h'
            });
        } catch (error) {
            console.error('Failed to load user preferences:', error);
            // Use defaults if loading fails
        }
    }, [api]);

    // NEW: Check shopping access on mount
    useEffect(() => {
        const checkAccess = async () => {
            try {
                const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
                const response = await fetch(`${apiUrl}/api/users/shopping-access-status/`, {
                    headers: {'Authorization': `Bearer ${token}`}
                });
                const data = await response.json();
                setAccessStatus(data);
            } catch (error) {
                console.error('Failed to check shopping access:', error);
                setAccessStatus({ available: false, message: 'Failed to check access' });
            } finally {
                setAccessLoading(false);
            }
        };
        checkAccess();
    }, [token]);

    // Load lists and user preferences on initial mount
    useEffect(() => {
        const loadLists = async () => {
            try {
                console.log('📋 Loading shopping lists (direct call)...');
                const data = await api.getShoppingLists();
                setLists(data.results || data);
            } catch (error) {
                console.error('❌ Load lists error:', error);
            }
        };

        loadLists();
        loadUserPreferences();
    }, [api, loadUserPreferences]);

    // Start user guide on first visit - wait for initialization
    useEffect(() => {
        if (!isInitialized) {
            return; // Wait for guide system to initialize
        }

        // Delay guide start slightly to ensure UI is rendered
        const timer = setTimeout(() => {
            startGuide('shopping');
        }, 1000);

        return () => clearTimeout(timer);
    }, [isInitialized, startGuide]); // Re-run when initialized

    // Save generated recipes to localStorage whenever they change
    // Load recipes specific to the active list (SHARED by all collaborators)
    useEffect(() => {
        if (activeList?.id) {
            try {
                const saved = localStorage.getItem(`generatedRecipes_${activeList.id}`);
                if (saved) {
                    const parsed = JSON.parse(saved);
                    // Convert timestamp strings back to Date objects
                    const recipes = parsed.map((recipe: any) => ({
                        ...recipe,
                        timestamp: new Date(recipe.timestamp)
                    }));
                    console.log(`📚 Loading ${recipes.length} recipes for list: ${activeList.id}`);
                    setGeneratedRecipes(recipes);
                } else {
                    console.log(`📚 No saved recipes for list: ${activeList.id}`);
                    // Clear recipes if switching to a list with no saved recipes
                    setGeneratedRecipes([]);
                }
            } catch (error) {
                console.error('Failed to load generated recipes from localStorage:', error);
                setGeneratedRecipes([]);
            }
        } else {
            // Clear recipes when no active list
            console.log('📚 No active list, clearing recipes');
            setGeneratedRecipes([]);
        }
    }, [activeList?.id]);

    // Save recipes specific to the active list (SHARED by all collaborators)
    useEffect(() => {
        if (activeList?.id && generatedRecipes.length > 0) {
            try {
                localStorage.setItem(`generatedRecipes_${activeList.id}`, JSON.stringify(generatedRecipes));
            } catch (error) {
                console.error('Failed to save generated recipes to localStorage:', error);
            }
        }
    }, [generatedRecipes, activeList?.id]);

    // Store stable references to prevent useEffect loops
    const connectToListRef = useRef(connectToList);
    const disconnectRef = useRef(disconnect);
    const apiRef = useRef(api);

    // Update refs when values change
    useEffect(() => {
        connectToListRef.current = connectToList;
        disconnectRef.current = disconnect;
        apiRef.current = api;
    }, [connectToList, disconnect, api]);

    useEffect(() => {
        const loadActiveListData = async () => {
            if (activeList && activeList.id) {
                console.log(`📋 Loading fresh data for active list: ${activeList.name} (${activeList.id})`);

                try {
                    // Get fresh data for the specific list to ensure we have the latest items
                    const freshListData = await apiRef.current.get(`/shopping/lists/${activeList.id}/`);

                    // Update the specific list in the lists array
                    setLists(prevLists =>
                        prevLists.map(list =>
                            list.id === activeList.id ? freshListData : list
                        )
                    );

                    const freshList = freshListData;

                    if (freshList) {
                        // Convert string values to numbers for weight and liquid quantities
                        const processedItems = (Array.isArray(freshList.items) ? freshList.items : []).map((item: any) => ({
                            ...item,
                            weight_quantity: parseFloat(item.weight_quantity) || 0,
                            liquid_quantity: parseFloat(item.liquid_quantity) || 0,
                        }));

                        console.log('📋 Setting items with fresh server data:', processedItems);
                        setItems(processedItems);
                    } else {
                        console.warn('📋 Active list not found in fresh data, using cached items');
                        // Fallback to cached data
                        const processedItems = (Array.isArray(activeList.items) ? activeList.items : []).map((item: any) => ({
                            ...item,
                            weight_quantity: parseFloat(item.weight_quantity) || 0,
                            liquid_quantity: parseFloat(item.liquid_quantity) || 0,
                        }));
                        setItems(processedItems);
                    }
                } catch (error) {
                    console.error('📋 Failed to load fresh list data, using cached items:', error);
                    // Fallback to cached data
                    const processedItems = (Array.isArray(activeList.items) ? activeList.items : []).map((item: any) => ({
                        ...item,
                        weight_quantity: parseFloat(item.weight_quantity) || 0,
                        liquid_quantity: parseFloat(item.liquid_quantity) || 0,
                    }));
                    setItems(processedItems);
                }

                // Connect to WebSocket for real-time collaboration
                if (activeList.is_collaborative && activeList.id) {
                    console.log(`🔗 Attempting to connect to WebSocket for list: ${activeList.id}`);
                    connectToListRef.current(activeList.id);
                }
            } else {
                console.log(`🔗 No active list, disconnecting WebSocket`);
                disconnectRef.current();
            }
        };

        loadActiveListData();

        return () => {
            console.log(`🔗 useEffect cleanup - disconnecting WebSocket`);
            disconnectRef.current();
        };
    }, [activeList?.id, activeList?.is_collaborative]); // Only depend on specific properties that matter for connection

    // Quantity type helper functions (declared before useEffect to avoid dependency issues)
    const getActiveQuantityType = useCallback((itemId: string): 'weight' | 'liquid' | 'none' => {
        return activeQuantityType.get(itemId) || 'none';
    }, [activeQuantityType]);

    const setQuantityType = useCallback((itemId: string, type: 'weight' | 'liquid' | 'none') => {
        setActiveQuantityType(prev => {
            const newMap = new Map(prev);
            newMap.set(itemId, type);
            return newMap;
        });
    }, []);

    // Set up real-time event handlers
    useEffect(() => {
        // Only set up handlers if we have an active collaborative list with a valid ID
        if (!activeList || !activeList.id || !activeList.is_collaborative) {
            console.log('⚠️ Skipping WebSocket setup:', {
                hasActiveList: !!activeList,
                hasId: !!(activeList?.id),
                isCollaborative: activeList?.is_collaborative
            });
            return;
        }

        console.log('🔄 Setting up WebSocket event handlers for list:', activeList.id);

        const handleItemAdded = (data: any) => {
            console.log('📦 Item added via WebSocket:', data);
            console.log('📦 [AUTO-COUNTER] Checking item for auto-enable:');
            console.log('📦 [AUTO-COUNTER] - auto_enable_counter:', data.item?.auto_enable_counter);
            console.log('📦 [AUTO-COUNTER] - weight_quantity:', data.item?.weight_quantity);
            console.log('📦 [AUTO-COUNTER] - liquid_quantity:', data.item?.liquid_quantity);

            setItems(prev => {
                // Avoid duplicates
                const exists = prev.some(item => item.id === data.item.id);
                if (exists) return prev;
                return [...prev, data.item];
            });

            // Auto-enable counter if flag is set
            if (data.item?.auto_enable_counter) {
                console.log(`📦 [AUTO-COUNTER] ✅ Auto-enabling ${data.item.auto_enable_counter} counter for item: ${data.item.name}`);
                setQuantityType(data.item.id, data.item.auto_enable_counter);
            } else if (data.item?.weight_quantity > 0) {
                console.log(`📦 [AUTO-COUNTER] ✅ Auto-enabling weight counter (inferred from weight_quantity=${data.item.weight_quantity})`);
                setQuantityType(data.item.id, 'weight');
            } else if (data.item?.liquid_quantity > 0) {
                console.log(`📦 [AUTO-COUNTER] ✅ Auto-enabling liquid counter (inferred from liquid_quantity=${data.item.liquid_quantity})`);
                setQuantityType(data.item.id, 'liquid');
            } else {
                console.log(`📦 [AUTO-COUNTER] ℹ️ No auto-counter needed for: ${data.item.name}`);
            }

            toast.success(`"${data.item.name}" added to list`);
        };

        const handleItemToggled = (data: any) => {
            console.log('📡 Item toggled via WebSocket:', data);
            setItems(prev => {
                const newItems = prev.map(item =>
                    item.id === data.item.id ? { ...item, ...data.item } : item
                );
                return newItems;
            });
            // Clear the toggling state for this item
            setIsToggling(prev => {
                const newSet = new Set(prev);
                newSet.delete(data.item.id);
                return newSet;
            });
        };

        const handleItemUpdated = (data: any) => {
            console.log('📦 Item updated via WebSocket:', data);
            console.log('📦 Updated item data:', data.item);
            console.log('📦 Weight quantity in update:', data.item.weight_quantity, typeof data.item.weight_quantity);
            console.log('📦 Liquid quantity in update:', data.item.liquid_quantity, typeof data.item.liquid_quantity);

            // Check if this update is from the current user to prevent auto-switching on own updates
            const isMyUpdate = data.updated_by?.username === user?.username || data.updated_by?.id === user?.id;
            console.log('📦 Is this my own update?', isMyUpdate, 'Updated by:', data.updated_by?.username, 'My username:', user?.username);

            setItems(prevItems => {
                const newItems = prevItems.map(item => {
                    if (item.id === data.item.id) {
                        // Convert string values to numbers if needed
                        const updatedItemData = { ...data.item };
                        if (updatedItemData.weight_quantity !== undefined) {
                            updatedItemData.weight_quantity = parseFloat(updatedItemData.weight_quantity) || 0;
                        }
                        if (updatedItemData.liquid_quantity !== undefined) {
                            updatedItemData.liquid_quantity = parseFloat(updatedItemData.liquid_quantity) || 0;
                        }

                        const updatedItem = { ...item, ...updatedItemData };
                        console.log('📦 Item before update:', item);
                        console.log('📦 Item after update:', updatedItem);
                        console.log('📦 Weight after conversion:', updatedItem.weight_quantity, typeof updatedItem.weight_quantity);
                        console.log('📦 Liquid after conversion:', updatedItem.liquid_quantity, typeof updatedItem.liquid_quantity);

                        // Only auto-enable counters for updates from OTHER users, not my own updates
                        if (!isMyUpdate) {
                            const currentToggleState = getActiveQuantityType(item.id);

                            // Check which fields were actually updated by comparing old vs new values
                            const weightWasUpdated = item.weight_quantity !== updatedItem.weight_quantity;
                            const liquidWasUpdated = item.liquid_quantity !== updatedItem.liquid_quantity;

                            console.log('📦 Update analysis:', {
                                weightWasUpdated,
                                liquidWasUpdated,
                                oldWeight: item.weight_quantity,
                                newWeight: updatedItem.weight_quantity,
                                oldLiquid: item.liquid_quantity,
                                newLiquid: updatedItem.liquid_quantity,
                                currentToggleState
                            });

                            // Only auto-switch if the updated field has new data and user isn't already tracking it
                            if (weightWasUpdated && (updatedItem.weight_quantity || 0) > 0 && currentToggleState !== 'weight') {
                                console.log('🔄 Auto-enabling weight counter due to weight UPDATE from other user:', updatedItem.name);
                                setQuantityType(item.id, 'weight');
                            }
                            else if (liquidWasUpdated && (updatedItem.liquid_quantity || 0) > 0 && currentToggleState !== 'liquid') {
                                console.log('🔄 Auto-enabling liquid counter due to liquid UPDATE from other user:', updatedItem.name);
                                setQuantityType(item.id, 'liquid');
                            }
                        } else {
                            console.log('📦 Skipping auto-switch for my own update to avoid unwanted toggling');
                        }

                        return updatedItem;
                    }
                    return item;
                });
                return newItems;
            });
            // Clear the updating states for this item
            setIsUpdatingQuantity(prev => {
                const newSet = new Set(prev);
                newSet.delete(data.item.id);
                return newSet;
            });
            setIsUpdatingWeight(prev => {
                const newSet = new Set(prev);
                newSet.delete(data.item.id);
                return newSet;
            });
            setIsUpdatingLiquid(prev => {
                const newSet = new Set(prev);
                newSet.delete(data.item.id);
                return newSet;
            });
        };

        const handleItemDeleted = (data: any) => {
            console.log('🗑️ Item deleted via WebSocket:', data);

            // Find the item name before removing it
            const deletedItem = items.find(item => item.id === data.item_id);
            const itemName = deletedItem?.name || 'Item';

            // Remove item from state
            setItems(prev => prev.filter(item => item.id !== data.item_id));

            // Show notification if deleted by someone else
            if (data.deleted_by?.username !== user?.username) {
                toast.success(`${data.deleted_by?.username || 'Someone'} removed "${itemName}"`);
            }
        };

        const handleQuantityTypeChanged = (data: any) => {
            console.log('🔄 Quantity type changed via WebSocket:', data);
            const { item_id, item_name, quantity_type, changed_by } = data;

            // Update the quantity type for this item
            setQuantityType(item_id, quantity_type);

            // Show notification to user
            const typeText = quantity_type === 'none' ? 'disabled quantity tracking'
                : quantity_type === 'weight' ? 'enabled weight tracking'
                    : 'enabled liquid tracking';

            toast(`${changed_by} ${typeText} for "${item_name}"`, {
                duration: 3000,
                icon: quantity_type === 'weight' ? '📊' : quantity_type === 'liquid' ? '🥤' : '🔢'
            });
        };

        const handleItemsBatchAdded = (data: any) => {
            console.log('📦 Batch items added via WebSocket (AI recipe):', data);
            if (data.items && Array.isArray(data.items)) {
                setItems(prev => {
                    // Filter out any items that already exist
                    const existingIds = new Set(prev.map(item => item.id));
                    const newItems = data.items.filter((item: any) => !existingIds.has(item.id));
                    if (newItems.length > 0) {
                        toast.success(`${data.user} added ${newItems.length} ingredients from a recipe`);

                        // Auto-enable counters ONLY for items with weight or liquid
                        newItems.forEach((item: any) => {
                            // Only enable counter if item has weight or liquid data
                            if (item.auto_enable_counter === 'weight' || (item.weight_quantity && item.weight_quantity > 0)) {
                                console.log(`🔓 Auto-enabling weight counter for ${item.name}`);
                                setQuantityType(item.id, 'weight');
                            } else if (item.auto_enable_counter === 'liquid' || (item.liquid_quantity && item.liquid_quantity > 0)) {
                                console.log(`🔓 Auto-enabling liquid counter for ${item.name}`);
                                setQuantityType(item.id, 'liquid');
                            }
                            // Otherwise leave as 'none' (default) - button will show "Enable"
                        });

                        return [...prev, ...newItems];
                    }
                    return prev;
                });
            }
        };

        // Removed unused handleItemDeleted function

        const handleListDeleted = (data: any) => {
            console.log('📋 🔴 LIST DELETED HANDLER CALLED 🔴');
            console.log('📋 List deleted via WebSocket:', data);

            // Generate unique ID for this handler call to track it
            const handlerCallId = `${Date.now()}_${Math.random()}`;
            console.log(`📋 Handler call ID: ${handlerCallId}`);

            // Prevent duplicate notifications - use a global flag with the list ID
            const notificationKey = `list_deleted_${data.list_id}`;
            if ((window as any)[notificationKey]) {
                console.error(`❌❌❌ DUPLICATE DETECTED! Already showed notification for list ${data.list_id}`);
                console.error(`❌ This is duplicate call #${((window as any)[notificationKey + '_count'] || 1) + 1}`);
                (window as any)[notificationKey + '_count'] = ((window as any)[notificationKey + '_count'] || 1) + 1;
                return;
            }
            (window as any)[notificationKey] = true;
            (window as any)[notificationKey + '_count'] = 1;
            console.log(`✅ First notification for list ${data.list_id} - showing toast`);

            // Clear the flag after 3 seconds to allow future notifications
            setTimeout(() => {
                delete (window as any)[notificationKey];
                delete (window as any)[notificationKey + '_count'];
            }, 3000);

            // Check if current user was the creator
            const isCreator = data.deleted_by.id === lists.find(list => list.id === data.list_id)?.creator?.id;

            if (isCreator) {
                toast.error(`List "${data.list_name}" has been moved to archive`);
            } else {
                // For participants, provide guidance about list transfer
                toast.error(`List "${data.list_name}" was archived by ${data.deleted_by.username}. Check Archive to see if ownership has been transferred.`);
            }

            // If the deleted list is currently active, clear it
            if (activeList && activeList.id === data.list_id) {
                console.log('📋 Current active list was deleted, clearing and disconnecting');
                setActiveList(null);
                setItems([]);
                disconnect();
            }

            // Always reload the lists to remove the deleted one from active lists
            setTimeout(async () => {
                try {
                    const data = await api.getShoppingLists();
                    setLists(data.results || data);
                    console.log('📋 Lists refreshed after list deletion');

                    // Trigger custom event to notify archive page
                    window.dispatchEvent(new CustomEvent('listsChanged', {
                        detail: { type: 'list_deleted', data }
                    }));
                } catch (error) {
                    console.error('Failed to reload lists:', error);
                }
            }, 500);
        };

        const handleListAccessGranted = (data: any) => {
            console.log('🎉 List access granted via WebSocket:', data);
            toast.success(`You have been added to "${data.list.name}" by ${data.invited_by.username}`);

            // Reload the shopping lists to include the new one
            setTimeout(async () => {
                try {
                    const listsData = await api.getShoppingLists();
                    setLists(listsData.results || listsData);
                    console.log('📋 Lists refreshed after gaining access to new list');
                } catch (error) {
                    console.error('Failed to reload lists after access granted:', error);
                }
            }, 500);
        };

        // Register event handlers and get cleanup functions
        const cleanupItemAdded = onItemAdded(handleItemAdded);
        const cleanupItemToggled = onItemToggled(handleItemToggled);
        const cleanupItemUpdated = onItemUpdated(handleItemUpdated);
        const cleanupItemDeleted = onItemDeleted(handleItemDeleted);
        const cleanupItemsBatchAdded = onItemsBatchAdded(handleItemsBatchAdded);
        const cleanupQuantityTypeChanged = onQuantityTypeChanged(handleQuantityTypeChanged);
        const cleanupListDeleted = onListDeleted(handleListDeleted);
        const cleanupListAccessGranted = onListAccessGranted(handleListAccessGranted);

        // Return cleanup function
        return () => {
            console.log('🧹 Cleaning up WebSocket event handlers');
            if (cleanupItemAdded) cleanupItemAdded();
            if (cleanupItemToggled) cleanupItemToggled();
            if (cleanupItemUpdated) cleanupItemUpdated();
            if (cleanupItemDeleted) cleanupItemDeleted();
            if (cleanupItemsBatchAdded) cleanupItemsBatchAdded();
            if (cleanupQuantityTypeChanged) cleanupQuantityTypeChanged();
            if (cleanupListDeleted) cleanupListDeleted();
            if (cleanupListAccessGranted) cleanupListAccessGranted();
        };
    }, [activeList, onItemAdded, onItemToggled, onItemUpdated, onItemDeleted, onItemsBatchAdded, onQuantityTypeChanged, onListDeleted, onListAccessGranted, wsConnectionId, api, disconnect, lists, getActiveQuantityType, setQuantityType]); // Depend on activeList, handlers, and connection changes

    // Cleanup intervals on unmount
    useEffect(() => {
        return () => {
            if ((window as any).deleteCountdownInterval) {
                clearInterval((window as any).deleteCountdownInterval);
                delete (window as any).deleteCountdownInterval;
            }
            if ((window as any).leaveCountdownInterval) {
                clearInterval((window as any).leaveCountdownInterval);
                delete (window as any).leaveCountdownInterval;
            }
        };
    }, []);

    // Check for new lists when user returns to the page
    useEffect(() => {
        const handleVisibilityChange = async () => {
            if (!document.hidden) {
                console.log('👀 Page became visible, checking for new lists...');
                try {
                    const data = await api.getShoppingLists();
                    const newLists = data.results || data;

                    // Check if we have more lists than before
                    if (newLists.length > lists.length) {
                        console.log('📋 Found new lists, updating...');
                        setLists(newLists);

                        // Show a subtle notification about new lists
                        const newListsCount = newLists.length - lists.length;
                        if (newListsCount > 0) {
                            toast.success(`You have ${newListsCount} new shared list${newListsCount > 1 ? 's' : ''}`);
                        }
                    } else {
                        setLists(newLists);
                    }
                } catch (error) {
                    console.error('Failed to check for new lists:', error);
                }
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);

        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
        };
    }, [api, lists.length]);

    // Listen for real-time list changes from user notification WebSocket
    useEffect(() => {
        const handleListsChanged = async (event: any) => {
            const { type, data } = event.detail;
            console.log('🔔 Received listsChanged event:', type, data);

            if (type === 'access_granted') {
                // User was added to a new list - refresh the lists
                try {
                    const listsData = await api.getShoppingLists();
                    setLists(listsData.results || listsData);
                    console.log('📋 Lists refreshed after gaining access to new list');
                } catch (error) {
                    console.error('Failed to reload lists after access granted:', error);
                }
            } else if (type === 'participant_left') {
                // Someone left a list - might need to refresh if it's the current list
                if (activeList && activeList.id === data.list_id) {
                    // Refresh collaborators for current list
                    try {
                        loadCollaborators(activeList.id);
                    } catch (error) {
                        console.error('Failed to refresh collaborators:', error);
                    }
                }
            } else if (type === 'ownership_transferred') {
                // Ownership was transferred - refresh lists
                try {
                    const listsData = await api.getShoppingLists();
                    setLists(listsData.results || listsData);
                    console.log('📋 Lists refreshed after ownership transfer');

                    // If the transferred list was the active list, clear it since it's now in archive
                    if (activeList && activeList.id === data.list.id) {
                        console.log('📋 Active list ownership transferred, clearing active list');
                        setActiveList(null);
                        setItems([]);
                        disconnect();
                    }
                } catch (error) {
                    console.error('Failed to reload lists after ownership transfer:', error);
                }
            } else if (type === 'collaborator_added') {
                // Collaborator was added - refresh lists to update participant counts
                try {
                    const listsData = await api.getShoppingLists();
                    setLists(listsData.results || listsData);
                    console.log('📋 Lists refreshed after collaborator added');
                } catch (error) {
                    console.error('Failed to reload lists after collaborator added:', error);
                }
            }
        };

        window.addEventListener('listsChanged', handleListsChanged);

        return () => {
            window.removeEventListener('listsChanged', handleListsChanged);
        };
    }, [api, activeList, loadCollaborators, disconnect]);

    // Listen for recipe completion events
    useEffect(() => {
        const handleRecipeCompleted = (event: any) => {
            const { recipe_name, canonical_recipe_id } = event.detail;
            console.log('🎉 Recipe completed:', recipe_name, canonical_recipe_id);

            // Update the generatedRecipes state:
            // - If recipe has canonicalId, mark as complete
            // - If recipe doesn't have canonicalId (temp ID), update with real ID and mark complete
            setGeneratedRecipes(prev =>
                prev.map(recipe => {
                    // Match by existing canonical ID OR by name if it's a generating recipe
                    if (recipe.canonicalId === canonical_recipe_id ||
                        (recipe.isGenerating && recipe.name === recipe_name)) {
                        return {
                            ...recipe,
                            isGenerating: false,
                            canonicalId: canonical_recipe_id,  // Update with real ID
                            id: canonical_recipe_id  // Update main ID too
                        };
                    }
                    return recipe;
                })
            );

            // Show success notification
            toast.success(
                `🎉 Full recipe for "${recipe_name}" is ready! View it in your recipes.`,
                { duration: 6000 }
            );
        };

        window.addEventListener('recipeCompleted', handleRecipeCompleted);

        return () => {
            window.removeEventListener('recipeCompleted', handleRecipeCompleted);
        };
    }, []);

    const handleAddItem = async () => {
        console.log('🛒 Attempting to add item:', {
            newItem: newItem.trim(),
            activeList: activeList,
            activeListId: activeList?.id,
            hasActiveList: !!activeList,
            hasActiveListId: !!activeList?.id
        });

        if (!newItem.trim() || !activeList || !activeList.id) {
            console.log('❌ Cannot add item - missing requirements:', {
                hasNewItem: !!newItem.trim(),
                hasActiveList: !!activeList,
                hasActiveListId: !!activeList?.id
            });
            toast.error('Please select a list first');
            return;
        }

        try {
            console.log('📤 Adding item via WebSocket to list:', activeList.id);

            // Send via WebSocket for real-time collaboration
            console.log('🔍 WebSocket status check:', {
                isConnected,
                hasSendCustomMessage: !!sendCustomMessage,
                activeListId: activeList.id,
                activeListCollaborative: activeList.is_collaborative
            });
            if (isConnected && sendCustomMessage) {
                sendCustomMessage({
                    type: 'add_item',
                    item: {
                        name: newItem,
                        quantity: 1,
                        weight_quantity: 0,
                        liquid_quantity: 0,
                        unit: 'unit',
                        category: 'other'
                    }
                });
                console.log('📡 Item add message sent via WebSocket');
                setNewItem('');
                // Don't show success toast here - wait for WebSocket confirmation
            } else {
                // Fallback to HTTP API if WebSocket not connected
                console.log('📤 WebSocket not connected, falling back to HTTP API');
                const response = await api.addItemToList(activeList.id, {
                    name: newItem,
                    quantity: 1,
                    unit: 'unit',
                    category: 'other'
                });
                console.log('✅ Item added successfully via HTTP:', response);
                setItems([...items, response]);
                setNewItem('');
                toast.success(`"${newItem}" added to list`);
            }
        } catch (error) {
            console.error('❌ Add item error:', error);
            const errorMessage = getUserFriendlyError(error);
            toast.error(errorMessage);
        }
    };

    const handleAiAddItems = async () => {
        if (!aiInput.trim() || !activeList) return;

        setLoading(true);
        const currentQuery = aiInput; // Store before clearing
        try {
            console.log('[MULTILANG AI] Starting AI add items request...');
            const response = await api.aiAddItems(activeList.id, aiInput);
            console.log('[MULTILANG AI] Received response:', response);
            console.log('[MULTILANG AI] 🔑 canonical_recipe_id:', response.canonical_recipe_id);

            if (response.success) {
                // NEW: Handle fast recipe response
                const recipeName = response.recipe_name || currentQuery;
                const recipeNameTranslations = response.recipe_name_translations || {};
                const isGenerating = response.is_generating || false;
                const isNew = response.is_new || false;

                console.log('[MULTILANG AI] Recipe name translations:', recipeNameTranslations);
                console.log('[MULTILANG AI] Is generating:', isGenerating);
                console.log('[MULTILANG AI] Is new:', isNew);

                // Add new items to state (from items_created)
                const newItems = response.items_created || response.new_items || response.items || [];
                const updatedItems = response.items_updated || [];

                console.log('[MULTILANG AI] New items received:', newItems.length);
                console.log('[MULTILANG AI] First item sample:', newItems[0]);

                // Merge updated items with existing items
                const updatedItemsMap = new Map(updatedItems.map((item: any) => [item.id, item]));
                const mergedItems = items.map(item =>
                    updatedItemsMap.has(item.id) ? updatedItemsMap.get(item.id) : item
                );

                setItems([...mergedItems, ...newItems]);

                // Auto-enable counters ONLY for items with weight or liquid
                newItems.forEach((item: any) => {
                    console.log(`🔍 Checking auto-enable for: ${item.name}`, {
                        auto_enable_counter: item.auto_enable_counter,
                        weight_quantity: item.weight_quantity,
                        liquid_quantity: item.liquid_quantity
                    });

                    // Only enable counter if item has weight or liquid data
                    if (item.auto_enable_counter === 'weight' || (item.weight_quantity && item.weight_quantity > 0)) {
                        console.log(`🔓 Auto-enabling weight counter for ${item.name}`);
                        setQuantityType(item.id, 'weight');
                    } else if (item.auto_enable_counter === 'liquid' || (item.liquid_quantity && item.liquid_quantity > 0)) {
                        console.log(`🔓 Auto-enabling liquid counter for ${item.name}`);
                        setQuantityType(item.id, 'liquid');
                    }
                    // Otherwise leave as 'none' (default) - button will show "Enable"
                });

                // Show appropriate toast message
                if (isNew && isGenerating) {
                    toast.success(
                        `✅ Added ${newItems.length} ingredients from "${recipeName}"\n🔄 Full recipe generating in background...`,
                        { duration: 5000 }
                    );
                } else if (isNew) {
                    toast.success(`✅ Added ${newItems.length} ingredients from "${recipeName}"`);
                } else {
                    toast.success(`✅ Added ingredients from existing recipe "${recipeName}"`);
                }

                // Store recipe link for display (with generation status)
                // Always add to generatedRecipes, even if canonical_recipe_id is null (for new recipes)
                // SIMPLE DEDUPLICATION: Check if recipe already exists by name or canonical ID
                const newRecipeLink = {
                    id: response.canonical_recipe_id || `temp_${Date.now()}`,  // Temporary ID for new recipes
                    canonicalId: response.canonical_recipe_id || null,
                    name: recipeName,
                    query: currentQuery,
                    timestamp: new Date(),
                    isGenerating: isGenerating,
                    isNew: isNew
                };

                console.log('[MULTILANG AI] 📚 Creating recipe link:', newRecipeLink);

                // Simple duplicate check: skip if recipe with same canonicalId or name already exists
                setGeneratedRecipes(prev => {
                    const isDuplicate = prev.some(existing =>
                        (newRecipeLink.canonicalId && existing.canonicalId === newRecipeLink.canonicalId) ||
                        (existing.name.toLowerCase() === newRecipeLink.name.toLowerCase())
                    );

                    if (isDuplicate) {
                        console.log(`🔁 Recipe "${recipeName}" already in list, skipping duplicate`);
                        return prev;
                    }

                    return [newRecipeLink, ...prev]; // Add to beginning
                });

                setAiInput('');
            }
        } catch (error: any) {
            console.error('AI add error:', error);

            // Check if error includes suggestions (404 with suggestions)
            if (error?.response?.status === 404 && error?.response?.data?.show_suggestions) {
                const errorData = error.response.data;
                setFailedRecipeQuery(errorData.failed_query || currentQuery);
                setRecipeSuggestions(errorData.suggestions || []);
                setShowRecipeSuggestions(true);
            } else {
                toast.error('Failed to add recipe ingredients');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleSuggestionClick = async (suggestion: string) => {
        setShowRecipeSuggestions(false);
        setAiInput(suggestion);
        // Auto-trigger search with the suggestion
        setTimeout(() => {
            handleAiAddItems();
        }, 100);
    };

    const [isToggling, setIsToggling] = useState<Set<string>>(new Set());
    const [isDeleting, setIsDeleting] = useState<Set<string>>(new Set());
    const [isUpdatingQuantity, setIsUpdatingQuantity] = useState<Set<string>>(new Set());
    const [isUpdatingWeight, setIsUpdatingWeight] = useState<Set<string>>(new Set());
    const [isUpdatingLiquid, setIsUpdatingLiquid] = useState<Set<string>>(new Set());

    // Track which quantity type is active for each item: 'weight', 'liquid', or 'none'
    const [userPreferences, setUserPreferences] = useState<{
        weight_unit: 'kg' | 'lbs';
        volume_unit: 'liters' | 'gallons';
        time_format: '24h' | '12h';
    }>({
        weight_unit: 'kg',
        volume_unit: 'liters',
        time_format: '24h'
    });

    const handleToggleItem = async (itemId: string) => {
        // Prevent multiple rapid toggles of the same item
        if (isToggling.has(itemId)) {
            console.log('🚫 Already toggling item', itemId, 'ignoring...');
            return;
        }

        try {
            setIsToggling(prev => new Set(prev).add(itemId));
            console.log('🔄 Frontend: Toggling item via WebSocket', itemId);

            // Send via WebSocket for real-time collaboration
            if (isConnected && sendCustomMessage) {
                sendCustomMessage({
                    type: 'toggle_item',
                    item_id: itemId
                });
                console.log('📡 Item toggle message sent via WebSocket');
                // Don't update UI here - wait for WebSocket response
            } else {
                // Fallback to HTTP API if WebSocket not connected
                console.log('📤 WebSocket not connected, falling back to HTTP API');

                // Optimistically update UI immediately
                setItems(prev => prev.map(item =>
                    item.id === itemId
                        ? { ...item, is_completed: !item.is_completed }
                        : item
                ));

                const response = await api.toggleItem(itemId);
                console.log('✅ Frontend: Toggle API call successful', response);

                // Update with server response to ensure consistency
                setItems(prev => prev.map(item =>
                    item.id === itemId ? response : item
                ));
            }

        } catch (error) {
            console.error('❌ Frontend: Toggle error:', error);
            // Revert optimistic update on error
            setItems(prev => prev.map(item =>
                item.id === itemId
                    ? { ...item, is_completed: !item.is_completed }
                    : item
            ));
        } finally {
            setIsToggling(prev => {
                const newSet = new Set(prev);
                newSet.delete(itemId);
                return newSet;
            });
        }
    };

    const handleDeleteItem = async (itemId: string, itemName: string) => {
        // Prevent multiple rapid deletions of the same item
        if (isDeleting.has(itemId)) {
            console.log('🚫 Already deleting item', itemId, 'ignoring...');
            return;
        }

        try {
            setIsDeleting(prev => new Set(prev).add(itemId));
            console.log('🗑️ Deleting item:', itemName);

            // Optimistically remove from UI immediately
            setItems(prev => prev.filter(item => item.id !== itemId));

            // Call delete API
            await api.deleteItem(itemId);

            toast.success(`"${itemName}" removed from list`);
            console.log('✅ Item deleted successfully');

        } catch (error) {
            console.error('❌ Delete item error:', error);
            const errorMessage = getUserFriendlyError(error);
            toast.error(errorMessage);

            // Revert optimistic update on error - reload items
            if (activeList?.id) {
                const data = await api.getShoppingLists();
                const currentList = (data.results || data).find((list: any) => list.id === activeList.id);
                if (currentList) {
                    setItems(currentList.items || []);
                }
            }
        } finally {
            setIsDeleting(prev => {
                const newSet = new Set(prev);
                newSet.delete(itemId);
                return newSet;
            });
        }
    };

    const handleUpdateQuantity = async (itemId: string, newQuantity: number, itemName: string) => {
        // Prevent multiple rapid updates of the same item
        if (isUpdatingQuantity.has(itemId) || newQuantity <= 0) {
            return;
        }

        try {
            setIsUpdatingQuantity(prev => new Set(prev).add(itemId));
            console.log('📊 Updating quantity via WebSocket for item:', itemName, 'to:', newQuantity);

            // Send via WebSocket for real-time collaboration
            if (isConnected && sendCustomMessage) {
                sendCustomMessage({
                    type: 'update_item',
                    item: {
                        id: itemId,
                        quantity: newQuantity
                    }
                });
                console.log('📡 Item quantity update message sent via WebSocket');
                // Don't update UI here - wait for WebSocket response
            } else {
                // Fallback to HTTP API if WebSocket not connected
                console.log('📤 WebSocket not connected, falling back to HTTP API');

                // Optimistically update UI immediately
                setItems(prev => prev.map(item =>
                    item.id === itemId
                        ? { ...item, quantity: newQuantity }
                        : item
                ));

                // Call update API (use PATCH for partial updates)
                await api.patch(`/shopping/items/${itemId}/`, {
                    quantity: newQuantity
                });

                console.log('✅ Quantity updated successfully via HTTP');
            }

        } catch (error) {
            console.error('❌ Update quantity error:', error);

            // Revert optimistic update on error - reload items
            if (activeList?.id) {
                const data = await api.getShoppingLists();
                const currentList = (data.results || data).find((list: any) => list.id === activeList.id);
                if (currentList) {
                    setItems(currentList.items || []);
                }
            }
        } finally {
            setIsUpdatingQuantity(prev => {
                const newSet = new Set(prev);
                newSet.delete(itemId);
                return newSet;
            });
        }
    };

    const handleQuantityChange = (itemId: string, delta: number, itemName: string) => {
        const item = items.find(i => i.id === itemId);
        if (!item) return;

        const newQuantity = Math.max(1, (parseFloat(item.quantity) || 1) + delta);
        handleUpdateQuantity(itemId, newQuantity, itemName);
    };

    const handleQuantityInput = (itemId: string, value: string, itemName: string) => {
        const numValue = parseFloat(value);
        if (!isNaN(numValue) && numValue > 0) {
            handleUpdateQuantity(itemId, numValue, itemName);
        }
    };

    // Weight quantity handlers
    const handleUpdateWeightQuantity = async (itemId: string, newWeight: number, itemName: string) => {
        console.log('📊 handleUpdateWeightQuantity called:', { itemId, newWeight, itemName });
        console.log('📊 Current isUpdatingWeight state:', Array.from(isUpdatingWeight));

        if (isUpdatingWeight.has(itemId)) {
            console.log('📊 Already updating weight for this item, skipping');
            return;
        }

        if (newWeight < 0) {
            console.log('📊 Negative weight value, skipping');
            return;
        }

        try {
            setIsUpdatingWeight(prev => new Set(prev).add(itemId));
            console.log('📊 Updating weight quantity for item:', itemName, 'to:', newWeight, 'grams');

            // Send via WebSocket for real-time collaboration
            if (isConnected && sendCustomMessage) {
                sendCustomMessage({
                    type: 'update_item',
                    item: {
                        id: itemId,
                        weight_quantity: newWeight
                    }
                });
                console.log('📡 Item weight update message sent via WebSocket');
                // Don't update UI here - wait for WebSocket response
            } else {
                // Fallback to HTTP API if WebSocket not connected
                console.log('📤 WebSocket not connected, falling back to HTTP API');

                // Optimistically update UI immediately
                setItems(prev => prev.map(item =>
                    item.id === itemId
                        ? { ...item, weight_quantity: newWeight }
                        : item
                ));
                console.log('📊 UI updated optimistically');

                // Call update API
                console.log('📊 Making API call to update weight quantity...');
                const result = await api.updateWeightQuantity(itemId, newWeight);
                console.log('📊 API response:', result);

                console.log('✅ Weight quantity updated successfully via HTTP');
            }

        } catch (error) {
            console.error('❌ Update weight quantity error:', error);
            console.error('❌ Error details:', error instanceof Error ? error.message : error);

            // Revert optimistic update on error - reload items
            if (activeList?.id) {
                const data = await api.getShoppingLists();
                const currentList = (data.results || data).find((list: any) => list.id === activeList.id);
                if (currentList) {
                    setItems(currentList.items || []);
                }
            }
        } finally {
            setIsUpdatingWeight(prev => {
                const newSet = new Set(prev);
                newSet.delete(itemId);
                return newSet;
            });
            console.log('📊 Weight update finally block executed');
        }
    };

    const handleWeightQuantityInput = (itemId: string, value: string, itemName: string) => {
        const grams = parseWeightInput(value, userPreferences.weight_unit);
        if (grams >= 0) {
            handleUpdateWeightQuantity(itemId, grams, itemName);
        }
    };

    const handleWeightQuantityChange = (itemId: string, delta: number, itemName: string) => {
        console.log('📊 Weight quantity change clicked:', { itemId, delta, itemName });

        const item = items.find(i => i.id === itemId);
        if (!item) {
            console.error('❌ Item not found for weight update:', itemId);
            return;
        }

        const currentWeight = item.weight_quantity || 0;
        console.log('📊 Current weight:', currentWeight, 'User unit:', userPreferences.weight_unit);

        // Determine increment based on user's preferred unit
        let increment = 100; // 100g default
        if (userPreferences.weight_unit === 'lbs') {
            increment = 113.4; // ~0.25 lbs in grams
        }

        const newWeight = Math.max(0, currentWeight + (delta * increment));
        console.log('📊 New weight will be:', newWeight, 'grams');

        handleUpdateWeightQuantity(itemId, newWeight, itemName);
    };

    // Liquid quantity handlers
    const handleUpdateLiquidQuantity = async (itemId: string, newLiquid: number, itemName: string) => {
        console.log('🥤 handleUpdateLiquidQuantity called:', { itemId, newLiquid, itemName });
        console.log('🥤 Current isUpdatingLiquid state:', Array.from(isUpdatingLiquid));

        if (isUpdatingLiquid.has(itemId)) {
            console.log('🥤 Already updating liquid for this item, skipping');
            return;
        }

        if (newLiquid < 0) {
            console.log('🥤 Negative liquid value, skipping');
            return;
        }

        try {
            setIsUpdatingLiquid(prev => new Set(prev).add(itemId));
            console.log('🥤 Updating liquid quantity for item:', itemName, 'to:', newLiquid, 'ml');

            // Send via WebSocket for real-time collaboration
            if (isConnected && sendCustomMessage) {
                sendCustomMessage({
                    type: 'update_item',
                    item: {
                        id: itemId,
                        liquid_quantity: newLiquid
                    }
                });
                console.log('📡 Item liquid update message sent via WebSocket');
                // Don't update UI here - wait for WebSocket response
            } else {
                // Fallback to HTTP API if WebSocket not connected
                console.log('📤 WebSocket not connected, falling back to HTTP API');

                // Optimistically update UI immediately
                setItems(prev => prev.map(item =>
                    item.id === itemId
                        ? { ...item, liquid_quantity: newLiquid }
                        : item
                ));
                console.log('🥤 UI updated optimistically');

                // Call update API
                console.log('🥤 Making API call to update liquid quantity...');
                const result = await api.updateLiquidQuantity(itemId, newLiquid);
                console.log('🥤 API response:', result);

                console.log('✅ Liquid quantity updated successfully via HTTP');
            }

        } catch (error) {
            console.error('❌ Update liquid quantity error:', error);
            console.error('❌ Error details:', error instanceof Error ? error.message : error);

            // Revert optimistic update on error - reload items
            if (activeList?.id) {
                const data = await api.getShoppingLists();
                const currentList = (data.results || data).find((list: any) => list.id === activeList.id);
                if (currentList) {
                    setItems(currentList.items || []);
                }
            }
        } finally {
            setIsUpdatingLiquid(prev => {
                const newSet = new Set(prev);
                newSet.delete(itemId);
                return newSet;
            });
            console.log('🥤 Liquid update finally block executed');
        }
    };

    const handleLiquidQuantityInput = (itemId: string, value: string, itemName: string) => {
        const ml = parseVolumeInput(value, userPreferences.volume_unit);
        if (ml >= 0) {
            handleUpdateLiquidQuantity(itemId, ml, itemName);
        }
    };

    const handleLiquidQuantityChange = (itemId: string, delta: number, itemName: string) => {
        console.log('🥤 Liquid quantity change clicked:', { itemId, delta, itemName });

        const item = items.find(i => i.id === itemId);
        if (!item) {
            console.error('❌ Item not found for liquid update:', itemId);
            return;
        }

        const currentLiquid = item.liquid_quantity || 0;
        console.log('🥤 Current liquid:', currentLiquid, 'User unit:', userPreferences.volume_unit);

        // Determine increment based on user's preferred unit
        let increment = 100; // 100ml default
        if (userPreferences.volume_unit === 'gallons') {
            increment = 236.6; // ~0.5 cups in ml (1/16 gallon)
        }

        const newLiquid = Math.max(0, currentLiquid + (delta * increment));
        console.log('🥤 New liquid will be:', newLiquid, 'ml');

        handleUpdateLiquidQuantity(itemId, newLiquid, itemName);
    };

    const handleInputChange = (value: string, setter: (value: string) => void) => {
        setter(value);

        // Send typing indicator
        if (isConnected) {
            sendTyping(true);

            // Clear previous timeout
            if (typingTimeout) {
                clearTimeout(typingTimeout);
            }

            // Set new timeout to stop typing indicator
            const timeout = setTimeout(() => {
                sendTyping(false);
            }, 1000);

            setTypingTimeout(timeout);
        }
    };

    const handleCreateList = async () => {
        if (!newListName.trim()) return;

        try {
            console.log('🆕 Creating new list:', newListName);
            const response = await api.createShoppingList({
                name: newListName,
                is_collaborative: true
            });
            console.log('✅ List created:', response);

            // Reload lists manually to get the updated list
            const data = await api.getShoppingLists();
            setLists(data.results || data);

            // Set the newly created list as active
            console.log('🎯 Setting new list as active:', response);

            // Ensure the response has the proper structure for activeList
            const newActiveList = {
                ...response,
                items: response.items || [], // Ensure items array exists
                user_permissions: response.user_permissions || {
                    can_edit: true,
                    can_add_items: true,
                    can_invite_others: true
                }
            };

            setActiveList(newActiveList);
            setItems([]); // Clear items for the new list

            // Clear form
            setNewListName('');
            setShowCreateForm(false);

            toast.success(`"${newListName}" created successfully!`);
        } catch (error) {
            console.error('Create list error:', error);
            const errorMessage = getUserFriendlyError(error);
            toast.error(errorMessage);
        }
    };

    const handleDeleteList = (listId: string, listName: string) => {
        console.log('🗑️ Starting delete process for list:', { listId, listName });

        // Prevent multiple delete processes
        if (deleteModal.isOpen) {
            console.log('❌ Delete modal already open, ignoring');
            return;
        }

        // Clear any existing interval first
        if ((window as any).deleteCountdownInterval) {
            clearInterval((window as any).deleteCountdownInterval);
            delete (window as any).deleteCountdownInterval;
        }

        setDeleteModal({
            isOpen: true,
            listId,
            listName,
            countdown: 5,
            isDeleting: false
        });

        // Start countdown timer with the listId in closure
        const interval = setInterval(() => {
            setDeleteModal(prev => {
                const newCountdown = prev.countdown - 1;
                if (newCountdown <= 0) {
                    clearInterval(interval);
                    // Auto-confirm deletion with the correct listId and listName
                    confirmDeleteListWithId(listId, listName);
                    return { ...prev, isOpen: false, countdown: 5 };
                }
                return { ...prev, countdown: newCountdown };
            });
        }, 1000);

        // Store interval ID for cleanup
        (window as any).deleteCountdownInterval = interval;
    };

    const confirmDeleteListWithId = async (listId: string, listName: string) => {
        // Prevent double execution
        if (deleteModal.isDeleting) {
            console.log('❌ Already deleting, ignoring duplicate call');
            return;
        }

        // Additional check to prevent multiple simultaneous deletions
        if ((window as any).isDeletingList) {
            console.log('❌ Global delete in progress, ignoring');
            return;
        }

        // Set deleting flags
        (window as any).isDeletingList = true;
        setDeleteModal(prev => ({ ...prev, isDeleting: true }));

        try {
            console.log('🗑️ Deleting list with ID:', listId, 'Name:', listName);

            if (!listId || listId.trim() === '') {
                throw new Error('Invalid list ID');
            }

            await api.deleteShoppingList(listId);

            // Clear the interval if it exists
            if ((window as any).deleteCountdownInterval) {
                clearInterval((window as any).deleteCountdownInterval);
                delete (window as any).deleteCountdownInterval;
            }

            // If the deleted list was active, clear it first
            if (activeList?.id === listId) {
                console.log('🗑️ Clearing deleted active list');
                setActiveList(null);
                setItems([]);
                disconnect();
            }

            // Reload lists manually
            const data = await api.getShoppingLists();
            setLists(data.results || data);

            // Close modal - toast will be shown by WebSocket listener to avoid duplicates
            console.log('✅ List deleted successfully, WebSocket will notify');
            setDeleteModal({ isOpen: false, listId: '', listName: '', countdown: 5, isDeleting: false });
        } catch (error: any) {
            console.error('Delete list error:', error);

            // Check if it's a permission error (non-creator trying to delete)
            if (error.message && error.message.includes('Only the creator can delete')) {
                console.log('🚪 Non-creator trying to delete, showing leave option');

                // Close the delete modal
                setDeleteModal({ isOpen: false, listId: '', listName: '', countdown: 5, isDeleting: false });

                // Show the leave modal with countdown
                setLeaveModal({
                    isOpen: true,
                    listId,
                    listName,
                    countdown: 5,
                    isLeaving: false
                });

                // Start countdown for leave modal
                let countdownValue = 5;
                const leaveCountdownInterval = setInterval(() => {
                    countdownValue--;
                    setLeaveModal(prev => ({ ...prev, countdown: countdownValue }));

                    if (countdownValue <= 0) {
                        clearInterval(leaveCountdownInterval);
                    }
                }, 1000);

                // Store interval globally for cleanup
                (window as any).leaveCountdownInterval = leaveCountdownInterval;

                return; // Exit early, don't show error toast
            }

            // Handle other types of errors
            let errorMessage = 'Failed to delete list';

            if (error.message) {
                if (error.message.includes('permission')) {
                    errorMessage = 'You do not have permission to delete this list';
                } else if (error.message.includes('not found')) {
                    errorMessage = 'List not found or no longer exists';
                } else {
                    errorMessage = error.message;
                }
            }

            toast.error(errorMessage);
            // Close modal on error too
            setDeleteModal({ isOpen: false, listId: '', listName: '', countdown: 5, isDeleting: false });
        } finally {
            // Clear global delete flag
            delete (window as any).isDeletingList;
        }
    };

    const confirmDeleteList = async () => {
        // This is called when user manually confirms deletion
        if (!deleteModal.listId) {
            console.error('No list ID in deleteModal:', deleteModal);
            toast.error('Invalid list ID');
            return;
        }

        // Clear the countdown timer since user manually confirmed
        if ((window as any).deleteCountdownInterval) {
            clearInterval((window as any).deleteCountdownInterval);
            delete (window as any).deleteCountdownInterval;
        }

        console.log('🗑️ User manually confirmed deletion during countdown');
        await confirmDeleteListWithId(deleteModal.listId, deleteModal.listName);
    };

    const cancelDelete = () => {
        // Clear the interval
        if ((window as any).deleteCountdownInterval) {
            clearInterval((window as any).deleteCountdownInterval);
            delete (window as any).deleteCountdownInterval;
        }

        setDeleteModal({ isOpen: false, listId: '', listName: '', countdown: 5, isDeleting: false });
        toast.success('Deletion cancelled');
    };

    const confirmLeaveList = async () => {
        if (!leaveModal.listId) {
            console.error('No list ID in leaveModal:', leaveModal);
            toast.error('Invalid list ID');
            return;
        }

        // Clear the countdown timer since user manually confirmed
        if ((window as any).leaveCountdownInterval) {
            clearInterval((window as any).leaveCountdownInterval);
            delete (window as any).leaveCountdownInterval;
        }

        console.log('🚪 User manually confirmed leaving during countdown');
        await confirmLeaveListWithId(leaveModal.listId, leaveModal.listName);
    };

    const confirmLeaveListWithId = async (listId: string, listName: string) => {
        // Prevent double execution
        if (leaveModal.isLeaving) {
            console.log('❌ Already leaving, ignoring duplicate call');
            return;
        }

        // Set leaving flag
        setLeaveModal(prev => ({ ...prev, isLeaving: true }));

        try {
            console.log('🚪 Leaving list with ID:', listId, 'Name:', listName);

            if (!listId || listId.trim() === '') {
                throw new Error('Invalid list ID');
            }

            await api.leaveList(listId);

            // If this was the active list, clear it and disconnect
            if (activeList && activeList.id === listId) {
                console.log('🚪 Left the currently active list, clearing and disconnecting');
                setActiveList(null);
                setItems([]);
                disconnect();
            }

            // Reload lists to remove the one we left
            const data = await api.getShoppingLists();
            setLists(data.results || data);

            // Show success message and close modal
            toast.success(`You have left "${listName}"`);
            setLeaveModal({ isOpen: false, listId: '', listName: '', countdown: 5, isLeaving: false });
        } catch (error: any) {
            console.error('Leave list error:', error);

            let errorMessage = 'Failed to leave list';

            if (error.message) {
                errorMessage = error.message;
            }

            toast.error(errorMessage);
            setLeaveModal({ isOpen: false, listId: '', listName: '', countdown: 5, isLeaving: false });
        }
    };

    const cancelLeave = () => {
        // Clear the interval
        if ((window as any).leaveCountdownInterval) {
            clearInterval((window as any).leaveCountdownInterval);
            delete (window as any).leaveCountdownInterval;
        }

        setLeaveModal({ isOpen: false, listId: '', listName: '', countdown: 5, isLeaving: false });
        toast.success('Leave cancelled');
    };

    const handleSendToInventory = async () => {
        if (!activeList) return;

        // Get completed items
        const completedItems = items.filter(item => item.is_completed);

        if (completedItems.length === 0) {
            toast.error('No completed items to send to inventory');
            return;
        }

        setLoadingInventory(true);
        try {
            const itemIds = completedItems.map(item => item.id);
            const result = await api.sendToInventory(activeList.id, itemIds, true);

            console.log('[INVENTORY] AI suggestions:', result);
            setInventorySuggestions(result.suggestions || []);
            setShowInventoryModal(true);

            toast.success(`AI categorized ${result.item_count} items!`);
        } catch (error: any) {
            console.error('[INVENTORY] Error:', error);
            toast.error('Failed to get inventory suggestions');
        } finally {
            setLoadingInventory(false);
        }
    };

    const confirmInventoryTransfer = async () => {
        if (!inventorySuggestions.length) return;

        try {
            // Convert suggestions to inventory items
            const items = inventorySuggestions.map(sugg => {
                // Extract the correct name from translations
                const itemName = typeof sugg.name === 'object'
                    ? (sugg.name[i18n.language] || sugg.name['en'] || Object.values(sugg.name)[0])
                    : sugg.name;

                const itemData: any = {
                    name: itemName,
                    quantity: sugg.suggested_quantity,
                    unit: sugg.suggested_unit,
                    location: sugg.suggested_location,
                    category: sugg.suggested_category,
                    shopping_list_id: activeList?.id
                };

                // Only add expiration_date if we have a valid suggestion
                if (sugg.suggested_expiration_days && sugg.suggested_expiration_days > 0) {
                    const expirationDate = new Date();
                    expirationDate.setDate(expirationDate.getDate() + sugg.suggested_expiration_days);
                    itemData.expiration_date = expirationDate.toISOString().split('T')[0];
                }

                return itemData;
            });

            const result = await api.bulkCreateInventory(items);

            // Show detailed message about created vs merged items
            if (result.merged_count > 0) {
                toast.success(`✅ ${result.message || `Added to inventory: ${result.created_count} new, ${result.merged_count} merged with existing items`}`);
            } else {
                toast.success(`✅ Added ${result.created_count} items to inventory!`);
            }

            setShowInventoryModal(false);
            setInventorySuggestions([]);

            // Optionally: Delete completed items from shopping list
            // or mark them in some way

        } catch (error: any) {
            console.error('[INVENTORY] Transfer error:', error);
            toast.error('Failed to transfer to inventory');
        }
    };

    const handleMockOrder = async (storeType: string) => {
        setLoading(true);
        try {
            const orderItems = items.filter(item => !item.is_completed).map(item => ({
                name: item.name,
                quantity: item.quantity
            }));

            const response = await api.mockStoreOrder({
                store_type: storeType,
                items: orderItems
            });

            alert(`Mock ${storeType} order placed! Total: ₪${response.total_price_nis || 'N/A'}`);
        } catch (error) {
            console.error('Mock order error:', error);
        } finally {
            setLoading(false);
        }
    };


    // Function to toggle quantity type for an item
    const toggleQuantityType = (itemId: string, currentType: 'weight' | 'liquid' | 'none') => {
        let newType: 'weight' | 'liquid' | 'none';

        // Cycle through: none -> weight -> liquid -> none
        if (currentType === 'none') {
            newType = 'weight';
        } else if (currentType === 'weight') {
            newType = 'liquid';
        } else {
            newType = 'none';
        }

        setActiveQuantityType(prev => {
            const newMap = new Map(prev);
            newMap.set(itemId, newType);
            return newMap;
        });

        // Broadcast quantity type change to other collaborators
        if (isConnected) {
            const item = items.find(item => item.id === itemId);
            if (item) {
                console.log(`🔄 Broadcasting quantity type change for ${item.name}: ${currentType} → ${newType}`);

                sendCustomMessage({
                    type: 'quantity_type_changed',
                    item_id: itemId,
                    item_name: item.name,
                    quantity_type: newType,
                    changed_by: user?.username || 'Unknown'
                });
            }
        }
    };


    const categorizedItems = items.reduce((acc: any, item: any) => {
        if (!acc[item.category]) acc[item.category] = [];
        acc[item.category].push(item);
        return acc;
    }, {});

    return (
        <div className="max-w-7xl mx-auto p-6">
            {/* NEW: Show loading or lock screen if email not verified */}
            {accessLoading ? (
                <div className="flex justify-center items-center min-h-[60vh]">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                </div>
            ) : !accessStatus?.available ? (
                <LockedFeature
                    featureName="Shopping Lists"
                    description="Please verify your email to use Shopping Lists"
                    benefits={[
                        'Create and manage shopping lists',
                        'Real-time collaboration with family',
                        'Share lists with others',
                        'Inventory management',
                        'Smart recipe-to-list conversion'
                    ]}
                />
            ) : (
            <>
            {/* Original content starts here */}
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-3xl font-bold">🛒 {t('shopping.title')}</h2>
                {isConnected && (
                    <div className="flex items-center gap-2 text-green-600">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        <span className="text-sm">Live Connected</span>
                    </div>
                )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                <div className="bg-white rounded-lg shadow-lg p-4">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-xl font-semibold">{t('shopping.myLists')}</h3>
                        <button
                            id="create-list-button"
                            onClick={() => setShowCreateForm(!showCreateForm)}
                            className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition"
                        >
                            ➕ {t('common.add')}
                        </button>
                    </div>

                    {/* Create New List Form */}
                    {showCreateForm && (
                        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                            <input
                                type="text"
                                value={newListName}
                                onChange={(e) => setNewListName(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleCreateList()}
                                placeholder={t('shopping.newListName')}
                                className="w-full px-3 py-2 text-sm border rounded focus:ring-2 focus:ring-green-500 mb-2"
                            />
                            <div className="flex gap-2">
                                <button
                                    onClick={handleCreateList}
                                    className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                                >
                                    {t('shopping.create')}
                                </button>
                                <button
                                    onClick={() => setShowCreateForm(false)}
                                    className="px-3 py-1 bg-gray-300 text-gray-700 text-sm rounded hover:bg-gray-400"
                                >
                                    {t('shopping.cancel')}
                                </button>
                            </div>
                        </div>
                    )}

                    <div className="space-y-2">
                        {lists.map(list => (
                            <div
                                key={list.id}
                                className={`p-3 rounded transition border ${activeList?.id === list.id
                                    ? 'bg-blue-500 text-white border-blue-600'
                                    : 'bg-gray-100 hover:bg-gray-200 border-gray-200'
                                    }`}
                            >
                                <div className="flex justify-between items-start">
                                    <button
                                        onClick={() => {
                                            console.log('🎯 Setting active list:', list);
                                            if (list && list.id) {
                                                setActiveList(list);
                                            } else {
                                                console.error('❌ Cannot set active list: invalid list object', list);
                                                toast.error('Invalid list selected');
                                            }
                                        }}
                                        className="flex-1 text-left"
                                    >
                                        <div className="font-medium">{list.name}</div>
                                        <div className="text-sm opacity-75">
                                            {activeList?.id === list.id ? items.length : (list.items?.length || 0)} {t('shopping.items')}
                                            {(() => {
                                                // Use real-time collaborator count for active list, fallback to stored count
                                                const collaboratorCount = activeList?.id === list.id
                                                    ? collaborators.length
                                                    : (list.collaborators?.length || 0);
                                                return collaboratorCount > 1 && (
                                                    <span className="ml-2">• {collaboratorCount} {t('shopping.people')}</span>
                                                );
                                            })()}
                                        </div>
                                    </button>

                                    <div className="flex items-center gap-2 ml-2">
                                        {list.is_collaborative && (
                                            <span className={`text-xs px-2 py-1 rounded ${activeList?.id === list.id
                                                ? 'bg-blue-400 text-blue-100'
                                                : 'bg-green-100 text-green-700'
                                                }`}>
                                                👥
                                            </span>
                                        )}
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDeleteList(list.id, list.name);
                                            }}
                                            className={`p-1 rounded text-xs transition ${activeList?.id === list.id
                                                ? 'hover:bg-blue-400 text-blue-100'
                                                : 'hover:bg-red-100 text-red-600'
                                                }`}
                                            title={t('shopping.deleteList')}
                                        >
                                            🗑️
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}

                        {lists.length === 0 && !showCreateForm && (
                            <div className="text-center py-8 text-gray-500">
                                <p className="mb-2">{t('shopping.noLists')}</p>
                                <p className="text-sm">{t('shopping.createFirstList')}</p>
                            </div>
                        )}
                    </div>
                </div>

                <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-6">
                    {activeList ? (
                        <>
                            <h3 className="text-2xl font-semibold mb-4">{activeList.name}</h3>

                            <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg" id="ai-add-section">
                                <label className="block text-sm font-medium mb-2">
                                    🤖 {t('shopping.aiAddLabel')}
                                </label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={aiInput}
                                        onChange={(e) => handleInputChange(e.target.value, setAiInput)}
                                        onKeyPress={(e) => e.key === 'Enter' && handleAiAddItems()}
                                        placeholder={!activeList ? t('shopping.selectListFirst') : t('shopping.aiPlaceholder')}
                                        className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                        disabled={loading || !activeList}
                                    />
                                    <button
                                        onClick={handleAiAddItems}
                                        disabled={loading || !activeList}
                                        className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition"
                                    >
                                        {loading ? t('shopping.processing') : t('shopping.aiAdd')}
                                    </button>
                                </div>

                                {/* AI Messages Section - Between input and recipe links */}
                                {aiMessages.length > 0 && (
                                    <div className="mt-4 space-y-2 p-3 bg-blue-50/80 rounded-lg border border-blue-200">
                                        <div className="flex items-center justify-between mb-2">
                                            <p className="text-xs font-medium text-blue-800">
                                                💬 {t('shopping.aiMessages')}:
                                            </p>
                                            <button
                                                onClick={() => {
                                                    if (window.confirm(t('shopping.clearAllMessages'))) {
                                                        setAiMessages([]);
                                                    }
                                                }}
                                                className="text-xs text-gray-500 hover:text-red-600 transition"
                                                title={t('shopping.clearMessages')}
                                            >
                                                {t('shopping.clearMessages')}
                                            </button>
                                        </div>
                                        <div className="space-y-2 max-h-32 overflow-y-auto">
                                            {aiMessages.map(message => (
                                                <div
                                                    key={message.id}
                                                    className="flex items-start gap-2 p-2 bg-white rounded border border-blue-100 shadow-sm"
                                                >
                                                    <span className="text-blue-600 text-sm mt-0.5">ℹ️</span>
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-xs text-gray-700 leading-relaxed">
                                                            {message.text}
                                                        </p>
                                                        <p className="text-[10px] text-gray-400 mt-1">
                                                            {message.timestamp.toLocaleTimeString()}
                                                        </p>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Recipe Links Section */}
                                {generatedRecipes.length > 0 && (
                                    <div className="mt-4 space-y-2 p-3 bg-white/60 rounded-lg border border-purple-200">
                                        <div className="flex items-center justify-between mb-2">
                                            <p className="text-xs font-medium text-gray-700">
                                                📚 {t('shopping.generatedRecipes')} ({generatedRecipes.length}):
                                            </p>
                                            <button
                                                onClick={() => {
                                                    if (window.confirm(t('shopping.clearRecipeLinks'))) {
                                                        setGeneratedRecipes([]);
                                                        if (activeList?.id) {
                                                            localStorage.removeItem(`generatedRecipes_${activeList.id}`);
                                                        }
                                                    }
                                                }}
                                                className="text-xs text-gray-500 hover:text-red-600 transition"
                                                title={t('shopping.clearMessages')}
                                            >
                                                {t('shopping.clearMessages')}
                                            </button>
                                        </div>
                                        <div className="space-y-1.5 max-h-40 overflow-y-auto">
                                            {generatedRecipes.slice(0, 10).map((recipe, index) => (
                                                <div
                                                    key={`${recipe.id}-${index}`}
                                                    className="flex items-center gap-2 text-sm hover:bg-purple-50 p-1.5 rounded transition"
                                                >
                                                    <span className="text-purple-600 text-lg leading-none">→</span>
                                                    <button
                                                        type="button"
                                                        onClick={(e) => {
                                                            e.preventDefault();
                                                            e.stopPropagation();

                                                            // Validate canonicalId before opening
                                                            if (!recipe.canonicalId) {
                                                                console.error('❌ Cannot open recipe: canonicalId is null/undefined', recipe);
                                                                toast.error(recipe.isGenerating
                                                                    ? '⏳ Recipe is still generating, please wait...'
                                                                    : '❌ Recipe ID not found. Try generating it again.'
                                                                );
                                                                return;
                                                            }

                                                            // Navigate to recipe detail page in discovery
                                                            const url = `/discover?id=${recipe.canonicalId}`;
                                                            console.log(`🔗 Navigating to recipe: ${recipe.name} at ${url}`);
                                                            console.log(`🔗 Recipe object:`, recipe);
                                                            window.location.href = url;
                                                        }}
                                                        className={`text-purple-600 hover:text-purple-800 hover:underline flex-1 truncate text-left cursor-pointer ${!recipe.canonicalId ? 'opacity-50 cursor-not-allowed' : ''}`}
                                                        title={!recipe.canonicalId
                                                            ? (recipe.isGenerating ? 'Recipe is generating...' : 'Recipe ID not available')
                                                            : `${t('shopping.viewRecipe')}: ${recipe.name}`}
                                                        disabled={!recipe.canonicalId}
                                                    >
                                                        <span className="font-medium">{recipe.name}</span>
                                                        <span className="text-gray-500 ml-1 text-xs">
                                                            ({t('shopping.from')} "{recipe.query}")
                                                        </span>
                                                    </button>
                                                    <span className="text-xs text-gray-400 flex-shrink-0">
                                                        {recipe.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                        {generatedRecipes.length > 10 && (
                                            <p className="text-xs text-gray-500 mt-2 text-center">
                                                + {generatedRecipes.length - 10} {t('shopping.more')} ({t('shopping.scrollToSeeAll')})
                                            </p>
                                        )}
                                    </div>
                                )}
                            </div>

                            <div className="mb-6">
                                <div className="flex gap-2">
                                    <input
                                        id="manual-add-input"
                                        type="text"
                                        value={newItem}
                                        onChange={(e) => handleInputChange(e.target.value, setNewItem)}
                                        onKeyPress={(e) => e.key === 'Enter' && handleAddItem()}
                                        placeholder={!activeList ? t('shopping.selectListFirst') : t('shopping.addItemPlaceholder')}
                                        className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                        disabled={!activeList}
                                    />
                                    <button
                                        onClick={handleAddItem}
                                        disabled={!activeList}
                                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
                                    >
                                        {t('shopping.addItem')}
                                    </button>
                                </div>
                            </div>

                            {/* Typing Indicators */}
                            {typingUsers.length > 0 && (
                                <div className="mb-4 p-2 bg-yellow-50 rounded-lg">
                                    <div className="text-sm text-yellow-700 flex items-center gap-2">
                                        <div className="flex space-x-1">
                                            <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                            <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                            <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                        </div>
                                        <span>
                                            {typingUsers.map(user => user.username).join(', ')}
                                            {' '}{typingUsers.length === 1 ? t('shopping.isTyping') : t('shopping.areTyping')} {t('shopping.typing')}
                                        </span>
                                    </div>
                                </div>
                            )}

                            <div className="space-y-4">
                                {Object.entries(categorizedItems).map(([category, categoryItems]) => (
                                    <div key={category}>
                                        <h4 className="font-medium text-gray-700 capitalize mb-2">
                                            {t(`shopping.categories.${category.toLowerCase()}`, category.replace('_', ' '))}
                                        </h4>
                                        <div className="space-y-2">
                                            {(categoryItems as any[]).map(item => (
                                                <div
                                                    key={item.id}
                                                    className={`p-3 rounded-lg border ${item.is_completed
                                                        ? 'bg-gray-50 opacity-60'
                                                        : 'bg-white hover:shadow-md'
                                                        }`}
                                                    style={{
                                                        borderLeftWidth: '4px',
                                                        borderLeftColor: item.display_color || '#6B7280'
                                                    }}
                                                >
                                                    <div className="flex flex-col gap-2">
                                                        {/* Top row: checkbox, name, and indicators */}
                                                        <div className="flex items-center justify-between">
                                                            <div className="flex items-center gap-3 flex-1">
                                                                <input
                                                                    type="checkbox"
                                                                    checked={item.is_completed}
                                                                    onChange={() => handleToggleItem(item.id)}
                                                                    className="w-5 h-5 text-gray-600 accent-gray-600"
                                                                    disabled={isToggling.has(item.id) || isDeleting.has(item.id) || isUpdatingQuantity.has(item.id) || isUpdatingWeight.has(item.id) || isUpdatingLiquid.has(item.id)}
                                                                />

                                                                <div className="flex-1">
                                                                    <div className="flex items-center gap-2 flex-wrap">
                                                                        {/* MULTILANG DEBUG */}
                                                                        {(() => {
                                                                            console.log('[MULTILANG FRONTEND] Item data:', {
                                                                                id: item.id,
                                                                                name: item.name,
                                                                                display_name: item.display_name,
                                                                                name_translations: item.name_translations,
                                                                                original_language: item.original_language
                                                                            });
                                                                            console.log('[MULTILANG FRONTEND] Current i18n language:', i18n.language);
                                                                            // Use name_translations first, then fallback to display_name/name
                                                                            const displayName = item.name_translations?.[i18n.language] || item.display_name || item.name;
                                                                            console.log('[MULTILANG FRONTEND] Will display:', displayName);
                                                                            return null;
                                                                        })()}

                                                                        <span className={`font-medium ${item.is_completed ? 'line-through text-gray-500' : ''}`}>
                                                                            {item.name_translations?.[i18n.language] || item.display_name || item.name}
                                                                        </span>

                                                                        {/* User indicator */}
                                                                        {item.user_color && (
                                                                            <div
                                                                                className="w-5 h-5 rounded-full flex items-center justify-center text-white text-xs font-semibold"
                                                                                style={{ backgroundColor: item.user_color }}
                                                                                title={`Added by ${item.added_by_first_name || item.added_by_name}`}
                                                                            >
                                                                                {(item.added_by_first_name || item.added_by_name || 'U').charAt(0).toUpperCase()}
                                                                            </div>
                                                                        )}

                                                                        {/* Recent indicator */}
                                                                        {item.is_recent && (
                                                                            <span className="text-xs bg-green-100 text-green-700 px-1 py-0.5 rounded-full">
                                                                                ✨ {t('shopping.new')}
                                                                            </span>
                                                                        )}

                                                                        {/* AI suggested */}
                                                                        {item.ai_suggested && (
                                                                            <span className="text-xs bg-purple-100 text-purple-700 px-1 py-0.5 rounded-full">
                                                                                🤖 {t('shopping.aiSuggested')}
                                                                            </span>
                                                                        )}
                                                                    </div>

                                                                    {/* Added by info */}
                                                                    <div className="text-xs text-gray-400 mt-1">
                                                                        {t('shopping.addedBy')} {item.added_by_first_name || item.added_by_name}
                                                                        {item.is_completed && item.completed_by_name && (
                                                                            <span> • {t('shopping.completedBy')} {item.completed_by_name}</span>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            </div>

                                                            {/* Delete button */}
                                                            <button
                                                                onClick={() => handleDeleteItem(item.id, item.display_name || item.name)}
                                                                disabled={isDeleting.has(item.id) || isToggling.has(item.id) || isUpdatingQuantity.has(item.id) || isUpdatingWeight.has(item.id) || isUpdatingLiquid.has(item.id)}
                                                                className={`ml-2 p-2 rounded-lg transition-colors ${isDeleting.has(item.id)
                                                                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                                                                    : 'hover:bg-red-100 text-red-600 hover:text-red-700'
                                                                    }`}
                                                                title={t('shopping.removeItem')}
                                                            >
                                                                {isDeleting.has(item.id) ? (
                                                                    <div className="w-4 h-4 flex items-center justify-center">
                                                                        <div className="w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                                                                    </div>
                                                                ) : (
                                                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                                    </svg>
                                                                )}
                                                            </button>
                                                        </div>

                                                        {/* Bottom row: All quantity counters */}
                                                        <div className="flex items-center gap-2 flex-wrap ml-8">
                                                            {/* Main Quantity Counter */}
                                                            <div className="flex items-center gap-1 bg-gray-50 border border-gray-200 rounded px-1 py-1">
                                                                <button
                                                                    onClick={() => handleQuantityChange(item.id, -1, item.name)}
                                                                    disabled={isUpdatingQuantity.has(item.id) || isDeleting.has(item.id) || isUpdatingWeight.has(item.id) || isUpdatingLiquid.has(item.id) || item.quantity <= 1}
                                                                    className="w-4 h-4 flex items-center justify-center bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-300 text-gray-600 rounded border text-xs font-bold transition-colors"
                                                                    title={t('shopping.decreaseQuantity')}
                                                                >
                                                                    −
                                                                </button>

                                                                <input
                                                                    type="number"
                                                                    value={item.quantity}
                                                                    onChange={(e) => handleQuantityInput(item.id, e.target.value, item.name)}
                                                                    disabled={isUpdatingQuantity.has(item.id) || isDeleting.has(item.id) || isUpdatingWeight.has(item.id) || isUpdatingLiquid.has(item.id)}
                                                                    className="w-16 h-6 text-center text-sm font-semibold border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
                                                                    min="1"
                                                                    step="0.1"
                                                                />

                                                                <button
                                                                    onClick={() => handleQuantityChange(item.id, 1, item.name)}
                                                                    disabled={isUpdatingQuantity.has(item.id) || isDeleting.has(item.id) || isUpdatingWeight.has(item.id) || isUpdatingLiquid.has(item.id)}
                                                                    className="w-4 h-4 flex items-center justify-center bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-300 text-gray-600 rounded border text-xs font-bold transition-colors"
                                                                    title={t('shopping.increaseQuantity')}
                                                                >
                                                                    +
                                                                </button>

                                                                <span className="text-xs text-gray-500">
                                                                    {translateUnit(item.unit)}
                                                                </span>
                                                            </div>

                                                            {/* Quantity Type Toggle */}
                                                            <div className="flex items-center gap-1 bg-gray-50 border border-gray-200 rounded px-1 py-1">
                                                                <button
                                                                    onClick={() => toggleQuantityType(item.id, getActiveQuantityType(item.id))}
                                                                    className={`text-xs px-2 py-1 rounded transition-colors ${getActiveQuantityType(item.id) === 'none'
                                                                        ? 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                                                                        : getActiveQuantityType(item.id) === 'weight'
                                                                            ? 'bg-orange-200 text-orange-700 hover:bg-orange-300'
                                                                            : 'bg-blue-200 text-blue-700 hover:bg-blue-300'
                                                                        }`}
                                                                    title={t('shopping.toggleQuantityType')}
                                                                >
                                                                    {getActiveQuantityType(item.id) === 'none'
                                                                        ? `🔢 ${t('shopping.enable')}`
                                                                        : getActiveQuantityType(item.id) === 'weight'
                                                                            ? `📊 ${t('shopping.weight')}`
                                                                            : `🥤 ${t('shopping.liquid')}`
                                                                    }
                                                                </button>
                                                            </div>

                                                            {/* Weight Quantity Counter - Only show when weight is active */}
                                                            {getActiveQuantityType(item.id) === 'weight' && (
                                                                <div className="flex items-center gap-1 bg-orange-50 border border-orange-200 rounded px-1 py-1">
                                                                    <span className="text-xs text-orange-600 font-medium">📊</span>

                                                                    <button
                                                                        onClick={() => handleWeightQuantityChange(item.id, -1, item.name)}
                                                                        disabled={isUpdatingWeight.has(item.id) || isDeleting.has(item.id) || (item.weight_quantity || 0) <= 0}
                                                                        className="w-4 h-4 flex items-center justify-center bg-orange-100 hover:bg-orange-200 disabled:bg-gray-50 disabled:text-gray-300 text-orange-600 rounded border text-xs font-bold transition-colors"
                                                                        title={t('shopping.decreaseWeight')}
                                                                    >
                                                                        −
                                                                    </button>

                                                                    <input
                                                                        type="text"
                                                                        value={(() => {
                                                                            const rawValue = item.weight_quantity || 0;
                                                                            const formatted = formatWeight(rawValue, userPreferences.weight_unit);
                                                                            console.log('📊 Rendering weight input - raw:', rawValue, 'formatted:', formatted, 'for item:', item.name);
                                                                            return formatted;
                                                                        })()}
                                                                        onChange={(e) => handleWeightQuantityInput(item.id, e.target.value, item.name)}
                                                                        disabled={isUpdatingWeight.has(item.id) || isDeleting.has(item.id)}
                                                                        className="w-20 h-6 text-center text-sm font-semibold border rounded focus:ring-1 focus:ring-orange-500 focus:border-orange-500 disabled:bg-gray-50"
                                                                        placeholder={`0 ${userPreferences.weight_unit === 'kg' ? 'kg' : 'lbs'}`}
                                                                        title={t('shopping.weightQuantity')}
                                                                    />

                                                                    <button
                                                                        onClick={() => handleWeightQuantityChange(item.id, 1, item.name)}
                                                                        disabled={isUpdatingWeight.has(item.id) || isDeleting.has(item.id)}
                                                                        className="w-4 h-4 flex items-center justify-center bg-orange-100 hover:bg-orange-200 disabled:bg-gray-50 disabled:text-gray-300 text-orange-600 rounded border text-xs font-bold transition-colors"
                                                                        title={t('shopping.increaseWeight')}
                                                                    >
                                                                        +
                                                                    </button>
                                                                </div>
                                                            )}

                                                            {/* Liquid Quantity Counter - Only show when liquid is active */}
                                                            {getActiveQuantityType(item.id) === 'liquid' && (
                                                                <div className="flex items-center gap-1 bg-blue-50 border border-blue-200 rounded px-1 py-1">
                                                                    <span className="text-xs text-blue-600 font-medium">🥤</span>

                                                                    <button
                                                                        onClick={() => handleLiquidQuantityChange(item.id, -1, item.name)}
                                                                        disabled={isUpdatingLiquid.has(item.id) || isDeleting.has(item.id) || (item.liquid_quantity || 0) <= 0}
                                                                        className="w-4 h-4 flex items-center justify-center bg-blue-100 hover:bg-blue-200 disabled:bg-gray-50 disabled:text-gray-300 text-blue-600 rounded border text-xs font-bold transition-colors"
                                                                        title={t('shopping.decreaseLiquid')}
                                                                    >
                                                                        −
                                                                    </button>

                                                                    <input
                                                                        type="text"
                                                                        value={(() => {
                                                                            const rawValue = item.liquid_quantity || 0;
                                                                            const formatted = formatVolume(rawValue, userPreferences.volume_unit);
                                                                            console.log('🥤 Rendering liquid input - raw:', rawValue, 'formatted:', formatted, 'for item:', item.name);
                                                                            return formatted;
                                                                        })()}
                                                                        onChange={(e) => handleLiquidQuantityInput(item.id, e.target.value, item.name)}
                                                                        disabled={isUpdatingLiquid.has(item.id) || isDeleting.has(item.id)}
                                                                        className="w-20 h-6 text-center text-sm font-semibold border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
                                                                        placeholder={`0 ${userPreferences.volume_unit === 'liters' ? 'L' : 'gal'}`}
                                                                        title={t('shopping.liquidQuantity')}
                                                                    />

                                                                    <button
                                                                        onClick={() => handleLiquidQuantityChange(item.id, 1, item.name)}
                                                                        disabled={isUpdatingLiquid.has(item.id) || isDeleting.has(item.id)}
                                                                        className="w-4 h-4 flex items-center justify-center bg-blue-100 hover:bg-blue-200 disabled:bg-gray-50 disabled:text-gray-300 text-blue-600 rounded border text-xs font-bold transition-colors"
                                                                        title={t('shopping.increaseLiquid')}
                                                                    >
                                                                        +
                                                                    </button>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>

                                                    {/* Notes */}
                                                    {item.notes && (
                                                        <div className="mt-2 ml-8 text-sm text-gray-600 italic">
                                                            📝 {item.notes}
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Send to Inventory Section */}
                            {items.filter(item => item.is_completed).length > 0 && (
                                <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <h4 className="font-semibold text-gray-900 mb-1">
                                                📦 {t('shopping.readyToStock')}
                                            </h4>
                                            <p className="text-sm text-gray-600">
                                                {t('shopping.sendCompletedItems', { count: items.filter(item => item.is_completed).length })}
                                            </p>
                                        </div>
                                        <button
                                            onClick={handleSendToInventory}
                                            disabled={loadingInventory}
                                            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 font-medium"
                                        >
                                            <Package className="w-5 h-5" />
                                            {loadingInventory ? t('shopping.processing') : t('shopping.sendToInventory')}
                                        </button>
                                    </div>
                                </div>
                            )}

                            <div className="mt-8 p-4 bg-gray-50 rounded-lg">
                                <h4 className="font-semibold mb-3">{t('shopping.orderFromStore')}</h4>
                                <div className="flex gap-3">
                                    <button
                                        onClick={() => handleMockOrder('wolt')}
                                        disabled={loading}
                                        className="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
                                    >
                                        🛵 {t('shopping.orderViaWolt')}
                                    </button>
                                    <button
                                        onClick={() => handleMockOrder('shufersal')}
                                        disabled={loading}
                                        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                                    >
                                        🛒 {t('shopping.checkPrices')}
                                    </button>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="text-center text-gray-500 py-12">
                            {t('shopping.selectList')}
                        </div>
                    )}
                </div>

                {/* Collaboration Sidebar - Always Visible */}
                <div className="lg:col-span-1">
                    <CollaboratorManager
                        listId={activeList?.id}
                        canInvite={activeList?.user_permissions?.can_invite_others || true}
                    />
                </div>
            </div>

            {/* Delete Confirmation Modal */}
            <DeleteConfirmationModal
                isOpen={deleteModal.isOpen}
                onConfirm={confirmDeleteList}
                onCancel={cancelDelete}
                listName={deleteModal.listName}
                countdown={deleteModal.countdown}
                isDeleting={deleteModal.isDeleting}
            />

            <LeaveConfirmationModal
                isOpen={leaveModal.isOpen}
                listName={leaveModal.listName}
                countdown={leaveModal.countdown}
                isLeaving={leaveModal.isLeaving}
                onConfirm={confirmLeaveList}
                onCancel={cancelLeave}
            />

            {/* Inventory Review Modal */}
            {showInventoryModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="sticky top-0 bg-white border-b p-6 flex items-center justify-between">
                            <h2 className="text-2xl font-bold text-gray-900">
                                {t('shopping.reviewAI')}
                            </h2>
                            <button
                                onClick={() => setShowInventoryModal(false)}
                                className="p-2 hover:bg-gray-100 rounded-lg transition"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="p-6">
                            <p className="text-gray-600 mb-6">
                                {t('shopping.reviewDescription')}
                            </p>

                            <div className="space-y-4 mb-6">
                                {inventorySuggestions.map((sugg, index) => {
                                    // Extract the correct name from translations
                                    const displayName = typeof sugg.name === 'object'
                                        ? (sugg.name[i18n.language] || sugg.name['en'] || Object.values(sugg.name)[0])
                                        : sugg.name;

                                    return (
                                        <div
                                            key={index}
                                            className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition"
                                        >
                                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                                <div>
                                                    <label className="text-xs text-gray-600">{t('shopping.itemName')}</label>
                                                    <p className="font-semibold">{displayName}</p>
                                                </div>
                                                <div>
                                                    <label className="text-xs text-gray-600">{t('shopping.location')}</label>
                                                    <p className="font-medium capitalize">{sugg.suggested_location}</p>
                                                </div>
                                                <div>
                                                    <label className="text-xs text-gray-600">{t('shopping.category')}</label>
                                                    <p className="font-medium capitalize">{sugg.suggested_category}</p>
                                                </div>
                                                <div>
                                                    <label className="text-xs text-gray-600">{t('shopping.expiresIn')}</label>
                                                    <p className="font-medium">{sugg.suggested_expiration_days} {t('shopping.days')}</p>
                                                </div>
                                            </div>
                                            <div className="mt-2 text-xs text-gray-500">
                                                {t('shopping.aiConfidence')}: {(sugg.confidence * 100).toFixed(0)}%
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>

                            <div className="flex gap-3">
                                <button
                                    onClick={() => setShowInventoryModal(false)}
                                    className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
                                >
                                    {t('common.cancel')}
                                </button>
                                <button
                                    onClick={confirmInventoryTransfer}
                                    className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
                                >
                                    <Check className="w-4 h-4 mr-2" />
                                    {t('shopping.addAllToInventory')}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Recipe Suggestions Modal */}
            {showRecipeSuggestions && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg max-w-2xl w-full p-6 shadow-xl">
                        <div className="flex items-start mb-4">
                            <div className="flex-shrink-0 w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
                                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                            </div>
                            <div className="ml-4 flex-1">
                                <h3 className="text-lg font-semibold text-gray-900 mb-1">
                                    {t('discover.suggestions.title')}
                                </h3>
                                <p className="text-sm text-gray-600 mb-4">
                                    {t('discover.suggestions.description', { query: failedRecipeQuery })}
                                </p>
                            </div>
                            <button
                                onClick={() => setShowRecipeSuggestions(false)}
                                className="text-gray-400 hover:text-gray-600 transition-colors"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="mb-4">
                            <h4 className="text-sm font-medium text-gray-700 mb-3">
                                {t('discover.suggestions.tryThese')}:
                            </h4>
                            <div className="grid grid-cols-2 gap-3">
                                {recipeSuggestions.map((suggestion, index) => (
                                    <button
                                        key={index}
                                        onClick={() => handleSuggestionClick(suggestion)}
                                        className="px-4 py-3 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg text-left hover:from-purple-100 hover:to-pink-100 hover:border-purple-300 transition-all duration-200 group"
                                    >
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-gray-800 capitalize">
                                                {suggestion}
                                            </span>
                                            <svg className="w-4 h-4 text-purple-400 group-hover:text-purple-600 group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                            </svg>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="flex items-center justify-between pt-4 border-t">
                            <p className="text-xs text-gray-500">
                                {t('discover.suggestions.hint')}
                            </p>
                            <button
                                onClick={() => setShowRecipeSuggestions(false)}
                                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 font-medium transition-colors"
                            >
                                {t('discover.suggestions.close')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
            </>
            )}
            {/* End of conditional render */}
        </div>
    );
};

export default ShoppingList;