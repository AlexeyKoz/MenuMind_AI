import React, { useState, useEffect } from 'react';
import { Plus, MinusCircle, PlusCircle } from 'lucide-react';
import { BottomSheet } from '../../../components/mobile/BottomSheet';
import { TouchTarget } from '../../../components/mobile/TouchTarget';
import { useTranslation } from 'react-i18next';
import { cn } from '../../../lib/utils';

interface QuickAddDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    onAddItem: (item: { name: string; quantity: number; category: string }) => void;
    recentItems?: Array<{ id: string; name: string }>;
}

const CATEGORIES = [
    { id: 'produce', icon: '🥬', label: 'Produce' },
    { id: 'dairy', icon: '🥛', label: 'Dairy' },
    { id: 'meat', icon: '🥩', label: 'Meat' },
    { id: 'bakery', icon: '🍞', label: 'Bakery' },
    { id: 'frozen', icon: '🧊', label: 'Frozen' },
    { id: 'pantry', icon: '🥫', label: 'Pantry' },
    { id: 'beverages', icon: '🥤', label: 'Beverages' },
    { id: 'other', icon: '📦', label: 'Other' }
];

export const QuickAddDrawer: React.FC<QuickAddDrawerProps> = ({
    isOpen,
    onClose,
    onAddItem,
    recentItems = []
}) => {
    const { t } = useTranslation();
    const [itemName, setItemName] = useState('');
    const [quantity, setQuantity] = useState(1);
    const [category, setCategory] = useState('other');

    useEffect(() => {
        if (isOpen) {
            // Reset form when opened
            setItemName('');
            setQuantity(1);
            setCategory('other');
        }
    }, [isOpen]);

    const handleAdd = () => {
        if (!itemName.trim()) return;

        onAddItem({
            name: itemName.trim(),
            quantity,
            category
        });

        // Close drawer and reset
        onClose();
    };

    const handleQuickAdd = (item: { id: string; name: string }) => {
        onAddItem({
            name: item.name,
            quantity: 1,
            category: 'other'
        });
    };

    return (
        <BottomSheet
            isOpen={isOpen}
            onClose={onClose}
            title={t('add_item', 'Add Item')}
            snapPoints={[0.5, 0.9]}
        >
            <div className="px-6 py-4">
                {/* Item Name Input */}
                <input
                    type="text"
                    value={itemName}
                    onChange={(e) => setItemName(e.target.value)}
                    placeholder={t('item_name_placeholder', 'Item name...')}
                    className="w-full h-14 px-4 text-lg border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                    autoFocus
                    enterKeyHint="done"
                    onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
                />

                {/* Quantity Picker */}
                <div className="mt-6 flex items-center justify-center gap-4">
                    <TouchTarget
                        size={56}
                        onClick={() => setQuantity(Math.max(1, quantity - 1))}
                        disabled={quantity <= 1}
                    >
                        <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center">
                            <MinusCircle className="w-8 h-8 text-gray-600" />
                        </div>
                    </TouchTarget>

                    <div className="text-center min-w-[100px]">
                        <div className="text-4xl font-bold text-gray-900">{quantity}</div>
                        <div className="text-sm text-gray-500">{t('quantity', 'Quantity')}</div>
                    </div>

                    <TouchTarget
                        size={56}
                        onClick={() => setQuantity(quantity + 1)}
                    >
                        <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                            <PlusCircle className="w-8 h-8 text-blue-600" />
                        </div>
                    </TouchTarget>
                </div>

                {/* Category Selection */}
                <div className="mt-6">
                    <h3 className="text-sm font-medium text-gray-700 mb-3">
                        {t('category', 'Category')}
                    </h3>
                    <div className="flex overflow-x-auto gap-2 pb-2 hide-scrollbar">
                        {CATEGORIES.map(cat => (
                            <button
                                key={cat.id}
                                onClick={() => setCategory(cat.id)}
                                className={cn(
                                    'flex-shrink-0 px-4 py-2 rounded-full whitespace-nowrap text-sm font-medium transition-all',
                                    category === cat.id
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                )}
                            >
                                <span className="mr-1">{cat.icon}</span>
                                {t(`category.${cat.id}`, cat.label)}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Add Button */}
                <button
                    onClick={handleAdd}
                    disabled={!itemName.trim()}
                    className="w-full h-14 mt-6 bg-blue-600 text-white text-lg font-semibold rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed transition-all active:scale-98"
                >
                    {t('add_to_list', 'Add to List')}
                </button>

                {/* Recent Items */}
                {recentItems.length > 0 && (
                    <div className="mt-6">
                        <h3 className="text-sm font-medium text-gray-700 mb-3">
                            {t('recent_items', 'Recent Items')}
                        </h3>
                        <div className="flex flex-wrap gap-2">
                            {recentItems.slice(0, 6).map(item => (
                                <button
                                    key={item.id}
                                    onClick={() => handleQuickAdd(item)}
                                    className="px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-full text-sm hover:bg-gray-100 transition-colors"
                                >
                                    + {item.name}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </BottomSheet>
    );
};

