import React, { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';
import { toast } from 'react-hot-toast';
import {
    Calendar,
    Plus,
    TrendingUp,
    Utensils,
    Coffee,
    Sun,
    Moon,
    Cookie,
    Edit2,
    Trash2,
    Sparkles,
    ChevronLeft,
    ChevronRight,
    Settings,
    X
} from 'lucide-react';
import type {
    DailySummary,
    NutritionEntry,
    UserNutritionSettings,
    AISuggestionResponse
} from '../types';

// Manual Entry Modal Component
interface ManualEntryModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (entry: any) => void;
    editEntry?: NutritionEntry | null;
    selectedDate: string;
    selectedMealType?: 'breakfast' | 'lunch' | 'dinner' | 'snack';
}

const ManualEntryModal: React.FC<ManualEntryModalProps> = ({
    isOpen,
    onClose,
    onSave,
    editEntry,
    selectedDate,
    selectedMealType
}) => {
    const { t } = useTranslation();
    const [formData, setFormData] = useState({
        date: selectedDate,
        meal_type: selectedMealType || 'lunch',
        time: '',
        food_name: '',
        portion_size: '',
        portion_unit: 'grams',
        calories: '',
        protein: '',
        carbs: '',
        fat: '',
        fiber: '',
        sugar: '',
        sodium: '',
        notes: ''
    });

    useEffect(() => {
        if (editEntry) {
            setFormData({
                date: editEntry.date,
                meal_type: editEntry.meal_type,
                time: editEntry.time || '',
                food_name: editEntry.food_name,
                portion_size: editEntry.portion_size.toString(),
                portion_unit: editEntry.portion_unit,
                calories: editEntry.calories.toString(),
                protein: editEntry.protein.toString(),
                carbs: editEntry.carbs.toString(),
                fat: editEntry.fat.toString(),
                fiber: editEntry.fiber?.toString() || '',
                sugar: editEntry.sugar?.toString() || '',
                sodium: editEntry.sodium?.toString() || '',
                notes: editEntry.notes || ''
            });
        } else {
            setFormData(prev => ({
                ...prev,
                date: selectedDate,
                meal_type: selectedMealType || 'lunch'
            }));
        }
    }, [editEntry, selectedDate, selectedMealType]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        // Validate required fields
        if (!formData.food_name || !formData.calories || !formData.protein) {
            toast.error(t('nutrition.validationError'));
            return;
        }

        const entry = {
            ...formData,
            portion_size: parseFloat(formData.portion_size) || 1,
            calories: parseFloat(formData.calories),
            protein: parseFloat(formData.protein),
            carbs: parseFloat(formData.carbs) || 0,
            fat: parseFloat(formData.fat) || 0,
            fiber: formData.fiber ? parseFloat(formData.fiber) : undefined,
            sugar: formData.sugar ? parseFloat(formData.sugar) : undefined,
            sodium: formData.sodium ? parseFloat(formData.sodium) : undefined
        };

        onSave(entry);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
                    <h2 className="text-xl font-bold text-gray-900">
                        {editEntry ? t('nutrition.editEntry') : t('nutrition.addManualEntry')}
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-lg transition"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    {/* Date and Meal Type */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('nutrition.date')}
                            </label>
                            <input
                                type="date"
                                value={formData.date}
                                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('nutrition.mealType')}
                            </label>
                            <select
                                value={formData.meal_type}
                                onChange={(e) => setFormData({ ...formData, meal_type: e.target.value as any })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                required
                            >
                                <option value="breakfast">{t('nutrition.meals.breakfast')}</option>
                                <option value="lunch">{t('nutrition.meals.lunch')}</option>
                                <option value="dinner">{t('nutrition.meals.dinner')}</option>
                                <option value="snack">{t('nutrition.meals.snack')}</option>
                            </select>
                        </div>
                    </div>

                    {/* Time (optional) */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            {t('nutrition.timeOptional')}
                        </label>
                        <input
                            type="time"
                            value={formData.time}
                            onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                        />
                    </div>

                    {/* Food Name */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            {t('nutrition.foodName')}
                        </label>
                        <input
                            type="text"
                            value={formData.food_name}
                            onChange={(e) => setFormData({ ...formData, food_name: e.target.value })}
                            placeholder="e.g., Grilled Chicken Breast"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                            required
                        />
                    </div>

                    {/* Portion */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('nutrition.portionSize')}
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                value={formData.portion_size}
                                onChange={(e) => setFormData({ ...formData, portion_size: e.target.value })}
                                placeholder="150"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                {t('nutrition.unit')}
                            </label>
                            <select
                                value={formData.portion_unit}
                                onChange={(e) => setFormData({ ...formData, portion_unit: e.target.value })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                            >
                                <option value="grams">{t('nutrition.units.grams')}</option>
                                <option value="ml">{t('nutrition.units.ml')}</option>
                                <option value="pieces">{t('nutrition.units.pieces')}</option>
                                <option value="serving">{t('nutrition.units.serving')}</option>
                                <option value="cup">{t('nutrition.units.cup')}</option>
                                <option value="tbsp">{t('nutrition.units.tbsp')}</option>
                                <option value="tsp">{t('nutrition.units.tsp')}</option>
                            </select>
                        </div>
                    </div>

                    {/* Main Macros (Required) */}
                    <div className="bg-indigo-50 p-4 rounded-lg">
                        <h3 className="font-medium text-indigo-900 mb-3">
                            {t('nutrition.nutritionInfoRequired')}
                        </h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('nutrition.caloriesKcal')}
                                </label>
                                <input
                                    type="number"
                                    step="0.1"
                                    value={formData.calories}
                                    onChange={(e) => setFormData({ ...formData, calories: e.target.value })}
                                    placeholder="250"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('nutrition.proteinG')}
                                </label>
                                <input
                                    type="number"
                                    step="0.1"
                                    value={formData.protein}
                                    onChange={(e) => setFormData({ ...formData, protein: e.target.value })}
                                    placeholder="30"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('nutrition.carbsG')}
                                </label>
                                <input
                                    type="number"
                                    step="0.1"
                                    value={formData.carbs}
                                    onChange={(e) => setFormData({ ...formData, carbs: e.target.value })}
                                    placeholder="10"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('nutrition.fatG')}
                                </label>
                                <input
                                    type="number"
                                    step="0.1"
                                    value={formData.fat}
                                    onChange={(e) => setFormData({ ...formData, fat: e.target.value })}
                                    placeholder="12"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Optional Nutrients */}
                    <div>
                        <h3 className="font-medium text-gray-900 mb-2">
                            {t('nutrition.additionalNutrients')}
                        </h3>
                        <div className="grid grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('nutrition.fiberG')}
                                </label>
                                <input
                                    type="number"
                                    step="0.1"
                                    value={formData.fiber}
                                    onChange={(e) => setFormData({ ...formData, fiber: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('nutrition.sugarG')}
                                </label>
                                <input
                                    type="number"
                                    step="0.1"
                                    value={formData.sugar}
                                    onChange={(e) => setFormData({ ...formData, sugar: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    {t('nutrition.sodiumMg')}
                                </label>
                                <input
                                    type="number"
                                    step="0.1"
                                    value={formData.sodium}
                                    onChange={(e) => setFormData({ ...formData, sodium: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Notes */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            {t('nutrition.notesOptional')}
                        </label>
                        <textarea
                            value={formData.notes}
                            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                            placeholder={t('nutrition.notesPlaceholder')}
                            rows={3}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                        />
                    </div>

                    {/* Actions */}
                    <div className="flex justify-end gap-3 pt-4 border-t">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
                        >
                            {t('nutrition.cancel')}
                        </button>
                        <button
                            type="submit"
                            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium"
                        >
                            {editEntry ? t('nutrition.updateEntry') : t('nutrition.addEntry')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// Helper function to safely convert to number
const toNumber = (value: any): number => {
    if (typeof value === 'number') return value;
    const parsed = parseFloat(value);
    return isNaN(parsed) ? 0 : parsed;
};

// Main Nutrition Tracker Component
const NutritionTracker: React.FC = () => {
    const { t } = useTranslation();
    const { token, logout } = useAuth();
    const api = useMemo(() => new ApiService(token, () => {
        console.log('🔐 Token expired - logging out user');
        toast.error(t('nutrition.sessionExpired'));
        logout();
    }), [token, logout, t]);

    // State
    const [selectedDate, setSelectedDate] = useState<string>(
        new Date().toISOString().split('T')[0]
    );
    const [summary, setSummary] = useState<DailySummary | null>(null);
    const [settings, setSettings] = useState<UserNutritionSettings | null>(null);
    const [aiSuggestions, setAiSuggestions] = useState<AISuggestionResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [showManualModal, setShowManualModal] = useState(false);
    const [editingEntry, setEditingEntry] = useState<NutritionEntry | null>(null);
    const [selectedMealType, setSelectedMealType] = useState<'breakfast' | 'lunch' | 'dinner' | 'snack' | undefined>();

    // Load data
    useEffect(() => {
        loadData();
    }, [selectedDate]);

    const loadData = async () => {
        setLoading(true);
        try {
            const [summaryData, settingsData] = await Promise.all([
                api.getTodaySummary(),
                api.getNutritionSettings()
            ]);
            setSummary(summaryData);
            setSettings(settingsData);

            // Load AI suggestions if enabled
            if (settingsData.ai_coach_enabled) {
                try {
                    const suggestions = await api.getAISuggestions({});
                    setAiSuggestions(suggestions);
                } catch (error) {
                    console.error('Failed to load AI suggestions:', error);
                }
            }
        } catch (error) {
            console.error('Failed to load nutrition data:', error);
            toast.error(t('nutrition.failedToLoad'));
        } finally {
            setLoading(false);
        }
    };

    const handleAddEntry = async (entry: any) => {
        try {
            if (editingEntry) {
                await api.updateNutritionEntry(editingEntry.id, entry);
                toast.success(t('nutrition.entryUpdated'));
            } else {
                await api.createNutritionEntry(entry);
                toast.success(t('nutrition.entryAdded'));
            }
            setShowManualModal(false);
            setEditingEntry(null);
            setSelectedMealType(undefined);
            loadData();
        } catch (error) {
            console.error('Failed to save entry:', error);
            toast.error(t('nutrition.failedToSave'));
        }
    };

    const handleDeleteEntry = async (id: string) => {
        if (!window.confirm(t('nutrition.deleteEntry'))) return;

        try {
            await api.deleteNutritionEntry(id);
            toast.success(t('nutrition.entryDeleted'));
            loadData();
        } catch (error) {
            console.error('Failed to delete entry:', error);
            toast.error(t('nutrition.failedToDelete'));
        }
    };

    const getMealIcon = (mealType: string) => {
        switch (mealType) {
            case 'breakfast': return <Coffee className="w-5 h-5" />;
            case 'lunch': return <Sun className="w-5 h-5" />;
            case 'dinner': return <Moon className="w-5 h-5" />;
            case 'snack': return <Cookie className="w-5 h-5" />;
            default: return <Utensils className="w-5 h-5" />;
        }
    };

    const getMealLabel = (mealType: string) => {
        return t(`nutrition.meals.${mealType}`);
    };

    const ProgressBar: React.FC<{ label: string; current: number; goal: number; color: string }> = ({
        label,
        current,
        goal,
        color
    }) => {
        const percentage = goal > 0 ? Math.min((current / goal) * 100, 100) : 0;
        const remaining = Math.max(goal - current, 0);

        return (
            <div className="mb-4">
                <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium text-gray-700">{label}</span>
                    <span className="text-gray-600">
                        {current.toFixed(0)} / {goal.toFixed(0)} ({percentage.toFixed(0)}%)
                    </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                        className="h-3 rounded-full transition-all duration-300"
                        style={{
                            width: `${percentage}%`,
                            backgroundColor: color
                        }}
                    />
                </div>
                <div className="text-xs text-gray-500 mt-1">
                    {t('nutrition.remaining', { value: remaining.toFixed(0) })}
                </div>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="max-w-7xl mx-auto p-6">
                <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-bold text-gray-900">{t('nutrition.title')}</h1>
                <div className="flex items-center gap-3">
                    {settings && !settings.ai_coach_enabled && (
                        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 flex items-center gap-2">
                            <span className="text-amber-800 text-sm">{t('nutrition.aiCoachDisabled')}</span>
                            <a
                                href="/settings"
                                className="text-amber-600 hover:text-amber-700 text-sm font-medium"
                            >
                                {t('nutrition.enableAICoach')}
                            </a>
                        </div>
                    )}
                    <a
                        href="/settings"
                        className="flex items-center gap-2 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
                    >
                        <Settings className="w-4 h-4" />
                        {t('nutrition.settings')}
                    </a>
                </div>
            </div>

            {/* Date Navigator */}
            <div className="bg-white rounded-lg shadow-sm p-4 mb-6 flex items-center justify-between">
                <button
                    onClick={() => {
                        const date = new Date(selectedDate);
                        date.setDate(date.getDate() - 1);
                        setSelectedDate(date.toISOString().split('T')[0]);
                    }}
                    className="p-2 hover:bg-gray-100 rounded-lg transition"
                >
                    <ChevronLeft className="w-5 h-5" />
                </button>

                <div className="flex items-center gap-3">
                    <Calendar className="w-5 h-5 text-gray-600" />
                    <input
                        type="date"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                    <button
                        onClick={() => setSelectedDate(new Date().toISOString().split('T')[0])}
                        className="px-4 py-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition font-medium"
                    >
                        {t('nutrition.today')}
                    </button>
                </div>

                <button
                    onClick={() => {
                        const date = new Date(selectedDate);
                        date.setDate(date.getDate() + 1);
                        setSelectedDate(date.toISOString().split('T')[0]);
                    }}
                    className="p-2 hover:bg-gray-100 rounded-lg transition"
                    disabled={selectedDate >= new Date().toISOString().split('T')[0]}
                >
                    <ChevronRight className="w-5 h-5" />
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left: Progress */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Progress Card */}
                    <div className="bg-white rounded-lg shadow-sm p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold text-gray-900">{t('nutrition.todaysProgress')}</h2>
                            <div className="text-sm text-gray-600">
                                {summary?.goals.source === 'ai_calculated' ? t('nutrition.aiCalculated') : t('nutrition.manualGoals')}
                            </div>
                        </div>

                        {summary && (
                            <>
                                <ProgressBar
                                    label="Calories"
                                    current={toNumber(summary.consumed.calories)}
                                    goal={toNumber(summary.goals.calories)}
                                    color="#4F46E5"
                                />
                                <ProgressBar
                                    label="Protein"
                                    current={toNumber(summary.consumed.protein)}
                                    goal={toNumber(summary.goals.protein)}
                                    color="#10B981"
                                />
                                {settings?.track_carbs && (
                                    <ProgressBar
                                        label="Carbs"
                                        current={toNumber(summary.consumed.carbs)}
                                        goal={toNumber(summary.goals.carbs)}
                                        color="#F59E0B"
                                    />
                                )}
                                {settings?.track_fat && (
                                    <ProgressBar
                                        label="Fat"
                                        current={toNumber(summary.consumed.fat)}
                                        goal={toNumber(summary.goals.fat)}
                                        color="#EF4444"
                                    />
                                )}
                            </>
                        )}
                    </div>

                    {/* Meals */}
                    <div className="space-y-4">
                        {['breakfast', 'lunch', 'dinner', 'snack'].map((mealType) => {
                            const mealEntries = summary?.meals.filter((m) => m.meal_type === mealType) || [];
                            const mealTotals = mealEntries.reduce(
                                (acc, entry) => ({
                                    calories: acc.calories + toNumber(entry.calories),
                                    protein: acc.protein + toNumber(entry.protein)
                                }),
                                { calories: 0, protein: 0 }
                            );

                            return (
                                <div key={mealType} className="bg-white rounded-lg shadow-sm p-6">
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="flex items-center gap-3">
                                            {getMealIcon(mealType)}
                                            <h3 className="text-lg font-bold text-gray-900">
                                                {getMealLabel(mealType)}
                                            </h3>
                                            {mealEntries.length > 0 && (
                                                <span className="text-sm text-gray-600">
                                                    ({mealTotals.calories.toFixed(0)} kcal, {mealTotals.protein.toFixed(0)}g protein)
                                                </span>
                                            )}
                                        </div>
                                        <button
                                            onClick={() => {
                                                setSelectedMealType(mealType as any);
                                                setShowManualModal(true);
                                            }}
                                            className="flex items-center gap-2 px-3 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm"
                                        >
                                            <Plus className="w-4 h-4" />
                                            {t('nutrition.add')}
                                        </button>
                                    </div>

                                    {mealEntries.length === 0 ? (
                                        <p className="text-gray-500 text-sm italic">{t('nutrition.noEntriesYet')}</p>
                                    ) : (
                                        <div className="space-y-2">
                                            {mealEntries.map((entry) => (
                                                <div
                                                    key={entry.id}
                                                    className="flex items-start justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
                                                >
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2">
                                                            <h4 className="font-medium text-gray-900">
                                                                {entry.food_name}
                                                            </h4>
                                                            {entry.entry_type === 'recipe' && (
                                                                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">
                                                                    {t('nutrition.recipe')}
                                                                </span>
                                                            )}
                                                            {entry.entry_type === 'product' && (
                                                                <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                                                                    {t('nutrition.inventory')}
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div className="text-sm text-gray-600 mt-1">
                                                            {toNumber(entry.portion_size).toFixed(1)} {entry.portion_unit} • {toNumber(entry.calories).toFixed(0)} kcal • {toNumber(entry.protein).toFixed(0)}g protein
                                                            {entry.time && ` • ${entry.time}`}
                                                        </div>
                                                        {entry.notes && (
                                                            <p className="text-sm text-gray-500 mt-1">{entry.notes}</p>
                                                        )}
                                                    </div>
                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={() => {
                                                                setEditingEntry(entry);
                                                                setShowManualModal(true);
                                                            }}
                                                            className="p-2 text-gray-600 hover:bg-white rounded-lg transition"
                                                        >
                                                            <Edit2 className="w-4 h-4" />
                                                        </button>
                                                        <button
                                                            onClick={() => handleDeleteEntry(entry.id)}
                                                            className="p-2 text-red-600 hover:bg-white rounded-lg transition"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Right: AI Suggestions */}
                <div className="space-y-6">
                    {settings?.ai_coach_enabled && aiSuggestions?.ai_enabled && (
                        <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg shadow-sm p-6 border border-purple-200">
                            <div className="flex items-center gap-2 mb-4">
                                <Sparkles className="w-5 h-5 text-purple-600" />
                                <h3 className="text-lg font-bold text-purple-900">{t('nutrition.aiCoach')}</h3>
                            </div>
                            <p className="text-sm text-purple-800 mb-4">
                                {aiSuggestions.message}
                            </p>
                            {aiSuggestions.suggestions && aiSuggestions.suggestions.length > 0 && (
                                <div className="space-y-2">
                                    <h4 className="font-medium text-purple-900 text-sm mb-2">
                                        {t('nutrition.suggestedMeals')}
                                    </h4>
                                    {aiSuggestions.suggestions.map((suggestion, index) => (
                                        <div
                                            key={index}
                                            className="bg-white p-3 rounded-lg border border-purple-200"
                                        >
                                            <div className="font-medium text-gray-900 text-sm">
                                                {suggestion.name}
                                            </div>
                                            <div className="text-xs text-gray-600 mt-1">
                                                {suggestion.calories} kcal • {suggestion.protein}g protein
                                            </div>
                                            <p className="text-xs text-gray-500 mt-1">
                                                {suggestion.reason}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Quick Stats */}
                    {summary && (
                        <div className="bg-white rounded-lg shadow-sm p-6">
                            <h3 className="text-lg font-bold text-gray-900 mb-4">{t('nutrition.summary')}</h3>
                            <div className="space-y-3">
                                <div className="flex justify-between">
                                    <span className="text-gray-600">{t('nutrition.calories')}</span>
                                    <span className="font-medium">
                                        {toNumber(summary.consumed.calories).toFixed(0)} / {toNumber(summary.goals.calories).toFixed(0)}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-600">{t('nutrition.protein')}</span>
                                    <span className="font-medium">
                                        {toNumber(summary.consumed.protein).toFixed(0)}g / {toNumber(summary.goals.protein).toFixed(0)}g
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-600">{t('nutrition.entries')}</span>
                                    <span className="font-medium">{summary.meals.length}</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Manual Entry Modal */}
            <ManualEntryModal
                isOpen={showManualModal}
                onClose={() => {
                    setShowManualModal(false);
                    setEditingEntry(null);
                    setSelectedMealType(undefined);
                }}
                onSave={handleAddEntry}
                editEntry={editingEntry}
                selectedDate={selectedDate}
                selectedMealType={selectedMealType}
            />
        </div>
    );
};

export default NutritionTracker;
