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

// Nutrition types
export interface NutritionEntry {
    id: string;
    meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
    food_description: string;
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
    created_at: string;
}

export interface NutritionGoals {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
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

