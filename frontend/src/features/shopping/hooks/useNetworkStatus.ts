import { useState, useEffect } from 'react';

export const useNetworkStatus = () => {
    const [isOnline, setIsOnline] = useState(navigator.onLine);
    const [connectionType, setConnectionType] = useState<string>('unknown');

    useEffect(() => {
        const handleOnline = () => {
            setIsOnline(true);
            console.log('🟢 Connection restored');
        };

        const handleOffline = () => {
            setIsOnline(false);
            console.log('🔴 Connection lost');
        };

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        // Get connection type if available
        const connection = (navigator as any).connection;
        if (connection) {
            setConnectionType(connection.effectiveType);
            connection.addEventListener('change', () => {
                setConnectionType(connection.effectiveType);
            });
        }

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    return { isOnline, connectionType };
};

