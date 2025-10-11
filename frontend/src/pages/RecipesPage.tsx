import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { RecipeFinder } from '../components/RecipeFinder';
import toast from 'react-hot-toast';

const RecipesPage: React.FC = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [shoppingListId, setShoppingListId] = useState<string | undefined>();

    useEffect(() => {
        // Get shopping list ID from URL params if present
        const listId = searchParams.get('listId');
        if (listId) {
            setShoppingListId(listId);
        }
    }, [searchParams]);

    const handleRecipeFound = (recipe: any) => {
        console.log('Recipe found:', recipe);
        toast.success(`Found recipe: ${recipe.name}!`);

        // Optional: Navigate to recipe details or shopping list
        // navigate(`/recipes/${recipe.id}`);
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <h1 className="text-3xl font-bold text-gray-900">
                            AI Recipe Finder
                        </h1>
                        <button
                            onClick={() => navigate(-1)}
                            className="text-indigo-600 hover:text-indigo-700 font-medium"
                        >
                            ← Back
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="py-8">
                <RecipeFinder
                    shoppingListId={shoppingListId}
                    onRecipeFound={handleRecipeFound}
                />
            </main>

            {/* Info Section */}
            <section className="max-w-4xl mx-auto px-6 py-8">
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6">
                    <h3 className="text-lg font-bold text-indigo-900 mb-3">
                        How it works
                    </h3>
                    <ol className="space-y-2 text-sm text-indigo-800">
                        <li className="flex gap-2">
                            <span className="font-bold">1.</span>
                            <span>Describe what you want to cook in natural language</span>
                        </li>
                        <li className="flex gap-2">
                            <span className="font-bold">2.</span>
                            <span>Our AI searches the web for the best recipes</span>
                        </li>
                        <li className="flex gap-2">
                            <span className="font-bold">3.</span>
                            <span>Get a detailed recipe with ingredients and steps</span>
                        </li>
                        <li className="flex gap-2">
                            <span className="font-bold">4.</span>
                            <span>Ingredients are automatically added to your shopping list!</span>
                        </li>
                    </ol>
                </div>
            </section>
        </div>
    );
};

export default RecipesPage;




