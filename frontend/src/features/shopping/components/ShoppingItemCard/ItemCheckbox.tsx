import React from 'react';
import { Check } from 'lucide-react';
import { TouchTarget } from '../../../../components/mobile/TouchTarget';
import { cn } from '../../../../utils';

interface ItemCheckboxProps {
    checked: boolean;
    onChange: () => void;
}

export const ItemCheckbox: React.FC<ItemCheckboxProps> = ({
    checked,
    onChange
}) => {
    return (
        <TouchTarget
            size={56}
            onClick={onChange}
            className={cn(
                'rounded-lg border-2 transition-all',
                checked
                    ? 'bg-green-500 border-green-600'
                    : 'bg-white border-gray-300 hover:border-gray-400'
            )}
        >
            {checked && <Check className="w-6 h-6 text-white stroke-[3]" />}
        </TouchTarget>
    );
};

