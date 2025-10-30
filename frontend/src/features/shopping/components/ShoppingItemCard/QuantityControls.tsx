import React from 'react';
import { MinusCircle, PlusCircle } from 'lucide-react';
import { TouchTarget } from '../../../../components/mobile/TouchTarget';
import { ShoppingItem } from '../../types/shopping.types';

interface QuantityControlsProps {
    item: ShoppingItem;
    onUpdateQuantity: (id: string, quantity: number) => void;
}

export const QuantityControls: React.FC<QuantityControlsProps> = ({
    item,
    onUpdateQuantity
}) => {
    const handleDecrement = () => {
        if (item.quantity > 1) {
            onUpdateQuantity(item.id, item.quantity - 1);
        }
    };

    const handleIncrement = () => {
        onUpdateQuantity(item.id, item.quantity + 1);
    };

    return (
        <div className="flex items-center gap-2">
            <TouchTarget
                size={44}
                onClick={handleDecrement}
                disabled={item.quantity <= 1}
            >
                <MinusCircle className="w-5 h-5 text-gray-600" />
            </TouchTarget>

            <span className="text-2xl font-bold min-w-[32px] text-center">
                {item.quantity}
            </span>

            <TouchTarget
                size={44}
                onClick={handleIncrement}
            >
                <PlusCircle className="w-5 h-5 text-blue-600" />
            </TouchTarget>
        </div>
    );
};

