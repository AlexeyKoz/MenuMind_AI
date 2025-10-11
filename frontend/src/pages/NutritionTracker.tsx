import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';

const NutritionTracker: React.FC = () => {
    const { token, logout } = useAuth();
    const [todayData, setTodayData] = useState<any>(null);
    const [mealInput, setMealInput] = useState('');
    const [mealType, setMealType] = useState('lunch');
    const [coaching, setCoaching] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const api = new ApiService(token, () => {
        console.log('🔐 Token expired - logging out user');
        alert('Your session has expired. Please log in again.');
        logout();
    });

    useEffect(() => {
        loadTodayData();
    }, []);

    const loadTodayData = async () => {
        try {
            const data = await api.getNutritionToday();
            setTodayData(data);
        } catch (error) {
            console.error('Load nutrition error:', error);
        }
    };

    const handleLogMeal = async () => {
        if (!mealInput.trim()) return;

        setLoading(true);
        try {
            const response = await api.aiLogMeal(mealInput, mealType);
            if (response.success) {
                setMealInput('');
                loadTodayData();
            }
        } catch (error) {
            console.error('Log meal error:', error);
        } finally {
            setLoading(false);
        }
    };

    const getCoachingAdvice = async () => {
        setLoading(true);
        try {
            const advice = await api.getCoaching();
            setCoaching(advice);
        } catch (error) {
            console.error('Get coaching error:', error);
        } finally {
            setLoading(false);
        }
    };

    const macroProgress = todayData ? [
        { name: 'Calories', current: todayData.totals.calories, goal: todayData.goals.calories, color: '#FF6384' },
        { name: 'Protein', current: todayData.totals.protein, goal: todayData.goals.protein, color: '#36A2EB' },
        { name: 'Carbs', current: todayData.totals.carbs, goal: todayData.goals.carbs, color: '#FFCE56' },
        { name: 'Fat', current: todayData.totals.fat, goal: todayData.goals.fat, color: '#4BC0C0' }
    ] : [];

    return (
        <div className="max-w-7xl mx-auto p-6">
            <h2 className="text-3xl font-bold mb-6">Nutrition Tracker</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-xl font-semibold mb-4">Log Your Meal with AI</h3>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-2">Meal Type</label>
                            <select
                                value={mealType}
                                onChange={(e) => setMealType(e.target.value)}
                                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="breakfast">Breakfast</option>
                                <option value="lunch">Lunch</option>
                                <option value="dinner">Dinner</option>
                                <option value="snack">Snack</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Describe your meal (AI will analyze nutrition)
                            </label>
                            <textarea
                                value={mealInput}
                                onChange={(e) => setMealInput(e.target.value)}
                                placeholder="e.g., Grilled chicken breast 200g with brown rice and steamed broccoli"
                                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                rows={3}
                            />
                        </div>
                        <button
                            onClick={handleLogMeal}
                            disabled={loading}
                            className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition"
                        >
                            {loading ? 'Analyzing...' : '🤖 AI Analyze & Log Meal'}
                        </button>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-xl font-semibold mb-4">Today's Progress</h3>
                    <div className="space-y-4">
                        {macroProgress.map((macro) => (
                            <div key={macro.name}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="font-medium">{macro.name}</span>
                                    <span>{macro.current} / {macro.goal}</span>
                                </div>
                                <div className="bg-gray-200 rounded-full h-3">
                                    <div
                                        className="h-3 rounded-full transition-all"
                                        style={{
                                            width: `${Math.min((macro.current / macro.goal) * 100, 100)}%`,
                                            backgroundColor: macro.color
                                        }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <div className="mt-6 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg shadow-lg p-6">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-semibold">AI Nutrition Coach</h3>
                    <button
                        onClick={getCoachingAdvice}
                        disabled={loading}
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                    >
                        Get Coaching Advice
                    </button>
                </div>

                {coaching && (
                    <div className="space-y-4">
                        <div className="bg-white rounded-lg p-4">
                            <h4 className="font-semibold mb-2">Current Status</h4>
                            <p>{coaching.current_status}</p>
                        </div>

                        <div className="bg-white rounded-lg p-4">
                            <h4 className="font-semibold mb-2">Recommendations</h4>
                            <ul className="list-disc list-inside space-y-1">
                                {coaching.recommendations?.map((rec: string, index: number) => (
                                    <li key={index}>{rec}</li>
                                ))}
                            </ul>
                        </div>

                        <div className="bg-white rounded-lg p-4">
                            <h4 className="font-semibold mb-2">Meal Suggestions</h4>
                            <div className="space-y-2">
                                {coaching.meal_suggestions?.map((meal: string, index: number) => (
                                    <div key={index} className="p-2 bg-gray-50 rounded">
                                        {meal}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default NutritionTracker;