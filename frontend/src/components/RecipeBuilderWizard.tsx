import React, { useState } from 'react';
import { Edit2, X, Plus, Trash2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import i18n from '../i18n';

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
    temperature?: string | { value: number; unit: string };
    tips?: string[];
    text_translations?: {
        en?: string;
        ru?: string;
        he?: string;
    };
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
    const { t, i18n: i18nHook } = useTranslation();
    const currentLang = i18nHook.language || i18n.language || 'en';
    const [sessionId, setSessionId] = useState<string>('');
    const [currentStep, setCurrentStep] = useState<number>(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string>('');
    const [aiSuggestions, setAiSuggestions] = useState<string[]>([]);

    // Duplicate detection state
    const [showDuplicateModal, setShowDuplicateModal] = useState(false);
    const [duplicateRecipe, setDuplicateRecipe] = useState<any>(null);

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
                setError(err.message || t('recipeBuilder.errors.failedToStart'));
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
                case 1: // Basic Info - CHECK FOR DUPLICATES FIRST
                    result = await onBuilderStep({
                        session_id: sessionId,
                        step: 'basic_info',
                        data: basicInfo
                    });

                    // Check if duplicate detected in Step 1
                    if (result && result.is_duplicate) {
                        console.log('[BUILDER] Duplicate detected in Step 1:', result.existing_recipe);
                        setDuplicateRecipe(result.existing_recipe);
                        setShowDuplicateModal(true);
                        setLoading(false);
                        return; // Don't proceed, wait for user choice
                    }

                    if (result.success) {
                        setAiSuggestions(result.ai_suggestions || []);
                        setCurrentStep(2);
                    }
                    break;

                case 2: // Ingredients
                    // Validate at least one ingredient before sending
                    const validIngredients = ingredients.filter(ing => ing.trim());
                    if (validIngredients.length === 0) {
                        setError(t('recipeBuilder.step2.error', { defaultValue: 'Please add at least one ingredient' }));
                        setLoading(false);
                        return;
                    }

                    result = await onBuilderStep({
                        session_id: sessionId,
                        step: 'ingredients',
                        data: {
                            ingredients: validIngredients
                        }
                    });
                    if (result.success) {
                        setCurrentStep(3);
                    }
                    break;

                case 3: // Steps
                    // Validate steps description before sending
                    if (!stepsDescription.trim()) {
                        setError(t('recipeBuilder.step3.error', { defaultValue: 'Please describe the cooking steps' }));
                        setLoading(false);
                        return;
                    }

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

                    // Check if duplicate detected
                    if (result && result.is_duplicate) {
                        console.log('[BUILDER] Duplicate detected:', result.existing_recipe);
                        setDuplicateRecipe(result.existing_recipe);
                        setShowDuplicateModal(true);
                        setLoading(false);
                        return; // Don't complete yet, wait for user choice
                    }

                    if (result.success) {
                        onComplete(result);
                    }
                    break;
            }

            // Check for duplicate BEFORE checking success
            // (duplicate returns success:false but is_duplicate:true)
            if (result && result.is_duplicate) {
                console.log('[BUILDER] Duplicate detected:', result.existing_recipe);
                setDuplicateRecipe(result.existing_recipe);
                setShowDuplicateModal(true);
                setError(''); // Clear any error message
                setLoading(false);
                return; // Don't show error, show modal instead
            }

            if (result && !result.success) {
                setError(result.error || t('recipeBuilder.errors.stepFailed'));
            }
        } catch (err: any) {
            setError(err.message || t('recipeBuilder.errors.stepFailed'));
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

    // Duplicate modal handlers
    const handleViewExisting = () => {
        if (duplicateRecipe) {
            // Navigate to existing recipe
            window.location.href = `/discover?recipe=${duplicateRecipe.id}`;
        }
    };

    const handleCreateFork = async () => {
        setShowDuplicateModal(false);
        setLoading(true);

        try {
            // If we're in Step 1, proceed with skip_duplicate_check
            // If we're in Step 5, call finalize with fork option
            if (currentStep === 1) {
                // Update basic_info step with skip_duplicate_check flag
                const result = await onBuilderStep({
                    session_id: sessionId,
                    step: 'basic_info',
                    data: {
                        ...basicInfo,
                        skip_duplicate_check: true,
                        create_fork: true  // Signal to create fork at the end
                    }
                });

                if (result.success) {
                    setAiSuggestions(result.ai_suggestions || []);
                    setCurrentStep(2); // Proceed to next step
                } else {
                    setError(result.error || t('recipeBuilder.errors.stepFailed'));
                }
            } else {
                // Step 5 finalize
                const result = await onBuilderStep({
                    session_id: sessionId,
                    step: 'finalize',
                    data: {
                        ...finalizeOptions,
                        skip_duplicate_check: true,
                        is_public: false  // Forks are private by default
                    }
                });

                if (result.success) {
                    onComplete(result);
                } else {
                    setError(result.error || t('recipeBuilder.errors.stepFailed'));
                }
            }
        } catch (err: any) {
            setError(err.message || t('recipeBuilder.errors.stepFailed'));
        } finally {
            setLoading(false);
        }
    };

    const handleCreateNew = async () => {
        setShowDuplicateModal(false);
        setLoading(true);

        try {
            // If we're in Step 1, proceed with skip_duplicate_check
            // If we're in Step 5, call finalize with new version
            if (currentStep === 1) {
                // Update basic_info step with skip_duplicate_check flag
                const result = await onBuilderStep({
                    session_id: sessionId,
                    step: 'basic_info',
                    data: {
                        ...basicInfo,
                        skip_duplicate_check: true
                    }
                });

                if (result.success) {
                    setAiSuggestions(result.ai_suggestions || []);
                    setCurrentStep(2); // Proceed to next step
                } else {
                    setError(result.error || t('recipeBuilder.errors.stepFailed'));
                }
            } else {
                // Step 5 finalize
                const result = await onBuilderStep({
                    session_id: sessionId,
                    step: 'finalize',
                    data: {
                        ...finalizeOptions,
                        skip_duplicate_check: true
                    }
                });

                if (result.success) {
                    onComplete(result);
                } else {
                    setError(result.error || t('recipeBuilder.errors.stepFailed'));
                }
            }
        } catch (err: any) {
            setError(err.message || t('recipeBuilder.errors.stepFailed'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-lg p-8">
            {/* Progress Bar */}
            <div className="mb-8">
                <div className="flex justify-between mb-2">
                    {[
                        t('recipeBuilder.progressSteps.basicInfo'),
                        t('recipeBuilder.progressSteps.ingredients'),
                        t('recipeBuilder.progressSteps.steps'),
                        t('recipeBuilder.progressSteps.review'),
                        t('recipeBuilder.progressSteps.finalize')
                    ].map((label, index) => (
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
                    <h4 className="font-semibold text-blue-900 mb-2">
                        💡 {t('recipeBuilder.aiSuggestionsTitle', { defaultValue: 'AI Suggestions' })}
                    </h4>
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
                            {t('recipeBuilder.step1.title')}
                        </h2>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                {t('recipeBuilder.step1.recipeNameRequired')}
                            </label>
                            <input
                                type="text"
                                value={basicInfo.name}
                                onChange={(e) => setBasicInfo({ ...basicInfo, name: e.target.value })}
                                placeholder={t('recipeBuilder.step1.recipeNamePlaceholder')}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                {t('recipeBuilder.step1.cuisine')}
                            </label>
                            <input
                                type="text"
                                value={basicInfo.cuisine}
                                onChange={(e) => setBasicInfo({ ...basicInfo, cuisine: e.target.value })}
                                placeholder={t('recipeBuilder.step1.cuisinePlaceholder')}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    {t('recipeBuilder.step1.servings')}
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
                                    {t('recipeBuilder.step1.difficulty')}
                                </label>
                                <select
                                    value={basicInfo.difficulty}
                                    onChange={(e) => setBasicInfo({ ...basicInfo, difficulty: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="beginner">{t('recipeBuilder.step1.difficultyBeginner')}</option>
                                    <option value="intermediate">{t('recipeBuilder.step1.difficultyIntermediate')}</option>
                                    <option value="advanced">{t('recipeBuilder.step1.difficultyAdvanced')}</option>
                                </select>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                {t('recipeBuilder.step1.description')}
                            </label>
                            <textarea
                                value={basicInfo.description}
                                onChange={(e) => setBasicInfo({ ...basicInfo, description: e.target.value })}
                                placeholder={t('recipeBuilder.step1.descriptionPlaceholder')}
                                rows={3}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>
                    </div>
                )}

                {currentStep === 2 && (
                    <div className="space-y-4">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                            {t('recipeBuilder.step2.title')}
                        </h2>
                        <p className="text-gray-600 mb-4">
                            {t('recipeBuilder.step2.description')}
                        </p>

                        <div className="space-y-2">
                            {ingredients.map((ingredient, index) => (
                                <div key={index} className="flex gap-2">
                                    <input
                                        type="text"
                                        value={ingredient}
                                        onChange={(e) => updateIngredient(index, e.target.value)}
                                        placeholder={t('recipeBuilder.step2.ingredientPlaceholder')}
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
                            {t('recipeBuilder.step2.addIngredient')}
                        </button>
                    </div>
                )}

                {currentStep === 3 && (
                    <div className="space-y-4">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                            {t('recipeBuilder.step3.title')}
                        </h2>
                        <p className="text-gray-600 mb-4">
                            {t('recipeBuilder.step3.description')}
                        </p>

                        <textarea
                            value={stepsDescription}
                            onChange={(e) => setStepsDescription(e.target.value)}
                            placeholder={t('recipeBuilder.step3.stepsPlaceholder')}
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
                                {t('recipeBuilder.step4.title')}
                            </h2>
                            <div className="text-sm text-gray-600">
                                {t('recipeBuilder.step4.editHint')}
                            </div>
                        </div>

                        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <p className="text-blue-800 text-sm">
                                {t('recipeBuilder.step4.reviewNotice')}
                            </p>
                        </div>

                        {/* Basic Info Section */}
                        <div className="border rounded-lg p-6 bg-gray-50">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-bold text-gray-900">{t('recipeBuilder.step4.basicInfoTitle')}</h3>
                                <button
                                    onClick={() => setEditingBasicInfo(!editingBasicInfo)}
                                    className="flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition text-sm"
                                >
                                    <Edit2 className="w-4 h-4" />
                                    {editingBasicInfo ? t('recipeBuilder.step4.done') : t('recipeBuilder.step4.edit')}
                                </button>
                            </div>

                            {editingBasicInfo ? (
                                <div className="space-y-3">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">{t('recipeBuilder.step4.name')}</label>
                                        <input
                                            type="text"
                                            value={reviewData.basic_info.name}
                                            onChange={(e) => updateBasicInfoField('name', e.target.value)}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">{t('recipeBuilder.step4.cuisine')}</label>
                                            <input
                                                type="text"
                                                value={reviewData.basic_info.cuisine || ''}
                                                onChange={(e) => updateBasicInfoField('cuisine', e.target.value)}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">{t('recipeBuilder.step4.difficulty')}</label>
                                            <select
                                                value={reviewData.basic_info.difficulty}
                                                onChange={(e) => updateBasicInfoField('difficulty', e.target.value)}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                            >
                                                <option value="beginner">{t('recipeBuilder.step1.difficultyBeginner')}</option>
                                                <option value="intermediate">{t('recipeBuilder.step1.difficultyIntermediate')}</option>
                                                <option value="advanced">{t('recipeBuilder.step1.difficultyAdvanced')}</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">{t('recipeBuilder.step4.servings')}</label>
                                        <input
                                            type="number"
                                            value={reviewData.basic_info.servings}
                                            onChange={(e) => updateBasicInfoField('servings', parseInt(e.target.value))}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                            min={1}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">{t('recipeBuilder.step4.description')}</label>
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
                                    <p><strong>{t('recipeBuilder.step4.name')}:</strong> {reviewData.basic_info.name}</p>
                                    <p><strong>{t('recipeBuilder.step4.cuisine')}:</strong> {reviewData.basic_info.cuisine || t('recipeBuilder.step4.notSpecified')}</p>
                                    <p><strong>{t('recipeBuilder.step4.difficulty')}:</strong> {reviewData.basic_info.difficulty}</p>
                                    <p><strong>{t('recipeBuilder.step4.servings')}:</strong> {reviewData.basic_info.servings}</p>
                                    {reviewData.basic_info.description && (
                                        <p><strong>{t('recipeBuilder.step4.description')}:</strong> {reviewData.basic_info.description}</p>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Ingredients Section */}
                        <div className="border rounded-lg p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-bold text-gray-900">
                                    {t('recipeBuilder.step4.ingredientsTitle')} ({reviewData.ingredients.length})
                                </h3>
                                <button
                                    onClick={addReviewIngredient}
                                    className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition text-sm"
                                >
                                    <Plus className="w-4 h-4" />
                                    {t('recipeBuilder.step4.add')}
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
                                                placeholder={t('recipeBuilder.step4.amountPlaceholder')}
                                                className="px-2 py-1 border border-gray-300 rounded text-sm"
                                            />
                                            <input
                                                type="text"
                                                value={ing.unit || ''}
                                                onChange={(e) => updateReviewIngredient(index, 'unit', e.target.value)}
                                                placeholder={t('recipeBuilder.step4.unitPlaceholder')}
                                                className="px-2 py-1 border border-gray-300 rounded text-sm"
                                            />
                                            <input
                                                type="text"
                                                value={ing.name}
                                                onChange={(e) => updateReviewIngredient(index, 'name', e.target.value)}
                                                placeholder={t('recipeBuilder.step4.ingredientPlaceholder')}
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
                                <h3 className="text-lg font-bold text-gray-900">
                                    {t('recipeBuilder.step4.stepsTitle')} ({reviewData.steps.length})
                                </h3>
                                <button
                                    onClick={addReviewStep}
                                    className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition text-sm"
                                >
                                    <Plus className="w-4 h-4" />
                                    {t('recipeBuilder.step4.addStep')}
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
                                                value={(() => {
                                                    const lang = currentLang as 'en' | 'ru' | 'he';
                                                    const translated = step.text_translations?.[lang];
                                                    console.log(`[STEP ${index + 1}] lang=${lang}, has_translations=${!!step.text_translations}, translated=${!!translated}, instruction=${step.instruction.substring(0, 30)}...`);
                                                    return translated || step.instruction;
                                                })()}
                                                onChange={(e) => updateReviewStep(index, 'instruction', e.target.value)}
                                                placeholder={t('recipeBuilder.step4.stepInstructionPlaceholder')}
                                                className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                                                rows={2}
                                            />
                                            <div className="flex gap-2">
                                                <input
                                                    type="number"
                                                    value={step.time_minutes || ''}
                                                    onChange={(e) => updateReviewStep(index, 'time_minutes', parseInt(e.target.value) || null)}
                                                    placeholder={t('recipeBuilder.step4.timePlaceholder')}
                                                    className="w-24 px-2 py-1 border border-gray-300 rounded text-sm"
                                                />
                                                <input
                                                    type="text"
                                                    value={
                                                        step.temperature
                                                            ? typeof step.temperature === 'object'
                                                                ? `${step.temperature.value}°${step.temperature.unit === 'celsius' ? 'C' : 'F'}`
                                                                : step.temperature
                                                            : ''
                                                    }
                                                    onChange={(e) => updateReviewStep(index, 'temperature', e.target.value)}
                                                    placeholder={t('recipeBuilder.step4.tempPlaceholder')}
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
                                <h4 className="font-semibold text-yellow-900 mb-2">{t('recipeBuilder.step4.estimatedTimesTitle')}</h4>
                                <div className="grid grid-cols-3 gap-4 text-sm text-yellow-800">
                                    <div>
                                        <strong>{t('recipeBuilder.step4.prep')}</strong> {reviewData.estimated_times.prep_time || 0} {t('recipeBuilder.step4.minutes')}
                                    </div>
                                    <div>
                                        <strong>{t('recipeBuilder.step4.cook')}</strong> {reviewData.estimated_times.cook_time || 0} {t('recipeBuilder.step4.minutes')}
                                    </div>
                                    <div>
                                        <strong>{t('recipeBuilder.step4.total')}</strong> {reviewData.estimated_times.total_time || 0} {t('recipeBuilder.step4.minutes')}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Diet Labels */}
                        {reviewData.diet_labels && reviewData.diet_labels.length > 0 && (
                            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                                <h4 className="font-semibold text-green-900 mb-2">{t('recipeBuilder.step4.dietLabelsTitle')}</h4>
                                <div className="flex flex-wrap gap-2">
                                    {reviewData.diet_labels.map((label, index) => {
                                        // Translate diet label: "vegetarian" -> t('discover.dietLabels.vegetarian')
                                        const translatedLabel = t(`discover.dietLabels.${label}`, { defaultValue: label });
                                        return (
                                            <span key={index} className="px-3 py-1 bg-green-200 text-green-800 rounded-full text-sm">
                                                {translatedLabel}
                                            </span>
                                        );
                                    })}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {currentStep === 5 && (
                    <div className="space-y-4">
                        <h2 className="text-2xl font-bold text-gray-900 mb-4">
                            {t('recipeBuilder.step5.title')}
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
                                {t('recipeBuilder.step5.makePublic')}
                            </label>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                {t('recipeBuilder.step5.additionalDescription')}
                            </label>
                            <textarea
                                value={finalizeOptions.description}
                                onChange={(e) => setFinalizeOptions({ ...finalizeOptions, description: e.target.value })}
                                placeholder={t('recipeBuilder.step5.additionalDescriptionPlaceholder')}
                                rows={4}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>

                        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                            <h4 className="font-semibold text-green-900 mb-2">{t('recipeBuilder.step5.readyToSave')}</h4>
                            <p className="text-green-800 text-sm">
                                {t('recipeBuilder.step5.saveNotice', {
                                    visibility: finalizeOptions.is_public
                                        ? t('recipeBuilder.step5.published')
                                        : t('recipeBuilder.step5.keptPrivate')
                                })}
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
                    {currentStep === 1 ? t('recipeBuilder.buttons.cancel') : t('recipeBuilder.buttons.back')}
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
                            {t('recipeBuilder.buttons.processing')}
                        </span>
                    ) : currentStep === 5 ? (
                        t('recipeBuilder.buttons.createRecipe')
                    ) : currentStep === 4 ? (
                        t('recipeBuilder.buttons.confirmContinue')
                    ) : (
                        t('recipeBuilder.buttons.next')
                    )}
                </button>
            </div>

            {/* Duplicate Recipe Modal */}
            {showDuplicateModal && duplicateRecipe && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full p-6">
                        <div className="mb-6">
                            <h2 className="text-2xl font-bold text-gray-900 mb-2">
                                ⚠️ {t('recipeBuilder.duplicate.title', { defaultValue: 'Recipe Already Exists' })}
                            </h2>
                            <p className="text-gray-600">
                                {t('recipeBuilder.duplicate.message', {
                                    defaultValue: 'A recipe with this name already exists in the Discovery page.',
                                    name: basicInfo.name
                                })}
                            </p>
                        </div>

                        {/* Existing Recipe Info */}
                        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <h3 className="font-semibold text-blue-900 mb-2">
                                {t('recipeBuilder.duplicate.existingRecipe', { defaultValue: 'Existing Recipe:' })}
                            </h3>
                            <div className="space-y-1 text-sm text-blue-800">
                                <p><strong>{t('recipeBuilder.step4.name')}:</strong> {duplicateRecipe.name}</p>
                                {duplicateRecipe.cuisine && (
                                    <p><strong>{t('recipeBuilder.step4.cuisine')}:</strong> {duplicateRecipe.cuisine}</p>
                                )}
                                <p><strong>{t('recipeBuilder.step4.difficulty')}:</strong> {duplicateRecipe.difficulty}</p>
                                <p><strong>{t('recipeBuilder.step4.servings')}:</strong> {duplicateRecipe.servings}</p>
                                {duplicateRecipe.description && (
                                    <p className="mt-2"><strong>{t('recipeBuilder.step4.description')}:</strong> {duplicateRecipe.description}</p>
                                )}
                            </div>
                        </div>

                        {/* Options */}
                        <div className="space-y-3">
                            <button
                                onClick={handleViewExisting}
                                className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center justify-center gap-2"
                            >
                                <span>👁️</span>
                                {t('recipeBuilder.duplicate.viewExisting', { defaultValue: 'View Existing Recipe' })}
                            </button>

                            <button
                                onClick={handleCreateFork}
                                className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center justify-center gap-2"
                            >
                                <span>🍴</span>
                                {t('recipeBuilder.duplicate.createFork', { defaultValue: 'Create Personal Fork (Private)' })}
                            </button>

                            <button
                                onClick={handleCreateNew}
                                className="w-full px-6 py-3 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors font-medium flex items-center justify-center gap-2"
                            >
                                <span>➕</span>
                                {t('recipeBuilder.duplicate.createNew', { defaultValue: 'Create New Public Version' })}
                            </button>

                            <button
                                onClick={() => setShowDuplicateModal(false)}
                                className="w-full px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                            >
                                {t('recipeBuilder.buttons.cancel')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default RecipeBuilderWizard;
