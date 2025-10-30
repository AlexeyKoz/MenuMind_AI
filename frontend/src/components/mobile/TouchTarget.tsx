import React, { ReactNode } from 'react';
import { cn } from '../../lib/utils';

interface TouchTargetProps {
    size?: 44 | 48 | 56; // Standard touch sizes
    children: ReactNode;
    className?: string;
    onClick?: () => void;
    disabled?: boolean;
}

export const TouchTarget: React.FC<TouchTargetProps> = ({
    size = 44,
    children,
    className,
    onClick,
    disabled = false
}) => {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={cn(
                'relative inline-flex items-center justify-center',
                'touch-manipulation', // Improves touch response
                'transition-transform active:scale-95',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                className
            )}
            style={{
                minWidth: `${size}px`,
                minHeight: `${size}px`,
            }}
        >
            {children}
        </button>
    );
};

