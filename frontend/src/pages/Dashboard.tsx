import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';

const Dashboard: React.FC = () => {
    const { user, token, logout } = useAuth();
    const [todayNutrition, setTodayNutrition] = useState<any>(null);
    const [weeklyData, setWeeklyData] = useState<any>(null);
    const [insights, setInsights] = useState<any[]>([]);

    // Create API service with useMemo to prevent recreation on every render
    const api = useMemo(() => new ApiService(token, () => {
        console.log('🔐 Token expired - logging out user');
        alert('Your session has expired. Please log in again.');
        logout();
    }), [token, logout]);

    const loadDashboardData = useCallback(async () => {
        try {
            const [nutrition, weekly] = await Promise.all([
                api.getNutritionToday(),
                api.getWeeklyReport()
            ]);
            setTodayNutrition(nutrition);
            setWeeklyData(weekly);
            setInsights(weekly.insights || []);
        } catch (error) {
            console.error('Dashboard load error:', error);
            // Set empty data to prevent continuous loading
            setTodayNutrition({ totals: { calories: 0, protein: 0, carbs: 0, fat: 0 }, goals: { calories: 2000 }, progress: { calories: 0 } });
            setWeeklyData({ daily_data: {}, insights: [] });
            setInsights([]);
        }
    }, [api]);

    useEffect(() => {
        loadDashboardData();
    }, [loadDashboardData]);

    const macroData = todayNutrition ? [
        { name: 'Protein', value: todayNutrition.totals.protein, color: '#FF6384' },
        { name: 'Carbs', value: todayNutrition.totals.carbs, color: '#36A2EB' },
        { name: 'Fat', value: todayNutrition.totals.fat, color: '#FFCE56' }
    ] : [];

    const weeklyChartData = weeklyData?.daily_data ? Object.entries(weeklyData.daily_data).map(([date, data]: [string, any]) => ({
        date: new Date(date).toLocaleDateString('en', { weekday: 'short' }),
        calories: data.calories,
        protein: data.protein
    })) : [];

    return (
        <div className="max-w-7xl mx-auto p-6">
            <h2 className="text-3xl font-bold mb-6">Welcome back, {user?.first_name || user?.username}! 👋</h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-xl font-semibold mb-4">Today's Calories</h3>
                    <div className="text-center">
                        <div className="text-4xl font-bold text-green-600">
                            {todayNutrition?.totals.calories || 0}
                        </div>
                        <div className="text-gray-600">
                            of {todayNutrition?.goals.calories || 2000} goal
                        </div>
                        <div className="mt-4 bg-gray-200 rounded-full h-4">
                            <div
                                className="bg-green-500 h-4 rounded-full transition-all"
                                style={{ width: `${Math.min(todayNutrition?.progress.calories || 0, 100)}%` }}
                            />
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-xl font-semibold mb-4">Macro Distribution</h3>
                    {macroData.length > 0 ? (
                        <div className="space-y-3">
                            {macroData.map((macro, index) => (
                                <div key={index} className="space-y-1">
                                    <div className="flex justify-between text-sm">
                                        <span className="font-medium">{macro.name}</span>
                                        <span className="text-gray-600">{macro.value}g</span>
                                    </div>
                                    <div className="bg-gray-200 rounded-full h-2">
                                        <div
                                            className="h-2 rounded-full transition-all"
                                            style={{
                                                width: `${(macro.value / macroData.reduce((sum, m) => sum + m.value, 0)) * 100}%`,
                                                backgroundColor: macro.color
                                            }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-gray-500 text-sm">No macro data yet</p>
                    )}
                </div>

                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-xl font-semibold mb-4">AI Insights</h3>
                    <div className="space-y-3">
                        {insights.slice(0, 3).map((insight: any, index: number) => (
                            <div key={index} className="flex items-start space-x-2">
                                <span className="text-2xl">
                                    {insight.type === 'achievement' ? '🏆' :
                                        insight.type === 'warning' ? '⚠️' : '💡'}
                                </span>
                                <div>
                                    <p className="font-semibold text-sm">{insight.title}</p>
                                    <p className="text-xs text-gray-600">{insight.description}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-semibold mb-4">Weekly Nutrition Trend</h3>
                {weeklyChartData.length > 0 ? (
                    <div className="space-y-4">
                        <div className="grid grid-cols-7 gap-2">
                            {weeklyChartData.map((day: any, index: number) => (
                                <div key={index} className="text-center">
                                    <div className="text-xs text-gray-600 mb-2">{day.date}</div>
                                    <div className="bg-indigo-100 rounded p-2">
                                        <div className="text-sm font-semibold text-indigo-900">
                                            {Math.round(day.calories)}
                                        </div>
                                        <div className="text-xs text-indigo-600">cal</div>
                                    </div>
                                    <div className="bg-green-100 rounded p-2 mt-1">
                                        <div className="text-sm font-semibold text-green-900">
                                            {Math.round(day.protein)}
                                        </div>
                                        <div className="text-xs text-green-600">g</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="flex justify-center gap-4 text-sm pt-2">
                            <div className="flex items-center gap-1">
                                <div className="w-3 h-3 bg-indigo-500 rounded"></div>
                                <span>Calories</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-3 h-3 bg-green-500 rounded"></div>
                                <span>Protein</span>
                            </div>
                        </div>
                    </div>
                ) : (
                    <p className="text-gray-500 text-sm">No weekly data yet</p>
                )}
            </div>
        </div>
    );
};

export default Dashboard;