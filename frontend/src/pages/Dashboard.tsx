/**
 * Dashboard Page
 * 
 * Comprehensive analytics and AI insights for shopping, recipes, inventory, and nutrition.
 */
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';
import { toast } from 'react-hot-toast';
import {
    TrendingDown, TrendingUp, DollarSign, ChefHat, Package, Activity,
    ShoppingCart, UtensilsCrossed, AlertTriangle, Flame, Trophy, Sparkles,
    Calendar, RefreshCw
} from 'lucide-react';

interface DashboardData {
    period: string;
    overview: {
        total_spent: number;
        recipes_cooked: number;
        inventory_items: number;
        nutrition_days_logged: number | null;
    };
    shopping: any;
    recipes: any;
    inventory: any;
    nutrition: any | null;
    achievements: any;
    ai_insight_of_day: string | null;
}

const Dashboard: React.FC = () => {
    const { t } = useTranslation();
    const { user, token, logout } = useAuth();
    const api = useMemo(() => new ApiService(token, () => {
        console.log('🔐 Token expired - logging out user');
        toast.error(t('dashboard.sessionExpired'));
        logout();
    }), [token, logout, t]);

    const [loading, setLoading] = useState(true);
    const [data, setData] = useState<DashboardData | null>(null);
    const [period, setPeriod] = useState<'7days' | '30days' | '90days' | '1year'>('30days');
    const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));

    const loadDashboard = useCallback(async () => {
        try {
            setLoading(true);
            const response = await api.getDashboardOverview({ period, include_ai: true });
            setData(response);
        } catch (error) {
            console.error('Failed to load dashboard:', error);
            toast.error(t('dashboard.failedToLoadData'));
        } finally {
            setLoading(false);
        }
    }, [api, period, t]);

    useEffect(() => {
        loadDashboard();
    }, [loadDashboard]);

    const toggleSection = (section: string) => {
        setExpandedSections(prev => {
            const newSet = new Set(prev);
            if (newSet.has(section)) {
                newSet.delete(section);
            } else {
                newSet.add(section);
            }
            return newSet;
        });
    };

    const getPeriodLabel = () => {
        return t(`dashboard.periods.${period}`);
    };

    if (loading && !data) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600 font-medium">{t('dashboard.loadingDashboard')}</p>
                </div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center">
                <div className="text-center">
                    <p className="text-red-600 font-medium">{t('dashboard.failedToLoad')}</p>
                    <button
                        onClick={loadDashboard}
                        className="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                    >
                        {t('dashboard.tryAgain')}
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
                    <div className="flex items-center justify-between flex-wrap gap-4">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                                🏠 {t('dashboard.title')}
                                <span className="text-sm font-normal text-gray-500">{t('dashboard.welcomeBack', { name: user?.first_name || user?.username })}</span>
                            </h1>
                        </div>

                        <div className="flex items-center gap-4">
                            {/* Period Selector */}
                            <div className="flex items-center gap-2">
                                <Calendar className="w-5 h-5 text-gray-400" />
                                <select
                                    value={period}
                                    onChange={(e) => setPeriod(e.target.value as any)}
                                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                                >
                                    <option value="7days">{t('dashboard.periods.7days')}</option>
                                    <option value="30days">{t('dashboard.periods.30days')}</option>
                                    <option value="90days">{t('dashboard.periods.90days')}</option>
                                    <option value="1year">{t('dashboard.periods.1year')}</option>
                                </select>
                            </div>

                            {/* Refresh Button */}
                            <button
                                onClick={loadDashboard}
                                disabled={loading}
                                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition disabled:opacity-50"
                                title={t('dashboard.refresh')}
                            >
                                <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                            </button>

                            {/* AI Status */}
                            <div className="flex items-center gap-2 px-4 py-2 bg-green-50 text-green-700 rounded-lg border border-green-200">
                                <Sparkles className="w-5 h-5" />
                                <span className="font-medium">{t('dashboard.aiActive')}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Quick Overview Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                    <QuickStatCard
                        icon={<DollarSign className="w-8 h-8" />}
                        value={`$${data.overview.total_spent.toFixed(0)}`}
                        label={t('dashboard.overview.spentOnGroceries')}
                        color="green"
                    />
                    <QuickStatCard
                        icon={<ChefHat className="w-8 h-8" />}
                        value={data.overview.recipes_cooked}
                        label={t('dashboard.overview.recipesCooked')}
                        color="purple"
                    />
                    <QuickStatCard
                        icon={<Package className="w-8 h-8" />}
                        value={data.overview.inventory_items}
                        label={t('dashboard.overview.itemsInInventory')}
                        color="blue"
                    />
                    <QuickStatCard
                        icon={<Activity className="w-8 h-8" />}
                        value={data.overview.nutrition_days_logged ?? 'N/A'}
                        label={t('dashboard.overview.daysLogged')}
                        color="orange"
                    />
                </div>

                {/* AI Insight of the Day */}
                {data.ai_insight_of_day && (
                    <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl shadow-lg p-6 mb-6 text-white">
                        <div className="flex items-start gap-4">
                            <Sparkles className="w-8 h-8 flex-shrink-0 mt-1" />
                            <div>
                                <h2 className="text-xl font-bold mb-2">{t('dashboard.aiInsightTitle')}</h2>
                                <p className="text-lg opacity-95">{data.ai_insight_of_day}</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Main Sections */}
                <div className="space-y-6">
                    <ShoppingInsightsSection
                        data={data.shopping}
                        period={getPeriodLabel()}
                        expanded={expandedSections.has('shopping')}
                        onToggle={() => toggleSection('shopping')}
                    />

                    <RecipeInsightsSection
                        data={data.recipes}
                        period={getPeriodLabel()}
                        expanded={expandedSections.has('recipes')}
                        onToggle={() => toggleSection('recipes')}
                    />

                    <InventoryInsightsSection
                        data={data.inventory}
                        expanded={expandedSections.has('inventory')}
                        onToggle={() => toggleSection('inventory')}
                    />

                    {data.nutrition && (
                        <NutritionCoachSection
                            data={data.nutrition}
                            period={getPeriodLabel()}
                            expanded={expandedSections.has('nutrition')}
                            onToggle={() => toggleSection('nutrition')}
                        />
                    )}

                    <AchievementsSection
                        data={data.achievements}
                        expanded={expandedSections.has('achievements')}
                        onToggle={() => toggleSection('achievements')}
                    />
                </div>
            </div>
        </div>
    );
};

// Quick Stat Card Component
const QuickStatCard: React.FC<{
    icon: React.ReactNode;
    value: string | number;
    label: string;
    color: 'green' | 'purple' | 'blue' | 'orange';
}> = ({ icon, value, label, color }) => {
    const colorClasses = {
        green: 'from-green-500 to-emerald-600',
        purple: 'from-purple-500 to-indigo-600',
        blue: 'from-blue-500 to-cyan-600',
        orange: 'from-orange-500 to-red-600'
    };

    return (
        <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition">
            <div className={`inline-flex p-3 rounded-lg bg-gradient-to-br ${colorClasses[color]} text-white mb-4`}>
                {icon}
            </div>
            <div>
                <div className="text-3xl font-bold text-gray-900 mb-1">{value}</div>
                <div className="text-sm text-gray-600">{label}</div>
            </div>
        </div>
    );
};

// Shopping Insights Section
const ShoppingInsightsSection: React.FC<{
    data: any;
    period: string;
    expanded: boolean;
    onToggle: () => void;
}> = ({ data, period, expanded, onToggle }) => {
    const { t } = useTranslation();
    if (!data) return null;

    return (
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <button
                onClick={onToggle}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition"
            >
                <div className="flex items-center gap-3">
                    <ShoppingCart className="w-6 h-6 text-green-600" />
                    <h2 className="text-2xl font-bold text-gray-900">{t('dashboard.shopping.title')}</h2>
                </div>
                <div className="text-gray-400">
                    {expanded ? '▼' : '▶'}
                </div>
            </button>

            {expanded && (
                <div className="p-6 border-t border-gray-200 space-y-6">
                    {/* Budget Overview */}
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-3">{t('dashboard.shopping.budgetOverview')} ({period})</h3>
                        <div className="space-y-2">
                            <div className="flex justify-between items-center">
                                <span className="text-gray-700">{t('dashboard.shopping.totalSpent')}</span>
                                <span className="text-2xl font-bold text-gray-900">
                                    ${data.total_spent} / ${data.budget}
                                    <span className="text-sm text-gray-500 ml-2">({data.budget_percentage}%)</span>
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-3">
                                <div
                                    className={`h-3 rounded-full ${data.budget_percentage > 100 ? 'bg-red-500' : data.budget_percentage > 85 ? 'bg-yellow-500' : 'bg-green-500'}`}
                                    style={{ width: `${Math.min(data.budget_percentage, 100)}%` }}
                                ></div>
                            </div>
                            <div className="grid grid-cols-2 gap-4 mt-4">
                                <div className="bg-gray-50 p-3 rounded-lg">
                                    <div className="text-sm text-gray-600">{t('dashboard.shopping.vsLastPeriod')}</div>
                                    <div className={`text-xl font-bold flex items-center gap-2 ${data.vs_last_period.difference < 0 ? 'text-green-600' : 'text-red-600'}`}>
                                        {data.vs_last_period.difference < 0 ? <TrendingDown className="w-5 h-5" /> : <TrendingUp className="w-5 h-5" />}
                                        ${Math.abs(data.vs_last_period.difference).toFixed(2)}
                                        {data.vs_last_period.difference < 0 && ` ${t('dashboard.shopping.saved')}`}
                                    </div>
                                </div>
                                <div className="bg-gray-50 p-3 rounded-lg">
                                    <div className="text-sm text-gray-600">{t('dashboard.shopping.avgPerWeek')}</div>
                                    <div className="text-xl font-bold text-gray-900">${data.avg_per_week.toFixed(2)}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Category Breakdown */}
                    {data.category_breakdown && data.category_breakdown.length > 0 && (
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-3">{t('dashboard.shopping.categoryBreakdown')}</h3>
                            <div className="space-y-2">
                                {data.category_breakdown.map((cat: any, index: number) => (
                                    <div key={index} className="flex items-center gap-3">
                                        <div className="flex-1">
                                            <div className="flex justify-between mb-1">
                                                <span className="text-gray-700">{cat.category}</span>
                                                <span className="font-semibold text-gray-900">${cat.amount} ({cat.percentage}%)</span>
                                            </div>
                                            <div className="w-full bg-gray-200 rounded-full h-2">
                                                <div
                                                    className="bg-indigo-600 h-2 rounded-full"
                                                    style={{ width: `${cat.percentage}%` }}
                                                ></div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Top Items */}
                    {data.top_items && data.top_items.length > 0 && (
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-3">{t('dashboard.shopping.topItems')}</h3>
                            <div className="space-y-2">
                                {data.top_items.slice(0, 5).map((item: any, index: number) => (
                                    <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                                        <div>
                                            <span className="font-medium text-gray-900">{item.name}</span>
                                            <span className="text-sm text-gray-600 ml-2">({item.count}x)</span>
                                        </div>
                                        <span className="text-sm text-gray-600">{t('dashboard.shopping.every')} {item.frequency}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

// Recipe Insights Section (simplified - will be similar structure)
const RecipeInsightsSection: React.FC<{
    data: any;
    period: string;
    expanded: boolean;
    onToggle: () => void;
}> = ({ data, period, expanded, onToggle }) => {
    const { t } = useTranslation();
    if (!data) return null;

    return (
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <button
                onClick={onToggle}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition"
            >
                <div className="flex items-center gap-3">
                    <UtensilsCrossed className="w-6 h-6 text-purple-600" />
                    <h2 className="text-2xl font-bold text-gray-900">{t('dashboard.recipes.title')}</h2>
                </div>
                <div className="text-gray-400">
                    {expanded ? '▼' : '▶'}
                </div>
            </button>

            {expanded && (
                <div className="p-6 border-t border-gray-200">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-purple-50 p-4 rounded-lg">
                            <div className="text-3xl font-bold text-purple-600">{data.total_cooked}</div>
                            <div className="text-sm text-gray-600">{t('dashboard.recipes.totalCooked')}</div>
                        </div>
                        <div className="bg-indigo-50 p-4 rounded-lg">
                            <div className="text-3xl font-bold text-indigo-600">{data.unique_recipes}</div>
                            <div className="text-sm text-gray-600">{t('dashboard.recipes.uniqueRecipes')}</div>
                        </div>
                        <div className="bg-pink-50 p-4 rounded-lg">
                            <div className="text-3xl font-bold text-pink-600">{data.reviews_written}</div>
                            <div className="text-sm text-gray-600">{t('dashboard.recipes.reviewsWritten')}</div>
                        </div>
                        <div className="bg-amber-50 p-4 rounded-lg">
                            <div className="text-3xl font-bold text-amber-600">{data.avg_rating_given}⭐</div>
                            <div className="text-sm text-gray-600">{t('dashboard.recipes.avgRatingGiven')}</div>
                        </div>
                    </div>

                    {data.favorite && data.favorite.name && (
                        <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg">
                            <div className="text-sm text-gray-600">{t('dashboard.recipes.favoriteRecipe')}</div>
                            <div className="text-xl font-bold text-gray-900">
                                {data.favorite.name}
                                <span className="text-sm font-normal text-gray-600 ml-2">({t('dashboard.recipes.cookedTimes', { count: data.favorite.count })})</span>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

// Inventory Insights Section (simplified)
const InventoryInsightsSection: React.FC<{
    data: any;
    expanded: boolean;
    onToggle: () => void;
}> = ({ data, expanded, onToggle }) => {
    const { t } = useTranslation();
    if (!data) return null;

    return (
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <button
                onClick={onToggle}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition"
            >
                <div className="flex items-center gap-3">
                    <Package className="w-6 h-6 text-blue-600" />
                    <h2 className="text-2xl font-bold text-gray-900">{t('dashboard.inventory.title')}</h2>
                    {(data.expiring_soon_count > 0 || data.low_stock_count > 0) && (
                        <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-semibold">
                            {t('dashboard.inventory.alerts', { count: data.expiring_soon_count + data.low_stock_count })}
                        </span>
                    )}
                </div>
                <div className="text-gray-400">
                    {expanded ? '▼' : '▶'}
                </div>
            </button>

            {expanded && (
                <div className="p-6 border-t border-gray-200 space-y-6">
                    <div className="grid grid-cols-3 gap-4">
                        <div className="bg-blue-50 p-4 rounded-lg">
                            <div className="text-3xl font-bold text-blue-600">{data.total_items}</div>
                            <div className="text-sm text-gray-600">{t('dashboard.inventory.totalItems')}</div>
                        </div>
                        <div className="bg-yellow-50 p-4 rounded-lg">
                            <div className="text-3xl font-bold text-yellow-600">{data.low_stock_count}</div>
                            <div className="text-sm text-gray-600">{t('dashboard.inventory.lowStock')}</div>
                        </div>
                        <div className="bg-red-50 p-4 rounded-lg">
                            <div className="text-3xl font-bold text-red-600">{data.expiring_soon_count}</div>
                            <div className="text-sm text-gray-600">{t('dashboard.inventory.expiringSoon')}</div>
                        </div>
                    </div>

                    {/* Expiring Items */}
                    {data.expiring_items && (data.expiring_items.tomorrow?.length > 0 || data.expiring_items.in_2_3_days?.length > 0) && (
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                                <AlertTriangle className="w-5 h-5 text-red-600" />
                                {t('dashboard.inventory.immediateAttention')}
                            </h3>

                            {data.expiring_items.tomorrow?.length > 0 && (
                                <div className="mb-4">
                                    <div className="text-sm font-semibold text-red-700 mb-2">{t('dashboard.inventory.expiresTomorrow')}</div>
                                    <div className="space-y-2">
                                        {data.expiring_items.tomorrow.map((item: any, index: number) => (
                                            <div key={index} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                                                <span className="font-medium text-gray-900">{item.name}</span>
                                                <span className="text-sm text-gray-600 ml-2">({item.quantity} {item.unit})</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {data.expiring_items.in_2_3_days?.length > 0 && (
                                <div>
                                    <div className="text-sm font-semibold text-yellow-700 mb-2">{t('dashboard.inventory.expiresIn23Days')}</div>
                                    <div className="space-y-2">
                                        {data.expiring_items.in_2_3_days.map((item: any, index: number) => (
                                            <div key={index} className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                                                <span className="font-medium text-gray-900">{item.name}</span>
                                                <span className="text-sm text-gray-600 ml-2">({item.quantity} {item.unit})</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

// Nutrition Coach Section (simplified)
const NutritionCoachSection: React.FC<{
    data: any;
    period: string;
    expanded: boolean;
    onToggle: () => void;
}> = ({ data, period, expanded, onToggle }) => {
    const { t } = useTranslation();
    if (!data) return null;

    return (
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <button
                onClick={onToggle}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition"
            >
                <div className="flex items-center gap-3">
                    <Activity className="w-6 h-6 text-orange-600" />
                    <h2 className="text-2xl font-bold text-gray-900">{t('dashboard.nutrition.title')}</h2>
                    {data.current_streak > 0 && (
                        <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm font-semibold flex items-center gap-1">
                            <Flame className="w-4 h-4" />
                            {t('dashboard.nutrition.dayStreak', { count: data.current_streak })}
                        </span>
                    )}
                </div>
                <div className="text-gray-400">
                    {expanded ? '▼' : '▶'}
                </div>
            </button>

            {expanded && (
                <div className="p-6 border-t border-gray-200 space-y-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-orange-50 p-4 rounded-lg">
                            <div className="text-3xl font-bold text-orange-600">{data.days_logged}/{data.total_days}</div>
                            <div className="text-sm text-gray-600">{t('dashboard.nutrition.daysLoggedOf')} ({data.logging_percentage}%)</div>
                        </div>
                        <div className="bg-green-50 p-4 rounded-lg">
                            <div className="text-3xl font-bold text-green-600">{data.goal_achievement.calories.percentage}%</div>
                            <div className="text-sm text-gray-600">{t('dashboard.nutrition.calorieGoalsHit')}</div>
                        </div>
                        <div className="bg-blue-50 p-4 rounded-lg">
                            <div className="text-3xl font-bold text-blue-600">{data.goal_achievement.protein.percentage}%</div>
                            <div className="text-sm text-gray-600">{t('dashboard.nutrition.proteinGoalsHit')}</div>
                        </div>
                        <div className="bg-red-50 p-4 rounded-lg">
                            <div className="text-3xl font-bold text-red-600 flex items-center gap-1">
                                <Flame className="w-8 h-8" />
                                {data.current_streak}
                            </div>
                            <div className="text-sm text-gray-600">{t('dashboard.nutrition.dayStreakLabel')}</div>
                        </div>
                    </div>

                    {data.monthly_totals && (
                        <div className="p-4 bg-gradient-to-r from-orange-50 to-red-50 rounded-lg">
                            <h3 className="text-lg font-semibold text-gray-900 mb-3">{t('dashboard.nutrition.monthlySummary')}</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <div className="text-sm text-gray-600">{t('dashboard.nutrition.avgCaloriesPerDay')}</div>
                                    <div className="text-2xl font-bold text-gray-900">{data.monthly_totals.avg_per_day.calories} {t('dashboard.nutrition.kcal')}</div>
                                </div>
                                <div>
                                    <div className="text-sm text-gray-600">{t('dashboard.nutrition.avgProteinPerDay')}</div>
                                    <div className="text-2xl font-bold text-gray-900">{data.monthly_totals.avg_per_day.protein}g</div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

// Achievements Section
const AchievementsSection: React.FC<{
    data: any;
    expanded: boolean;
    onToggle: () => void;
}> = ({ data, expanded, onToggle }) => {
    const { t } = useTranslation();
    if (!data) return null;

    return (
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <button
                onClick={onToggle}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition"
            >
                <div className="flex items-center gap-3">
                    <Trophy className="w-6 h-6 text-yellow-600" />
                    <h2 className="text-2xl font-bold text-gray-900">{t('dashboard.achievements.title')}</h2>
                    {data.badges_earned?.length > 0 && (
                        <span className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm font-semibold">
                            {t('dashboard.achievements.badges', { count: data.badges_earned.length })}
                        </span>
                    )}
                </div>
                <div className="text-gray-400">
                    {expanded ? '▼' : '▶'}
                </div>
            </button>

            {expanded && (
                <div className="p-6 border-t border-gray-200 space-y-6">
                    {/* Current Streaks */}
                    {data.current_streaks && Object.keys(data.current_streaks).length > 0 && (
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                                <Flame className="w-5 h-5 text-orange-600" />
                                {t('dashboard.achievements.currentStreaks')}
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {Object.entries(data.current_streaks).map(([type, count]: [string, any]) => (
                                    <div key={type} className="p-4 bg-gradient-to-br from-orange-50 to-red-50 rounded-lg border border-orange-200">
                                        <div className="text-3xl font-bold text-orange-600 flex items-center gap-2">
                                            <Flame className="w-8 h-8" />
                                            {count}
                                        </div>
                                        <div className="text-sm text-gray-700 capitalize">{type.replace('_', ' ')}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Badges Earned */}
                    {data.badges_earned && data.badges_earned.length > 0 && (
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-3">{t('dashboard.achievements.badgesEarned', { count: data.badges_earned.length })}</h3>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                {data.badges_earned.map((badge: any) => (
                                    <div key={badge.id} className="p-4 bg-gradient-to-br from-yellow-50 to-amber-50 rounded-lg border border-yellow-200 text-center">
                                        <div className="text-4xl mb-2">{badge.icon}</div>
                                        <div className="font-semibold text-gray-900">{badge.name}</div>
                                        <div className="text-xs text-gray-600 mt-1">{badge.description}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Next Goals */}
                    {data.next_goals && data.next_goals.length > 0 && (
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-3">{t('dashboard.achievements.nextGoals')}</h3>
                            <div className="space-y-3">
                                {data.next_goals.map((goal: any, index: number) => (
                                    <div key={index} className="p-4 bg-gray-50 rounded-lg">
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="font-medium text-gray-900">{goal.name}</span>
                                            <span className="text-sm text-gray-600">{goal.progress}/{goal.target}</span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                            <div
                                                className="bg-indigo-600 h-2 rounded-full"
                                                style={{ width: `${(goal.progress / goal.target) * 100}%` }}
                                            ></div>
                                        </div>
                                        <div className="text-xs text-gray-600 mt-1">
                                            {t('dashboard.achievements.moreToGo', { count: goal.remaining })}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default Dashboard;
