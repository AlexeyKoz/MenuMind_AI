import React from 'react';
import { ShoppingItem } from '../../types/shopping.types';
import { useTranslation } from 'react-i18next';

interface ItemNameProps {
    item: ShoppingItem;
}

export const ItemName: React.FC<ItemNameProps> = ({ item }) => {
    const { i18n } = useTranslation();
    const currentLang = i18n.language;

    // Get translated name if available, fallback to default name
    const displayName = item.name_translations?.[currentLang] || item.name;

    return (
        <div className="flex-1 min-w-0">
            <span className={`text-lg font-medium ${item.is_completed ? 'line-through text-gray-500' : 'text-gray-900'}`}>
                {displayName}
            </span>
        </div>
    );
};

