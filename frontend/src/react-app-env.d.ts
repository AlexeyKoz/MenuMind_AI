/// <reference types="react-scripts" />

// Google Analytics gtag type declaration
interface Window {
    gtag?: (
        command: 'config' | 'event' | 'consent',
        targetId: string | 'update',
        config?: Record<string, any>
    ) => void;
}
