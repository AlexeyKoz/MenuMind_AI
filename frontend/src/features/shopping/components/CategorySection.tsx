import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { ShoppingItem } from '../types/shopping.types';
import { ShoppingItemCard } from './ShoppingItemCard';
import { cn } from '../../../lib/utils';

interface CategorySectionProps {
    category: {
        id: string;
        icon: string;
        label: string;
        items: ShoppingItem[];
    };
    onToggleItem: (id: string) => void;
    onUpdateQuantity: (id: string, quantity: number) => void;
    onDeleteItem: (id: string) => void;
}

export const CategorySection: React.FC<CategorySectionProps> = ({
    category,
    onToggleItem,
    onUpdateQuantity,
    onDeleteItem
}) => {
    const [isCollapsed, setIsCollapsed] = useState(false);

    const completedCount = category.items.filter(i => i.is_completed).length;
    const totalCount = category.items.length;
    const progress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

    return (
        <div className="mb-4">
            {/* Category Header */}
            <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors touch-manipulation"
                style={{ minHeight: '56px' }}
            >
                <div className="flex items-center gap-3">
                    <span className="text-2xl">{category.icon}</span>
                    <div className="text-left">
                        <h3 className="text-lg font-semibold text-gray-900">
                            {category.label}
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                            <span className="text-sm text-gray-600">
                                {completedCount}/{totalCount} items
                            </span>
                            {/* Progress bar */}
                            <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-green-500 transition-all duration-300"
                                    style={{ width: `${progress}%` }}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                <ChevronDown
                    className={cn(
                        'w-5 h-5 text-gray-400 transition-transform duration-200',
                        isCollapsed && 'rotate-180'
                    )}
                />
            </button>

            {/* Category Items */}
            {!isCollapsed && (
                <div className="mt-2 space-y-2 px-2">
                    {category.items.map(item => (
                        <ShoppingItemCard
                            key={item.id}
                            item={item}
                            onToggle={onToggleItem}
                            onUpdateQuantity={onUpdateQuantity}
                            onDelete={onDeleteItem}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};

