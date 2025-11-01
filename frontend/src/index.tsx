import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import i18n from './i18n'; // Initialize i18n
import AppWithProviders from './AppWithProviders';
import * as serviceWorkerRegistration from './serviceWorkerRegistration';
import { initSentry } from './sentry';

// Initialize Sentry for error tracking
initSentry();

const root = ReactDOM.createRoot(
    document.getElementById('root') as HTMLElement
);

// Disabled StrictMode to prevent duplicate WebSocket connections/listeners
// StrictMode intentionally double-mounts components in development
root.render(
    <AppWithProviders />
);

// Register service worker for PWA support
serviceWorkerRegistration.register();