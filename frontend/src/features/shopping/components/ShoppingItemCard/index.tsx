import React from 'react';
import { ShoppingItem } from '../../types/shopping.types';
import { ItemCheckbox } from './ItemCheckbox';
import { ItemName } from './ItemName';
import { QuantityControls } from './QuantityControls';
import { useSwipeGestures } from '../../hooks/useSwipeGestures';
import { cn } from '../../../../lib/utils';

interface ShoppingItemCardProps {
    item: ShoppingItem;
    onToggle: (id: string) => void;
    onUpdateQuantity: (id: string, quantity: number) => void;
    onDelete: (id: string) => void;
}

const getCategoryIcon = (category: string): string => {
    const icons: Record<string, string> = {
        produce: '🥬',
        dairy: '🥛',
        meat: '🥩',
        bakery: '🍞',
        frozen: '🧊',
        pantry: '🥫',
        beverages: '🥤',
        other: '📦'
    };
    return icons[category] || '📦';
};

export const ShoppingItemCard: React.FC<ShoppingItemCardProps> = ({
    item,
    onToggle,
    onUpdateQuantity,
    onDelete
}) => {
    const { swipeState, handlers } = useSwipeGestures(
        item.id,
        () => onToggle(item.id),  // Swipe right = complete
        () => onDelete(item.id)    // Swipe left = delete
    );

    const getSwipeBackground = () => {
        if (swipeState.currentX > 50) {
            return 'bg-gradient-to-r from-green-500 to-green-600';
        } else if (swipeState.currentX < -50) {
            return 'bg-gradient-to-r from-red-500 to-red-600';
        }
        return '';
    };

    return (
        <div
            {...handlers}
            className={cn(
                'relative mb-2 bg-white rounded-lg shadow-sm',
                'transition-all duration-200',
                'min-h-[72px]',
                item.is_completed && 'bg-gray-50 opacity-60',
                getSwipeBackground()
            )}
            style={{
                transform: `translateX(${swipeState.currentX}px)`,
            }}
        >
            <div className="flex items-center gap-3 p-4">
                {/* LEFT: Checkbox (56x56px touch target) */}
                <ItemCheckbox
                    checked={item.is_completed}
                    onChange={() => onToggle(item.id)}
                />

                {/* CENTER: Item details */}
                <div className="flex-1 min-w-0">
                    <ItemName item={item} />

                    {/* Category chip */}
                    {item.category && (
                        <span className="inline-block mt-1 px-2 py-0.5 text-sm bg-blue-100 text-blue-800 rounded">
                            {getCategoryIcon(item.category)} {item.category}
                        </span>
                    )}
                </div>

                {/* RIGHT: Quantity controls */}
                <QuantityControls
                    item={item}
                    onUpdateQuantity={onUpdateQuantity}
                />
            </div>

            {/* Swipe indicator */}
            {swipeState.isDragging && Math.abs(swipeState.currentX) > 30 && (
                <div className="absolute inset-y-0 left-0 right-0 flex items-center justify-center pointer-events-none">
                    <span className="text-white text-lg font-bold">
                        {swipeState.currentX > 0 ? '✓ Complete' : '✗ Delete'}
                    </span>
                </div>
            )}
        </div>
    );
};

