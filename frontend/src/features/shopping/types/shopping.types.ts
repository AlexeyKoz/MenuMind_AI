export interface ShoppingItem {
    id: string;
    shopping_list_id: string;
    name: string;
    name_translations: Record<string, string>;
    quantity: number;
    weight_quantity: number;
    liquid_quantity: number;
    category: string;
    is_completed: boolean;
    added_by: string | null;
    created_at: string;
    updated_at: string;
}

export interface ShoppingList {
    id: string;
    name: string;
    created_by: string;
    collaborators: string[];
    created_at: string;
    updated_at: string;
}

export interface CategoryInfo {
    id: string;
    icon: string;
    label: string;
    items: ShoppingItem[];
}

