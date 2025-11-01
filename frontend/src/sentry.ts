import * as Sentry from '@sentry/react';

/**
 * Initialize Sentry for error tracking and performance monitoring
 */
export const initSentry = () => {
    // Only initialize in production or if explicitly enabled
    if (process.env.NODE_ENV === 'production' || process.env.REACT_APP_SENTRY_ENABLED === 'true') {
        Sentry.init({
            dsn: "https://a286cf89396658abbc772704749dded4@o4510275117383680.ingest.de.sentry.io/4510275122823248",
            integrations: [
                Sentry.browserTracingIntegration(),
                Sentry.replayIntegration({
                    maskAllText: true,
                    blockAllMedia: true,
                }),
            ],
            // Performance Monitoring
            tracesSampleRate: 1.0, // Capture 100% of transactions in development
            tracePropagationTargets: ["localhost", /^https:\/\/yourserver\.io\/api/],
            
            // Session Replay
            replaysSessionSampleRate: 0.1, // 10% of sessions
            replaysOnErrorSampleRate: 1.0, // 100% when errors occur
            
            // Environment
            environment: process.env.NODE_ENV || 'development',
            
            // Optional: Release version
            // release: "menumine-ai-frontend@" + process.env.REACT_APP_VERSION,
        });

        console.log('✅ Sentry initialized for error tracking');
    } else {
        console.log('ℹ️ Sentry disabled (development mode)');
    }
};

/**
 * Set user information in Sentry
 */
export const setSentryUser = (user: { 
    id: string; 
    email?: string; 
    username: string;
    first_name?: string;
}) => {
    Sentry.setUser({
        id: user.id,
        email: user.email,
        username: user.username,
        name: user.first_name || user.username,
    });
    console.log('👤 Sentry user context set:', user.username);
};

/**
 * Clear user information from Sentry (on logout)
 */
export const clearSentryUser = () => {
    Sentry.setUser(null);
    console.log('👤 Sentry user context cleared');
};

/**
 * Capture a custom error
 */
export const captureError = (error: Error, context?: Record<string, any>) => {
    if (context) {
        Sentry.setContext('custom', context);
    }
    Sentry.captureException(error);
};

/**
 * Capture a custom message
 */
export const captureMessage = (message: string, level: Sentry.SeverityLevel = 'info') => {
    Sentry.captureMessage(message, level);
};

