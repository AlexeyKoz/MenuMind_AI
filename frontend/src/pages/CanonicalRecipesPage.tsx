import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { RecipeCard, RecipeBuilderWizard, ReviewsSection, LoadingSpinner } from '../components';
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';
import { Heart } from 'lucide-react';
import toast from 'react-hot-toast';

/**
 * CanonicalRecipesPage - Browse and discover deduplicated recipes
 * 
 * Features:
 * - Browse all canonical recipes (no duplicates!)
 * - Filter by cuisine, difficulty, diet labels
 * - Sort by popularity, rating, recent, most cooked
 * - Like and rate recipes
 * - View recipe details with reviews
 * - Create new recipes with AI builder wizard
 */
const CanonicalRecipesPage: React.FC = () => {
    const { t } = useTranslation();
    const { token, user, logout } = useAuth();
    const api = new ApiService(token, () => {
        console.log('🔐 Token expired - logging out user');
        alert(t('discover.sessionExpired'));
        logout();
    });

    const [recipes, setRecipes] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedRecipe, setSelectedRecipe] = useState<any>(null);
    const [showBuilder, setShowBuilder] = useState(false);
    const [recipeLiked, setRecipeLiked] = useState(false);
    const [liking, setLiking] = useState(false);

    // Filters
    const [search, setSearch] = useState('');
    const [cuisine, setCuisine] = useState('');
    const [difficulty, setDifficulty] = useState('');
    const [dietLabels, setDietLabels] = useState<string[]>([]);
    const [sortBy, setSortBy] = useState('popular');

    useEffect(() => {
        loadRecipes();
    }, [search, cuisine, difficulty, dietLabels, sortBy]);

    // Handle direct recipe link from query parameter
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const recipeId = params.get('recipe');

        console.log(`📖 CanonicalRecipesPage - Checking for recipe param: ${recipeId}`);

        if (recipeId) {
            console.log(`✅ Recipe ID found in URL: ${recipeId}, loading recipe...`);
            // Auto-open the recipe if provided in URL
            const loadRecipeFromUrl = async () => {
                try {
                    console.log(`🔍 Fetching recipe with ID: ${recipeId}`);
                    const recipe = await api.getCanonicalRecipe(recipeId);
                    console.log(`✅ Recipe loaded:`, recipe.name);
                    setSelectedRecipe(recipe);

                    // Remove query param from URL to clean it up
                    window.history.replaceState({}, '', window.location.pathname);
                } catch (err: any) {
                    console.error('❌ Failed to load recipe from URL:', err);
                }
            };

            loadRecipeFromUrl();
        } else {
            console.log(`⚠️ No recipe ID in URL`);
        }
    }, [api]);

    const loadRecipes = async () => {
        setLoading(true);
        setError('');

        try {
            const result = await api.getCanonicalRecipes({
                search: search || undefined,
                cuisine: cuisine || undefined,
                difficulty: difficulty || undefined,
                diet_labels: dietLabels.length > 0 ? dietLabels : undefined,
                sort: sortBy  // Backend expects 'sort' parameter with values: popular, top_rated, most_cooked, recent
            });

            setRecipes(result.results || result);
        } catch (err: any) {
            setError(err.message || 'Failed to load recipes');
        } finally {
            setLoading(false);
        }
    };

    const handleLike = async (recipeId: string) => {
        const result = await api.likeCanonicalRecipe(recipeId);
        return result;
    };

    const handleRate = async (recipeId: string, rating: number) => {
        await api.rateCanonicalRecipe(recipeId, rating);
        await loadRecipes(); // Refresh to show updated rating
    };

    const handleRecipeClick = async (recipeId: string) => {
        try {
            const recipe = await api.getCanonicalRecipe(recipeId);

            // Check if recipe is already liked
            try {
                const likeStatus = await api.getLikeStatus(recipeId);
                setRecipeLiked(likeStatus.is_liked || false);
            } catch (likeErr) {
                // If we can't get like status, assume not liked
                setRecipeLiked(false);
            }

            setSelectedRecipe(recipe);
        } catch (err: any) {
            alert(err.message || 'Failed to load recipe details');
        }
    };

    const handleLikeAction = async () => {
        if (!selectedRecipe || liking) return;

        setLiking(true);
        try {
            await api.likeCanonicalRecipe(selectedRecipe.id);

            // Toggle the liked state
            setRecipeLiked(!recipeLiked);

            // Show success message
            if (!recipeLiked) {
                toast.success(t('discover.recipeAddedToFavorites'));
            } else {
                toast.success(t('discover.recipeRemovedFromFavorites'));
            }

            // Refresh recipes to update like count in the grid
            await loadRecipes();

        } catch (error: any) {
            console.error('Like error:', error);
            toast.error(error.message || t('discover.failedToUpdateLike'));
        } finally {
            setLiking(false);
        }
    };

    const handleBuilderComplete = (result: any) => {
        setShowBuilder(false);
        alert(t('discover.recipeCreatedSuccessfully', { name: result.recipe_summary.name }));
        loadRecipes();
    };

    const toggleDietLabel = (label: string) => {
        setDietLabels(prev =>
            prev.includes(label)
                ? prev.filter(l => l !== label)
                : [...prev, label]
        );
    };

    if (showBuilder) {
        return (
            <div className="min-h-screen bg-gray-50 py-8 px-4">
                <RecipeBuilderWizard
                    onStartBuilder={api.startBuilder}
                    onBuilderStep={api.builderStep}
                    onComplete={handleBuilderComplete}
                    onCancel={() => setShowBuilder(false)}
                />
            </div>
        );
    }

    if (selectedRecipe) {
        return (
            <div className="min-h-screen bg-gray-50 py-8 px-4">
                <div className="max-w-4xl mx-auto">
                    <button
                        onClick={() => setSelectedRecipe(null)}
                        className="mb-6 flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                        </svg>
                        {t('discover.backToRecipes')}
                    </button>

                    <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
                        <div className="flex justify-between items-start mb-4">
                            <div className="flex-1">
                                <h1 className="text-4xl font-bold text-gray-900">
                                    {selectedRecipe.name}
                                </h1>
                                <p className="text-lg text-gray-600 mt-2">
                                    {selectedRecipe.description}
                                </p>
                            </div>

                            {/* Like Button */}
                            <button
                                onClick={handleLikeAction}
                                disabled={liking}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all font-medium ${recipeLiked
                                    ? 'bg-red-600 text-white hover:bg-red-700'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    } ${liking ? 'opacity-50 cursor-not-allowed' : ''}`}
                                title={recipeLiked ? t('discover.removeFromFavorites') : t('discover.addToFavorites')}
                            >
                                <Heart className={`w-5 h-5 ${recipeLiked ? 'fill-current' : ''}`} />
                                {liking ? t('discover.updating') : recipeLiked ? t('discover.favorited') : t('discover.addToFavorites')}
                            </button>
                        </div>

                        {/* Recipe Stats */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                            <div className="text-center p-4 bg-gray-50 rounded-lg">
                                <div className="text-2xl font-bold text-gray-900">{selectedRecipe.servings}</div>
                                <div className="text-sm text-gray-600">{t('discover.servings')}</div>
                            </div>
                            <div className="text-center p-4 bg-gray-50 rounded-lg">
                                <div className="text-2xl font-bold text-gray-900">{selectedRecipe.total_time_minutes}</div>
                                <div className="text-sm text-gray-600">{t('discover.minutes')}</div>
                            </div>
                            <div className="text-center p-4 bg-gray-50 rounded-lg">
                                <div className="text-2xl font-bold text-gray-900">{selectedRecipe.difficulty}</div>
                                <div className="text-sm text-gray-600">{t('discover.difficulty')}</div>
                            </div>
                            <div className="text-center p-4 bg-gray-50 rounded-lg">
                                <div className="text-2xl font-bold text-gray-900">{selectedRecipe.total_cooked}</div>
                                <div className="text-sm text-gray-600">{t('discover.timesCooked')}</div>
                            </div>
                        </div>

                        {/* Ingredients & Steps */}
                        <div className="grid md:grid-cols-2 gap-8">
                            {/* Ingredients */}
                            <div>
                                <h3 className="text-2xl font-bold mb-4 flex items-center gap-2 text-gray-900">
                                    <span className="text-3xl">🥘</span>
                                    {t('discover.ingredients')}
                                </h3>
                                {selectedRecipe.base_ingredients && selectedRecipe.base_ingredients.length > 0 ? (
                                    <div className="space-y-3">
                                        {selectedRecipe.base_ingredients.map((ing: any, idx: number) => (
                                            <div key={idx} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
                                                <div className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-600 rounded-full text-sm font-semibold">
                                                    {idx + 1}
                                                </div>
                                                <div className="flex-1">
                                                    <span className="font-semibold text-blue-600">
                                                        {ing.amount && ing.unit ? `${ing.amount} ${ing.unit}` : ''}
                                                    </span>
                                                    {' '}
                                                    <span className="text-gray-900">{ing.name}</span>
                                                    {ing.notes && (
                                                        <p className="text-sm text-gray-500 mt-1">{ing.notes}</p>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-gray-500 italic">{t('discover.noIngredientsListed')}</p>
                                )}
                            </div>

                            {/* Steps */}
                            <div>
                                <h3 className="text-2xl font-bold mb-4 flex items-center gap-2 text-gray-900">
                                    <span className="text-3xl">📝</span>
                                    {t('discover.instructions')}
                                </h3>
                                {selectedRecipe.base_steps && selectedRecipe.base_steps.length > 0 ? (
                                    <div className="space-y-4">
                                        {selectedRecipe.base_steps.map((step: any, idx: number) => (
                                            <div key={idx} className="flex items-start gap-3">
                                                <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-green-100 text-green-700 rounded-full font-bold">
                                                    {idx + 1}
                                                </div>
                                                <div className="flex-1 pt-1">
                                                    <p className="text-gray-900 leading-relaxed">
                                                        {step.instruction || step.text || step}
                                                    </p>
                                                    {step.time_minutes && (
                                                        <p className="text-sm text-gray-500 mt-1">
                                                            ⏱️ {t('discover.minutesLabel', { time: step.time_minutes })}
                                                        </p>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-gray-500 italic">{t('discover.noInstructionsListed')}</p>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Reviews Section */}
                    <div className="bg-white rounded-xl shadow-lg p-8">
                        <ReviewsSection
                            recipeId={selectedRecipe.id}
                            currentUserId={user?.username}
                            onGetReviews={api.getReviews}
                            onAddReview={api.addReview}
                            onUpdateReview={api.updateReview}
                            onDeleteReview={api.deleteReview}
                            onMarkHelpful={api.markReviewHelpful}
                        />
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-8 px-4">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-4xl font-bold text-gray-900 mb-2">
                            {t('discover.title')}
                        </h1>
                        <p className="text-gray-600">
                            {t('discover.subtitle')}
                        </p>
                    </div>
                    <button
                        onClick={() => setShowBuilder(true)}
                        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                        </svg>
                        {t('discover.createRecipe')}
                    </button>
                </div>

                {/* Filters */}
                <div className="bg-white rounded-xl shadow-md p-6 mb-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                        {/* Search */}
                        <input
                            type="text"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder={t('discover.searchPlaceholder')}
                            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />

                        {/* Cuisine */}
                        <select
                            value={cuisine}
                            onChange={(e) => setCuisine(e.target.value)}
                            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="">{t('discover.allCuisines')}</option>
                            <option value="Italian">{t('discover.cuisines.italian')}</option>
                            <option value="Mexican">{t('discover.cuisines.mexican')}</option>
                            <option value="Chinese">{t('discover.cuisines.chinese')}</option>
                            <option value="Indian">{t('discover.cuisines.indian')}</option>
                            <option value="Japanese">{t('discover.cuisines.japanese')}</option>
                            <option value="French">{t('discover.cuisines.french')}</option>
                        </select>

                        {/* Difficulty */}
                        <select
                            value={difficulty}
                            onChange={(e) => setDifficulty(e.target.value)}
                            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="">{t('discover.allDifficulties')}</option>
                            <option value="beginner">{t('discover.difficulties.beginner')}</option>
                            <option value="intermediate">{t('discover.difficulties.intermediate')}</option>
                            <option value="advanced">{t('discover.difficulties.advanced')}</option>
                        </select>

                        {/* Sort */}
                        <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value)}
                            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="popular">{t('discover.mostPopular')}</option>
                            <option value="top_rated">{t('discover.topRated')}</option>
                            <option value="most_cooked">{t('discover.mostCooked')}</option>
                            <option value="recent">{t('discover.mostRecent')}</option>
                        </select>
                    </div>

                    {/* Diet Labels */}
                    <div className="flex flex-wrap gap-2">
                        {[
                            { key: 'vegetarian', label: t('discover.dietLabels.vegetarian') },
                            { key: 'vegan', label: t('discover.dietLabels.vegan') },
                            { key: 'gluten-free', label: t('discover.dietLabels.glutenFree') },
                            { key: 'dairy-free', label: t('discover.dietLabels.dairyFree') },
                            { key: 'keto', label: t('discover.dietLabels.keto') },
                            { key: 'paleo', label: t('discover.dietLabels.paleo') }
                        ].map((item) => (
                            <button
                                key={item.key}
                                onClick={() => toggleDietLabel(item.key)}
                                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${dietLabels.includes(item.key)
                                    ? 'bg-green-600 text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                {item.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Error */}
                {error && (
                    <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                        {error}
                    </div>
                )}

                {/* Recipes Grid */}
                {loading ? (
                    <div className="flex justify-center py-12">
                        <LoadingSpinner />
                    </div>
                ) : recipes.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                        {t('discover.noRecipesFound')}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {recipes.map((recipe) => (
                            <RecipeCard
                                key={recipe.id}
                                recipe={recipe}
                                onLike={handleLike}
                                onRate={handleRate}
                                onClick={handleRecipeClick}
                                showStats={true}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default CanonicalRecipesPage;


