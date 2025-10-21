import { BulkCreateInventoryResponse } from '../types';

class ApiService {
    private token: string | null;
    private baseURL: string;
    private onTokenExpired?: () => void;

    constructor(token: string | null, onTokenExpired?: () => void) {
        this.token = token;
        this.baseURL = 'http://localhost:8000/api';
        this.onTokenExpired = onTokenExpired;
    }

    private async request(endpoint: string, options: RequestInit = {}): Promise<any> {
        const url = `${this.baseURL}${endpoint}`;
        const config: RequestInit = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`,
                ...options.headers
            }
        };

        const response = await fetch(url, config);

        // Handle token expiration (401 Unauthorized)
        if (response.status === 401) {
            console.warn('🔐 Token expired or invalid - logging out user');

            // Call the token expiration callback if provided
            if (this.onTokenExpired) {
                this.onTokenExpired();
            }

            throw new Error('Your session has expired. Please log in again.');
        }

        if (!response.ok) {
            // Try to extract detailed error message from response body
            try {
                // Try to parse JSON error response
                const errorText = await response.text();
                console.log('🔍 Raw error response:', errorText);

                if (errorText) {
                    try {
                        const errorData = JSON.parse(errorText);

                        // Provide user-friendly error messages
                        if (errorData.detail && typeof errorData.detail === 'string') {
                            throw new Error(errorData.detail);
                        }

                        const errorMessage = errorData.error || errorData.message || response.statusText;
                        console.log('📋 Parsed error message:', errorMessage);
                        throw new Error(errorMessage);
                    } catch (jsonParseError) {
                        // If JSON parsing fails, use the raw text if meaningful
                        if (errorText.length > 0 && errorText !== response.statusText) {
                            throw new Error(errorText);
                        }
                    }
                }

                // Fall back to status text
                throw new Error(`API Error: ${response.statusText}`);
            } catch (error) {
                // If it's already an Error we threw, re-throw it
                if (error instanceof Error && error.message !== `API Error: ${response.statusText}`) {
                    throw error;
                }
                // Final fallback
                throw new Error(`API Error: ${response.statusText}`);
            }
        }

        // Check if response has content before trying to parse JSON
        const contentType = response.headers.get('content-type');
        const hasJsonContent = contentType && contentType.includes('application/json');
        const hasContent = response.status !== 204; // 204 No Content

        if (hasJsonContent && hasContent) {
            const text = await response.text();
            return text ? JSON.parse(text) : {};
        }

        // For non-JSON responses or empty responses, return a success indicator
        return { success: true, status: response.status };
    }

    // Generic HTTP methods
    get = (endpoint: string) => this.request(endpoint);
    post = (endpoint: string, data?: any) => this.request(endpoint, {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined
    });
    put = (endpoint: string, data?: any) => this.request(endpoint, {
        method: 'PUT',
        body: data ? JSON.stringify(data) : undefined
    });
    patch = (endpoint: string, data?: any) => this.request(endpoint, {
        method: 'PATCH',
        body: data ? JSON.stringify(data) : undefined
    });
    delete = (endpoint: string) => this.request(endpoint, {
        method: 'DELETE'
    });

    // Shopping endpoints
    getShoppingLists = () => this.request('/shopping/lists/');
    createShoppingList = (data: any) => this.request('/shopping/lists/', {
        method: 'POST',
        body: JSON.stringify(data)
    });
    deleteShoppingList = (listId: string) => this.request(`/shopping/lists/${listId}/`, {
        method: 'DELETE'
    });
    leaveList = (listId: string) => this.request(`/shopping/lists/${listId}/leave_list/`, {
        method: 'POST'
    });

    // Archive endpoints
    getArchivedLists = () => this.request('/shopping/lists/archived/');
    restoreList = (listId: string) => this.request(`/shopping/lists/${listId}/restore/`, {
        method: 'POST'
    });
    permanentDeleteList = (listId: string) => this.request(`/shopping/lists/${listId}/permanent-delete/`, {
        method: 'DELETE'
    });
    addItemToList = (listId: string, data: any) => this.request(`/shopping/lists/${listId}/add_item/`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
    aiAddItems = (listId: string, text: string) => this.request(`/shopping/lists/${listId}/ai_add_items/`, {
        method: 'POST',
        body: JSON.stringify({ text })
    });
    toggleItem = (itemId: string) => this.request(`/shopping/items/${itemId}/toggle_complete/`, {
        method: 'POST'
    });
    deleteItem = (itemId: string) => this.request(`/shopping/items/${itemId}/`, {
        method: 'DELETE'
    });
    updateWeightQuantity = (itemId: string, weight_quantity: number) => this.request(`/shopping/items/${itemId}/update_weight_quantity/`, {
        method: 'PATCH',
        body: JSON.stringify({ weight_quantity })
    });
    updateLiquidQuantity = (itemId: string, liquid_quantity: number) => this.request(`/shopping/items/${itemId}/update_liquid_quantity/`, {
        method: 'PATCH',
        body: JSON.stringify({ liquid_quantity })
    });
    mockStoreOrder = (data: any) => this.request('/shopping/lists/mock_store_order/', {
        method: 'POST',
        body: JSON.stringify(data)
    });

    // Nutrition endpoints
    getNutritionToday = () => this.request('/nutrition/entries/today_summary/');
    logMeal = (data: any) => this.request('/nutrition/entries/', {
        method: 'POST',
        body: JSON.stringify(data)
    });
    aiLogMeal = (text: string, mealType: string) => this.request('/nutrition/entries/ai_log_meal/', {
        method: 'POST',
        body: JSON.stringify({ text, meal_type: mealType })
    });
    getWeeklyReport = () => this.request('/nutrition/entries/weekly_report/');
    getCoaching = () => this.request('/nutrition/entries/get_coaching/', {
        method: 'POST'
    });

    // AI endpoints
    aiAssistant = (text: string, contextType: string) => this.request('/ai/assistant/', {
        method: 'POST',
        body: JSON.stringify({ text, context_type: contextType })
    });
    generateRecipes = () => this.request('/ai/recipes/', {
        method: 'POST'
    });

    // Collaboration endpoints
    addCollaborator = (listId: string, data: any) => this.request(`/shopping/lists/${listId}/add_collaborator/`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
    getCollaborators = (listId: string) => this.request(`/shopping/lists/${listId}/collaborators/`);
    updateCollaboratorPermissions = (listId: string, data: any) => this.request(`/shopping/lists/${listId}/update_collaborator_permissions/`, {
        method: 'POST',
        body: JSON.stringify(data)
    });

    // User collaboration endpoints
    getMyCollaborationKey = () => this.request('/users/profile/my_collaboration_key/');
    generateCollaborationKey = () => this.request('/users/profile/generate_collaboration_key/', {
        method: 'POST'
    });
    updatePersonalColor = (color: string) => this.request('/users/profile/update_personal_color/', {
        method: 'POST',
        body: JSON.stringify({ color })
    });

    // Recipe endpoints
    getRecipes = () => this.request('/recipes/recipes/');
    getRecipe = (recipeId: string) => this.request(`/recipes/recipes/${recipeId}/`);
    getMyRecipes = () => this.request('/recipes/recipes/my_recipes/');
    getPopularRecipes = () => this.request('/recipes/recipes/popular/');
    getRecipeVersions = (recipeId: string) => this.request(`/recipes/recipes/${recipeId}/versions/`);
    saveRecipe = (recipeId: string, data?: any) => this.request(`/recipes/recipes/${recipeId}/save_recipe/`, {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined
    });
    unsaveRecipe = (recipeId: string) => this.request(`/recipes/recipes/${recipeId}/unsave_recipe/`, {
        method: 'DELETE'
    });

    // Recipe Archive Operations
    getArchivedRecipes = () => this.request('/recipes/recipes/archived_recipes/');

    restoreRecipe = (recipeId: string) => this.request(`/recipes/recipes/${recipeId}/restore_recipe/`, {
        method: 'POST'
    });

    permanentlyDeleteRecipe = (recipeId: string) => this.request(`/recipes/recipes/${recipeId}/permanently_delete_recipe/`, {
        method: 'DELETE'
    });

    markRecipeCooked = (recipeId: string) => this.request(`/recipes/recipes/${recipeId}/mark_cooked/`, {
        method: 'POST'
    });
    findRecipe = (query: string, shoppingListId?: string, addToList?: boolean) => this.request('/recipes/recipes/find_recipe/', {
        method: 'POST',
        body: JSON.stringify({
            query,
            shopping_list_id: shoppingListId,
            add_to_list: addToList
        })
    });

    // Get recipe translation in specific language
    getRecipeTranslation = async (recipeId: string, language: string) => {
        return this.request(`/recipes/canonical/${recipeId}/translation/${language}/`, {
            method: 'GET'
        });
    };

    // RCIP file operations
    downloadRCIP = async (recipeId: string, recipeName: string) => {
        const url = `${this.baseURL}/recipes/recipes/${recipeId}/download_rcip/`;
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to download recipe');
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `${recipeName.replace(/\s+/g, '_')}.rcip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);
    };

    uploadRCIP = async (file: File) => {
        const url = `${this.baseURL}/recipes/recipes/upload_rcip/`;
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
            },
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            try {
                const errorData = JSON.parse(errorText);
                throw new Error(errorData.error || 'Upload failed');
            } catch {
                throw new Error('Upload failed');
            }
        }

        return await response.json();
    };

    // Canonical Recipe endpoints (Phase 4)
    getCanonicalRecipes = (params?: {
        search?: string;
        cuisine?: string;
        difficulty?: string;
        diet_labels?: string[];
        source_type?: string;
        sort?: string;
        page?: number;
    }) => {
        // Add current language to params
        const language = localStorage.getItem('i18nextLng') || 'en';

        if (!params) {
            return this.request(`/recipes/canonical/?lang=${language}`);
        }

        const queryParams = new URLSearchParams();

        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                if (Array.isArray(value)) {
                    // Handle arrays (like diet_labels)
                    value.forEach(item => queryParams.append(key, String(item)));
                } else {
                    queryParams.append(key, String(value));
                }
            }
        });

        // Add current language
        queryParams.append('lang', language);

        const queryString = queryParams.toString();
        return this.request(`/recipes/canonical/${queryString ? '?' + queryString : ''}`);
    };

    getCanonicalRecipe = (recipeId: string) =>
        this.request(`/recipes/canonical/${recipeId}/`);

    likeCanonicalRecipe = (recipeId: string) =>
        this.request(`/recipes/canonical/${recipeId}/like/`, { method: 'POST' });

    getLikeStatus = (recipeId: string) =>
        this.request(`/recipes/canonical/${recipeId}/likes_status/`);

    rateCanonicalRecipe = (recipeId: string, rating: number) =>
        this.request(`/recipes/canonical/${recipeId}/rate/`, {
            method: 'POST',
            body: JSON.stringify({ rating })
        });

    addReview = (recipeId: string, data: { title: string; content: string; rating: number }) =>
        this.request(`/recipes/canonical/${recipeId}/add_review/`, {
            method: 'POST',
            body: JSON.stringify(data)
        });

    getReviews = (recipeId: string, params?: { ordering?: string; page?: number }) => {
        if (!params) {
            return this.request(`/recipes/canonical/${recipeId}/reviews/`);
        }

        const queryParams = new URLSearchParams();

        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) {
                queryParams.append(key, String(value));
            }
        });

        const queryString = queryParams.toString();
        return this.request(`/recipes/canonical/${recipeId}/reviews/${queryString ? '?' + queryString : ''}`);
    };

    updateReview = (recipeId: string, reviewId: string, data: { title?: string; content?: string; rating?: number }) =>
        this.request(`/recipes/canonical/${recipeId}/reviews/${reviewId}/`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });

    deleteReview = (recipeId: string, reviewId: string) =>
        this.request(`/recipes/canonical/${recipeId}/reviews/${reviewId}/`, {
            method: 'DELETE'
        });

    markReviewHelpful = (recipeId: string, reviewId: string) =>
        this.request(`/recipes/canonical/${recipeId}/reviews/${reviewId}/helpful/`, {
            method: 'POST'
        });

    // Recipe Builder endpoints (Phase 4)
    startBuilder = () =>
        this.request('/recipes/recipes/start_builder/', { method: 'POST' });

    builderStep = (payload: {
        session_id: string;
        step: 'basic_info' | 'ingredients' | 'steps' | 'review' | 'finalize';
        data: any;
    }) =>
        this.request('/recipes/recipes/builder_step/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

    // ===== INVENTORY MANAGEMENT (Phase 5) =====

    // Inventory CRUD
    getInventory = () =>
        this.request('/shopping/inventory/');

    getInventoryByLocation = (location?: string) =>
        this.request(`/shopping/inventory/by_location/${location ? `?location=${location}` : ''}`);

    getInventoryExpiringSoon = (days: number = 7) =>
        this.request(`/shopping/inventory/expiring_soon/?days=${days}`);

    getInventoryLowStock = () =>
        this.request('/shopping/inventory/low_stock/');

    getInventoryItem = (id: string) =>
        this.request(`/shopping/inventory/${id}/`);

    createInventoryItem = (data: {
        name: string;
        quantity: number;
        unit: string;
        location: 'fridge' | 'freezer' | 'pantry' | 'counter';
        category: string;
        expiration_date?: string;
        notes?: string;
        shopping_list?: string;
    }) =>
        this.request('/shopping/inventory/', {
            method: 'POST',
            body: JSON.stringify(data)
        });

    updateInventoryItem = (id: string, data: Partial<{
        name: string;
        quantity: number;
        unit: string;
        location: string;
        category: string;
        expiration_date: string;
        notes: string;
        low_stock_threshold: number;
        auto_add_to_list: boolean;
    }>) =>
        this.request(`/shopping/inventory/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });

    deleteInventoryItem = (id: string) =>
        this.request(`/shopping/inventory/${id}/`, {
            method: 'DELETE'
        });

    // Inventory Actions
    moveInventoryItem = (id: string, newLocation: 'fridge' | 'freezer' | 'pantry' | 'counter') =>
        this.request(`/shopping/inventory/${id}/move/`, {
            method: 'PATCH',
            body: JSON.stringify({ new_location: newLocation })
        });

    getInventoryHistory = (id: string) =>
        this.request(`/shopping/inventory/${id}/history/`);

    // Bulk Operations
    bulkCreateInventory = (items: Array<{
        name: string;
        quantity: number;
        unit: string;
        location: string;
        category: string;
        expiration_date?: string;
        shopping_list_id?: string;
    }>): Promise<BulkCreateInventoryResponse> =>
        this.request('/shopping/inventory/bulk_create/', {
            method: 'POST',
            body: JSON.stringify({ items })
        });

    consumeInventory = (
        items: Array<{ inventory_id: string; quantity_used: number; unit: string }>,
        recipeId?: string,
        notes?: string
    ) =>
        this.request('/shopping/inventory/consume/', {
            method: 'POST',
            body: JSON.stringify({
                items,
                recipe_id: recipeId,
                notes
            })
        });

    // AI Features
    generateRecipesFromInventory = (options?: {
        max_recipes?: number;
        prioritize_expiring?: boolean;
        max_missing_ingredients?: number;
    }) =>
        this.request('/shopping/inventory/generate_recipes/', {
            method: 'POST',
            body: JSON.stringify(options || {})
        });

    // Shopping List → Inventory Integration
    sendToInventory = (listId: string, itemIds: string[], aiCategorize: boolean = true) =>
        this.request(`/shopping/lists/${listId}/send_to_inventory/`, {
            method: 'POST',
            body: JSON.stringify({
                item_ids: itemIds,
                ai_categorize: aiCategorize
            })
        });

    // ========================================
    // NUTRITION TRACKING & AI COACH
    // ========================================

    // Nutrition Settings
    getNutritionSettings = () =>
        this.request('/nutrition/settings/');

    updateNutritionSettings = (settings: Partial<any>) =>
        this.request('/nutrition/settings/update/', {
            method: 'PATCH',
            body: JSON.stringify(settings)
        });

    getNutritionGoals = () =>
        this.request('/nutrition/settings/goals/');

    // Nutrition Entries (CRUD)
    getNutritionEntries = (params?: {
        date?: string;
        start_date?: string;
        end_date?: string;
        meal_type?: 'breakfast' | 'lunch' | 'dinner' | 'snack';
    }) => {
        const queryParams = new URLSearchParams();
        if (params?.date) queryParams.append('date', params.date);
        if (params?.start_date) queryParams.append('start_date', params.start_date);
        if (params?.end_date) queryParams.append('end_date', params.end_date);
        if (params?.meal_type) queryParams.append('meal_type', params.meal_type);

        const queryString = queryParams.toString();
        return this.request(`/nutrition/entries/${queryString ? `?${queryString}` : ''}`);
    };

    createNutritionEntry = (entry: {
        date: string;
        meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
        time?: string;
        entry_type?: 'manual' | 'recipe' | 'product' | 'ai_suggested';
        food_name: string;
        portion_size: number;
        portion_unit: string;
        calories: number;
        protein: number;
        carbs: number;
        fat: number;
        fiber?: number;
        sugar?: number;
        sodium?: number;
        notes?: string;
    }) =>
        this.request('/nutrition/entries/', {
            method: 'POST',
            body: JSON.stringify(entry)
        });

    updateNutritionEntry = (id: string, entry: Partial<any>) =>
        this.request(`/nutrition/entries/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(entry)
        });

    deleteNutritionEntry = (id: string) =>
        this.request(`/nutrition/entries/${id}/`, {
            method: 'DELETE'
        });

    // Log from Recipe/Inventory
    logFromRecipe = (data: {
        recipe_id: string;
        portion_multiplier: number;
        meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
        date: string;
        time?: string;
        notes?: string;
    }) =>
        this.request('/nutrition/entries/from_recipe/', {
            method: 'POST',
            body: JSON.stringify(data)
        });

    logFromInventory = (data: {
        inventory_item_id: string;
        amount_grams: number;
        meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
        date: string;
        time?: string;
        update_inventory?: boolean;
        notes?: string;
    }) =>
        this.request('/nutrition/entries/from_inventory/', {
            method: 'POST',
            body: JSON.stringify(data)
        });

    // Summaries
    getTodaySummary = () =>
        this.request('/nutrition/entries/today_summary/');

    getWeeklySummary = (weekStart?: string) => {
        const params = weekStart ? `?week_start=${weekStart}` : '';
        return this.request(`/nutrition/entries/weekly_summary/${params}`);
    };

    getMonthlySummary = (month?: string) => {
        const params = month ? `?month=${month}` : '';
        return this.request(`/nutrition/entries/monthly_summary/${params}`);
    };

    // AI Features (only work if AI coach is enabled)
    getAISuggestions = (params?: {
        meal_type?: 'breakfast' | 'lunch' | 'dinner' | 'snack';
        max_calories?: number;
    }) =>
        this.request('/nutrition/ai/suggestions/', {
            method: 'POST',
            body: JSON.stringify(params || {})
        });

    askAICoach = (question: string) =>
        this.request('/nutrition/ai/coaching/', {
            method: 'POST',
            body: JSON.stringify({ question })
        });

    getAIWeeklyReport = () =>
        this.request('/nutrition/ai/weekly_report/');

    // ========================================
    // DASHBOARD & ANALYTICS
    // ========================================

    // Dashboard Overview
    getDashboardOverview = (params?: { period?: '7days' | '30days' | '90days' | '1year'; include_ai?: boolean }) => {
        const queryParams = new URLSearchParams();
        if (params?.period) queryParams.append('period', params.period);
        if (params?.include_ai !== undefined) queryParams.append('include_ai', String(params.include_ai));
        const queryString = queryParams.toString();
        return this.request(`/analytics/dashboard/overview/${queryString ? '?' + queryString : ''}`);
    };

    // AI Insights
    getAIInsights = (params?: { period?: string }) => {
        const queryParams = new URLSearchParams();
        if (params?.period) queryParams.append('period', params.period);
        const queryString = queryParams.toString();
        return this.request(`/analytics/dashboard/ai_insights/${queryString ? '?' + queryString : ''}`);
    };

    regenerateAIInsights = (period?: string) =>
        this.request('/analytics/dashboard/ai_insights/regenerate/', {
            method: 'POST',
            body: JSON.stringify({ period: period || '30days' })
        });

    // Achievements
    getAchievements = () =>
        this.request('/analytics/dashboard/achievements/');

    getAchievementsList = () =>
        this.request('/analytics/achievements/');

    // Streaks
    getStreaks = () =>
        this.request('/analytics/streaks/');

    // Cooking Logs
    getCookingLogs = () =>
        this.request('/analytics/cooking-logs/');

    logRecipeCooking = (data: { recipe: string; canonical_recipe?: string; servings?: number; notes?: string }) =>
        this.request('/analytics/cooking-logs/', {
            method: 'POST',
            body: JSON.stringify(data)
        });

    // ============================================
    // USER PREFERENCES METHODS (NEW)
    // ============================================

    /**
     * Get user preferences (language, unit system, etc.)
     */
    getUserPreferences = async (): Promise<any> => {
        return this.get('/users/profile/preferences/');
    };

    /**
     * Update user preferences
     */
    updateUserPreferences = async (data: Partial<{
        preferred_language: 'en' | 'ru' | 'he';
        unit_system: 'metric' | 'imperial';
        timezone?: string;
        date_format?: string;
    }>): Promise<any> => {
        return this.patch('/users/profile/preferences/', data);
    };


}

export default ApiService;