// User types
export interface User {
    id: string;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    partner?: User;
    daily_calories_goal: number;
    daily_protein_goal: number;
    daily_carbs_goal: number;
    daily_fat_goal: number;
    collaboration_key?: string;
    personal_color?: string;
    shopping_role?: 'creator' | 'collaborator' | 'both';
}

// Shopping types
export interface Collaborator {
    id: string;
    username: string;
    first_name: string;
    color: string;
    can_edit: boolean;
    can_add_items: boolean;
    can_invite_others: boolean;
    is_creator: boolean;
    joined_at: string;
}

export interface ShoppingList {
    id: string;
    name: string;
    creator: User;
    items: ShoppingItem[];
    is_active: boolean;
    is_collaborative: boolean;
    collaborators: Collaborator[];
    items_count: number;
    completed_items_count: number;
    user_permissions: {
        can_edit: boolean;
        can_add_items: boolean;
        can_invite_others: boolean;
        is_creator: boolean;
    } | null;
    created_at: string;
    updated_at: string;
}

export interface ShoppingItem {
    id: string;
    name: string;
    quantity: number;
    unit: string;
    category: string;
    is_completed: boolean;
    completed_by?: string;
    completed_by_name?: string;
    completed_at?: string;
    added_by: string;
    added_by_name: string;
    added_by_first_name: string;
    ai_suggested?: boolean;
    user_color: string;
    priority: number;
    display_color: string;
    is_recent: boolean;
    notes?: string;
    created_at: string;
    updated_at: string;
}

// ========================================
// NUTRITION TRACKING & AI COACH TYPES
// ========================================

export interface UserNutritionSettings {
    // Master toggle
    ai_coach_enabled: boolean;

    // Content permissions
    allow_recipes_access: boolean;
    allow_inventory_access: boolean;
    allow_shopping_access: boolean;

    // Personal data permissions
    allow_personal_data_access: boolean;
    allow_weight_data: boolean;
    allow_height_data: boolean;
    allow_age_data: boolean;
    allow_gender_data: boolean;
    allow_activity_level: boolean;
    allow_health_conditions: boolean;

    // Goals
    goal_mode: 'manual' | 'ai_calculated';
    manual_calories_goal?: number;
    manual_protein_goal?: number;
    manual_carbs_goal?: number;
    manual_fat_goal?: number;

    // Coaching
    coaching_frequency: 'daily' | 'weekly' | 'never';
    coaching_style: 'supportive' | 'strict' | 'balanced';
    track_calories: boolean;
    track_protein: boolean;
    track_carbs: boolean;
    track_fat: boolean;
    track_meal_timing: boolean;

    // Metadata
    created_at: string;
    updated_at: string;
    active_permissions: string[];
}

export interface NutritionEntry {
    id: string;
    user: string;
    date: string;
    meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
    time?: string;
    entry_type: 'manual' | 'recipe' | 'product' | 'ai_suggested';

    // Optional links
    recipe?: string;
    recipe_name?: string;
    inventory_item?: string;
    inventory_item_name?: string;

    // Food details
    food_name: string;
    portion_size: number;
    portion_unit: string;

    // Nutrition data
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
    fiber?: number;
    sugar?: number;
    sodium?: number;

    // Metadata
    notes?: string;
    photo?: string;
    created_at: string;
    updated_at: string;
    macros_summary: {
        calories: number;
        protein: number;
        carbs: number;
        fat: number;
    };
}

export interface NutritionGoals {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
    source?: 'manual' | 'ai_calculated' | 'manual_fallback' | 'insufficient_data_fallback';
    bmr?: number;
    tdee?: number;
}

export interface DailySummary {
    date: string;
    goals: NutritionGoals;
    consumed: {
        calories: number;
        protein: number;
        carbs: number;
        fat: number;
    };
    remaining: {
        calories: number;
        protein: number;
        carbs: number;
        fat: number;
    };
    percentage: {
        calories: number;
        protein: number;
        carbs: number;
        fat: number;
    };
    meals: NutritionEntry[];
}

export interface WeeklySummary {
    week_start: string;
    week_end: string;
    daily_averages: {
        calories: number;
        protein: number;
        carbs: number;
        fat: number;
    };
    weekly_totals: {
        calories: number;
        protein: number;
        carbs: number;
        fat: number;
    };
    goal_adherence: {
        calories: number;
        protein: number;
    };
    days: Array<{
        date: string;
        calories: number;
        protein: number;
        entry_count: number;
    }>;
}

export interface AISuggestion {
    name: string;
    source: 'recipe' | 'inventory' | 'general';
    calories: number;
    protein: number;
    reason: string;
}

export interface AISuggestionResponse {
    ai_enabled: boolean;
    message: string;
    suggestions?: AISuggestion[];
}

export interface AICoachingResponse {
    advice: string;
    suggestions?: Array<{
        name: string;
        reason: string;
    }>;
}

export interface LogFromRecipeRequest {
    recipe_id: string;
    portion_multiplier: number;
    meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
    date: string;
    time?: string;
    notes?: string;
}

export interface LogFromInventoryRequest {
    inventory_item_id: string;
    amount_grams: number;
    meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
    date: string;
    time?: string;
    update_inventory?: boolean;
    notes?: string;
}

// Inventory types
export interface InventoryItem {
    id: string;
    name: string;
    quantity: number;
    unit: string;
    category: string;
    location: 'fridge' | 'freezer' | 'pantry' | 'counter';
    expiration_date?: string;
    purchase_date?: string;
    nutrition_data?: Record<string, any>;
    barcode?: string;
    low_stock_threshold: number;
    auto_add_to_list: boolean;
    notes?: string;
    shopping_list?: string;
    shopping_list_name?: string;
    is_expired: boolean;
    is_expiring_soon: boolean;
    is_low_stock: boolean;
    expiry_status: 'expired' | 'urgent' | 'warning' | 'ok';
    created_at: string;
    updated_at: string;
}

export interface BulkCreateInventoryResponse {
    success: boolean;
    created_count: number;
    merged_count: number;
    total_count: number;
    error_count: number;
    items: InventoryItem[];
    errors: Array<{ item: string; error: string }>;
    message?: string;
}

