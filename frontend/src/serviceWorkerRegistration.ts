export const register = () => {
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            const swUrl = `${process.env.PUBLIC_URL}/service-worker.js`;

            navigator.serviceWorker
                .register(swUrl)
                .then((registration) => {
                    console.log('✅ Service Worker registered:', registration);

                    // Listen for updates
                    registration.addEventListener('updatefound', () => {
                        const newWorker = registration.installing;
                        if (newWorker) {
                            newWorker.addEventListener('statechange', () => {
                                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                    // New service worker available
                                    console.log('🔄 New content available, please refresh.');
                                    // Optionally show update notification to user
                                }
                            });
                        }
                    });

                    // Enable background sync if supported
                    if ('sync' in registration) {
                        console.log('✅ Background Sync supported');
                    }
                })
                .catch((error) => {
                    console.error('❌ Service Worker registration failed:', error);
                });
        });

        // Handle messages from service worker
        navigator.serviceWorker.addEventListener('message', (event) => {
            if (event.data.type === 'GET_ACCESS_TOKEN') {
                const token = localStorage.getItem('access_token');
                event.ports[0].postMessage(token);
            }
        });
    }
};

export const unregister = () => {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready
            .then((registration) => {
                registration.unregister();
            })
            .catch((error) => {
                console.error(error.message);
            });
    }
};

