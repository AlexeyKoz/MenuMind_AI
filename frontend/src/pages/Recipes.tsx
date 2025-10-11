import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';
import toast from 'react-hot-toast';
import {
    Search, Upload, Download, BookOpen, Clock, Users,
    ChefHat, Heart, ExternalLink, FileJson,
    Filter, X, Check, AlertTriangle, Sparkles, Zap, Archive, ShoppingCart
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
    const { token, logout } = useAuth();
    const api = new ApiService(token, () => {
        console.log('🔐 Token expired - logging out user');
        alert('Your session has expired. Please log in again.');
        logout();
    });
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Tab state
    const [activeTab, setActiveTab] = useState<'library' | 'generator'>('library');

    // Library state
    const [recipes, setRecipes] = useState<Recipe[]>([]);
    const [filteredRecipes, setFilteredRecipes] = useState<Recipe[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
    const [showFilters, setShowFilters] = useState(false);
    const [aiQuery, setAiQuery] = useState('');
    const [aiLoading, setAiLoading] = useState(false);

    // Generator state
    const [generatedRecipes, setGeneratedRecipes] = useState<Recipe[]>([]);
    const [generatorLoading, setGeneratorLoading] = useState(false);

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
        if (activeTab === 'library') {
            loadRecipes();
        }
    }, [activeTab]);

    useEffect(() => {
        filterRecipes();
    }, [recipes, searchQuery, difficultyFilter, cuisineFilter, savedOnlyFilter]);

    const loadRecipes = async () => {
        setLoading(true);
        try {
            const data = await api.getMyRecipes();
            console.log('📚 Raw API response:', data);

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
            toast.error(error.message || 'Failed to load recipes');
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
            toast.error('Please upload a .rcip file');
            return;
        }

        setLoading(true);
        try {
            const result = await api.uploadRCIP(file);
            toast.success(result.message || 'Recipe imported successfully!');
            loadRecipes();
        } catch (error: any) {
            console.error('Upload error:', error);
            toast.error(error.message || 'Failed to upload recipe');
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
            toast.success(`Downloaded ${recipe.name}.rcip`);
        } catch (error: any) {
            console.error('Download error:', error);
            toast.error('Failed to download recipe');
        }
    };

    const handleSaveRecipe = async (recipe: Recipe) => {
        try {
            await api.saveRecipe(recipe.id);
            toast.success('Recipe saved to your collection!');
            loadRecipes();
        } catch (error: any) {
            console.error('Save error:', error);
            toast.error('Failed to save recipe');
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
            toast.success(`"${archiveConfirmation.recipe.name}" moved to archive`);
            setArchiveConfirmation({ show: false, recipe: null, countdown: 5 });
            loadRecipes();
            if (selectedRecipe?.id === archiveConfirmation.recipe.id) {
                setSelectedRecipe(null);
            }
        } catch (error: any) {
            console.error('Archive error:', error);
            toast.error('Failed to archive recipe');
        }
    };

    const cancelArchiveRecipe = () => {
        setArchiveConfirmation({ show: false, recipe: null, countdown: 5 });
    };

    const handleMarkCooked = async (recipe: Recipe) => {
        try {
            const result = await api.markRecipeCooked(recipe.id);
            const action = result.cooked ? 'cooked' : 'uncooked';
            toast.success(`Recipe marked as ${action}! ${result.cooked ? '🍳' : '↩️'}`);
            loadRecipes();
        } catch (error: any) {
            console.error('Mark cooked error:', error);
            toast.error('Failed to mark as cooked');
        }
    };

    const handleAISearch = async () => {
        if (!aiQuery.trim()) {
            toast.error('Please enter a recipe to search for');
            return;
        }

        setAiLoading(true);
        try {
            const result = await api.findRecipe(aiQuery);
            console.log('[AI SEARCH] Find recipe result:', result);

            // The recipe is already created and saved by the backend
            // The response includes: canonical_recipe, user_recipe, created
            if (result.canonical_recipe) {
                toast.success(`Recipe found: ${result.canonical_recipe.name}!`);

                // The backend already creates a user_recipe (fork), but we also need to like the canonical
                const canonicalId = result.canonical_recipe.id;
                if (canonicalId) {
                    try {
                        console.log(`[AI SEARCH] Auto-liking canonical recipe ID: ${canonicalId}`);
                        const likeResult = await api.likeCanonicalRecipe(canonicalId);
                        console.log('[AI SEARCH] Like result:', likeResult);

                        if (likeResult.saved_to_my_recipes) {
                            toast.success('✅ Recipe added to My Recipes!');
                            console.log('[AI SEARCH] ✅ Recipe saved to My Recipes');
                        }
                    } catch (likeError: any) {
                        console.error('[AI SEARCH] ❌ Failed to auto-like recipe:', likeError);
                        // Don't show error to user since recipe is already created
                    }
                } else {
                    console.warn('[AI SEARCH] ⚠️ No canonical recipe ID found');
                }
            } else {
                console.warn('[AI SEARCH] ⚠️ No canonical_recipe in result:', result);
                toast.success('Recipe found and saved!');
            }

            setAiQuery('');
            await loadRecipes();
        } catch (error: any) {
            console.error('AI search error:', error);
            toast.error(error.message || 'Failed to find recipe');
        } finally {
            setAiLoading(false);
        }
    };

    const handleGenerateRecipes = async () => {
        setGeneratorLoading(true);
        try {
            const data = await api.generateRecipes();
            const recipes = data.recipes || [];
            setGeneratedRecipes(recipes);

            if (recipes.length > 0) {
                toast.success(`Generated ${recipes.length} recipes from your inventory!`);

                // Auto-like each generated recipe to add them to My Recipes
                console.log('[AI GENERATOR] Auto-liking generated recipes...');
                let savedCount = 0;

                // Wait for all likes to complete
                const likePromises = recipes.map(async (recipe: Recipe) => {
                    if (recipe.id) {
                        try {
                            console.log(`[AI GENERATOR] Liking recipe ID: ${recipe.id}, Name: ${recipe.name}`);
                            const result = await api.likeCanonicalRecipe(recipe.id);
                            console.log(`[AI GENERATOR] Like result:`, result);

                            if (result.saved_to_my_recipes) {
                                savedCount++;
                                console.log(`[AI GENERATOR] ✅ Saved to My Recipes: ${recipe.name}`);
                            } else {
                                console.warn(`[AI GENERATOR] ⚠️ Liked but not saved to My Recipes: ${recipe.name}`);
                            }
                        } catch (likeError: any) {
                            console.error(`[AI GENERATOR] ❌ Failed to like ${recipe.name}:`, likeError);
                            console.error(`[AI GENERATOR] Error details:`, likeError.message);
                        }
                    } else {
                        console.warn(`[AI GENERATOR] Recipe has no ID:`, recipe);
                    }
                });

                // Wait for all likes to complete
                await Promise.all(likePromises);
                console.log(`[AI GENERATOR] Finished liking. Total saved: ${savedCount}/${recipes.length}`);

                if (savedCount > 0) {
                    toast.success(`✅ ${savedCount} recipe${savedCount > 1 ? 's' : ''} added to My Recipes!`);
                }

                // Refresh recipes list to show the newly saved recipes
                console.log('[AI GENERATOR] Refreshing recipes list...');
                await loadRecipes();
            }
        } catch (error: any) {
            console.error('Generate recipes error:', error);
            toast.error(error.message || 'Failed to generate recipes');
        } finally {
            setGeneratorLoading(false);
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
            {/* Header with Tabs */}
            <div className="max-w-7xl mx-auto mb-8">
                <div className="bg-white rounded-2xl shadow-xl p-8">
                    <div className="flex justify-between items-start mb-6">
                        <div>
                            <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-2">
                                🍳 Recipes
                            </h1>
                            <p className="text-gray-600">
                                {activeTab === 'library'
                                    ? 'Browse and manage your recipe collection in RCIP format'
                                    : 'Generate AI-powered recipes from your inventory'}
                            </p>
                        </div>
                    </div>

                    {/* Tab Navigation */}
                    <div className="flex gap-2 mb-6">
                        <button
                            onClick={() => setActiveTab('library')}
                            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition ${activeTab === 'library'
                                ? 'bg-indigo-600 text-white shadow-lg'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                        >
                            <BookOpen className="w-5 h-5" />
                            Recipe Library
                        </button>

                        <button
                            onClick={() => setActiveTab('generator')}
                            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition ${activeTab === 'generator'
                                ? 'bg-purple-600 text-white shadow-lg'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                        >
                            <Zap className="w-5 h-5" />
                            AI Generator
                        </button>
                    </div>

                    {/* Library Tab Content */}
                    {activeTab === 'library' && (
                        <>
                            {/* AI Search Panel - Always Visible */}
                            <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
                                <div className="flex items-center gap-3">
                                    <Sparkles className="w-6 h-6 text-purple-600" />
                                    <input
                                        type="text"
                                        value={aiQuery}
                                        onChange={(e) => setAiQuery(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && handleAISearch()}
                                        placeholder="🤖 AI Search: Describe the recipe you want (e.g., 'Italian pasta carbonara')"
                                        className="flex-1 px-4 py-3 border border-purple-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        disabled={aiLoading}
                                    />
                                    <button
                                        onClick={handleAISearch}
                                        disabled={aiLoading}
                                        className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50 font-medium"
                                    >
                                        {aiLoading ? 'Searching...' : 'Find Recipe'}
                                    </button>
                                </div>
                                <p className="text-sm text-purple-700 mt-2">
                                    AI will search the web, find the recipe, convert it to RCIP format, and automatically save it to My Recipes
                                </p>
                            </div>

                            <div className="flex gap-2 mb-6">
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={loading}
                                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
                                >
                                    <Upload className="w-5 h-5" />
                                    Upload .rcip
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
                                    <div className="text-sm text-blue-800">Total Recipes</div>
                                </div>
                                <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg">
                                    <div className="text-3xl font-bold text-green-600">{stats.ingredients}</div>
                                    <div className="text-sm text-green-800">Ingredients</div>
                                </div>
                                <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg">
                                    <div className="text-3xl font-bold text-purple-600">{stats.steps}</div>
                                    <div className="text-sm text-purple-800">Cooking Steps</div>
                                </div>
                            </div>

                            {/* Search and Filters */}
                            <div className="flex gap-3">
                                <div className="flex-1 relative">
                                    <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                                    <input
                                        type="text"
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        placeholder="Search recipes..."
                                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    />
                                </div>

                                <button
                                    onClick={() => setShowFilters(!showFilters)}
                                    className="flex items-center gap-2 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                                >
                                    <Filter className="w-5 h-5" />
                                    Filters
                                </button>
                            </div>

                            {/* Filter Panel */}
                            {showFilters && (
                                <div className="mt-4 p-4 bg-gray-50 rounded-lg grid grid-cols-4 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Difficulty</label>
                                        <select
                                            value={difficultyFilter}
                                            onChange={(e) => setDifficultyFilter(e.target.value)}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                        >
                                            <option value="">All</option>
                                            <option value="beginner">Beginner</option>
                                            <option value="intermediate">Intermediate</option>
                                            <option value="advanced">Advanced</option>
                                        </select>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Cuisine</label>
                                        <input
                                            type="text"
                                            value={cuisineFilter}
                                            onChange={(e) => setCuisineFilter(e.target.value)}
                                            placeholder="e.g., Italian"
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
                                            <span className="text-sm font-medium text-gray-700">Saved Only</span>
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
                                            Clear Filters
                                        </button>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* Content Area */}
            <div className="max-w-7xl mx-auto">
                {activeTab === 'library' ? (
                    // Library View
                    loading ? (
                        <div className="text-center py-12">
                            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                            <p className="mt-4 text-gray-600">Loading recipes...</p>
                        </div>
                    ) : filteredRecipes.length === 0 ? (
                        <div className="text-center py-12 bg-white rounded-2xl shadow-xl">
                            <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                            <p className="text-gray-500 mb-2">No recipes found</p>
                            <p className="text-sm text-gray-400">Try adjusting your filters or upload a new recipe</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
                    )
                ) : (
                    // Generator View
                    <div>
                        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
                            <div className="flex justify-between items-center">
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Generate Recipes from Inventory</h2>
                                    <p className="text-gray-600">AI will analyze your inventory and suggest recipes you can make</p>
                                </div>
                                <button
                                    onClick={handleGenerateRecipes}
                                    disabled={generatorLoading}
                                    className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 transition shadow-lg flex items-center gap-2"
                                >
                                    <Zap className="w-5 h-5" />
                                    {generatorLoading ? 'Generating...' : 'Generate Recipes'}
                                </button>
                            </div>
                        </div>

                        {generatorLoading ? (
                            <div className="text-center py-12">
                                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                                <p className="mt-4 text-gray-600">Generating recipes...</p>
                            </div>
                        ) : generatedRecipes.length === 0 ? (
                            <div className="text-center py-12 bg-white rounded-2xl shadow-xl">
                                <Zap className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                                <p className="text-gray-500 mb-2">No recipes generated yet</p>
                                <p className="text-sm text-gray-400">Click the button above to generate AI-powered recipes based on your inventory</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {generatedRecipes.map((recipe, index) => (
                                    <div key={index} className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-2xl transition-all">
                                        <div className="bg-gradient-to-r from-orange-400 to-red-500 h-32 flex items-center justify-center">
                                            <ChefHat className="w-16 h-16 text-white opacity-50" />
                                        </div>
                                        <div className="p-6">
                                            <h3 className="text-xl font-bold mb-2">{recipe.name}</h3>
                                            <div className="flex justify-between text-sm text-gray-600 mb-4">
                                                <span>⏱ {recipe.prep_time_minutes} min</span>
                                                <span className="capitalize">📊 {recipe.difficulty}</span>
                                            </div>

                                            {recipe.nutrition_per_serving && (
                                                <div className="mb-4">
                                                    <h4 className="font-medium mb-2">Nutrition per serving:</h4>
                                                    <div className="text-sm grid grid-cols-2 gap-2">
                                                        <span>Calories: {recipe.nutrition_per_serving.calories}</span>
                                                        <span>Protein: {recipe.nutrition_per_serving.protein}g</span>
                                                        <span>Carbs: {recipe.nutrition_per_serving.carbs}g</span>
                                                        <span>Fat: {recipe.nutrition_per_serving.fat}g</span>
                                                    </div>
                                                </div>
                                            )}

                                            {recipe.missing_ingredients && recipe.missing_ingredients.length > 0 && (
                                                <div className="mb-4 p-2 bg-amber-50 border border-amber-200 rounded">
                                                    <h4 className="font-medium text-amber-800 text-sm mb-1">Missing ingredients:</h4>
                                                    <div className="text-xs text-amber-700">
                                                        {recipe.missing_ingredients.join(', ')}
                                                    </div>
                                                </div>
                                            )}

                                            <button
                                                onClick={() => setSelectedRecipe(recipe)}
                                                className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
                                            >
                                                View Recipe
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
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
                            Archive Recipe?
                        </h2>
                        <p className="text-gray-600 mb-4 text-center">
                            Are you sure you want to move <span className="font-semibold">"{archiveConfirmation.recipe.name}"</span> to the archive?
                        </p>
                        <p className="text-sm text-gray-500 mb-6 text-center">
                            You can restore it later from the Archive page, or you can find it again on the Discover page.
                        </p>

                        {/* Countdown */}
                        {archiveConfirmation.countdown > 0 && (
                            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6">
                                <div className="flex items-center justify-center gap-2 text-orange-700">
                                    <Clock className="w-5 h-5" />
                                    <span className="font-semibold">
                                        Auto-archiving in {archiveConfirmation.countdown} seconds
                                    </span>
                                </div>
                                <p className="text-xs text-orange-600 text-center mt-2">
                                    Click "Archive Recipe" now to skip the wait
                                </p>
                            </div>
                        )}

                        <div className="flex gap-3">
                            <button
                                onClick={cancelArchiveRecipe}
                                className="flex-1 px-4 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={confirmArchiveRecipe}
                                className="flex-1 px-4 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition font-medium"
                            >
                                Archive Recipe
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
                            Allergens:
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
                    <span>🍳 Cooked {recipe.times_cooked}x</span>
                    <span>📋 Used {recipe.times_added_to_lists}x</span>
                </div>

                {/* Actions */}
                <div className="flex gap-2 flex-wrap">
                    <button
                        onClick={onView}
                        className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm font-medium"
                    >
                        View Recipe
                    </button>

                    <button
                        onClick={onDownload}
                        className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                        title="Download .rcip"
                    >
                        <Download className="w-4 h-4 text-gray-600" />
                    </button>

                    {recipe.is_saved ? (
                        <>
                            <button
                                onClick={onUnsave}
                                className="flex items-center gap-1.5 px-3 py-2 bg-orange-100 text-orange-700 border border-orange-300 rounded-lg hover:bg-orange-200 transition text-sm font-medium"
                                title="Move recipe to archive"
                            >
                                <Archive className="w-4 h-4" />
                                Move to Archive
                            </button>
                            <button
                                onClick={onMarkCooked}
                                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition text-sm font-medium ${recipe.last_cooked
                                    ? 'bg-green-600 text-white border border-green-600 hover:bg-green-700'
                                    : 'border border-green-300 text-green-600 hover:bg-green-50'
                                    }`}
                                title={recipe.last_cooked ? 'Unmark as cooked' : 'Mark as cooked'}
                            >
                                <ChefHat className="w-4 h-4" />
                                {recipe.last_cooked ? 'Cooked' : 'Mark as Cooked'}
                            </button>
                        </>
                    ) : (
                        <button
                            onClick={onSave}
                            className="px-4 py-2 border border-blue-300 rounded-lg hover:bg-blue-50 transition text-sm font-medium text-blue-700"
                            title="Save to collection"
                        >
                            <Heart className="w-4 h-4 text-blue-600 inline mr-1" />
                            Save
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
    const { token, logout } = useAuth();
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
            toast.error('Please select a shopping list');
            return;
        }

        if (checkedIngredients.size === 0) {
            toast.error('Please select at least one ingredient');
            return;
        }

        setAddingToList(true);
        const api = new ApiService(token, logout);

        try {
            // Get checked ingredients
            const ingredientsToAdd = Array.from(checkedIngredients).map(idx => recipe.ingredients[idx]);

            // Add each ingredient to the shopping list
            let successCount = 0;
            for (const ingredient of ingredientsToAdd) {
                try {
                    await api.addItemToList(selectedListId, {
                        name: ingredient.name,
                        quantity: ingredient.amount || 1,
                        unit: ingredient.unit || '',
                        notes: ingredient.notes || ''
                    });
                    successCount++;
                } catch (error) {
                    console.error(`Failed to add ${ingredient.name}:`, error);
                }
            }

            if (successCount > 0) {
                toast.success(`Added ${successCount} ingredient${successCount > 1 ? 's' : ''} to shopping list!`);
                setCheckedIngredients(new Set()); // Clear checkboxes
                setShowListSelector(false);
            } else {
                toast.error('Failed to add ingredients to shopping list');
            }
        } catch (error) {
            console.error('Error adding to shopping list:', error);
            toast.error('Failed to add ingredients to shopping list');
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
                                {recipe.total_time_minutes} minutes
                            </div>
                        )}

                        {recipe.servings && (
                            <div className="flex items-center gap-2">
                                <Users className="w-4 h-4" />
                                {recipe.servings} servings
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
                            <strong>Contains allergens:</strong>
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
                                🥘 Ingredients
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
                                                <span className="font-semibold text-indigo-600">{ing.human_amount || `${ing.amount || ''} ${ing.unit || ''}`.trim()}</span>
                                                {' '}
                                                <span>{ing.name}</span>
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
                                        {checkedIngredients.size} ingredient{checkedIngredients.size > 1 ? 's' : ''} selected
                                    </div>

                                    {shoppingLists.length === 0 ? (
                                        <div className="text-center py-3">
                                            <p className="text-sm text-gray-600 mb-2">
                                                You don't have any shopping lists yet.
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                Please create a shopping list first to add ingredients.
                                            </p>
                                        </div>
                                    ) : !showListSelector ? (
                                        <button
                                            onClick={() => setShowListSelector(true)}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                                        >
                                            <ShoppingCart className="w-4 h-4" />
                                            Add to Shopping List
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
                                                    {addingToList ? 'Adding...' : 'Confirm'}
                                                </button>
                                                <button
                                                    onClick={() => setShowListSelector(false)}
                                                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition"
                                                >
                                                    Cancel
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
                                📝 Instructions
                            </h3>
                            <div className="space-y-4">
                                {recipe.steps?.map((step: any, idx: number) => (
                                    <div key={idx} className="flex gap-3">
                                        <div className="flex-shrink-0 w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center font-bold">
                                            {idx + 1}
                                        </div>
                                        <div className="flex-1">
                                            <p className="text-gray-700">{step.human_text || step.instruction}</p>
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
                                <strong className="text-sm text-gray-700">Source:</strong>
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
                                RCIP Format (JSON)
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
                        {showJSON ? 'Hide' : 'Show'} JSON
                    </button>

                    <button
                        onClick={onDownload}
                        className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                    >
                        <Download className="w-4 h-4" />
                        Download .rcip
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
                                Cooked ✓
                            </>
                        ) : (
                            <>
                                <ChefHat className="w-4 h-4" />
                                Mark as Cooked
                            </>
                        )}
                    </button>

                    {recipe.is_saved ? (
                        <button
                            onClick={onUnsave}
                            className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition"
                        >
                            <Archive className="w-4 h-4" />
                            Move to Archive
                        </button>
                    ) : (
                        <button
                            onClick={onSave}
                            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                        >
                            <Heart className="w-4 h-4" />
                            Save to Collection
                        </button>
                    )}

                    <button
                        onClick={onClose}
                        className="ml-auto px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Recipes;
