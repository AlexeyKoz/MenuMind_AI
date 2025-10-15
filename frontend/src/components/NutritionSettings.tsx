import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import type { UserNutritionSettings } from '../types';
import ApiService from '../services/api';
import { Shield, Sparkles, Target, MessageCircle, Eye, EyeOff } from 'lucide-react';

interface NutritionSettingsProps {
    api: ApiService;
}

const NutritionSettings: React.FC<NutritionSettingsProps> = ({ api }) => {
    const [settings, setSettings] = useState<UserNutritionSettings | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            const data = await api.getNutritionSettings();
            setSettings(data);
        } catch (error) {
            console.error('Failed to load nutrition settings:', error);
            toast.error('Failed to load nutrition settings');
        } finally {
            setLoading(false);
        }
    };

    const updateSettings = async (updates: Partial<UserNutritionSettings>) => {
        if (!settings) return;

        setSaving(true);
        try {
            const newSettings = { ...settings, ...updates };
            await api.updateNutritionSettings(updates);
            setSettings(newSettings);
            toast.success('Settings updated!');
        } catch (error: any) {
            console.error('Failed to update settings:', error);
            toast.error(error.message || 'Failed to update settings');
        } finally {
            setSaving(false);
        }
    };

    const Toggle: React.FC<{
        enabled: boolean;
        onChange: (enabled: boolean) => void;
        disabled?: boolean;
        size?: 'sm' | 'lg';
    }> = ({ enabled, onChange, disabled, size = 'sm' }) => {
        const sizeClasses = size === 'lg'
            ? 'w-16 h-8 after:h-6 after:w-6 after:top-1 after:left-1'
            : 'w-11 h-6 after:h-5 after:w-5 after:top-0.5 after:left-[2px]';

        return (
            <button
                type="button"
                onClick={() => !disabled && onChange(!enabled)}
                disabled={disabled}
                className={`
                    ${sizeClasses}
                    relative inline-flex items-center rounded-full transition-colors
                    ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    ${enabled ? 'bg-green-600' : 'bg-gray-300'}
                    after:content-[''] after:absolute after:bg-white after:rounded-full after:transition-transform
                    ${enabled ? 'after:translate-x-full' : 'after:translate-x-0'}
                `}
            >
                <span className="sr-only">{enabled ? 'Enabled' : 'Disabled'}</span>
            </button>
        );
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    if (!settings) return null;

    return (
        <div className="space-y-8">
            {/* Master AI Coach Toggle */}
            <div className="bg-gradient-to-br from-purple-50 to-indigo-50 border-2 border-purple-200 rounded-xl p-6">
                <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                            <Sparkles className="w-6 h-6 text-purple-600" />
                            <h3 className="text-xl font-bold text-gray-900">AI Nutrition Coach</h3>
                        </div>
                        <p className="text-gray-700 text-sm">
                            {settings.ai_coach_enabled
                                ? '✅ AI Coach is currently ON - You\'ll get personalized meal suggestions and coaching'
                                : '⚠️ AI Coach is currently OFF - Manual logging only'}
                        </p>
                    </div>
                    <Toggle
                        enabled={settings.ai_coach_enabled}
                        onChange={(enabled) => updateSettings({ ai_coach_enabled: enabled })}
                        size="lg"
                    />
                </div>

                {!settings.ai_coach_enabled && (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mt-4">
                        <p className="text-amber-800 text-sm">
                            💡 <strong>Enable AI Coach</strong> to get smart meal suggestions based on your recipes, inventory, and goals!
                        </p>
                    </div>
                )}
            </div>

            {/* Data Access Permissions */}
            <div className={`bg-white rounded-xl border-2 p-6 ${!settings.ai_coach_enabled ? 'opacity-50' : ''}`}>
                <div className="flex items-center gap-3 mb-4">
                    <Shield className="w-5 h-5 text-indigo-600" />
                    <h3 className="text-lg font-bold text-gray-900">AI Data Access Permissions</h3>
                </div>
                <p className="text-gray-600 text-sm mb-6">
                    Control what data the AI can access to provide suggestions
                </p>

                <div className="space-y-4">
                    {/* Content Permissions */}
                    <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="font-medium text-gray-900 mb-3">Your Content</h4>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <div>
                                    <label className="text-sm font-medium text-gray-700">View my Recipes</label>
                                    <p className="text-xs text-gray-500">AI can suggest meals from your saved recipes</p>
                                </div>
                                <Toggle
                                    enabled={settings.allow_recipes_access}
                                    onChange={(enabled) => updateSettings({ allow_recipes_access: enabled })}
                                    disabled={!settings.ai_coach_enabled}
                                />
                            </div>

                            <div className="flex items-center justify-between">
                                <div>
                                    <label className="text-sm font-medium text-gray-700">View my Inventory</label>
                                    <p className="text-xs text-gray-500">AI can suggest meals from available ingredients</p>
                                </div>
                                <Toggle
                                    enabled={settings.allow_inventory_access}
                                    onChange={(enabled) => updateSettings({ allow_inventory_access: enabled })}
                                    disabled={!settings.ai_coach_enabled}
                                />
                            </div>

                            <div className="flex items-center justify-between">
                                <div>
                                    <label className="text-sm font-medium text-gray-700">View my Shopping Lists</label>
                                    <p className="text-xs text-gray-500">AI can understand your shopping patterns</p>
                                </div>
                                <Toggle
                                    enabled={settings.allow_shopping_access}
                                    onChange={(enabled) => updateSettings({ allow_shopping_access: enabled })}
                                    disabled={!settings.ai_coach_enabled}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Personal Data Permissions */}
                    <div className="bg-blue-50 rounded-lg p-4 border-2 border-blue-200">
                        <div className="flex items-center justify-between mb-3">
                            <div>
                                <h4 className="font-medium text-gray-900">Personal Profile Data</h4>
                                <p className="text-xs text-gray-600 mt-1">
                                    ℹ️ When OFF: You set goals manually<br />
                                    ℹ️ When ON: AI calculates optimal goals for you
                                </p>
                            </div>
                            <Toggle
                                enabled={settings.allow_personal_data_access}
                                onChange={(enabled) => {
                                    updateSettings({
                                        allow_personal_data_access: enabled,
                                        ...(enabled === false && {
                                            allow_weight_data: false,
                                            allow_height_data: false,
                                            allow_age_data: false,
                                            allow_gender_data: false,
                                            allow_activity_level: false,
                                            allow_health_conditions: false
                                        })
                                    });
                                }}
                                disabled={!settings.ai_coach_enabled}
                            />
                        </div>

                        {settings.allow_personal_data_access && settings.ai_coach_enabled && (
                            <div className="mt-4 bg-white rounded-lg p-3 space-y-2">
                                <p className="text-xs font-medium text-gray-700 mb-2">AI can see:</p>
                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.allow_weight_data}
                                        onChange={(e) => updateSettings({ allow_weight_data: e.target.checked })}
                                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                    />
                                    <span className="text-sm text-gray-700">Weight & Height</span>
                                </label>
                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.allow_age_data}
                                        onChange={(e) => updateSettings({ allow_age_data: e.target.checked })}
                                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                    />
                                    <span className="text-sm text-gray-700">Age & Gender</span>
                                </label>
                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.allow_gender_data}
                                        onChange={(e) => updateSettings({ allow_gender_data: e.target.checked })}
                                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                    />
                                    <span className="text-sm text-gray-700">Gender</span>
                                </label>
                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.allow_activity_level}
                                        onChange={(e) => updateSettings({ allow_activity_level: e.target.checked })}
                                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                    />
                                    <span className="text-sm text-gray-700">Activity Level</span>
                                </label>
                                <label className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.allow_health_conditions}
                                        onChange={(e) => updateSettings({ allow_health_conditions: e.target.checked })}
                                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                    />
                                    <span className="text-sm text-gray-700">Health Conditions & Allergies</span>
                                </label>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Goal Setting Mode */}
            <div className="bg-white rounded-xl border-2 p-6">
                <div className="flex items-center gap-3 mb-4">
                    <Target className="w-5 h-5 text-green-600" />
                    <h3 className="text-lg font-bold text-gray-900">Nutrition Goals</h3>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Goal Setting Mode</label>
                        <div className="space-y-2">
                            <label className="flex items-start gap-3 p-3 border-2 rounded-lg cursor-pointer hover:bg-gray-50 transition">
                                <input
                                    type="radio"
                                    name="goal_mode"
                                    value="manual"
                                    checked={settings.goal_mode === 'manual'}
                                    onChange={(e) => updateSettings({ goal_mode: 'manual' })}
                                    className="mt-0.5"
                                />
                                <div className="flex-1">
                                    <div className="font-medium text-gray-900">✏️ Manual - I set my own goals</div>
                                    <div className="text-xs text-gray-600 mt-1">
                                        You manually enter your daily calorie and macro goals below
                                    </div>
                                </div>
                            </label>

                            <label className={`flex items-start gap-3 p-3 border-2 rounded-lg cursor-pointer hover:bg-gray-50 transition ${!settings.allow_personal_data_access ? 'opacity-50 cursor-not-allowed' : ''}`}>
                                <input
                                    type="radio"
                                    name="goal_mode"
                                    value="ai_calculated"
                                    checked={settings.goal_mode === 'ai_calculated'}
                                    onChange={(e) => settings.allow_personal_data_access && updateSettings({ goal_mode: 'ai_calculated' })}
                                    disabled={!settings.allow_personal_data_access}
                                    className="mt-0.5"
                                />
                                <div className="flex-1">
                                    <div className="font-medium text-gray-900">
                                        🤖 AI Calculated - Based on my profile
                                    </div>
                                    <div className="text-xs text-gray-600 mt-1">
                                        {settings.allow_personal_data_access
                                            ? 'AI calculates optimal goals using BMR/TDEE formulas'
                                            : '⚠️ Requires "Personal Profile Data" access to be enabled'}
                                    </div>
                                </div>
                            </label>
                        </div>
                    </div>

                    {/* Manual Goals Input */}
                    <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="font-medium text-gray-900 mb-3">
                            {settings.goal_mode === 'manual' ? 'Your Goals' : 'Manual Goals (used as fallback)'}
                        </h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Daily Calories (kcal)
                                </label>
                                <input
                                    type="number"
                                    value={settings.manual_calories_goal || 2000}
                                    onChange={(e) => updateSettings({ manual_calories_goal: parseInt(e.target.value) })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                    min="500"
                                    max="5000"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Daily Protein (g)
                                </label>
                                <input
                                    type="number"
                                    value={settings.manual_protein_goal || 150}
                                    onChange={(e) => updateSettings({ manual_protein_goal: parseInt(e.target.value) })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                    min="0"
                                    max="500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Daily Carbs (g) <span className="text-gray-500 text-xs">optional</span>
                                </label>
                                <input
                                    type="number"
                                    value={settings.manual_carbs_goal || 200}
                                    onChange={(e) => updateSettings({ manual_carbs_goal: parseInt(e.target.value) })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                    min="0"
                                    max="800"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Daily Fat (g) <span className="text-gray-500 text-xs">optional</span>
                                </label>
                                <input
                                    type="number"
                                    value={settings.manual_fat_goal || 67}
                                    onChange={(e) => updateSettings({ manual_fat_goal: parseInt(e.target.value) })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                    min="0"
                                    max="300"
                                />
                            </div>
                        </div>

                        {settings.goal_mode === 'ai_calculated' && settings.allow_personal_data_access && (
                            <div className="mt-3 bg-blue-50 border border-blue-200 rounded p-3">
                                <p className="text-xs text-blue-800">
                                    💡 With AI mode, these values are used as fallback if we don't have enough profile data
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Coaching Preferences */}
            <div className={`bg-white rounded-xl border-2 p-6 ${!settings.ai_coach_enabled ? 'opacity-50' : ''}`}>
                <div className="flex items-center gap-3 mb-4">
                    <MessageCircle className="w-5 h-5 text-purple-600" />
                    <h3 className="text-lg font-bold text-gray-900">Coaching Preferences</h3>
                </div>

                <div className="space-y-4">
                    {/* Frequency */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Frequency</label>
                        <div className="grid grid-cols-3 gap-2">
                            {[
                                { value: 'daily', label: 'Daily' },
                                { value: 'weekly', label: 'Weekly' },
                                { value: 'never', label: 'Never' }
                            ].map((option) => (
                                <button
                                    key={option.value}
                                    onClick={() => updateSettings({ coaching_frequency: option.value as any })}
                                    disabled={!settings.ai_coach_enabled}
                                    className={`px-4 py-2 rounded-lg font-medium transition ${settings.coaching_frequency === option.value
                                            ? 'bg-indigo-600 text-white'
                                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                        } ${!settings.ai_coach_enabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                                >
                                    {option.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Style */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Coaching Style</label>
                        <div className="grid grid-cols-3 gap-2">
                            {[
                                { value: 'supportive', label: '😊 Supportive' },
                                { value: 'strict', label: '💪 Strict' },
                                { value: 'balanced', label: '⚖️ Balanced' }
                            ].map((option) => (
                                <button
                                    key={option.value}
                                    onClick={() => updateSettings({ coaching_style: option.value as any })}
                                    disabled={!settings.ai_coach_enabled}
                                    className={`px-4 py-2 rounded-lg font-medium transition ${settings.coaching_style === option.value
                                            ? 'bg-indigo-600 text-white'
                                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                        } ${!settings.ai_coach_enabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                                >
                                    {option.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* What to Track */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">What to Track</label>
                        <div className="grid grid-cols-2 gap-3">
                            <label className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={settings.track_calories}
                                    onChange={(e) => updateSettings({ track_calories: e.target.checked })}
                                    disabled={!settings.ai_coach_enabled}
                                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                />
                                <span className="text-sm text-gray-700">Calories</span>
                            </label>
                            <label className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={settings.track_protein}
                                    onChange={(e) => updateSettings({ track_protein: e.target.checked })}
                                    disabled={!settings.ai_coach_enabled}
                                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                />
                                <span className="text-sm text-gray-700">Protein</span>
                            </label>
                            <label className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={settings.track_carbs}
                                    onChange={(e) => updateSettings({ track_carbs: e.target.checked })}
                                    disabled={!settings.ai_coach_enabled}
                                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                />
                                <span className="text-sm text-gray-700">Carbs</span>
                            </label>
                            <label className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={settings.track_fat}
                                    onChange={(e) => updateSettings({ track_fat: e.target.checked })}
                                    disabled={!settings.ai_coach_enabled}
                                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                />
                                <span className="text-sm text-gray-700">Fat</span>
                            </label>
                            <label className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={settings.track_meal_timing}
                                    onChange={(e) => updateSettings({ track_meal_timing: e.target.checked })}
                                    disabled={!settings.ai_coach_enabled}
                                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                                />
                                <span className="text-sm text-gray-700">Meal Timing</span>
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            {/* Active Permissions Summary */}
            {settings.ai_coach_enabled && settings.active_permissions.length > 0 && (
                <div className="bg-green-50 border-2 border-green-200 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <Eye className="w-4 h-4 text-green-600" />
                        <h4 className="font-medium text-green-900">Active Permissions:</h4>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {settings.active_permissions.map((perm) => (
                            <span
                                key={perm}
                                className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium"
                            >
                                {perm.replace('_', ' ')}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {saving && (
                <div className="fixed bottom-4 right-4 bg-indigo-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Saving...
                </div>
            )}
        </div>
    );
};

export default NutritionSettings;




