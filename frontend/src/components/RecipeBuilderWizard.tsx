import React, { useState } from 'react';
import { Edit2, X, Plus, Trash2 } from 'lucide-react';

interface RecipeBuilderWizardProps {
    onStartBuilder: () => Promise<{ session_id: string }>;
    onBuilderStep: (payload: {
        session_id: string;
        step: 'basic_info' | 'ingredients' | 'steps' | 'review' | 'finalize';
        data: any;
    }) => Promise<any>;
    onComplete: (recipe: any) => void;
    onCancel: () => void;
}

interface StructuredIngredient {
    name: string;
    amount?: number;
    unit?: string;
    notes?: string;
}

interface StructuredStep {
    order: number;
    instruction: string;
    time_minutes?: number;
    temperature?: string;
    tips?: string[];
}

/**
 * RecipeBuilderWizard - Multi-step AI-assisted recipe creation
 * 
 * Steps:
 * 1. Basic Info (name, cuisine, servings, difficulty)
 * 2. Ingredients (AI structures quantities & units)
 * 3. Cooking Steps (AI converts description to structured steps)
 * 4. Review & Edit (see and edit final recipe before saving)
 * 5. Finalize (publish or keep private)
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

    // Review step state - editable recipe data
    const [reviewData, setReviewData] = useState<{
        basic_info: any;
        ingredients: StructuredIngredient[];
        steps: StructuredStep[];
        diet_labels: string[];
        estimated_times: any;
    } | null>(null);

    const [editingBasicInfo, setEditingBasicInfo] = useState(false);

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
                        // After steps, fetch compiled recipe for review
                        const reviewResult = await onBuilderStep({
                            session_id: sessionId,
                            step: 'review',
                            data: {}
                        });

                        if (reviewResult.success && reviewResult.data) {
                            setReviewData(reviewResult.data);
                            setCurrentStep(4);
                        }
                    }
                    break;

                case 4: // Review & Edit
                    // Save the edited review data back to session
                    result = await onBuilderStep({
                        session_id: sessionId,
                        step: 'review',
                        data: {
                            save_edits: true,
                            edited_data: reviewData
                        }
                    });
                    if (result.success) {
                        setCurrentStep(5);
                    }
                    break;

                case 5: // Finalize
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

    // Review step editing functions
    const updateReviewIngredient = (index: number, field: keyof StructuredIngredient, value: any) => {
        if (!reviewData) return;
        const updated = [...reviewData.ingredients];
        updated[index] = { ...updated[index], [field]: value };
        setReviewData({ ...reviewData, ingredients: updated });
    };

    const addReviewIngredient = () => {
        if (!reviewData) return;
        setReviewData({
            ...reviewData,
            ingredients: [...reviewData.ingredients, { name: '', amount: 0, unit: '', notes: '' }]
        });
    };

    const removeReviewIngredient = (index: number) => {
        if (!reviewData) return;
        setReviewData({
            ...reviewData,
            ingredients: reviewData.ingredients.filter((_, i) => i !== index)
        });
    };

    const updateReviewStep = (index: number, field: keyof StructuredStep, value: any) => {
        if (!reviewData) return;
        const updated = [...reviewData.steps];
        updated[index] = { ...updated[index], [field]: value };
        setReviewData({ ...reviewData, steps: updated });
    };

    const addReviewStep = () => {
        if (!reviewData) return;
        setReviewData({
            ...reviewData,
            steps: [...reviewData.steps, { order: reviewData.steps.length + 1, instruction: '', time_minutes: 0 }]
        });
    };

    const removeReviewStep = (index: number) => {
        if (!reviewData) return;
        const updated = reviewData.steps.filter((_, i) => i !== index);
        // Reorder steps
        updated.forEach((step, i) => step.order = i + 1);
        setReviewData({ ...reviewData, steps: updated });
    };

    const updateBasicInfoField = (field: string, value: any) => {
        if (!reviewData) return;
        setReviewData({
            ...reviewData,
            basic_info: { ...reviewData.basic_info, [field]: value }
        });
    };

    return (
        <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-lg p-8">
            {/* Progress Bar */}
            <div className="mb-8">
                <div className="flex justify-between mb-2">
                    {['Basic Info', 'Ingredients', 'Steps', 'Review & Edit', 'Finalize'].map((label, index) => (
                        <div
                            key={label}
                            className={`text-xs sm:text-sm font-medium ${index + 1 === currentStep
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
                        style={{ width: `${(currentStep / 5) * 100}%` }}
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

                {currentStep === 4 && reviewData && (
                    <div className="space-y-6">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-2xl font-bold text-gray-900">
                                Step 4: Review & Edit Your Recipe
                            </h2>
                            <div className="text-sm text-gray-600">
                                ✏️ Click any field to edit
                            </div>
                        </div>

                        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <p className="text-blue-800 text-sm">
                                🎨 <strong>Review your recipe</strong> - AI has structured everything for you. Edit any field before finalizing!
                            </p>
                        </div>

                        {/* Basic Info Section */}
                        <div className="border rounded-lg p-6 bg-gray-50">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-bold text-gray-900">📋 Basic Information</h3>
                                <button
                                    onClick={() => setEditingBasicInfo(!editingBasicInfo)}
                                    className="flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition text-sm"
                                >
                                    <Edit2 className="w-4 h-4" />
                                    {editingBasicInfo ? 'Done' : 'Edit'}
                                </button>
                            </div>

                            {editingBasicInfo ? (
                                <div className="space-y-3">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                                        <input
                                            type="text"
                                            value={reviewData.basic_info.name}
                                            onChange={(e) => updateBasicInfoField('name', e.target.value)}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Cuisine</label>
                                            <input
                                                type="text"
                                                value={reviewData.basic_info.cuisine || ''}
                                                onChange={(e) => updateBasicInfoField('cuisine', e.target.value)}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Difficulty</label>
                                            <select
                                                value={reviewData.basic_info.difficulty}
                                                onChange={(e) => updateBasicInfoField('difficulty', e.target.value)}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                            >
                                                <option value="beginner">Beginner</option>
                                                <option value="intermediate">Intermediate</option>
                                                <option value="advanced">Advanced</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Servings</label>
                                        <input
                                            type="number"
                                            value={reviewData.basic_info.servings}
                                            onChange={(e) => updateBasicInfoField('servings', parseInt(e.target.value))}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                            min={1}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                                        <textarea
                                            value={reviewData.basic_info.description || ''}
                                            onChange={(e) => updateBasicInfoField('description', e.target.value)}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                            rows={3}
                                        />
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-2 text-sm">
                                    <p><strong>Name:</strong> {reviewData.basic_info.name}</p>
                                    <p><strong>Cuisine:</strong> {reviewData.basic_info.cuisine || 'Not specified'}</p>
                                    <p><strong>Difficulty:</strong> {reviewData.basic_info.difficulty}</p>
                                    <p><strong>Servings:</strong> {reviewData.basic_info.servings}</p>
                                    {reviewData.basic_info.description && (
                                        <p><strong>Description:</strong> {reviewData.basic_info.description}</p>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Ingredients Section */}
                        <div className="border rounded-lg p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-bold text-gray-900">🥕 Ingredients ({reviewData.ingredients.length})</h3>
                                <button
                                    onClick={addReviewIngredient}
                                    className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition text-sm"
                                >
                                    <Plus className="w-4 h-4" />
                                    Add
                                </button>
                            </div>

                            <div className="space-y-2">
                                {reviewData.ingredients.map((ing, index) => (
                                    <div key={index} className="flex gap-2 items-start p-3 bg-gray-50 rounded-lg">
                                        <div className="flex-1 grid grid-cols-4 gap-2">
                                            <input
                                                type="number"
                                                value={ing.amount || ''}
                                                onChange={(e) => updateReviewIngredient(index, 'amount', parseFloat(e.target.value))}
                                                placeholder="Amt"
                                                className="px-2 py-1 border border-gray-300 rounded text-sm"
                                            />
                                            <input
                                                type="text"
                                                value={ing.unit || ''}
                                                onChange={(e) => updateReviewIngredient(index, 'unit', e.target.value)}
                                                placeholder="Unit"
                                                className="px-2 py-1 border border-gray-300 rounded text-sm"
                                            />
                                            <input
                                                type="text"
                                                value={ing.name}
                                                onChange={(e) => updateReviewIngredient(index, 'name', e.target.value)}
                                                placeholder="Ingredient"
                                                className="col-span-2 px-2 py-1 border border-gray-300 rounded text-sm"
                                            />
                                        </div>
                                        <button
                                            onClick={() => removeReviewIngredient(index)}
                                            className="p-2 text-red-600 hover:bg-red-50 rounded transition"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Steps Section */}
                        <div className="border rounded-lg p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-bold text-gray-900">👨‍🍳 Cooking Steps ({reviewData.steps.length})</h3>
                                <button
                                    onClick={addReviewStep}
                                    className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition text-sm"
                                >
                                    <Plus className="w-4 h-4" />
                                    Add Step
                                </button>
                            </div>

                            <div className="space-y-3">
                                {reviewData.steps.map((step, index) => (
                                    <div key={index} className="flex gap-3 items-start p-3 bg-gray-50 rounded-lg">
                                        <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                                            {step.order}
                                        </div>
                                        <div className="flex-1 space-y-2">
                                            <textarea
                                                value={step.instruction}
                                                onChange={(e) => updateReviewStep(index, 'instruction', e.target.value)}
                                                placeholder="Step instruction..."
                                                className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                                                rows={2}
                                            />
                                            <div className="flex gap-2">
                                                <input
                                                    type="number"
                                                    value={step.time_minutes || ''}
                                                    onChange={(e) => updateReviewStep(index, 'time_minutes', parseInt(e.target.value) || null)}
                                                    placeholder="Time (min)"
                                                    className="w-24 px-2 py-1 border border-gray-300 rounded text-sm"
                                                />
                                                <input
                                                    type="text"
                                                    value={step.temperature || ''}
                                                    onChange={(e) => updateReviewStep(index, 'temperature', e.target.value)}
                                                    placeholder="Temp (optional)"
                                                    className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                                                />
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => removeReviewStep(index)}
                                            className="p-2 text-red-600 hover:bg-red-50 rounded transition"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Time Estimates */}
                        {reviewData.estimated_times && (
                            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                                <h4 className="font-semibold text-yellow-900 mb-2">⏱️ Estimated Times</h4>
                                <div className="grid grid-cols-3 gap-4 text-sm text-yellow-800">
                                    <div>
                                        <strong>Prep:</strong> {reviewData.estimated_times.prep_time || 0} min
                                    </div>
                                    <div>
                                        <strong>Cook:</strong> {reviewData.estimated_times.cook_time || 0} min
                                    </div>
                                    <div>
                                        <strong>Total:</strong> {reviewData.estimated_times.total_time || 0} min
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Diet Labels */}
                        {reviewData.diet_labels && reviewData.diet_labels.length > 0 && (
                            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                                <h4 className="font-semibold text-green-900 mb-2">🌱 Auto-Detected Labels</h4>
                                <div className="flex flex-wrap gap-2">
                                    {reviewData.diet_labels.map((label, index) => (
                                        <span key={index} className="px-3 py-1 bg-green-200 text-green-800 rounded-full text-sm">
                                            {label}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {currentStep === 5 && (
                    <div className="space-y-4">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                            Step 5: Finalize Recipe
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
                                Make this recipe public (visible to all users on Discover page)
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
                            <h4 className="font-semibold text-green-900 mb-2">🎉 Ready to save!</h4>
                            <p className="text-green-800 text-sm">
                                Click "Create Recipe" to save your recipe. It will be added to your collection and {finalizeOptions.is_public ? 'published to the Discover page' : 'kept private'}.
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
                    ) : currentStep === 5 ? (
                        'Create Recipe'
                    ) : currentStep === 4 ? (
                        'Confirm & Continue'
                    ) : (
                        'Next'
                    )}
                </button>
            </div>
        </div>
    );
};

export default RecipeBuilderWizard;
