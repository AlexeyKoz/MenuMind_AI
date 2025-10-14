import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import './i18n'; // Initialize i18n
import App from './App';

const root = ReactDOM.createRoot(
    document.getElementById('root') as HTMLElement
);

// Disabled StrictMode to prevent duplicate WebSocket connections/listeners
// StrictMode intentionally double-mounts components in development
root.render(
    <App />
);