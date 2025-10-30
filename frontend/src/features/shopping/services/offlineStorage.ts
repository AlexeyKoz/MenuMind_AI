const DB_NAME = 'MenuMindAI';
const DB_VERSION = 1;

export const STORES = {
    shoppingLists: 'shopping_lists',
    shoppingItems: 'shopping_items',
    syncQueue: 'sync_queue',
    translations: 'translations_cache'
};

export interface SyncQueueItem {
    id: string;
    timestamp: number;
    operation: 'CREATE' | 'UPDATE' | 'DELETE';
    endpoint: string;
    payload: any;
    retries: number;
    lastError?: string;
}

export interface CachedShoppingList {
    id: string;
    name: string;
    items: string[]; // Item IDs
    updated_at: string;
    synced: boolean;
}

export interface CachedShoppingItem {
    id: string;
    shopping_list_id: string;
    name: string;
    name_translations: Record<string, string>;
    quantity: number;
    weight_quantity: number;
    liquid_quantity: number;
    category: string;
    is_completed: boolean;
    updated_at: string;
    synced: boolean;
}

export const initDB = (): Promise<IDBDatabase> => {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);

        request.onupgradeneeded = (event) => {
            const db = (event.target as IDBOpenDBRequest).result;

            // Shopping Lists Store
            if (!db.objectStoreNames.contains(STORES.shoppingLists)) {
                const listStore = db.createObjectStore(STORES.shoppingLists, {
                    keyPath: 'id'
                });
                listStore.createIndex('updated_at', 'updated_at');
                listStore.createIndex('synced', 'synced');
            }

            // Shopping Items Store
            if (!db.objectStoreNames.contains(STORES.shoppingItems)) {
                const itemStore = db.createObjectStore(STORES.shoppingItems, {
                    keyPath: 'id'
                });
                itemStore.createIndex('shopping_list_id', 'shopping_list_id');
                itemStore.createIndex('is_completed', 'is_completed');
                itemStore.createIndex('synced', 'synced');
            }

            // Sync Queue Store
            if (!db.objectStoreNames.contains(STORES.syncQueue)) {
                const queueStore = db.createObjectStore(STORES.syncQueue, {
                    keyPath: 'id'
                });
                queueStore.createIndex('timestamp', 'timestamp');
                queueStore.createIndex('operation', 'operation');
            }

            // Translations Cache Store
            if (!db.objectStoreNames.contains(STORES.translations)) {
                const translationStore = db.createObjectStore(STORES.translations, {
                    keyPath: 'key'
                });
                translationStore.createIndex('language', 'language');
                translationStore.createIndex('cachedAt', 'cachedAt');
            }
        };
    });
};

// Helper functions for CRUD operations
export const saveToStore = async <T>(
    storeName: string,
    data: T
): Promise<void> => {
    const db = await initDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.put(data);

        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
    });
};

export const getFromStore = async <T>(
    storeName: string,
    key: string
): Promise<T | null> => {
    const db = await initDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, 'readonly');
        const store = transaction.objectStore(storeName);
        const request = store.get(key);

        request.onsuccess = () => resolve(request.result || null);
        request.onerror = () => reject(request.error);
    });
};

export const getAllFromStore = async <T>(
    storeName: string
): Promise<T[]> => {
    const db = await initDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, 'readonly');
        const store = transaction.objectStore(storeName);
        const request = store.getAll();

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
};

export const deleteFromStore = async (
    storeName: string,
    key: string
): Promise<void> => {
    const db = await initDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.delete(key);

        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
    });
};

export const getItemsByIndex = async <T>(
    storeName: string,
    indexName: string,
    value: any
): Promise<T[]> => {
    const db = await initDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, 'readonly');
        const store = transaction.objectStore(storeName);
        const index = store.index(indexName);
        const request = index.getAll(value);

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
};

