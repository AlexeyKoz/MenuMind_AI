import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useUserGuide } from '../contexts/UserGuideContext';
import ApiService from '../services/api';
import toast from 'react-hot-toast';
import { AllergenWarningBanner } from '../components/WarningBanners';
import {
    Search, Upload, Download, BookOpen, Clock, Users,
    ChefHat, Heart, ExternalLink, FileJson,
    Filter, X, Check, AlertTriangle, Zap, Archive, ShoppingCart
} from 'lucide-react';

interface Recipe {
    id: string;
    name: string;
    description: string;
    rcip_version: string;
    ingredients: any[];
    steps: any[];
    author: string;
    source_url?: string;
    prep_time_minutes?: number;
    cook_time_minutes?: number;
    total_time_minutes?: number;
    servings: number;
    difficulty: string;
    cuisine: string;
    diet_labels: string[];
    times_cooked: number;
    times_added_to_lists: number;
    is_saved: boolean;
    created_at: string;
    last_cooked?: string | null;  // Track if user has marked as cooked
    nutrition_per_serving?: {
        calories?: number;
        protein?: number;
        carbs?: number;
        fat?: number;
    };
    missing_ingredients?: string[];
}

const Recipes: React.FC = () => {
    const { t, i18n } = useTranslation();
    const { token, logout } = useAuth();
    const { startGuide, isInitialized } = useUserGuide();
    const api = new ApiService(token, () => {
        console.log('🔐 Token expired - logging out user');
        alert(t('recipes.sessionExpired'));
        logout();
    });
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Library state
    const [recipes, setRecipes] = useState<Recipe[]>([]);
    const [filteredRecipes, setFilteredRecipes] = useState<Recipe[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
    const [showFilters, setShowFilters] = useState(false);

    // Generator state - REMOVED (not needed)

    // Filters
    const [difficultyFilter, setDifficultyFilter] = useState('');
    const [cuisineFilter, setCuisineFilter] = useState('');
    const [savedOnlyFilter, setSavedOnlyFilter] = useState(false);

    // Stats
    const [stats, setStats] = useState({
        total: 0,
        ingredients: 0,
        steps: 0
    });

    // Archive confirmation modal state
    const [archiveConfirmation, setArchiveConfirmation] = useState<{
        show: boolean;
        recipe: Recipe | null;
        countdown: number;
    }>({ show: false, recipe: null, countdown: 5 });

    useEffect(() => {
        loadRecipes();

        // Close recipe modal when language changes to force reload with new translations
        if (selectedRecipe) {
            setSelectedRecipe(null);
        }

        // Check if there's a recipe ID in the URL (from inventory navigation)
        const params = new URLSearchParams(window.location.search);
        const recipeId = params.get('id');

        if (recipeId) {
            console.log('[RECIPES] 🔗 Recipe ID found in URL:', recipeId);
            // Wait for recipes to load, then open the detail
            setTimeout(() => {
                const recipe = recipes.find(r => r.id === recipeId);
                if (recipe) {
                    console.log('[RECIPES] ✅ Opening recipe from URL:', recipe.name);
                    setSelectedRecipe(recipe);
                    // Clean URL after opening
                    window.history.replaceState({}, '', '/recipes');
                } else {
                    console.log('[RECIPES] ⚠️ Recipe not found, will retry after load');
                }
            }, 500);
        }
    }, [i18n.language]);  // Reload when language changes

    // Second effect to handle recipe opening after recipes are loaded
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const recipeId = params.get('id');

        if (recipeId && recipes.length > 0 && !selectedRecipe) {
            console.log('[RECIPES] 🔄 Recipes loaded, checking for recipe ID:', recipeId);
            const recipe = recipes.find(r => r.id === recipeId);
            if (recipe) {
                console.log('[RECIPES] ✅ Opening recipe:', recipe.name);
                setSelectedRecipe(recipe);
                // Clean URL after opening
                window.history.replaceState({}, '', '/recipes');
            }
        }
    }, [recipes, selectedRecipe]);

    // Start user guide on first visit - wait for initialization
    useEffect(() => {
        if (!isInitialized) {
            return; // Wait for guide system to initialize
        }

        const timer = setTimeout(() => {
            startGuide('recipes');
        }, 1000);

        return () => clearTimeout(timer);
    }, [isInitialized, startGuide]); // Re-run when initialized

    useEffect(() => {
        filterRecipes();
    }, [recipes, searchQuery, difficultyFilter, cuisineFilter, savedOnlyFilter]);

    const loadRecipes = async () => {
        setLoading(true);
        try {
            console.log(`\n${'='.repeat(80)}`);
            console.log(`📚 [LOAD] ⚡ CALLING API - Language: ${i18n.language}`);
            console.log(`📚 [LOAD] ⚡ Timestamp: ${new Date().toISOString()}`);
            console.log(`${'='.repeat(80)}\n`);

            const data = await api.getMyRecipes(i18n.language);

            console.log(`\n${'='.repeat(80)}`);
            console.log('📚 [LOAD] ✅ API RESPONSE RECEIVED');
            console.log('📚 [LOAD] Raw API response:', data);
            console.log(`📚 [LOAD] Loaded with language: ${i18n.language}`);

            // Log first recipe structure for debugging
            if (data.recipes && data.recipes.length > 0) {
                console.log(`📚 [LOAD] Total recipes: ${data.recipes.length}`);
                console.log('📚 [LOAD] First recipe sample:', data.recipes[0]);
                console.log('📚 [LOAD] First recipe NAME:', data.recipes[0].name);
                console.log('📚 [LOAD] First recipe ingredients[0]:', data.recipes[0].ingredients?.[0]);
                console.log('📚 [LOAD] First recipe steps[0]:', data.recipes[0].steps?.[0]);

                // Check if any recipe has empty ingredients/steps (indicating pending translation)
                const hasEmptyContent = data.recipes.some((r: any) =>
                    !r.ingredients || r.ingredients.length === 0 || !r.steps || r.steps.length === 0
                );

                if (hasEmptyContent && i18n.language !== 'en') {
                    console.log('⚠️ [LOAD] Some recipes have empty content - translation may be pending');
                    toast('🔄 Translating recipes... Reload in a few seconds to see translations', {
                        duration: 5000,
                        icon: '🌍'
                    });
                }
            }
            console.log(`${'='.repeat(80)}\n`);

            // Handle different response formats
            let recipeList: Recipe[] = [];

            if (Array.isArray(data)) {
                // Direct array
                recipeList = data;
            } else if (data.results && Array.isArray(data.results)) {
                // Paginated response
                recipeList = data.results;
            } else if (data.recipes && Array.isArray(data.recipes)) {
                // Custom response format
                recipeList = data.recipes;
            } else {
                console.warn('⚠️ Unexpected response format:', data);
                recipeList = [];
            }

            console.log('📚 Processed recipe list:', recipeList);
            setRecipes(recipeList);

            // Calculate stats
            const totalIngredients = recipeList.reduce((sum: number, r: Recipe) =>
                sum + (r.ingredients?.length || 0), 0
            );
            const totalSteps = recipeList.reduce((sum: number, r: Recipe) =>
                sum + (r.steps?.length || 0), 0
            );

            setStats({
                total: recipeList.length,
                ingredients: totalIngredients,
                steps: totalSteps
            });
        } catch (error: any) {
            console.error('Load recipes error:', error);
            toast.error(error.message || t('recipes.failedToLoad'));
        } finally {
            setLoading(false);
        }
    };

    const filterRecipes = () => {
        let filtered = recipes;

        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(r =>
                r.name.toLowerCase().includes(query) ||
                r.description?.toLowerCase().includes(query) ||
                r.cuisine?.toLowerCase().includes(query)
            );
        }

        if (difficultyFilter) {
            filtered = filtered.filter(r => r.difficulty === difficultyFilter);
        }

        if (cuisineFilter) {
            filtered = filtered.filter(r => r.cuisine === cuisineFilter);
        }

        if (savedOnlyFilter) {
            filtered = filtered.filter(r => r.is_saved);
        }

        setFilteredRecipes(filtered);
    };

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!file.name.endsWith('.rcip')) {
            toast.error(t('recipes.pleaseUploadRcip'));
            return;
        }

        setLoading(true);
        try {
            const result = await api.uploadRCIP(file);
            toast.success(result.message || t('recipes.recipeImported'));
            loadRecipes();
        } catch (error: any) {
            console.error('Upload error:', error);
            toast.error(error.message || t('recipes.failedToUpload'));
        } finally {
            setLoading(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const handleDownload = async (recipe: Recipe) => {
        try {
            await api.downloadRCIP(recipe.id, recipe.name);
            toast.success(t('recipes.downloaded', { name: recipe.name }));
        } catch (error: any) {
            console.error('Download error:', error);
            toast.error(t('recipes.failedToDownload'));
        }
    };

    const handleSaveRecipe = async (recipe: Recipe) => {
        try {
            await api.saveRecipe(recipe.id);
            toast.success(t('recipes.recipeSaved'));
            loadRecipes();
        } catch (error: any) {
            console.error('Save error:', error);
            toast.error(t('recipes.failedToSave'));
        }
    };

    // Countdown effect for archive confirmation
    useEffect(() => {
        if (archiveConfirmation.show && archiveConfirmation.countdown > 0) {
            const timer = setTimeout(() => {
                setArchiveConfirmation(prev => ({
                    ...prev,
                    countdown: prev.countdown - 1
                }));
            }, 1000);
            return () => clearTimeout(timer);
        } else if (archiveConfirmation.show && archiveConfirmation.countdown === 0) {
            // Auto-archive when countdown reaches 0
            confirmArchiveRecipe();
        }
    }, [archiveConfirmation.show, archiveConfirmation.countdown]);

    const handleUnsaveRecipe = (recipe: Recipe) => {
        setArchiveConfirmation({ show: true, recipe, countdown: 5 });
    };

    const confirmArchiveRecipe = async () => {
        if (!archiveConfirmation.recipe) return;

        try {
            await api.unsaveRecipe(archiveConfirmation.recipe.id);
            toast.success(t('recipes.movedToArchive', { name: archiveConfirmation.recipe.name }));
            setArchiveConfirmation({ show: false, recipe: null, countdown: 5 });
            loadRecipes();
            if (selectedRecipe?.id === archiveConfirmation.recipe.id) {
                setSelectedRecipe(null);
            }
        } catch (error: any) {
            console.error('Archive error:', error);
            toast.error(t('recipes.failedToArchive'));
        }
    };

    const cancelArchiveRecipe = () => {
        setArchiveConfirmation({ show: false, recipe: null, countdown: 5 });
    };

    const handleMarkCooked = async (recipe: Recipe) => {
        try {
            const result = await api.markRecipeCooked(recipe.id);
            const action = result.cooked ? 'cooked' : 'uncooked';
            toast.success(t('recipes.recipeMarked', { action, emoji: result.cooked ? '🍳' : '↩️' }));
            loadRecipes();
        } catch (error: any) {
            console.error('Mark cooked error:', error);
            toast.error(t('recipes.failedToMark'));
        }
    };

    const getAllergens = (recipe: Recipe): string[] => {
        const allergens = new Set<string>();
        recipe.ingredients?.forEach((ing: any) => {
            ing.allergens?.forEach((allergen: string) => allergens.add(allergen));
        });
        return Array.from(allergens);
    };

    const getDifficultyColor = (difficulty: string) => {
        switch (difficulty) {
            case 'beginner': return 'bg-green-100 text-green-800';
            case 'intermediate': return 'bg-yellow-100 text-yellow-800';
            case 'advanced': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 p-6">
            {/* Header */}
            <div className="max-w-7xl mx-auto mb-8">
                <div className="bg-white rounded-2xl shadow-xl p-8">
                    <div className="flex justify-between items-start mb-6">
                        <div>
                            <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-2">
                                {t('recipes.title')}
                            </h1>
                            <p className="text-gray-600">
                                {t('recipes.libraryDescription')}
                            </p>
                        </div>
                    </div>

                    {/* Allergen Warning Banner */}
                    <AllergenWarningBanner className="mb-6" />

                    {/* Upload Button */}
                    <div className="flex gap-2 mb-6">
                        <button
                            id="upload-rcip-button"
                            onClick={() => fileInputRef.current?.click()}
                            disabled={loading}
                            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
                        >
                            <Upload className="w-5 h-5" />
                            {t('recipes.uploadRcip')}
                        </button>

                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".rcip"
                            onChange={handleFileUpload}
                            className="hidden"
                        />
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-3 gap-4 mb-6">
                        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg">
                            <div className="text-3xl font-bold text-blue-600">{stats.total}</div>
                            <div className="text-sm text-blue-800">{t('recipes.totalRecipes')}</div>
                        </div>
                        <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg">
                            <div className="text-3xl font-bold text-green-600">{stats.ingredients}</div>
                            <div className="text-sm text-green-800">{t('recipes.ingredients')}</div>
                        </div>
                        <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg">
                            <div className="text-3xl font-bold text-purple-600">{stats.steps}</div>
                            <div className="text-sm text-purple-800">{t('recipes.cookingSteps')}</div>
                        </div>
                    </div>

                    {/* Search and Filters */}
                    <div className="flex gap-3" id="recipes-filter-section">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder={t('recipes.searchRecipes')}
                                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                        </div>

                        <button
                            onClick={() => setShowFilters(!showFilters)}
                            className="flex items-center gap-2 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                        >
                            <Filter className="w-5 h-5" />
                            {t('recipes.filters')}
                        </button>
                    </div>

                    {/* Filter Panel */}
                    {showFilters && (
                        <div className="mt-4 p-4 bg-gray-50 rounded-lg grid grid-cols-4 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">{t('recipes.difficulty')}</label>
                                <select
                                    value={difficultyFilter}
                                    onChange={(e) => setDifficultyFilter(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                >
                                    <option value="">{t('recipes.all')}</option>
                                    <option value="beginner">{t('recipes.beginner')}</option>
                                    <option value="intermediate">{t('recipes.intermediate')}</option>
                                    <option value="advanced">{t('recipes.advanced')}</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">{t('recipes.cuisine')}</label>
                                <input
                                    type="text"
                                    value={cuisineFilter}
                                    onChange={(e) => setCuisineFilter(e.target.value)}
                                    placeholder={t('recipes.cuisinePlaceholder')}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                />
                            </div>

                            <div className="flex items-end">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={savedOnlyFilter}
                                        onChange={(e) => setSavedOnlyFilter(e.target.checked)}
                                        className="w-4 h-4 text-indigo-600 rounded"
                                    />
                                    <span className="text-sm font-medium text-gray-700">{t('recipes.savedOnly')}</span>
                                </label>
                            </div>

                            <div className="flex items-end">
                                <button
                                    onClick={() => {
                                        setDifficultyFilter('');
                                        setCuisineFilter('');
                                        setSavedOnlyFilter(false);
                                    }}
                                    className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
                                >
                                    {t('recipes.clearFilters')}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Content Area */}
            <div className="max-w-7xl mx-auto">
                {loading ? (
                    <div className="text-center py-12">
                        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                        <p className="mt-4 text-gray-600">{t('recipes.loadingRecipes')}</p>
                    </div>
                ) : filteredRecipes.length === 0 ? (
                    <div className="text-center py-12 bg-white rounded-2xl shadow-xl">
                        <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-500 mb-2">{t('recipes.noRecipesFound')}</p>
                        <p className="text-sm text-gray-400">{t('recipes.noRecipesDescription')}</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="recipe-collection">
                        {filteredRecipes.map((recipe) => (
                            <RecipeCard
                                key={recipe.id}
                                recipe={recipe}
                                onView={() => setSelectedRecipe(recipe)}
                                onDownload={() => handleDownload(recipe)}
                                onSave={() => handleSaveRecipe(recipe)}
                                onUnsave={() => handleUnsaveRecipe(recipe)}
                                onMarkCooked={() => handleMarkCooked(recipe)}
                                getAllergens={getAllergens}
                                getDifficultyColor={getDifficultyColor}
                            />
                        ))}
                    </div>
                )}
            </div>

            {/* Recipe Detail Modal */}
            {selectedRecipe && (
                <RecipeDetailModal
                    recipe={selectedRecipe}
                    onClose={() => setSelectedRecipe(null)}
                    onDownload={() => handleDownload(selectedRecipe)}
                    onSave={() => handleSaveRecipe(selectedRecipe)}
                    onUnsave={() => handleUnsaveRecipe(selectedRecipe)}
                    onMarkCooked={() => handleMarkCooked(selectedRecipe)}
                    getAllergens={getAllergens}
                    getDifficultyColor={getDifficultyColor}
                />
            )}

            {/* Archive Confirmation Modal */}
            {archiveConfirmation.show && archiveConfirmation.recipe && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 animate-fade-in">
                        <div className="flex items-center justify-center mb-4">
                            <AlertTriangle className="w-16 h-16 text-orange-500" />
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-4 text-center">
                            {t('recipes.archiveRecipeTitle')}
                        </h2>
                        <p className="text-gray-600 mb-4 text-center">
                            {t('recipes.archiveConfirmation', { name: archiveConfirmation.recipe.name })}
                        </p>
                        <p className="text-sm text-gray-500 mb-6 text-center">
                            {t('recipes.archiveDescription')}
                        </p>

                        {/* Countdown */}
                        {archiveConfirmation.countdown > 0 && (
                            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6">
                                <div className="flex items-center justify-center gap-2 text-orange-700">
                                    <Clock className="w-5 h-5" />
                                    <span className="font-semibold">
                                        {t('recipes.autoArchiving', { count: archiveConfirmation.countdown })}
                                    </span>
                                </div>
                                <p className="text-xs text-orange-600 text-center mt-2">
                                    {t('recipes.archiveNow')}
                                </p>
                            </div>
                        )}

                        <div className="flex gap-3">
                            <button
                                onClick={cancelArchiveRecipe}
                                className="flex-1 px-4 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
                            >
                                {t('recipes.cancel')}
                            </button>
                            <button
                                onClick={confirmArchiveRecipe}
                                className="flex-1 px-4 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition font-medium"
                            >
                                {t('recipes.archiveRecipeButton')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// Recipe Card Component (same as before, but smaller for brevity)
interface RecipeCardProps {
    recipe: Recipe;
    onView: () => void;
    onDownload: () => void;
    onSave: () => void;
    onUnsave: () => void;
    onMarkCooked: () => void;
    getAllergens: (recipe: Recipe) => string[];
    getDifficultyColor: (difficulty: string) => string;
}

const RecipeCard: React.FC<RecipeCardProps> = ({
    recipe, onView, onDownload, onSave, onUnsave, onMarkCooked, getAllergens, getDifficultyColor
}) => {
    const { t } = useTranslation();
    const allergens = getAllergens(recipe);

    return (
        <div className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
            <div className="bg-gradient-to-r from-orange-400 to-red-500 h-32 flex items-center justify-center">
                <ChefHat className="w-16 h-16 text-white opacity-50" />
            </div>

            <div className="p-6">
                <div className="flex justify-between items-start mb-3">
                    <h3 className="text-xl font-bold text-gray-900 flex-1">{recipe.name}</h3>
                    {recipe.is_saved && (
                        <Heart className="w-5 h-5 text-red-500 fill-current flex-shrink-0 ml-2" />
                    )}
                </div>

                <p className="text-gray-600 text-sm mb-4 line-clamp-2">{recipe.description}</p>

                {/* Meta Info */}
                <div className="flex flex-wrap gap-2 mb-4">
                    {recipe.total_time_minutes && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm">
                            <Clock className="w-4 h-4" />
                            {recipe.total_time_minutes}m
                        </span>
                    )}

                    {recipe.servings && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-50 text-green-700 rounded-full text-sm">
                            <Users className="w-4 h-4" />
                            {recipe.servings}
                        </span>
                    )}

                    <span className={`px-3 py-1 rounded-full text-sm capitalize ${getDifficultyColor(recipe.difficulty)}`}>
                        {recipe.difficulty}
                    </span>
                </div>

                {/* Allergens */}
                {allergens.length > 0 && (
                    <div className="mb-4 p-2 bg-amber-50 border border-amber-200 rounded-lg">
                        <div className="flex items-center gap-1 text-amber-800 text-xs font-medium mb-1">
                            <AlertTriangle className="w-3 h-3" />
                            {t('recipes.allergens')}
                        </div>
                        <div className="flex flex-wrap gap-1">
                            {allergens.slice(0, 3).map((allergen, idx) => (
                                <span key={idx} className="px-2 py-0.5 bg-amber-100 text-amber-900 rounded text-xs">
                                    {allergen}
                                </span>
                            ))}
                            {allergens.length > 3 && (
                                <span className="px-2 py-0.5 bg-amber-100 text-amber-900 rounded text-xs">
                                    +{allergens.length - 3}
                                </span>
                            )}
                        </div>
                    </div>
                )}

                {/* Stats */}
                <div className="flex gap-4 text-xs text-gray-500 mb-4">
                    <span>🍳 {t('recipes.cookedCount', { count: recipe.times_cooked })}</span>
                    <span>📋 {t('recipes.used', { count: recipe.times_added_to_lists })}</span>
                </div>

                {/* Actions */}
                <div className="flex gap-2 flex-wrap">
                    <button
                        onClick={onView}
                        className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm font-medium"
                    >
                        {t('recipes.viewRecipe')}
                    </button>

                    <button
                        onClick={onDownload}
                        className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                        title={t('recipes.downloadRcip')}
                    >
                        <Download className="w-4 h-4 text-gray-600" />
                    </button>

                    {recipe.is_saved ? (
                        <>
                            <button
                                onClick={onUnsave}
                                className="flex items-center gap-1.5 px-3 py-2 bg-orange-100 text-orange-700 border border-orange-300 rounded-lg hover:bg-orange-200 transition text-sm font-medium"
                                title={t('recipes.moveToArchive')}
                            >
                                <Archive className="w-4 h-4" />
                                {t('recipes.moveToArchive')}
                            </button>
                            <button
                                onClick={onMarkCooked}
                                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition text-sm font-medium ${recipe.last_cooked
                                    ? 'bg-green-600 text-white border border-green-600 hover:bg-green-700'
                                    : 'border border-green-300 text-green-600 hover:bg-green-50'
                                    }`}
                                title={recipe.last_cooked ? t('recipes.cooked') : t('recipes.markAsCooked')}
                            >
                                <ChefHat className="w-4 h-4" />
                                {recipe.last_cooked ? t('recipes.cooked') : t('recipes.markAsCooked')}
                            </button>
                        </>
                    ) : (
                        <button
                            onClick={onSave}
                            className="px-4 py-2 border border-blue-300 rounded-lg hover:bg-blue-50 transition text-sm font-medium text-blue-700"
                            title={t('recipes.saveToCollection')}
                        >
                            <Heart className="w-4 h-4 text-blue-600 inline mr-1" />
                            {t('recipes.save')}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

// Recipe Detail Modal Component
interface RecipeDetailModalProps {
    recipe: Recipe;
    onClose: () => void;
    onDownload: () => void;
    onSave: () => void;
    onUnsave: () => void;
    onMarkCooked: () => void;
    getAllergens: (recipe: Recipe) => string[];
    getDifficultyColor: (difficulty: string) => string;
}

const RecipeDetailModal: React.FC<RecipeDetailModalProps> = ({
    recipe, onClose, onDownload, onSave, onUnsave, onMarkCooked, getAllergens, getDifficultyColor
}) => {
    const { t, i18n } = useTranslation();
    const { token, logout } = useAuth();

    // Debug: Log what recipe data we received
    console.log('🍳 [MODAL] Opened with recipe:', recipe.name);
    console.log('🍳 [MODAL] Current language:', i18n.language);
    console.log('🍳 [MODAL] Recipe ingredients[0]:', recipe.ingredients?.[0]);
    console.log('🍳 [MODAL] Recipe steps[0]:', recipe.steps?.[0]);

    const allergens = getAllergens(recipe);
    const [showJSON, setShowJSON] = useState(false);
    const [checkedIngredients, setCheckedIngredients] = useState<Set<number>>(new Set());
    const [shoppingLists, setShoppingLists] = useState<any[]>([]);
    const [selectedListId, setSelectedListId] = useState<string>('');
    const [showListSelector, setShowListSelector] = useState(false);
    const [addingToList, setAddingToList] = useState(false);

    const toggleIngredient = (index: number) => {
        const newSet = new Set(checkedIngredients);
        if (newSet.has(index)) {
            newSet.delete(index);
        } else {
            newSet.add(index);
        }
        setCheckedIngredients(newSet);
    };

    // Fetch shopping lists when modal opens (only for saved recipes)
    useEffect(() => {
        const fetchShoppingLists = async () => {
            if (recipe.is_saved && token) {
                try {
                    const api = new ApiService(token, logout);
                    const data = await api.getShoppingLists();
                    const lists = data.results || data;
                    setShoppingLists(lists);
                    // Auto-select first list if available
                    if (lists.length > 0) {
                        setSelectedListId(lists[0].id);
                    }
                } catch (error) {
                    console.error('Failed to fetch shopping lists:', error);
                }
            }
        };
        fetchShoppingLists();
    }, [recipe.is_saved, token, logout]);

    const handleAddToShoppingList = async () => {
        if (!selectedListId) {
            toast.error(t('recipes.pleaseSelectShoppingList'));
            return;
        }

        if (checkedIngredients.size === 0) {
            toast.error(t('recipes.pleaseSelectIngredients'));
            return;
        }

        setAddingToList(true);
        const api = new ApiService(token, logout);

        try {
            // Get checked ingredients
            const ingredientsToAdd = Array.from(checkedIngredients).map(idx => recipe.ingredients[idx]);

            // Helper function to parse quantity and determine counter type
            const parseIngredientQuantity = (ingredient: any) => {
                console.log(`\n[RECIPE ADD] ========================================`);
                console.log(`[RECIPE ADD] Processing ingredient:`, ingredient);
                console.log(`[RECIPE ADD] - name: "${ingredient.name}"`);
                console.log(`[RECIPE ADD] - amount: ${ingredient.amount}`);
                console.log(`[RECIPE ADD] - quantity: ${ingredient.quantity}`);
                console.log(`[RECIPE ADD] - unit: "${ingredient.unit}"`);

                const amount = ingredient.amount || ingredient.quantity || 1;
                const unit = (ingredient.unit || '').toLowerCase();
                const name = (ingredient.name || '').toLowerCase();

                console.log(`[RECIPE ADD] Parsed values:`);
                console.log(`[RECIPE ADD] - amount: ${amount}`);
                console.log(`[RECIPE ADD] - unit: "${unit}"`);
                console.log(`[RECIPE ADD] - name: "${name}"`);

                let weight_quantity = 0;
                let liquid_quantity = 0;
                let item_quantity = 1;
                let auto_enable_counter = null;

                // Weight units (grams, kg, oz, lb)
                if (unit.includes('g') || unit.includes('gram') || unit.includes('kg') ||
                    unit.includes('oz') || unit.includes('lb')) {
                    // Convert to grams
                    let grams = amount;
                    if (unit.includes('kg')) grams = amount * 1000;
                    else if (unit.includes('oz')) grams = amount * 28.35;
                    else if (unit.includes('lb')) grams = amount * 453.59;

                    weight_quantity = grams;
                    item_quantity = 1;
                    auto_enable_counter = 'weight';

                    console.log(`[RECIPE ADD] ${ingredient.name}: ${grams}g (weight counter)`);
                    console.log(`[RECIPE ADD] ✅ WEIGHT MODE ACTIVATED`);
                }
                // Volume/Liquid units (ml, l, cup, fl oz)
                else if (unit.includes('ml') || unit.includes('l') || unit.includes('liter') ||
                    unit.includes('cup') || unit.includes('fl') || unit.includes('fluid')) {
                    // Convert to ml
                    let ml = amount;
                    if (unit.includes('l') && !unit.includes('ml')) ml = amount * 1000;
                    else if (unit.includes('cup')) ml = amount * 240;
                    else if (unit.includes('fl oz')) ml = amount * 30;

                    liquid_quantity = ml;
                    item_quantity = 1;
                    auto_enable_counter = 'liquid';

                    console.log(`[RECIPE ADD] ${ingredient.name}: ${ml}ml (liquid counter)`);
                }
                // Infer from ingredient name if no clear unit
                else if (!unit || unit === 'unit' || unit === 'piece' || unit === 'pieces') {
                    // Check if it's likely a liquid
                    if (name.includes('water') || name.includes('milk') || name.includes('oil') ||
                        name.includes('broth') || name.includes('stock') || name.includes('juice') ||
                        name.includes('cream') || name.includes('sauce') || name.includes('liquid')) {
                        // Assume ml if small number, liters if large
                        liquid_quantity = amount < 10 ? amount * 1000 : amount;
                        item_quantity = 1;
                        auto_enable_counter = 'liquid';
                        console.log(`[RECIPE ADD] ${ingredient.name}: ${liquid_quantity}ml (inferred liquid)`);
                    }
                    // Check if it's a spice or herb (use weight)
                    else if (name.includes('salt') || name.includes('pepper') || name.includes('spice') ||
                        name.includes('herb') || name.includes('cumin') || name.includes('paprika')) {
                        weight_quantity = amount < 10 ? amount * 5 : amount; // Small amounts are teaspoons
                        item_quantity = 1;
                        auto_enable_counter = 'weight';
                        console.log(`[RECIPE ADD] ${ingredient.name}: ${weight_quantity}g (inferred spice)`);
                    }
                    // Default to quantity counter
                    else {
                        item_quantity = amount;
                        console.log(`[RECIPE ADD] ${ingredient.name}: ${amount} pieces (quantity counter)`);
                    }
                } else {
                    // Unknown unit, use quantity counter
                    item_quantity = amount;
                    console.log(`[RECIPE ADD] ${ingredient.name}: ${amount} ${unit} (quantity counter)`);
                }

                return { weight_quantity, liquid_quantity, quantity: item_quantity, auto_enable_counter };
            };

            // Add each ingredient to the shopping list
            let successCount = 0;
            console.log(`\n[RECIPE ADD] ========================================`);
            console.log(`[RECIPE ADD] Starting to add ${ingredientsToAdd.length} ingredients`);
            console.log(`[RECIPE ADD] ========================================\n`);

            for (const ingredient of ingredientsToAdd) {
                try {
                    const parsed = parseIngredientQuantity(ingredient);

                    console.log(`[RECIPE ADD] Parsed result:`, parsed);

                    const itemData: any = {
                        name: ingredient.name,
                        quantity: parsed.quantity,
                        unit: ingredient.unit || 'unit',
                        weight_quantity: parsed.weight_quantity,
                        liquid_quantity: parsed.liquid_quantity,
                        notes: ingredient.notes || ''
                    };

                    // Add auto-enable counter flag if needed
                    if (parsed.auto_enable_counter) {
                        itemData._auto_enable_counter = parsed.auto_enable_counter;
                    }

                    console.log(`\n[RECIPE ADD] 📤 Sending to API:`, itemData);
                    console.log(`[RECIPE ADD] - weight_quantity: ${itemData.weight_quantity}`);
                    console.log(`[RECIPE ADD] - liquid_quantity: ${itemData.liquid_quantity}`);
                    console.log(`[RECIPE ADD] - _auto_enable_counter: ${itemData._auto_enable_counter}`);

                    await api.addItemToList(selectedListId, itemData);
                    successCount++;

                    console.log(`[RECIPE ADD] ✅ Successfully added: ${ingredient.name}`);
                } catch (error) {
                    console.error(`[RECIPE ADD] ❌ Failed to add ${ingredient.name}:`, error);
                }
            }

            if (successCount > 0) {
                toast.success(t('recipes.addedIngredients', {
                    count: successCount,
                    plural: successCount > 1 ? 's' : ''
                }));
                setCheckedIngredients(new Set()); // Clear checkboxes
                setShowListSelector(false);
            } else {
                toast.error(t('recipes.failedToAddIngredients'));
            }
        } catch (error) {
            console.error('Error adding to shopping list:', error);
            toast.error(t('recipes.failedToAddIngredients'));
        } finally {
            setAddingToList(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full my-8">
                {/* Header */}
                <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6 rounded-t-2xl">
                    <div className="flex justify-between items-start">
                        <div className="flex-1">
                            <h2 className="text-3xl font-bold mb-2">{recipe.name}</h2>
                            <p className="text-indigo-100">{recipe.description}</p>
                        </div>
                        <button
                            onClick={onClose}
                            className="text-white hover:bg-white hover:bg-opacity-20 p-2 rounded-lg transition"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </div>

                    {/* Meta Info */}
                    <div className="flex flex-wrap gap-4 mt-4 text-sm">
                        {recipe.total_time_minutes && (
                            <div className="flex items-center gap-2">
                                <Clock className="w-4 h-4" />
                                {recipe.total_time_minutes} {t('recipes.minutes')}
                            </div>
                        )}

                        {recipe.servings && (
                            <div className="flex items-center gap-2">
                                <Users className="w-4 h-4" />
                                {recipe.servings} {t('recipes.servings')}
                            </div>
                        )}

                        <div className="flex items-center gap-2">
                            👨‍🍳 {recipe.author}
                        </div>

                        <div className={`px-3 py-1 rounded-full capitalize ${getDifficultyColor(recipe.difficulty)} bg-opacity-20 text-white`}>
                            {recipe.difficulty}
                        </div>
                    </div>
                </div>

                {/* Allergen Warning */}
                {allergens.length > 0 && (
                    <div className="p-4 bg-amber-50 border-b border-amber-200">
                        <div className="flex items-center gap-2 text-amber-900">
                            <AlertTriangle className="w-5 h-5" />
                            <strong>{t('recipes.containsAllergens')}</strong>
                            {allergens.map((allergen, idx) => (
                                <span key={idx} className="px-2 py-1 bg-amber-200 rounded text-sm">
                                    {allergen}
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Content */}
                <div className="p-6 max-h-[60vh] overflow-y-auto">
                    <div className="grid md:grid-cols-2 gap-6">
                        {/* Ingredients */}
                        <div>
                            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                                {t('recipes.ingredientsTitle')}
                            </h3>
                            <div className="space-y-2">
                                {recipe.ingredients?.map((ing: any, idx: number) => (
                                    <div key={idx} className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded">
                                        <input
                                            type="checkbox"
                                            checked={checkedIngredients.has(idx)}
                                            onChange={() => toggleIngredient(idx)}
                                            className="mt-1 w-4 h-4 text-indigo-600 rounded"
                                        />
                                        <div className="flex-1">
                                            <div className={checkedIngredients.has(idx) ? 'line-through text-gray-400' : ''}>
                                                <span className="font-semibold text-indigo-600">
                                                    {ing.human_amount || ((ing.amount || ing.quantity) && ing.unit ? `${ing.amount || ing.quantity} ${ing.unit}` : '')}
                                                </span>
                                                {' '}
                                                <span>
                                                    {ing.display_name?.[i18n.language] || ing.display_name?.en || ing.name}
                                                </span>
                                            </div>
                                            {ing.notes && (
                                                <p className="text-xs text-gray-500 mt-1">{ing.notes}</p>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Add to Shopping List (only for saved recipes) */}
                            {recipe.is_saved && checkedIngredients.size > 0 && (
                                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                                    <div className="text-sm text-blue-700 mb-2 font-medium">
                                        {t('recipes.ingredientsSelected', {
                                            count: checkedIngredients.size,
                                            plural: checkedIngredients.size > 1 ? 's' : ''
                                        })}
                                    </div>

                                    {shoppingLists.length === 0 ? (
                                        <div className="text-center py-3">
                                            <p className="text-sm text-gray-600 mb-2">
                                                {t('recipes.noShoppingLists')}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                {t('recipes.createShoppingListFirst')}
                                            </p>
                                        </div>
                                    ) : !showListSelector ? (
                                        <button
                                            onClick={() => setShowListSelector(true)}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                                        >
                                            <ShoppingCart className="w-4 h-4" />
                                            {t('recipes.addToShoppingList')}
                                        </button>
                                    ) : (
                                        <div className="space-y-2">
                                            <select
                                                value={selectedListId}
                                                onChange={(e) => setSelectedListId(e.target.value)}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            >
                                                {shoppingLists.map((list: any) => (
                                                    <option key={list.id} value={list.id}>
                                                        {list.name}
                                                    </option>
                                                ))}
                                            </select>
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={handleAddToShoppingList}
                                                    disabled={addingToList}
                                                    className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50"
                                                >
                                                    {addingToList ? t('recipes.adding') : t('recipes.confirm')}
                                                </button>
                                                <button
                                                    onClick={() => setShowListSelector(false)}
                                                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition"
                                                >
                                                    {t('recipes.cancel')}
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Steps */}
                        <div>
                            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                                {t('recipes.instructions')}
                            </h3>
                            <div className="space-y-4">
                                {recipe.steps?.map((step: any, idx: number) => (
                                    <div key={idx} className="flex gap-3">
                                        <div className="flex-shrink-0 w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center font-bold">
                                            {idx + 1}
                                        </div>
                                        <div className="flex-1">
                                            <p className="text-gray-700">
                                                {step.text_translations?.[i18n.language] || step.text || step.human_text || step.instruction}
                                            </p>
                                            {step.params && (
                                                <div className="flex gap-2 mt-2">
                                                    {step.params.time_minutes && (
                                                        <span className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded">
                                                            ⏱️ {step.params.time_minutes}m
                                                        </span>
                                                    )}
                                                    {step.params.temperature_c && (
                                                        <span className="text-xs px-2 py-1 bg-orange-50 text-orange-700 rounded">
                                                            🌡️ {step.params.temperature_c}°C
                                                        </span>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Source URL */}
                    {recipe.source_url && (
                        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                            <div className="flex items-center gap-2">
                                <ExternalLink className="w-4 h-4 text-gray-600" />
                                <strong className="text-sm text-gray-700">{t('recipes.source')}</strong>
                                <a
                                    href={recipe.source_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-indigo-600 hover:underline text-sm"
                                >
                                    {recipe.source_url}
                                </a>
                            </div>
                        </div>
                    )}

                    {/* JSON View */}
                    {showJSON && (
                        <div className="mt-6">
                            <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                                <FileJson className="w-5 h-5" />
                                {t('recipes.rcipFormat')}
                            </h3>
                            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-xs">
                                {JSON.stringify(recipe, null, 2)}
                            </pre>
                        </div>
                    )}
                </div>

                {/* Footer Actions */}
                <div className="p-6 border-t border-gray-200 flex gap-3">
                    <button
                        onClick={() => setShowJSON(!showJSON)}
                        className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                    >
                        <FileJson className="w-4 h-4" />
                        {showJSON ? t('recipes.hide') : t('recipes.show')} {t('recipes.json')}
                    </button>

                    <button
                        onClick={onDownload}
                        className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                    >
                        <Download className="w-4 h-4" />
                        {t('recipes.downloadRcip')}
                    </button>

                    <button
                        onClick={onMarkCooked}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${recipe.last_cooked
                            ? 'bg-green-600 text-white hover:bg-green-700'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                    >
                        {recipe.last_cooked ? (
                            <>
                                <Check className="w-4 h-4" />
                                {t('recipes.cookedCheck')}
                            </>
                        ) : (
                            <>
                                <ChefHat className="w-4 h-4" />
                                {t('recipes.markAsCooked')}
                            </>
                        )}
                    </button>

                    {recipe.is_saved ? (
                        <button
                            onClick={onUnsave}
                            className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition"
                        >
                            <Archive className="w-4 h-4" />
                            {t('recipes.moveToArchive')}
                        </button>
                    ) : (
                        <button
                            onClick={onSave}
                            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                        >
                            <Heart className="w-4 h-4" />
                            {t('recipes.saveToCollection')}
                        </button>
                    )}

                    <button
                        onClick={onClose}
                        className="ml-auto px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
                    >
                        {t('recipes.close')}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Recipes;
