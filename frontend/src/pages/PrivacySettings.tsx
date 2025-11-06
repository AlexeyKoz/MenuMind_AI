/**
 * Privacy Settings Page
 * 
 * GDPR/CCPA/Israel Amendment 13 Compliant
 * 
 * Features:
 * - Data export (portability)
 * - Account deletion (right to erasure)
 * - Cookie preferences management
 * - Data usage transparency
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './PrivacySettings.css';

interface CookieSettings {
    essential: boolean;
    functional: boolean;
    analytics: boolean;
    performance: boolean;
}

const PrivacySettings: React.FC = () => {
    const { user } = useAuth();
    const [cookieSettings, setCookieSettings] = useState<CookieSettings>({
        essential: true,
        functional: false,
        analytics: false,
        performance: false,
    });
    const [loading, setLoading] = useState(false);
    const [exportLoading, setExportLoading] = useState(false);
    const [deleteLoading, setDeleteLoading] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [deleteEmail, setDeleteEmail] = useState('');
    const [message, setMessage] = useState({ type: '', text: '' });

    useEffect(() => {
        loadCookieSettings();
    }, []);

    const loadCookieSettings = async () => {
        try {
            const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/legal/get_cookie_consent/`, {
                credentials: 'include',
            });
            const data = await response.json();

            if (data.has_consent && data.settings) {
                setCookieSettings(data.settings);
            }
        } catch (error) {
            console.error('Error loading cookie settings:', error);
        }
    };

    const handleSaveCookieSettings = async () => {
        setLoading(true);
        setMessage({ type: '', text: '' });

        try {
            const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/legal/cookie_consent/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    consent_type: 'custom',
                    functional: cookieSettings.functional,
                    analytics: cookieSettings.analytics,
                    performance: cookieSettings.performance,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to save cookie settings');
            }

            setMessage({ type: 'success', text: 'Cookie preferences saved successfully!' });

            // Reload page to apply new settings
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } catch (error) {
            console.error('Error saving cookie settings:', error);
            setMessage({ type: 'error', text: 'Failed to save cookie preferences. Please try again.' });
        } finally {
            setLoading(false);
        }
    };

    const handleExportData = async () => {
        setExportLoading(true);
        setMessage({ type: '', text: '' });

        try {
            const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
            const token = localStorage.getItem('token');

            const response = await fetch(`${apiUrl}/api/users/export-data/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to request data export');
            }

            const data = await response.json();

            setMessage({
                type: 'success',
                text: 'Data export requested! You will receive an email with a download link within 24-48 hours.'
            });
        } catch (error) {
            console.error('Error requesting data export:', error);
            setMessage({
                type: 'error',
                text: 'Failed to request data export. Please try again or contact support.'
            });
        } finally {
            setExportLoading(false);
        }
    };

    const handleDeleteAccount = async () => {
        if (deleteEmail !== user?.email) {
            setMessage({
                type: 'error',
                text: 'Email does not match your account email. Please try again.'
            });
            return;
        }

        setDeleteLoading(true);
        setMessage({ type: '', text: '' });

        try {
            const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
            const token = localStorage.getItem('token');

            const response = await fetch(`${apiUrl}/api/users/delete-account/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to request account deletion');
            }

            const data = await response.json();

            setMessage({
                type: 'success',
                text: 'Account deletion requested. Your account will be permanently deleted within 30 days. You will receive a confirmation email.'
            });

            // Log out after 3 seconds
            setTimeout(() => {
                localStorage.clear();
                window.location.href = '/login';
            }, 3000);
        } catch (error) {
            console.error('Error requesting account deletion:', error);
            setMessage({
                type: 'error',
                text: 'Failed to request account deletion. Please contact support.'
            });
        } finally {
            setDeleteLoading(false);
        }
    };

    if (!user) {
        return (
            <div className="privacy-settings">
                <div className="privacy-settings__not-logged-in">
                    <h2>Please Log In</h2>
                    <p>You must be logged in to manage your privacy settings.</p>
                    <a href="/login" className="privacy-settings__button privacy-settings__button--primary">
                        Go to Login
                    </a>
                </div>
            </div>
        );
    }

    return (
        <div className="privacy-settings">
            <div className="privacy-settings__container">
                <div className="privacy-settings__header">
                    <h1 className="privacy-settings__title">Privacy Settings</h1>
                    <p className="privacy-settings__subtitle">
                        Manage your data, privacy preferences, and exercising your rights under GDPR, CCPA, and Israel Privacy Protection Law.
                    </p>
                </div>

                {message.text && (
                    <div className={`privacy-settings__message privacy-settings__message--${message.type}`}>
                        {message.text}
                    </div>
                )}

                {/* Cookie Preferences Section */}
                <section className="privacy-settings__section">
                    <div className="privacy-settings__section-header">
                        <h2 className="privacy-settings__section-title">🍪 Cookie Preferences</h2>
                        <p className="privacy-settings__section-description">
                            Control which cookies we can use. Changes will take effect immediately after saving.
                        </p>
                    </div>

                    <div className="privacy-settings__cookie-options">
                        <div className="privacy-settings__cookie-option">
                            <label className="privacy-settings__label">
                                <input
                                    type="checkbox"
                                    checked={true}
                                    disabled
                                    className="privacy-settings__checkbox"
                                />
                                <div className="privacy-settings__option-text">
                                    <strong>Essential Cookies</strong>
                                    <span className="privacy-settings__required">(Required)</span>
                                    <p>Necessary for the website to function. Cannot be disabled.</p>
                                </div>
                            </label>
                        </div>

                        <div className="privacy-settings__cookie-option">
                            <label className="privacy-settings__label">
                                <input
                                    type="checkbox"
                                    checked={cookieSettings.functional}
                                    onChange={(e) => setCookieSettings({ ...cookieSettings, functional: e.target.checked })}
                                    className="privacy-settings__checkbox"
                                />
                                <div className="privacy-settings__option-text">
                                    <strong>Functional Cookies</strong>
                                    <p>Remember your preferences and settings.</p>
                                </div>
                            </label>
                        </div>

                        <div className="privacy-settings__cookie-option">
                            <label className="privacy-settings__label">
                                <input
                                    type="checkbox"
                                    checked={cookieSettings.analytics}
                                    onChange={(e) => setCookieSettings({ ...cookieSettings, analytics: e.target.checked })}
                                    className="privacy-settings__checkbox"
                                />
                                <div className="privacy-settings__option-text">
                                    <strong>Analytics Cookies</strong>
                                    <p>Help us understand how you use our site.</p>
                                </div>
                            </label>
                        </div>

                        <div className="privacy-settings__cookie-option">
                            <label className="privacy-settings__label">
                                <input
                                    type="checkbox"
                                    checked={cookieSettings.performance}
                                    onChange={(e) => setCookieSettings({ ...cookieSettings, performance: e.target.checked })}
                                    className="privacy-settings__checkbox"
                                />
                                <div className="privacy-settings__option-text">
                                    <strong>Performance Cookies</strong>
                                    <p>Monitor and optimize site performance.</p>
                                </div>
                            </label>
                        </div>
                    </div>

                    <button
                        onClick={handleSaveCookieSettings}
                        disabled={loading}
                        className="privacy-settings__button privacy-settings__button--primary"
                    >
                        {loading ? 'Saving...' : 'Save Cookie Preferences'}
                    </button>
                </section>

                {/* Data Portability Section */}
                <section className="privacy-settings__section">
                    <div className="privacy-settings__section-header">
                        <h2 className="privacy-settings__section-title">📦 Export Your Data</h2>
                        <p className="privacy-settings__section-description">
                            Download all your data in a machine-readable format. This includes your profile, recipes, meal plans, and settings.
                            <br />
                            <strong>Processing time:</strong> Up to 48 hours. You'll receive an email with a secure download link.
                        </p>
                    </div>

                    <div className="privacy-settings__data-info">
                        <div className="privacy-settings__info-item">
                            <strong>Account:</strong> {user.email}
                        </div>
                        <div className="privacy-settings__info-item">
                            <strong>Format:</strong> JSON (machine-readable)
                        </div>
                        <div className="privacy-settings__info-item">
                            <strong>Includes:</strong> Profile, recipes, meal plans, preferences, activity logs
                        </div>
                    </div>

                    <button
                        onClick={handleExportData}
                        disabled={exportLoading}
                        className="privacy-settings__button privacy-settings__button--secondary"
                    >
                        {exportLoading ? 'Requesting...' : 'Request Data Export'}
                    </button>
                </section>

                {/* Account Deletion Section */}
                <section className="privacy-settings__section privacy-settings__section--danger">
                    <div className="privacy-settings__section-header">
                        <h2 className="privacy-settings__section-title">🗑️ Delete Your Account</h2>
                        <p className="privacy-settings__section-description">
                            Permanently delete your account and all associated data. This action cannot be undone.
                            <br />
                            <strong>Grace period:</strong> 30 days. You can cancel the deletion request within this period.
                        </p>
                    </div>

                    <div className="privacy-settings__warning">
                        <strong>⚠️ Warning:</strong> This will permanently delete:
                        <ul>
                            <li>Your account and profile</li>
                            <li>All your recipes and meal plans</li>
                            <li>All your preferences and settings</li>
                            <li>All your activity history</li>
                        </ul>
                        <p>Backups will be retained for 30 days, then permanently destroyed.</p>
                    </div>

                    {!showDeleteConfirm ? (
                        <button
                            onClick={() => setShowDeleteConfirm(true)}
                            className="privacy-settings__button privacy-settings__button--danger"
                        >
                            Delete My Account
                        </button>
                    ) : (
                        <div className="privacy-settings__delete-confirm">
                            <p><strong>Are you absolutely sure?</strong></p>
                            <p>To confirm, please enter your email address:</p>
                            <input
                                type="email"
                                value={deleteEmail}
                                onChange={(e) => setDeleteEmail(e.target.value)}
                                placeholder={user.email}
                                className="privacy-settings__input"
                            />
                            <div className="privacy-settings__delete-actions">
                                <button
                                    onClick={handleDeleteAccount}
                                    disabled={deleteLoading || deleteEmail !== user.email}
                                    className="privacy-settings__button privacy-settings__button--danger"
                                >
                                    {deleteLoading ? 'Processing...' : 'Yes, Delete My Account'}
                                </button>
                                <button
                                    onClick={() => {
                                        setShowDeleteConfirm(false);
                                        setDeleteEmail('');
                                    }}
                                    className="privacy-settings__button privacy-settings__button--secondary"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}
                </section>

                {/* Legal Links */}
                <section className="privacy-settings__legal-links">
                    <h3>Legal Information</h3>
                    <div className="privacy-settings__links">
                        <a href="/legal/privacy" target="_blank" rel="noopener noreferrer">
                            Privacy Policy
                        </a>
                        <a href="/legal/terms" target="_blank" rel="noopener noreferrer">
                            Terms of Service
                        </a>
                        <a href="/legal/cookies" target="_blank" rel="noopener noreferrer">
                            Cookie Policy
                        </a>
                        <a href="mailto:Bishulme@gmail.com">
                            Contact Privacy Team
                        </a>
                    </div>
                </section>
            </div>
        </div>
    );
};

export default PrivacySettings;

