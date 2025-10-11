import React, { useState } from 'react';

interface RecipeBuilderWizardProps {
    onStartBuilder: () => Promise<{ session_id: string }>;
    onBuilderStep: (payload: {
        session_id: string;
        step: 'basic_info' | 'ingredients' | 'steps' | 'finalize';
        data: any;
    }) => Promise<any>;
    onComplete: (recipe: any) => void;
    onCancel: () => void;
}

/**
 * RecipeBuilderWizard - Multi-step AI-assisted recipe creation
 * 
 * Steps:
 * 1. Basic Info (name, cuisine, servings, difficulty)
 * 2. Ingredients (AI structures quantities & units)
 * 3. Cooking Steps (AI converts description to structured steps)
 * 4. Finalize (publish or keep private)
 */
const RecipeBuilderWizard: React.FC<RecipeBuilderWizardProps> = ({
    onStartBuilder,
    onBuilderStep,
    onComplete,
    onCancel
}) => {
    const [sessionId, setSessionId] = useState<string>('');
    const [currentStep, setCurrentStep] = useState<number>(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string>('');
    const [aiSuggestions, setAiSuggestions] = useState<string[]>([]);

    // Form state for each step
    const [basicInfo, setBasicInfo] = useState({
        name: '',
        cuisine: '',
        servings: 4,
        difficulty: 'intermediate',
        description: ''
    });

    const [ingredients, setIngredients] = useState<string[]>(['']);
    const [stepsDescription, setStepsDescription] = useState('');
    const [finalizeOptions, setFinalizeOptions] = useState({
        is_public: true,
        description: '',
        tags: [] as string[]
    });

    // Initialize session
    React.useEffect(() => {
        const initSession = async () => {
            try {
                const result = await onStartBuilder();
                setSessionId(result.session_id);
            } catch (err: any) {
                setError(err.message || 'Failed to start builder session');
            }
        };
        initSession();
    }, []);

    const handleNext = async () => {
        setLoading(true);
        setError('');

        try {
            let result;

            switch (currentStep) {
                case 1: // Basic Info
                    result = await onBuilderStep({
                        session_id: sessionId,
                        step: 'basic_info',
                        data: basicInfo
                    });
                    if (result.success) {
                        setAiSuggestions(result.ai_suggestions || []);
                        setCurrentStep(2);
                    }
                    break;

                case 2: // Ingredients
                    result = await onBuilderStep({
                        session_id: sessionId,
                        step: 'ingredients',
                        data: {
                            ingredients: ingredients.filter(ing => ing.trim())
                        }
                    });
                    if (result.success) {
                        setCurrentStep(3);
                    }
                    break;

                case 3: // Steps
                    result = await onBuilderStep({
                        session_id: sessionId,
                        step: 'steps',
                        data: {
                            steps_description: stepsDescription
                        }
                    });
                    if (result.success) {
                        setCurrentStep(4);
                    }
                    break;

                case 4: // Finalize
                    result = await onBuilderStep({
                        session_id: sessionId,
                        step: 'finalize',
                        data: finalizeOptions
                    });
                    if (result.success) {
                        onComplete(result);
                    }
                    break;
            }

            if (result && !result.success) {
                setError(result.error || 'Step failed');
            }
        } catch (err: any) {
            setError(err.message || 'Failed to process step');
        } finally {
            setLoading(false);
        }
    };

    const addIngredient = () => {
        setIngredients([...ingredients, '']);
    };

    const removeIngredient = (index: number) => {
        setIngredients(ingredients.filter((_, i) => i !== index));
    };

    const updateIngredient = (index: number, value: string) => {
        const updated = [...ingredients];
        updated[index] = value;
        setIngredients(updated);
    };

    return (
        <div className="max-w-3xl mx-auto bg-white rounded-xl shadow-lg p-8">
            {/* Progress Bar */}
            <div className="mb-8">
                <div className="flex justify-between mb-2">
                    {['Basic Info', 'Ingredients', 'Steps', 'Finalize'].map((label, index) => (
                        <div
                            key={label}
                            className={`text-sm font-medium ${index + 1 === currentStep
                                ? 'text-blue-600'
                                : index + 1 < currentStep
                                    ? 'text-green-600'
                                    : 'text-gray-400'
                                }`}
                        >
                            {label}
                        </div>
                    ))}
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${(currentStep / 4) * 100}%` }}
                    />
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                    {error}
                </div>
            )}

            {/* AI Suggestions */}
            {aiSuggestions.length > 0 && (
                <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h4 className="font-semibold text-blue-900 mb-2">💡 AI Suggestions:</h4>
                    <ul className="list-disc list-inside space-y-1 text-blue-800 text-sm">
                        {aiSuggestions.map((suggestion, index) => (
                            <li key={index}>{suggestion}</li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Step Content */}
            <div className="mb-8">
                {currentStep === 1 && (
                    <div className="space-y-4">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                            Step 1: Basic Information
                        </h2>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Recipe Name *
                            </label>
                            <input
                                type="text"
                                value={basicInfo.name}
                                onChange={(e) => setBasicInfo({ ...basicInfo, name: e.target.value })}
                                placeholder="e.g., Spaghetti Carbonara"
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Cuisine (optional)
                            </label>
                            <input
                                type="text"
                                value={basicInfo.cuisine}
                                onChange={(e) => setBasicInfo({ ...basicInfo, cuisine: e.target.value })}
                                placeholder="e.g., Italian, Mexican, Japanese"
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Servings
                                </label>
                                <input
                                    type="number"
                                    value={basicInfo.servings}
                                    onChange={(e) => setBasicInfo({ ...basicInfo, servings: parseInt(e.target.value) })}
                                    min={1}
                                    max={20}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Difficulty
                                </label>
                                <select
                                    value={basicInfo.difficulty}
                                    onChange={(e) => setBasicInfo({ ...basicInfo, difficulty: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="beginner">Beginner</option>
                                    <option value="intermediate">Intermediate</option>
                                    <option value="advanced">Advanced</option>
                                </select>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Description (optional)
                            </label>
                            <textarea
                                value={basicInfo.description}
                                onChange={(e) => setBasicInfo({ ...basicInfo, description: e.target.value })}
                                placeholder="Brief description of your recipe"
                                rows={3}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>
                    </div>
                )}

                {currentStep === 2 && (
                    <div className="space-y-4">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                            Step 2: Ingredients
                        </h2>
                        <p className="text-gray-600 mb-4">
                            Add ingredients one per line. AI will help structure them with proper quantities.
                        </p>

                        <div className="space-y-2">
                            {ingredients.map((ingredient, index) => (
                                <div key={index} className="flex gap-2">
                                    <input
                                        type="text"
                                        value={ingredient}
                                        onChange={(e) => updateIngredient(index, e.target.value)}
                                        placeholder="e.g., 2 cups flour, 3 eggs, 1 tsp salt"
                                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                    {ingredients.length > 1 && (
                                        <button
                                            onClick={() => removeIngredient(index)}
                                            className="px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-colors"
                                        >
                                            ✕
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>

                        <button
                            onClick={addIngredient}
                            className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                        >
                            + Add Ingredient
                        </button>
                    </div>
                )}

                {currentStep === 3 && (
                    <div className="space-y-4">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                            Step 3: Cooking Steps
                        </h2>
                        <p className="text-gray-600 mb-4">
                            Describe how to make this recipe. AI will structure it into clear steps.
                        </p>

                        <textarea
                            value={stepsDescription}
                            onChange={(e) => setStepsDescription(e.target.value)}
                            placeholder="Describe the cooking process in your own words. For example: First, boil water and cook pasta. While pasta cooks, fry bacon until crispy..."
                            rows={10}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            required
                        />
                    </div>
                )}

                {currentStep === 4 && (
                    <div className="space-y-4">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                            Step 4: Finalize Recipe
                        </h2>

                        <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                            <input
                                type="checkbox"
                                id="is_public"
                                checked={finalizeOptions.is_public}
                                onChange={(e) => setFinalizeOptions({ ...finalizeOptions, is_public: e.target.checked })}
                                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                            />
                            <label htmlFor="is_public" className="text-sm font-medium text-gray-700">
                                Make this recipe public (visible to all users)
                            </label>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Additional Description (optional)
                            </label>
                            <textarea
                                value={finalizeOptions.description}
                                onChange={(e) => setFinalizeOptions({ ...finalizeOptions, description: e.target.value })}
                                placeholder="Add any extra notes, tips, or story about this recipe"
                                rows={4}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>

                        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                            <h4 className="font-semibold text-green-900 mb-2">🎉 Almost done!</h4>
                            <p className="text-green-800 text-sm">
                                Click "Create Recipe" to save your recipe. AI will automatically detect diet labels and create a beautiful recipe card.
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {/* Navigation Buttons */}
            <div className="flex justify-between">
                <button
                    onClick={currentStep === 1 ? onCancel : () => setCurrentStep(currentStep - 1)}
                    className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                    disabled={loading}
                >
                    {currentStep === 1 ? 'Cancel' : 'Back'}
                </button>

                <button
                    onClick={handleNext}
                    disabled={loading || (currentStep === 1 && !basicInfo.name.trim())}
                    className={`px-6 py-2 rounded-lg font-medium transition-colors ${loading || (currentStep === 1 && !basicInfo.name.trim())
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                        }`}
                >
                    {loading ? (
                        <span className="flex items-center gap-2">
                            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                            Processing...
                        </span>
                    ) : currentStep === 4 ? (
                        'Create Recipe'
                    ) : (
                        'Next'
                    )}
                </button>
            </div>
        </div>
    );
};

export default RecipeBuilderWizard;

