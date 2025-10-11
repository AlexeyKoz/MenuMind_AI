import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';
import { toast } from 'react-hot-toast';

interface UserSettings {
    id: string;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    birth_date: string | null;
    height_cm: number | null;
    weight_kg: number | null;
    activity_level: string;
    daily_calories_goal: number;
    daily_protein_goal: number;
    daily_carbs_goal: number;
    daily_fat_goal: number;
    dietary_restrictions: string[];
    allergies: string[];
    preferred_language: string;
    weight_unit: string;
    volume_unit: string;
    time_format: string;
    personal_color: string;
    shopping_role: string;
}

interface ConfirmationModalProps {
    isOpen: boolean;
    onConfirm: () => void;
    onCancel: () => void;
    title: string;
    message: string;
    changes: { [key: string]: any };
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
    isOpen,
    onConfirm,
    onCancel,
    title,
    message,
    changes
}) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
                <p className="text-gray-600 mb-4">{message}</p>

                <div className="bg-gray-50 rounded-lg p-3 mb-4">
                    <h4 className="font-medium text-gray-900 mb-2">Changes to be made:</h4>
                    <ul className="text-sm text-gray-700 space-y-1">
                        {Object.entries(changes).map(([key, value]) => (
                            <li key={key}>
                                <span className="font-medium">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</span> {value}
                            </li>
                        ))}
                    </ul>
                </div>

                <div className="flex justify-end space-x-3">
                    <button
                        onClick={onCancel}
                        className="px-4 py-2 text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onConfirm}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                        Confirm Changes
                    </button>
                </div>
            </div>
        </div>
    );
};

const SettingsPage: React.FC = () => {
    const { token, logout } = useAuth();
    const api = useMemo(() => new ApiService(token, () => {
        console.log('🔐 Token expired - logging out user');
        alert('Your session has expired. Please log in again.');
        logout();
    }), [token, logout]);

    const [settings, setSettings] = useState<UserSettings | null>(null);
    const [formData, setFormData] = useState<Partial<UserSettings>>({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [hasChanges, setHasChanges] = useState(false);
    const [showConfirmation, setShowConfirmation] = useState(false);
    const [pendingChanges, setPendingChanges] = useState<{ [key: string]: any }>({});

    const activityLevels = [
        { value: 'sedentary', label: 'Sedentary' },
        { value: 'light', label: 'Lightly Active' },
        { value: 'moderate', label: 'Moderately Active' },
        { value: 'very', label: 'Very Active' },
        { value: 'extra', label: 'Extra Active' }
    ];

    const languages = [
        { value: 'en', label: 'English' },
        { value: 'he', label: 'Hebrew' },
        { value: 'ru', label: 'Russian' }
    ];

    const weightUnits = [
        { value: 'kg', label: 'Kilograms' },
        { value: 'lbs', label: 'Pounds' }
    ];

    const volumeUnits = [
        { value: 'liters', label: 'Liters' },
        { value: 'gallons', label: 'Gallons' }
    ];

    const timeFormats = [
        { value: '24h', label: '24 Hour' },
        { value: '12h', label: '12 Hour (AM/PM)' }
    ];

    const shoppingRoles = [
        { value: 'creator', label: 'List Creator' },
        { value: 'collaborator', label: 'Collaborator' },
        { value: 'both', label: 'Both Creator and Collaborator' }
    ];

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            setLoading(true);
            const response = await api.get('/users/profile/user_settings/');
            setSettings(response);
            setFormData(response);
        } catch (error) {
            console.error('Failed to load settings:', error);
            toast.error('Failed to load settings');
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (field: string, value: any) => {
        const newFormData = { ...formData, [field]: value };
        setFormData(newFormData);

        // Check if there are changes
        if (settings) {
            const changes: { [key: string]: any } = {};
            let hasAnyChanges = false;

            Object.keys(newFormData).forEach(key => {
                if (newFormData[key as keyof UserSettings] !== settings[key as keyof UserSettings]) {
                    changes[key] = newFormData[key as keyof UserSettings];
                    hasAnyChanges = true;
                }
            });

            setHasChanges(hasAnyChanges);
            setPendingChanges(changes);
        }
    };

    const handleSave = () => {
        if (Object.keys(pendingChanges).length > 0) {
            setShowConfirmation(true);
        }
    };

    const confirmSave = async () => {
        try {
            setSaving(true);
            setShowConfirmation(false);

            const response = await api.patch('/users/profile/update_settings/', pendingChanges);

            if (response.success) {
                setSettings(response.data);
                setFormData(response.data);
                setHasChanges(false);
                setPendingChanges({});
                toast.success('Settings updated successfully!');
            } else {
                toast.error('Failed to update settings');
            }
        } catch (error) {
            console.error('Failed to save settings:', error);
            toast.error('Failed to save settings');
        } finally {
            setSaving(false);
        }
    };

    const resetForm = () => {
        if (settings) {
            setFormData(settings);
            setHasChanges(false);
            setPendingChanges({});
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading settings...</p>
                </div>
            </div>
        );
    }

    if (!settings) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <p className="text-red-600">Failed to load settings</p>
                    <button
                        onClick={loadSettings}
                        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="bg-white shadow rounded-lg">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <h1 className="text-2xl font-bold text-gray-900">⚙️ Settings & Preferences</h1>
                        <p className="mt-1 text-gray-600">Customize your account and application preferences</p>
                    </div>

                    <div className="p-6 space-y-8">
                        {/* Personal Information */}
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">👤 Personal Information</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        First Name
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.first_name || ''}
                                        onChange={(e) => handleInputChange('first_name', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Last Name
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.last_name || ''}
                                        onChange={(e) => handleInputChange('last_name', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Email
                                    </label>
                                    <input
                                        type="email"
                                        value={formData.email || ''}
                                        onChange={(e) => handleInputChange('email', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Birth Date
                                    </label>
                                    <input
                                        type="date"
                                        value={formData.birth_date || ''}
                                        onChange={(e) => handleInputChange('birth_date', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Physical Information */}
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">📏 Physical Information</h2>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Height (cm)
                                    </label>
                                    <input
                                        type="number"
                                        value={formData.height_cm || ''}
                                        onChange={(e) => handleInputChange('height_cm', e.target.value ? parseInt(e.target.value) : null)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                        min="50"
                                        max="300"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Weight (kg)
                                    </label>
                                    <input
                                        type="number"
                                        step="0.1"
                                        value={formData.weight_kg || ''}
                                        onChange={(e) => handleInputChange('weight_kg', e.target.value ? parseFloat(e.target.value) : null)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                        min="20"
                                        max="500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Activity Level
                                    </label>
                                    <select
                                        value={formData.activity_level || 'moderate'}
                                        onChange={(e) => handleInputChange('activity_level', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        {activityLevels.map(level => (
                                            <option key={level.value} value={level.value}>
                                                {level.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Unit Preferences */}
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">📐 Unit Preferences</h2>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Weight Unit
                                    </label>
                                    <select
                                        value={formData.weight_unit || 'kg'}
                                        onChange={(e) => handleInputChange('weight_unit', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        {weightUnits.map(unit => (
                                            <option key={unit.value} value={unit.value}>
                                                {unit.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Volume Unit
                                    </label>
                                    <select
                                        value={formData.volume_unit || 'liters'}
                                        onChange={(e) => handleInputChange('volume_unit', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        {volumeUnits.map(unit => (
                                            <option key={unit.value} value={unit.value}>
                                                {unit.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Time Format
                                    </label>
                                    <select
                                        value={formData.time_format || '24h'}
                                        onChange={(e) => handleInputChange('time_format', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        {timeFormats.map(format => (
                                            <option key={format.value} value={format.value}>
                                                {format.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Application Preferences */}
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">🎨 Application Preferences</h2>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Language
                                    </label>
                                    <select
                                        value={formData.preferred_language || 'en'}
                                        onChange={(e) => handleInputChange('preferred_language', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        {languages.map(lang => (
                                            <option key={lang.value} value={lang.value}>
                                                {lang.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Personal Color
                                    </label>
                                    <div className="flex items-center space-x-2">
                                        <input
                                            type="color"
                                            value={formData.personal_color || '#4F46E5'}
                                            onChange={(e) => handleInputChange('personal_color', e.target.value)}
                                            className="w-12 h-10 border border-gray-300 rounded-md"
                                        />
                                        <input
                                            type="text"
                                            value={formData.personal_color || '#4F46E5'}
                                            onChange={(e) => handleInputChange('personal_color', e.target.value)}
                                            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                            placeholder="#4F46E5"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Shopping Role
                                    </label>
                                    <select
                                        value={formData.shopping_role || 'both'}
                                        onChange={(e) => handleInputChange('shopping_role', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        {shoppingRoles.map(role => (
                                            <option key={role.value} value={role.value}>
                                                {role.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Nutrition Goals */}
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">🥗 Nutrition Goals</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Daily Calories
                                    </label>
                                    <input
                                        type="number"
                                        value={formData.daily_calories_goal || 2000}
                                        onChange={(e) => handleInputChange('daily_calories_goal', parseInt(e.target.value))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                        min="800"
                                        max="5000"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Protein (g)
                                    </label>
                                    <input
                                        type="number"
                                        value={formData.daily_protein_goal || 50}
                                        onChange={(e) => handleInputChange('daily_protein_goal', parseInt(e.target.value))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                        min="10"
                                        max="300"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Carbs (g)
                                    </label>
                                    <input
                                        type="number"
                                        value={formData.daily_carbs_goal || 250}
                                        onChange={(e) => handleInputChange('daily_carbs_goal', parseInt(e.target.value))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                        min="20"
                                        max="800"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Fat (g)
                                    </label>
                                    <input
                                        type="number"
                                        value={formData.daily_fat_goal || 65}
                                        onChange={(e) => handleInputChange('daily_fat_goal', parseInt(e.target.value))}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                                        min="10"
                                        max="200"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-between">
                        <button
                            onClick={resetForm}
                            disabled={!hasChanges || saving}
                            className="px-4 py-2 text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            Reset
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={!hasChanges || saving}
                            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
                        >
                            {saving && (
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            )}
                            {saving ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </div>
            </div>

            <ConfirmationModal
                isOpen={showConfirmation}
                onConfirm={confirmSave}
                onCancel={() => setShowConfirmation(false)}
                title="Confirm Settings Changes"
                message="Are you sure you want to save these changes to your settings?"
                changes={pendingChanges}
            />
        </div>
    );
};

export default SettingsPage;
