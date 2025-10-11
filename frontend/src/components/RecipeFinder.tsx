import React, { useState } from 'react';
import {
    Search,
    ChefHat,
    Loader2,
    ShoppingCart,
    CheckCircle,
    AlertCircle,
    Clock,
    Users
} from 'lucide-react';

interface RecipeFinderProps {
    shoppingListId?: string;
    onRecipeFound?: (recipe: any) => void;
}

interface RecipeResult {
    success: boolean;
    message: string;
    recipe: {
        id: string;
        name: string;
        description: string;
        prep_time_minutes: number;
        cook_time_minutes: number;
        servings: number;
        difficulty: string;
        ingredients: Array<{
            name: string;
            human_amount: string;
            allergens: string[];
        }>;
        steps: Array<{
            step_id: string;
            human_text: string;
        }>;
        version: number;
        is_saved: boolean;
    };
    created: boolean;
    version: number;
    ingredients_added: number;
    shopping_list_items: Array<{
        id: string;
        name: string;
        quantity: number;
        unit: string;
    }>;
}

export const RecipeFinder: React.FC<RecipeFinderProps> = ({
    shoppingListId,
    onRecipeFound
}) => {
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<RecipeResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [addToList, setAddToList] = useState(true);

    const handleSearch = async () => {
        if (!query.trim()) {
            setError('Please describe what you want to cook');
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const token = localStorage.getItem('accessToken');

            const response = await fetch('/api/recipes/recipes/find_recipe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    query: query,
                    shopping_list_id: shoppingListId,
                    add_to_shopping_list: addToList && !!shoppingListId
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to find recipe');
            }

            const data: RecipeResult = await response.json();
            setResult(data);

            if (onRecipeFound) {
                onRecipeFound(data.recipe);
            }
        } catch (err: any) {
            setError(err.message || 'Failed to find recipe');
            console.error('Recipe search error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSearch();
        }
    };

    return (
        <div className="w-full max-w-4xl mx-auto p-6 space-y-6">
            {/* Search Input */}
            <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-start gap-3 mb-4">
                    <ChefHat className="w-8 h-8 text-indigo-600 mt-1" />
                    <div className="flex-1">
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">
                            What do you want to cook?
                        </h2>
                        <p className="text-sm text-gray-600">
                            Describe any dish and I'll find a recipe for you
                        </p>
                    </div>
                </div>

                <div className="space-y-4">
                    <div className="relative">
                        <textarea
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="E.g., 'Italian pasta carbonara', 'healthy chicken salad', 'chocolate cake for beginners'..."
                            className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                            rows={3}
                            disabled={loading}
                        />
                        <Search className="absolute right-4 top-4 w-5 h-5 text-gray-400" />
                    </div>

                    {shoppingListId && (
                        <label className="flex items-center gap-2 text-sm text-gray-700">
                            <input
                                type="checkbox"
                                checked={addToList}
                                onChange={(e) => setAddToList(e.target.checked)}
                                className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
                            />
                            <ShoppingCart className="w-4 h-4" />
                            Add ingredients to shopping list automatically
                        </label>
                    )}

                    <button
                        onClick={handleSearch}
                        disabled={loading || !query.trim()}
                        className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Searching for recipe...
                            </>
                        ) : (
                            <>
                                <Search className="w-5 h-5" />
                                Find Recipe
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                    <div>
                        <h3 className="font-semibold text-red-900">Error</h3>
                        <p className="text-sm text-red-700">{error}</p>
                    </div>
                </div>
            )}

            {/* Success Result */}
            {result && (
                <div className="bg-white rounded-lg shadow-md overflow-hidden">
                    {/* Header */}
                    <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-4 text-white">
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                    <CheckCircle className="w-6 h-6" />
                                    <span className="text-sm font-medium">
                                        {result.created ? 'New Recipe Found' : 'Existing Recipe'}
                                    </span>
                                    {result.version > 1 && (
                                        <span className="bg-white/20 px-2 py-0.5 rounded text-xs">
                                            v{result.version}
                                        </span>
                                    )}
                                </div>
                                <h2 className="text-2xl font-bold">{result.recipe.name}</h2>
                                {result.recipe.description && (
                                    <p className="text-indigo-100 mt-2">{result.recipe.description}</p>
                                )}
                            </div>
                        </div>

                        {/* Recipe Meta */}
                        <div className="flex flex-wrap gap-4 mt-4 text-sm">
                            {result.recipe.prep_time_minutes && (
                                <div className="flex items-center gap-1.5">
                                    <Clock className="w-4 h-4" />
                                    <span>Prep: {result.recipe.prep_time_minutes}min</span>
                                </div>
                            )}
                            {result.recipe.cook_time_minutes && (
                                <div className="flex items-center gap-1.5">
                                    <Clock className="w-4 h-4" />
                                    <span>Cook: {result.recipe.cook_time_minutes}min</span>
                                </div>
                            )}
                            <div className="flex items-center gap-1.5">
                                <Users className="w-4 h-4" />
                                <span>{result.recipe.servings} servings</span>
                            </div>
                            <div className="bg-white/20 px-2 py-0.5 rounded capitalize">
                                {result.recipe.difficulty}
                            </div>
                        </div>
                    </div>

                    {/* Shopping List Notification */}
                    {result.ingredients_added > 0 && (
                        <div className="bg-green-50 border-b border-green-200 px-6 py-3 flex items-center gap-3">
                            <ShoppingCart className="w-5 h-5 text-green-600" />
                            <span className="text-sm text-green-800">
                                <strong>{result.ingredients_added} ingredients</strong> added to your shopping list
                            </span>
                        </div>
                    )}

                    {/* Content */}
                    <div className="p-6 space-y-6">
                        {/* Ingredients */}
                        <div>
                            <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
                                <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 font-bold">
                                    {result.recipe.ingredients.length}
                                </div>
                                Ingredients
                            </h3>
                            <ul className="space-y-2">
                                {result.recipe.ingredients.map((ingredient, index) => (
                                    <li
                                        key={index}
                                        className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                                    >
                                        <div className="w-2 h-2 bg-indigo-600 rounded-full mt-2" />
                                        <div className="flex-1">
                                            <span className="font-medium text-gray-900">
                                                {ingredient.name}
                                            </span>
                                            {ingredient.human_amount && (
                                                <span className="text-gray-600 ml-2">
                                                    — {ingredient.human_amount}
                                                </span>
                                            )}
                                            {ingredient.allergens && ingredient.allergens.length > 0 && (
                                                <div className="flex flex-wrap gap-1 mt-1">
                                                    {ingredient.allergens.map((allergen, i) => (
                                                        <span
                                                            key={i}
                                                            className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded"
                                                        >
                                                            {allergen}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* Steps */}
                        <div>
                            <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
                                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 font-bold">
                                    {result.recipe.steps.length}
                                </div>
                                Instructions
                            </h3>
                            <ol className="space-y-4">
                                {result.recipe.steps.map((step, index) => (
                                    <li
                                        key={step.step_id}
                                        className="flex gap-4"
                                    >
                                        <div className="flex-shrink-0 w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold">
                                            {index + 1}
                                        </div>
                                        <p className="flex-1 text-gray-700 pt-1">
                                            {step.human_text}
                                        </p>
                                    </li>
                                ))}
                            </ol>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default RecipeFinder;




