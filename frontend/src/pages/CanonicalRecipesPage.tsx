import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import i18n from 'i18next';
import { RecipeCard, RecipeBuilderWizard, ReviewsSection, LoadingSpinner, AllergenWarning } from '../components';
import RecipeProgressModal from '../components/RecipeProgressModal';
import { useAuth } from '../contexts/AuthContext';
import ApiService from '../services/api';
import { Heart, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import { convertTemperaturesInText, getUserTemperatureUnit } from '../utils/recipeTextUtils';

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
    const [translationLoading, setTranslationLoading] = useState(false);
    const [translationPollInterval, setTranslationPollInterval] = useState<NodeJS.Timeout | null>(null);

    // AI Search
    const [aiQuery, setAiQuery] = useState('');
    const [aiLoading, setAiLoading] = useState(false);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [failedQuery, setFailedQuery] = useState('');
    const [showProgress, setShowProgress] = useState(false); // Progress modal

    // Filters
    const [search, setSearch] = useState('');
    const [cuisine, setCuisine] = useState('');
    const [difficulty, setDifficulty] = useState('');
    const [dietLabels, setDietLabels] = useState<string[]>([]);
    const [sortBy, setSortBy] = useState('popular');

    useEffect(() => {
        loadRecipes();
    }, [search, cuisine, difficulty, dietLabels, sortBy]);

    // Reload recipe list when language changes
    useEffect(() => {
        console.log(`🌍 Language changed to ${i18n.language}, reloading recipe list...`);
        loadRecipes();
    }, [i18n.language]);

    // Refetch selected recipe when language changes
    useEffect(() => {
        const handleLanguageChange = async () => {
            if (selectedRecipe && selectedRecipe.id) {
                console.log(`🌍 Language changed to ${i18n.language}, refetching recipe ${selectedRecipe.id}...`);
                try {
                    const updatedRecipe = await api.getCanonicalRecipe(selectedRecipe.id);
                    console.log(`✅ Recipe refetched with ${i18n.language} translation`);
                    console.log(`   Full recipe data:`, updatedRecipe);
                    console.log(`   Ingredients preview:`, updatedRecipe.base_ingredients?.slice(0, 2));
                    console.log(`   Steps preview:`, updatedRecipe.base_steps?.slice(0, 2));
                    console.log(`   Translation language:`, updatedRecipe.translation_language);
                    setSelectedRecipe(updatedRecipe);
                } catch (err) {
                    console.error('❌ Failed to refetch recipe on language change:', err);
                }
            } else {
                console.log(`⚠️ No recipe selected, skipping language change refetch`);
            }
        };

        // Only refetch if we have a recipe open
        if (selectedRecipe?.id) {
            handleLanguageChange();
        }
    }, [i18n.language]); // Only watch language, not recipe ID

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

    const startTranslationPolling = (recipeId: string) => {
        // Clear any existing interval
        if (translationPollInterval) {
            clearInterval(translationPollInterval);
        }

        // Poll every 2 seconds
        const interval = setInterval(async () => {
            try {
                const updatedRecipe = await api.getCanonicalRecipe(recipeId);

                // Check if translation is complete
                if (updatedRecipe.translation_language && !updatedRecipe.translation_status && !updatedRecipe.translation_in_progress) {
                    console.log('[TRANSLATION] Translation complete!');
                    setSelectedRecipe(updatedRecipe);
                    setTranslationLoading(false);
                    clearInterval(interval);
                    setTranslationPollInterval(null);
                }
            } catch (err) {
                console.error('[TRANSLATION] Polling error:', err);
                // Stop polling on error
                setTranslationLoading(false);
                clearInterval(interval);
                setTranslationPollInterval(null);
            }
        }, 2000);

        setTranslationPollInterval(interval);
    };

    // Cleanup polling on unmount
    useEffect(() => {
        return () => {
            if (translationPollInterval) {
                clearInterval(translationPollInterval);
            }
        };
    }, [translationPollInterval]);

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

            // Check if translation is pending or in progress
            if (recipe.translation_status === 'pending' || recipe.translation_in_progress) {
                console.log('[TRANSLATION] Translation pending/in_progress, starting poll...');
                setTranslationLoading(true);
                startTranslationPolling(recipeId);
            }
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
        // Fix: Use canonical_recipe.name instead of recipe_summary.name
        const recipeName = result?.canonical_recipe?.name || result?.recipe_summary?.name || 'Unknown Recipe';
        alert(t('discover.recipeCreatedSuccessfully', { name: recipeName }));
        loadRecipes();
    };

    const toggleDietLabel = (label: string) => {
        setDietLabels(prev =>
            prev.includes(label)
                ? prev.filter(l => l !== label)
                : [...prev, label]
        );
    };

    const handleAISearch = async () => {
        if (!aiQuery.trim()) {
            toast.error(t('discover.aiPleaseEnterRecipe'));
            return;
        }

        setAiLoading(true);
        setShowProgress(true); // Show progress modal

        console.log('[AI SEARCH] Starting API call...');

        try {
            const result = await api.findRecipe(aiQuery);
            console.log('[AI SEARCH] Find recipe result:', result);

            if (result.canonical_recipe) {
                toast.success(t('discover.aiFoundRecipe', { name: result.canonical_recipe.name }));

                // Reload recipes to show the newly added one
                await loadRecipes();

                // Auto-like to save to collection
                const canonicalId = result.canonical_recipe.id;
                if (canonicalId) {
                    try {
                        console.log(`[AI SEARCH] Auto-liking canonical recipe ID: ${canonicalId}`);
                        await api.likeCanonicalRecipe(canonicalId);
                        toast.success(t('discover.aiRecipeAdded'));
                    } catch (likeError: any) {
                        console.error('[AI SEARCH] Failed to auto-like recipe:', likeError);
                    }
                }
            }

            setAiQuery('');

            // Close progress modal (fallback if WebSocket didn't close it)
            setTimeout(() => {
                console.log('[AI SEARCH] Closing progress modal (fallback)');
                setShowProgress(false);
            }, 2000); // Wait 2s to let WebSocket complete message show

        } catch (error: any) {
            console.error('AI search error:', error);

            // Close progress modal on error
            setShowProgress(false);

            // Show suggestions modal instead of just an error
            setFailedQuery(aiQuery);
            setShowSuggestions(true);
            setAiQuery('');
        } finally {
            setAiLoading(false);
        }
    };

    const handleSuggestionClick = async (suggestion: string) => {
        setShowSuggestions(false);
        setAiQuery(suggestion);

        // Perform search with the suggestion
        setAiLoading(true);
        try {
            const result = await api.findRecipe(suggestion);
            console.log('[AI SEARCH] Find recipe result:', result);

            if (result.canonical_recipe) {
                toast.success(t('discover.aiFoundRecipe', { name: result.canonical_recipe.name }));

                // Reload recipes to show the newly added one
                await loadRecipes();

                // Auto-like to save to collection
                const canonicalId = result.canonical_recipe.id;
                if (canonicalId) {
                    try {
                        console.log(`[AI SEARCH] Auto-liking canonical recipe ID: ${canonicalId}`);
                        await api.likeCanonicalRecipe(canonicalId);
                        toast.success(t('discover.aiRecipeAdded'));
                    } catch (likeError: any) {
                        console.error('[AI SEARCH] Failed to auto-like recipe:', likeError);
                    }
                }
            }

            setAiQuery('');
        } catch (error: any) {
            console.error('AI search error:', error);
            toast.error(error.message || t('discover.aiFailedToFind'));
        } finally {
            setAiLoading(false);
        }
    };

    const generateSuggestions = (query: string): string[] => {
        const lower = query.toLowerCase();
        const suggestions: string[] = [];

        // Get suggestions based on current language
        const lang = i18n.language;

        // Multilingual suggestions
        const corrections: Record<string, Record<string, string[]>> = {
            'en': {
                'pasta': ['spaghetti carbonara', 'pasta bolognese', 'penne arrabbiata', 'fettuccine alfredo'],
                'chicken': ['chicken curry', 'grilled chicken', 'chicken soup', 'roasted chicken'],
                'beef': ['beef stew', 'beef stir fry', 'roast beef', 'beef tacos'],
                'fish': ['grilled salmon', 'fish and chips', 'baked cod', 'tuna salad'],
                'soup': ['tomato soup', 'chicken soup', 'vegetable soup', 'lentil soup'],
                'cake': ['chocolate cake', 'vanilla cake', 'carrot cake', 'red velvet cake'],
                'pie': ['apple pie', 'pumpkin pie', 'cherry pie', 'lemon meringue pie'],
                'cookie': ['chocolate chip cookies', 'oatmeal cookies', 'sugar cookies'],
                'pizza': ['margherita pizza', 'pepperoni pizza', 'vegetarian pizza'],
            },
            'ru': {
                'паста': ['спагетти карбонара', 'паста болоньезе', 'пенне аррабьята'],
                'курица': ['куриное карри', 'курица гриль', 'куриный суп', 'жареная курица'],
                'говядина': ['говяжье рагу', 'жареная говядина', 'ростбиф'],
                'рыба': ['лосось на гриле', 'рыба с картошкой', 'тунец'],
                'суп': ['томатный суп', 'куриный суп', 'овощной суп', 'борщ'],
                'торт': ['шоколадный торт', 'наполеон', 'медовик', 'тирамису'],
                'пирог': ['яблочный пирог', 'вишневый пирог', 'черничный пирог'],
                'пицца': ['маргарита', 'пепперони', 'вегетарианская пицца'],
                'салат': ['цезарь', 'греческий салат', 'оливье', 'винегрет'],
                'яблоч': ['яблочный пирог', 'шарлотка', 'яблочный штрудель'],
                'яблок': ['яблочный пирог', 'шарлотка', 'яблочный штрудель'],
            },
            'he': {
                'פסטה': ['ספגטי קרבונרה', 'פסטה בולונז', 'פסטה ארביאטה'],
                'עוף': ['קארי עוף', 'עוף בגריל', 'מרק עוף', 'עוף צלוי'],
                'בשר': ['תבשיל בשר', 'בשר צלי', 'המבורגר'],
                'דג': ['סלמון בגריל', 'דג עם צ\'יפס', 'טונה'],
                'מרק': ['מרק עגבניות', 'מרק עוף', 'מרק ירקות'],
                'עוגה': ['עוגת שוקולד', 'עוגת וניל', 'עוגת גבינה', 'תפוח עץ'],
                'פיצה': ['פיצה מרגריטה', 'פיצה פפרוני', 'פיצה צמחונית'],
                'סלט': ['סלט קיסר', 'סלט יווני', 'סלט ירקות'],
            }
        };

        // Find relevant suggestions for current language
        const langCorrections = corrections[lang as keyof typeof corrections] || corrections['en'];

        for (const [key, values] of Object.entries(langCorrections)) {
            if (lower.includes(key)) {
                suggestions.push(...values);
            }
        }

        // If no specific matches, provide popular recipes in current language
        if (suggestions.length === 0) {
            if (lang === 'ru') {
                suggestions.push('борщ', 'пельмени', 'шарлотка', 'оливье', 'блины');
            } else if (lang === 'he') {
                suggestions.push('שקשוקה', 'חומוס', 'פלאפל', 'שניצל', 'סלט ישראלי');
            } else {
                suggestions.push('spaghetti carbonara', 'chicken curry', 'chocolate cake', 'caesar salad');
            }
        }

        return suggestions.slice(0, 6); // Return max 6 suggestions
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
                                <div className="text-2xl font-bold text-gray-900">
                                    {t(`discover.difficulties.${selectedRecipe.difficulty}`, { defaultValue: selectedRecipe.difficulty })}
                                </div>
                                <div className="text-sm text-gray-600">{t('discover.difficulty')}</div>
                            </div>
                            <div className="text-center p-4 bg-gray-50 rounded-lg">
                                <div className="text-2xl font-bold text-gray-900">{selectedRecipe.total_cooked}</div>
                                <div className="text-sm text-gray-600">{t('discover.timesCooked')}</div>
                            </div>
                        </div>

                        {/* Allergen Warning - Prominent display before ingredients */}
                        {selectedRecipe.allergens && selectedRecipe.allergens.length > 0 && (
                            <div className="mb-8">
                                <AllergenWarning
                                    allergens={selectedRecipe.allergens}
                                    userAllergies={user?.allergies || []}
                                    className="shadow-md"
                                />
                            </div>
                        )}

                        {/* Ingredients & Steps */}
                        {translationLoading ? (
                            <div className="flex flex-col items-center justify-center py-12 space-y-4">
                                <LoadingSpinner />
                                <p className="text-gray-600 text-lg">
                                    {t('discover.translating')}
                                </p>
                                <p className="text-gray-500 text-sm">
                                    {t('discover.translatingDescription')}
                                </p>
                            </div>
                        ) : (
                            <div className="grid md:grid-cols-2 gap-8">{/* Ingredients */}
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
                                                            {(ing.amount || ing.quantity) && ing.unit ? `${ing.amount || ing.quantity} ${ing.unit}` : ''}
                                                        </span>
                                                        {' '}
                                                        <span className="text-gray-900">
                                                            {ing.display_name?.[i18n.language] || ing.display_name?.en || ing.name}
                                                        </span>
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
                                                        {step.step_number || idx + 1}
                                                    </div>
                                                    <div className="flex-1 pt-1">
                                                        <p className="text-gray-900 leading-relaxed">
                                                            {(() => {
                                                                const currentLang = i18n.language;
                                                                const translated = step.text_translations?.[currentLang];
                                                                const text = translated || step.text || step.instruction || step;

                                                                // Convert temperatures based on user preference
                                                                const tempUnit = getUserTemperatureUnit(user);
                                                                const textWithConvertedTemp = convertTemperaturesInText(text, tempUnit);

                                                                return textWithConvertedTemp;
                                                            })()}
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
                        )}
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
            {/* Recipe Generation Progress Modal */}
            <RecipeProgressModal
                isOpen={showProgress}
                onClose={() => setShowProgress(false)}
            />

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

                {/* AI Search Panel */}
                <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
                    <div className="flex items-center gap-3">
                        <Sparkles className="w-6 h-6 text-purple-600" />
                        <input
                            type="text"
                            value={aiQuery}
                            onChange={(e) => setAiQuery(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleAISearch()}
                            placeholder={t('discover.aiSearchPlaceholder')}
                            className="flex-1 px-4 py-3 border border-purple-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                            disabled={aiLoading}
                        />
                        <button
                            onClick={handleAISearch}
                            disabled={aiLoading}
                            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50 font-medium"
                        >
                            {aiLoading ? t('discover.aiSearching') : t('discover.aiFindRecipe')}
                        </button>
                    </div>
                    <p className="text-sm text-purple-700 mt-2">
                        {t('discover.aiSearchDescription')}
                    </p>
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

            {/* Suggestions Modal */}
            {showSuggestions && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg max-w-2xl w-full p-6 shadow-xl">
                        <div className="flex items-start mb-4">
                            <div className="flex-shrink-0 w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
                                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                            </div>
                            <div className="ml-4 flex-1">
                                <h3 className="text-lg font-semibold text-gray-900 mb-1">
                                    {t('discover.suggestions.title')}
                                </h3>
                                <p className="text-sm text-gray-600 mb-4">
                                    {t('discover.suggestions.description', { query: failedQuery })}
                                </p>
                            </div>
                            <button
                                onClick={() => setShowSuggestions(false)}
                                className="text-gray-400 hover:text-gray-600 transition-colors"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="mb-4">
                            <h4 className="text-sm font-medium text-gray-700 mb-3">
                                {t('discover.suggestions.tryThese')}:
                            </h4>
                            <div className="grid grid-cols-2 gap-3">
                                {generateSuggestions(failedQuery).map((suggestion, index) => (
                                    <button
                                        key={index}
                                        onClick={() => handleSuggestionClick(suggestion)}
                                        className="px-4 py-3 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg text-left hover:from-purple-100 hover:to-pink-100 hover:border-purple-300 transition-all duration-200 group"
                                    >
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-gray-800 capitalize">
                                                {suggestion}
                                            </span>
                                            <svg className="w-4 h-4 text-purple-400 group-hover:text-purple-600 group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                            </svg>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="flex items-center justify-between pt-4 border-t">
                            <p className="text-xs text-gray-500">
                                {t('discover.suggestions.hint')}
                            </p>
                            <button
                                onClick={() => setShowSuggestions(false)}
                                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 font-medium transition-colors"
                            >
                                {t('discover.suggestions.close')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CanonicalRecipesPage;


