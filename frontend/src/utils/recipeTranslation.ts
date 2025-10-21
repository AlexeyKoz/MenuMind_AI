/**
 * Recipe Translation Utilities
 * Translates recipe ingredients and steps on-the-fly based on current language
 */

import api from '../services/api';

// Cache for cooking terms
let cookingTermsCache: Record<string, Record<string, string>> = {};
let ingredientsCache: Record<string, Record<string, string>> = {};

/**
 * Translate cooking terms in a text
 */
export const translateCookingTerms = async (text: string, targetLanguage: string): Promise<string> => {
    if (!text || targetLanguage === 'en') return text;

    // For now, return original text
    // TODO: Implement cooking terms translation API endpoint
    return text;
};

/**
 * Translate a recipe ingredient name
 */
export const translateIngredientName = async (
    ingredientKey: string | undefined,
    originalName: string,
    targetLanguage: string
): Promise<string> => {
    if (targetLanguage === 'en') return originalName;

    // Check cache first
    if (ingredientKey && ingredientsCache[ingredientKey]?.[targetLanguage]) {
        return ingredientsCache[ingredientKey][targetLanguage];
    }

    // For now, return original
    // TODO: Implement ingredient translation lookup from IML
    return originalName;
};

/**
 * Translate all ingredients in a recipe
 */
export const translateIngredients = async (
    ingredients: any[],
    targetLanguage: string
): Promise<any[]> => {
    if (!ingredients || targetLanguage === 'en') return ingredients;

    return Promise.all(
        ingredients.map(async (ing) => ({
            ...ing,
            name: await translateIngredientName(ing.ingredient_key, ing.name, targetLanguage),
        }))
    );
};

/**
 * Translate all cooking steps in a recipe
 */
export const translateSteps = async (
    steps: any[],
    targetLanguage: string
): Promise<any[]> => {
    if (!steps || targetLanguage === 'en') return steps;

    return Promise.all(
        steps.map(async (step) => ({
            ...step,
            text: await translateCookingTerms(step.text || step.instruction || '', targetLanguage),
        }))
    );
};

/**
 * Translate entire recipe (ingredients + steps)
 */
export const translateRecipe = async (recipe: any, targetLanguage: string) => {
    if (!recipe || targetLanguage === 'en') return recipe;

    const [translatedIngredients, translatedSteps] = await Promise.all([
        translateIngredients(recipe.base_ingredients || [], targetLanguage),
        translateSteps(recipe.base_steps || [], targetLanguage),
    ]);

    return {
        ...recipe,
        base_ingredients: translatedIngredients,
        base_steps: translatedSteps,
    };
};

