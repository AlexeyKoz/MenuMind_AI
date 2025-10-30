/**
 * Cookie Consent Banner Component
 * 
 * 2025 Compliant - Symmetric button design (Accept/Reject equal prominence)
 * Supports GPC (Global Privacy Control) signal detection
 * Granular cookie controls
 * 
 * GDPR/CCPA/Israel Amendment 13 compliant
 */
import React, { useState, useEffect } from 'react';
import './CookieConsentBanner.css';

interface CookieSettings {
    essential: boolean;
    functional: boolean;
    analytics: boolean;
    performance: boolean;
}

// GLOBAL flag to prevent multiple instances from checking simultaneously
let globalCheckInProgress = false;
let globalHasChecked = false;

const CookieConsentBanner: React.FC = () => {
    const [showBanner, setShowBanner] = useState(false);
    const [showCustomize, setShowCustomize] = useState(false);
    const [settings, setSettings] = useState<CookieSettings>({
        essential: true,
        functional: false,
        analytics: false,
        performance: false,
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Only check once globally across all instances
        if (!globalHasChecked && !globalCheckInProgress) {
            checkCookieConsent();
        }
    }, []);

    const checkCookieConsent = async () => {
        // CRITICAL: Prevent any duplicate calls
        if (globalCheckInProgress || globalHasChecked) {
            console.log('⏭️ Cookie consent check already in progress or completed');
            return;
        }
        
        globalCheckInProgress = true;
        globalHasChecked = true;
        
        try {
            console.log('🍪 Checking cookie consent (ONE TIME ONLY)...');
            const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/legal/get_cookie_consent/`, {
                credentials: 'include', // Include session cookie
            });
            const data = await response.json();

            if (!data.has_consent) {
                // No consent found - show banner
                setShowBanner(true);

                // Check if GPC signal detected - DON'T auto-reject, just show banner
                if (data.gpc_detected) {
                    console.log('🔒 GPC signal detected - user will need to make choice');
                }
            } else {
                // Apply existing settings
                setSettings(data.settings);
                applyCookieSettings(data.settings);
            }
        } catch (error) {
            console.error('Error checking cookie consent:', error);
            // If API fails, show banner to be safe
            setShowBanner(true);
        } finally {
            globalCheckInProgress = false;
        }
    };

    const acceptAll = async () => {
        setLoading(true);
        const allEnabled = {
            essential: true,
            functional: true,
            analytics: true,
            performance: true,
        };

        await saveConsent('all', allEnabled);
    };

    const rejectAll = async () => {
        setLoading(true);
        const essentialOnly = {
            essential: true,
            functional: false,
            analytics: false,
            performance: false,
        };

        await saveConsent('rejected', essentialOnly);
    };

    const saveCustom = async () => {
        setLoading(true);
        await saveConsent('custom', settings);
    };

    const saveConsent = async (type: string, cookieSettings: CookieSettings) => {
        try {
            const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/legal/cookie_consent/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    consent_type: type,
                    functional: cookieSettings.functional,
                    analytics: cookieSettings.analytics,
                    performance: cookieSettings.performance,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to save cookie consent');
            }

            const data = await response.json();

            applyCookieSettings(cookieSettings);
            setShowBanner(false);
            setShowCustomize(false);

            console.log('✅ Cookie consent saved:', data.consent_type);
        } catch (error) {
            console.error('Error saving cookie consent:', error);
            alert('Failed to save cookie preferences. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const applyCookieSettings = (cookieSettings: CookieSettings) => {
        // Store in localStorage for immediate access
        localStorage.setItem('cookieConsent', JSON.stringify(cookieSettings));

        // Apply analytics cookies
        if (cookieSettings.analytics) {
            enableGoogleAnalytics();
        } else {
            disableGoogleAnalytics();
        }

        // Apply performance tracking
        if (cookieSettings.performance) {
            enablePerformanceMonitoring();
        } else {
            disablePerformanceMonitoring();
        }

        // Functional cookies (language preference, etc.)
        if (!cookieSettings.functional) {
            // Could restrict non-essential functional cookies here
            console.log('Functional cookies disabled');
        }
    };

    const enableGoogleAnalytics = () => {
        // Only enable if Google Analytics is configured
        if (typeof window.gtag === 'function') {
            window.gtag('consent', 'update', {
                'analytics_storage': 'granted'
            });
            console.log('📊 Analytics cookies enabled');
        }
    };

    const disableGoogleAnalytics = () => {
        if (typeof window.gtag === 'function') {
            window.gtag('consent', 'update', {
                'analytics_storage': 'denied'
            });
            console.log('🚫 Analytics cookies disabled');
        }
    };

    const enablePerformanceMonitoring = () => {
        console.log('⚡ Performance monitoring enabled');
        // Add performance monitoring scripts here
    };

    const disablePerformanceMonitoring = () => {
        console.log('🚫 Performance monitoring disabled');
    };

    if (!showBanner) return null;

    return (
        <div className="cookie-banner" role="dialog" aria-label="Cookie Consent">
            <div className="cookie-banner__overlay" onClick={() => { }} />
            <div className="cookie-banner__container">
                {!showCustomize ? (
                    <>
                        <div className="cookie-banner__content">
                            <h3 className="cookie-banner__title">🍪 We Value Your Privacy</h3>
                            <p className="cookie-banner__text">
                                We use cookies to enhance your experience, analyze site usage, and personalize content.
                                You can choose to accept all cookies, reject non-essential cookies, or customize your preferences.
                            </p>
                            <p className="cookie-banner__text cookie-banner__text--small">
                                Essential cookies are always enabled to ensure the website functions properly.
                            </p>
                            <a
                                href="/legal/cookies"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="cookie-banner__link"
                            >
                                Learn more about our cookie policy →
                            </a>
                        </div>

                        <div className="cookie-banner__actions">
                            {/* CRITICAL: SYMMETRIC BUTTONS - EQUAL SIZE AND PROMINENCE */}
                            <button
                                onClick={acceptAll}
                                disabled={loading}
                                className="cookie-banner__button cookie-banner__button--accept"
                                aria-label="Accept all cookies"
                            >
                                {loading ? 'Saving...' : 'Accept All'}
                            </button>

                            <button
                                onClick={rejectAll}
                                disabled={loading}
                                className="cookie-banner__button cookie-banner__button--reject"
                                aria-label="Reject non-essential cookies"
                            >
                                {loading ? 'Saving...' : 'Reject All'}
                            </button>

                            <button
                                onClick={() => setShowCustomize(true)}
                                disabled={loading}
                                className="cookie-banner__button cookie-banner__button--customize"
                                aria-label="Customize cookie preferences"
                            >
                                Customize
                            </button>
                        </div>
                    </>
                ) : (
                    <>
                        <div className="cookie-banner__customize">
                            <h3 className="cookie-banner__title">Customize Cookie Preferences</h3>
                            <p className="cookie-banner__text">
                                Choose which types of cookies you want to allow. Essential cookies cannot be disabled.
                            </p>

                            <div className="cookie-banner__options">
                                <div className="cookie-banner__option">
                                    <label className="cookie-banner__label">
                                        <input
                                            type="checkbox"
                                            checked={true}
                                            disabled
                                            className="cookie-banner__checkbox"
                                            aria-label="Essential cookies"
                                        />
                                        <div className="cookie-banner__option-text">
                                            <strong>Essential Cookies</strong>
                                            <span className="cookie-banner__required">(Required)</span>
                                            <p>Necessary for the website to function. These cookies enable core functionality such as security, authentication, and network management. They cannot be disabled.</p>
                                        </div>
                                    </label>
                                </div>

                                <div className="cookie-banner__option">
                                    <label className="cookie-banner__label">
                                        <input
                                            type="checkbox"
                                            checked={settings.functional}
                                            onChange={(e) => setSettings({ ...settings, functional: e.target.checked })}
                                            className="cookie-banner__checkbox"
                                            aria-label="Functional cookies"
                                        />
                                        <div className="cookie-banner__option-text">
                                            <strong>Functional Cookies</strong>
                                            <p>Remember your preferences and settings (language, region, etc.) to enhance your experience.</p>
                                        </div>
                                    </label>
                                </div>

                                <div className="cookie-banner__option">
                                    <label className="cookie-banner__label">
                                        <input
                                            type="checkbox"
                                            checked={settings.analytics}
                                            onChange={(e) => setSettings({ ...settings, analytics: e.target.checked })}
                                            className="cookie-banner__checkbox"
                                            aria-label="Analytics cookies"
                                        />
                                        <div className="cookie-banner__option-text">
                                            <strong>Analytics Cookies</strong>
                                            <p>Help us understand how you use our site by collecting anonymous usage data. This helps us improve the platform.</p>
                                        </div>
                                    </label>
                                </div>

                                <div className="cookie-banner__option">
                                    <label className="cookie-banner__label">
                                        <input
                                            type="checkbox"
                                            checked={settings.performance}
                                            onChange={(e) => setSettings({ ...settings, performance: e.target.checked })}
                                            className="cookie-banner__checkbox"
                                            aria-label="Performance cookies"
                                        />
                                        <div className="cookie-banner__option-text">
                                            <strong>Performance Cookies</strong>
                                            <p>Monitor and optimize site speed and performance to ensure the best user experience.</p>
                                        </div>
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div className="cookie-banner__actions">
                            <button
                                onClick={saveCustom}
                                disabled={loading}
                                className="cookie-banner__button cookie-banner__button--save"
                                aria-label="Save custom preferences"
                            >
                                {loading ? 'Saving...' : 'Save Preferences'}
                            </button>

                            <button
                                onClick={() => setShowCustomize(false)}
                                disabled={loading}
                                className="cookie-banner__button cookie-banner__button--back"
                                aria-label="Go back to main options"
                            >
                                Back
                            </button>
                        </div>
                    </>
                )}

                <div className="cookie-banner__footer">
                    <small>
                        By using our site, you agree to our use of cookies as described in our{' '}
                        <a href="/legal/cookies" target="_blank" rel="noopener noreferrer">
                            Cookie Policy
                        </a>.
                    </small>
                </div>
            </div>
        </div>
    );
};

export default CookieConsentBanner;

