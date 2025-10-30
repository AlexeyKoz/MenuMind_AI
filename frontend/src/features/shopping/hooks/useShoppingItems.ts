import { useState, useEffect, useCallback } from 'react';
import { ShoppingItem } from '../types/shopping.types';
import { useNetworkStatus } from './useNetworkStatus';
import { syncQueueService } from '../services/syncQueue';
import { saveToStore, getItemsByIndex, STORES, CachedShoppingItem } from '../services/offlineStorage';

// Mock API service - replace with actual API implementation
const apiService = {
    getShoppingItems: async (listId: string): Promise<ShoppingItem[]> => {
        const response = await fetch(`/api/shopping/lists/${listId}/items/`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        if (!response.ok) throw new Error('Failed to fetch items');
        return response.json();
    },

    toggleShoppingItem: async (itemId: string): Promise<void> => {
        const response = await fetch(`/api/shopping/items/${itemId}/toggle_complete/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        if (!response.ok) throw new Error('Failed to toggle item');
    },

    updateShoppingItem: async (itemId: string, data: any): Promise<void> => {
        const response = await fetch(`/api/shopping/items/${itemId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to update item');
    },

    addShoppingItem: async (listId: string, data: any): Promise<ShoppingItem> => {
        const response = await fetch(`/api/shopping/lists/${listId}/add_item/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to add item');
        return response.json();
    },

    deleteShoppingItem: async (itemId: string): Promise<void> => {
        const response = await fetch(`/api/shopping/items/${itemId}/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        if (!response.ok) throw new Error('Failed to delete item');
    }
};

export const useShoppingItems = (listId: string) => {
    const [items, setItems] = useState<ShoppingItem[]>([]);
    const [loading, setLoading] = useState(true);
    const { isOnline } = useNetworkStatus();

    // Load items (from cache or server)
    const loadItems = useCallback(async () => {
        try {
            if (isOnline) {
                // Try to load from server
                const serverItems = await apiService.getShoppingItems(listId);
                setItems(serverItems);

                // Update cache
                for (const item of serverItems) {
                    await saveToStore(STORES.shoppingItems, {
                        ...item,
                        synced: true
                    } as CachedShoppingItem);
                }
            } else {
                // Load from cache
                const cachedItems = await getItemsByIndex<CachedShoppingItem>(
                    STORES.shoppingItems,
                    'shopping_list_id',
                    listId
                );
                setItems(cachedItems as any);
            }
        } catch (error) {
            console.error('Failed to load items:', error);
            // Fallback to cache
            const cachedItems = await getItemsByIndex<CachedShoppingItem>(
                STORES.shoppingItems,
                'shopping_list_id',
                listId
            );
            setItems(cachedItems as any);
        } finally {
            setLoading(false);
        }
    }, [listId, isOnline]);

    useEffect(() => {
        loadItems();
    }, [loadItems]);

    // Toggle item completion (optimistic update)
    const toggleComplete = useCallback(async (itemId: string) => {
        const item = items.find(i => i.id === itemId);
        if (!item) return;

        // 1. IMMEDIATE UI UPDATE (Optimistic)
        const updatedItem = { ...item, is_completed: !item.is_completed };
        setItems(prev => prev.map(i => i.id === itemId ? updatedItem : i));

        // 2. Update local storage
        await saveToStore(STORES.shoppingItems, {
            ...updatedItem,
            synced: false
        } as CachedShoppingItem);

        // 3. Try server sync
        if (isOnline) {
            try {
                await apiService.toggleShoppingItem(itemId);

                // Mark as synced
                await saveToStore(STORES.shoppingItems, {
                    ...updatedItem,
                    synced: true
                } as CachedShoppingItem);
            } catch (error) {
                console.warn('Failed to sync toggle, adding to queue');
                await syncQueueService.addToQueue(
                    'UPDATE',
                    `/api/shopping/items/${itemId}/toggle_complete/`,
                    {}
                );
            }
        } else {
            // Offline - add to sync queue
            await syncQueueService.addToQueue(
                'UPDATE',
                `/api/shopping/items/${itemId}/toggle_complete/`,
                {}
            );
        }
    }, [items, isOnline]);

    // Update quantity (optimistic update)
    const updateQuantity = useCallback(async (itemId: string, quantity: number) => {
        const item = items.find(i => i.id === itemId);
        if (!item) return;

        // 1. IMMEDIATE UI UPDATE
        const updatedItem = { ...item, quantity };
        setItems(prev => prev.map(i => i.id === itemId ? updatedItem : i));

        // 2. Update local storage
        await saveToStore(STORES.shoppingItems, {
            ...updatedItem,
            synced: false
        } as CachedShoppingItem);

        // 3. Try server sync
        if (isOnline) {
            try {
                await apiService.updateShoppingItem(itemId, { quantity });

                await saveToStore(STORES.shoppingItems, {
                    ...updatedItem,
                    synced: true
                } as CachedShoppingItem);
            } catch (error) {
                await syncQueueService.addToQueue(
                    'UPDATE',
                    `/api/shopping/items/${itemId}/`,
                    { quantity }
                );
            }
        } else {
            await syncQueueService.addToQueue(
                'UPDATE',
                `/api/shopping/items/${itemId}/`,
                { quantity }
            );
        }
    }, [items, isOnline]);

    // Add new item (optimistic update)
    const addItem = useCallback(async (itemData: {
        name: string;
        quantity: number;
        category: string;
    }) => {
        // Create temporary item with client-side ID
        const tempId = `temp_${Date.now()}`;
        const newItem: ShoppingItem = {
            id: tempId,
            shopping_list_id: listId,
            name: itemData.name,
            name_translations: {},
            quantity: itemData.quantity,
            weight_quantity: 0,
            liquid_quantity: 0,
            category: itemData.category,
            is_completed: false,
            added_by: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };

        // 1. IMMEDIATE UI UPDATE
        setItems(prev => [newItem, ...prev]);

        // 2. Save to cache
        await saveToStore(STORES.shoppingItems, {
            ...newItem,
            synced: false
        } as CachedShoppingItem);

        // 3. Try server sync
        if (isOnline) {
            try {
                const serverItem = await apiService.addShoppingItem(listId, itemData);

                // Replace temp item with server item
                setItems(prev => prev.map(i => i.id === tempId ? serverItem : i));

                // Update cache with real ID
                await saveToStore(STORES.shoppingItems, {
                    ...serverItem,
                    synced: true
                } as CachedShoppingItem);
            } catch (error) {
                await syncQueueService.addToQueue(
                    'CREATE',
                    `/api/shopping/lists/${listId}/add_item/`,
                    itemData
                );
            }
        } else {
            await syncQueueService.addToQueue(
                'CREATE',
                `/api/shopping/lists/${listId}/add_item/`,
                itemData
            );
        }
    }, [listId, isOnline]);

    // Delete item (optimistic update)
    const deleteItem = useCallback(async (itemId: string) => {
        // 1. IMMEDIATE UI UPDATE
        setItems(prev => prev.filter(i => i.id !== itemId));

        // 2. Remove from cache (commented out to keep for sync)
        // await deleteFromStore(STORES.shoppingItems, itemId);

        // 3. Try server sync
        if (isOnline) {
            try {
                await apiService.deleteShoppingItem(itemId);
            } catch (error) {
                await syncQueueService.addToQueue(
                    'DELETE',
                    `/api/shopping/items/${itemId}/`,
                    {}
                );
            }
        } else {
            await syncQueueService.addToQueue(
                'DELETE',
                `/api/shopping/items/${itemId}/`,
                {}
            );
        }
    }, [isOnline]);

    return {
        items,
        loading,
        toggleComplete,
        updateQuantity,
        addItem,
        deleteItem,
        reload: loadItems
    };
};

