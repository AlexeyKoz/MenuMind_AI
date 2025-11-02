const CACHE_NAME = 'menumindai-v2'; // Updated to force new SW installation
const urlsToCache = [
    '/',
    '/static/css/main.css',
    '/static/js/main.js',
    '/static/js/bundle.js',
    '/manifest.json',
    '/favicon.ico'
];

// Install event - cache core assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Caching core assets');
                return cache.addAll(urlsToCache);
            })
    );
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[SW] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch event - network first, fall back to cache
self.addEventListener('fetch', (event) => {
    const { request } = event;

    // API calls - network first with offline fallback
    if (request.url.includes('/api/')) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Only cache GET requests (POST/PUT/DELETE cannot be cached)
                    if (response.ok && request.method === 'GET') {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // Offline - return cached response (only for GET requests)
                    if (request.method === 'GET') {
                        return caches.match(request).then((cachedResponse) => {
                            if (cachedResponse) {
                                return cachedResponse;
                            }
                            // Return offline fallback
                            return new Response(
                                JSON.stringify({ offline: true, message: 'You are offline' }),
                                {
                                    headers: { 'Content-Type': 'application/json' }
                                }
                            );
                        });
                    }
                    // For non-GET requests, just reject
                    return Promise.reject('Network error');
                })
        );
    } else {
        // Static assets - cache first, fall back to network
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                return cachedResponse || fetch(request).then((response) => {
                    // Cache new static assets (only GET requests)
                    if (response.ok && request.method === 'GET') {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                });
            })
        );
    }
});

// Background Sync - process offline queue
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync triggered:', event.tag);

    if (event.tag === 'sync-shopping-items') {
        event.waitUntil(syncShoppingItems());
    }
});

async function syncShoppingItems() {
    console.log('[SW] Syncing shopping items...');

    try {
        // Open IndexedDB and process queue
        const db = await openIndexedDB();
        const queue = await getQueueItems(db);

        for (const item of queue) {
            try {
                const response = await fetch(item.endpoint, {
                    method: item.operation === 'DELETE' ? 'DELETE' : 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${await getAccessToken()}`
                    },
                    body: item.operation !== 'DELETE' ? JSON.stringify(item.payload) : undefined
                });

                if (response.ok) {
                    await removeFromQueue(db, item.id);
                    console.log('[SW] Synced item:', item.id);
                }
            } catch (error) {
                console.error('[SW] Sync failed for item:', item.id, error);
            }
        }
    } catch (error) {
        console.error('[SW] Background sync failed:', error);
    }
}

function openIndexedDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('MenuMindAI', 1);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

function getQueueItems(db) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction('sync_queue', 'readonly');
        const store = transaction.objectStore('sync_queue');
        const request = store.getAll();
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

function removeFromQueue(db, id) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction('sync_queue', 'readwrite');
        const store = transaction.objectStore('sync_queue');
        const request = store.delete(id);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
    });
}

async function getAccessToken() {
    const clients = await self.clients.matchAll();
    if (clients.length > 0) {
        // Try to get token from client
        const response = await clients[0].postMessage({ type: 'GET_ACCESS_TOKEN' });
        return response;
    }
    return null;
}

