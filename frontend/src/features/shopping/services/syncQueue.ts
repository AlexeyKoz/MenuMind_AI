import { v4 as uuidv4 } from 'uuid';
import { SyncQueueItem, STORES, saveToStore, getAllFromStore, deleteFromStore } from './offlineStorage';

class SyncQueueService {
    private syncInterval: NodeJS.Timeout | null = null;
    private isProcessing = false;

    async addToQueue(
        operation: 'CREATE' | 'UPDATE' | 'DELETE',
        endpoint: string,
        payload: any
    ): Promise<void> {
        const queueItem: SyncQueueItem = {
            id: uuidv4(),
            timestamp: Date.now(),
            operation,
            endpoint,
            payload,
            retries: 0
        };

        await saveToStore(STORES.syncQueue, queueItem);
        console.log('📝 Added to sync queue:', queueItem);
    }

    start() {
        if (this.syncInterval) return;

        // Process queue every 30 seconds
        this.syncInterval = setInterval(() => {
            if (navigator.onLine && !this.isProcessing) {
                this.processQueue();
            }
        }, 30000);

        // Also process immediately when coming back online
        window.addEventListener('online', () => {
            console.log('🟢 Connection restored, processing sync queue...');
            this.processQueue();
        });

        console.log('🔄 Sync queue service started');
    }

    stop() {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = null;
        }
    }

    async processQueue(): Promise<void> {
        if (this.isProcessing) return;
        this.isProcessing = true;

        try {
            const queue = await getAllFromStore<SyncQueueItem>(STORES.syncQueue);
            console.log(`📤 Processing ${queue.length} queued operations`);

            for (const item of queue) {
                try {
                    // Max 5 retries with exponential backoff
                    if (item.retries >= 5) {
                        console.warn('⚠️ Max retries reached, removing from queue:', item);
                        await deleteFromStore(STORES.syncQueue, item.id);
                        continue;
                    }

                    const response = await fetch(item.endpoint, {
                        method: item.operation === 'DELETE' ? 'DELETE' : 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                        },
                        body: item.operation !== 'DELETE' ? JSON.stringify(item.payload) : undefined
                    });

                    if (response.ok) {
                        console.log('✅ Synced successfully:', item.endpoint);
                        await deleteFromStore(STORES.syncQueue, item.id);
                    } else {
                        // Increment retry count
                        item.retries++;
                        item.lastError = await response.text();
                        await saveToStore(STORES.syncQueue, item);
                        console.warn(`❌ Sync failed (retry ${item.retries}/5):`, item.endpoint);
                    }
                } catch (error) {
                    // Network error - will retry next cycle
                    item.retries++;
                    item.lastError = error instanceof Error ? error.message : 'Unknown error';
                    await saveToStore(STORES.syncQueue, item);
                    console.error('❌ Sync error:', error);
                }
            }
        } finally {
            this.isProcessing = false;
        }
    }

    async getQueueStatus(): Promise<{ pending: number; failed: number }> {
        const queue = await getAllFromStore<SyncQueueItem>(STORES.syncQueue);
        return {
            pending: queue.filter(item => item.retries < 5).length,
            failed: queue.filter(item => item.retries >= 5).length
        };
    }
}

export const syncQueueService = new SyncQueueService();

