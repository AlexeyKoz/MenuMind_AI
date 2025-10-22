import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { Utensils, X } from 'lucide-react';
import ApiService from '../services/api';

interface LogToNutritionButtonProps {
    api: ApiService;
    recipeId: string;
    recipeName: string;
    // Optional: if recipe has nutrition data
    calories?: number;
    protein?: number;
    servings?: number;
}

const LogToNutritionButton: React.FC<LogToNutritionButtonProps> = ({
    api,
    recipeId,
    recipeName,
    calories,
    protein,
    servings = 1
}) => {
    const [showModal, setShowModal] = useState(false);
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        portion_multiplier: 1,
        meal_type: 'lunch' as 'breakfast' | 'lunch' | 'dinner' | 'snack',
        date: new Date().toISOString().split('T')[0],
        time: new Date().toTimeString().slice(0, 5),
        notes: ''
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            await api.logFromRecipe({
                recipe_id: recipeId,
                ...formData
            });

            toast.success(`Logged "${recipeName}" to nutrition tracker!`);
            setShowModal(false);
            setFormData({
                portion_multiplier: 1,
                meal_type: 'lunch',
                date: new Date().toISOString().split('T')[0],
                time: new Date().toTimeString().slice(0, 5),
                notes: ''
            });
        } catch (error: any) {
            console.error('Failed to log recipe:', error);
            toast.error(error.message || 'Failed to log to nutrition tracker');
        } finally {
            setLoading(false);
        }
    };

    const portionCalories = calories ? (calories * formData.portion_multiplier).toFixed(0) : null;
    const portionProtein = protein ? (protein * formData.portion_multiplier).toFixed(0) : null;

    return (
        <>
            <button
                onClick={() => setShowModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium"
            >
                <Utensils className="w-4 h-4" />
                Log to Nutrition
            </button>

            {showModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg max-w-md w-full">
                        <div className="flex items-center justify-between p-4 border-b">
                            <h3 className="text-lg font-bold text-gray-900">Log Recipe to Nutrition</h3>
                            <button
                                onClick={() => setShowModal(false)}
                                className="p-2 hover:bg-gray-100 rounded-lg transition"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="p-4 space-y-4">
                            <div className="bg-blue-50 p-3 rounded-lg">
                                <div className="font-medium text-gray-900 mb-1">{recipeName}</div>
                                {calories && protein && (
                                    <div className="text-sm text-gray-600">
                                        {servings > 1 && `${servings} servings • `}
                                        {calories} kcal, {protein}g protein per serving
                                    </div>
                                )}
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    How much did you eat?
                                </label>
                                <select
                                    value={formData.portion_multiplier}
                                    onChange={(e) => setFormData({ ...formData, portion_multiplier: parseFloat(e.target.value) })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                                >
                                    <option value="0.25">1/4 serving</option>
                                    <option value="0.5">1/2 serving</option>
                                    <option value="1">1 serving (full portion)</option>
                                    <option value="1.5">1.5 servings</option>
                                    <option value="2">2 servings</option>
                                    <option value="3">3 servings</option>
                                </select>

                                {portionCalories && portionProtein && (
                                    <div className="mt-2 text-sm text-green-700 bg-green-50 p-2 rounded">
                                        ✓ Your portion: {portionCalories} kcal, {portionProtein}g protein
                                    </div>
                                )}
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Meal Type
                                </label>
                                <select
                                    value={formData.meal_type}
                                    onChange={(e) => setFormData({ ...formData, meal_type: e.target.value as any })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                                >
                                    <option value="breakfast">🌅 Breakfast</option>
                                    <option value="lunch">☀️ Lunch</option>
                                    <option value="dinner">🌙 Dinner</option>
                                    <option value="snack">🍪 Snack</option>
                                </select>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Date
                                    </label>
                                    <input
                                        type="date"
                                        value={formData.date}
                                        onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Time
                                    </label>
                                    <input
                                        type="time"
                                        value={formData.time}
                                        onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Notes (Optional)
                                </label>
                                <textarea
                                    value={formData.notes}
                                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                                    placeholder="Any additional notes..."
                                    rows={2}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                                />
                            </div>

                            <div className="flex justify-end gap-3 pt-4 border-t">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium disabled:opacity-50 flex items-center gap-2"
                                >
                                    {loading && (
                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                    )}
                                    {loading ? 'Logging...' : 'Log to Nutrition'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    );
};

export default LogToNutritionButton;













