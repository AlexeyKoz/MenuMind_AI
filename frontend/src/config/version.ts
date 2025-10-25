// MenuMind AI Version Configuration
export const APP_VERSION = '0.9.0';
export const APP_BUILD_DATE = '2025-10-25';
export const APP_NAME = 'MenuMind AI';

// Detailed version breakdown
export const VERSION_INFO = {
    major: 0,
    minor: 9,
    patch: 0,
    full: APP_VERSION,
    buildDate: APP_BUILD_DATE,
    name: APP_NAME,
};

// Get version string for display
export const getVersionString = (): string => {
    return `${APP_NAME} v${APP_VERSION}`;
};

// Check if version is pre-release (< 1.0.0)
export const isPreRelease = (): boolean => {
    return VERSION_INFO.major === 0;
};

export default VERSION_INFO;

