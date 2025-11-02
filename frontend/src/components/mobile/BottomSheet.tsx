import React, { ReactNode, useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { cn } from '../../utils';
import { TouchTarget } from './TouchTarget';

interface BottomSheetProps {
    isOpen: boolean;
    onClose: () => void;
    children: ReactNode;
    title?: string;
    snapPoints?: number[]; // [0.4, 0.9] = 40% or 90% of screen
}

export const BottomSheet: React.FC<BottomSheetProps> = ({
    isOpen,
    onClose,
    children,
    title,
    snapPoints = [0.4, 0.9]
}) => {
    const [currentSnap, setCurrentSnap] = useState(0);
    const [startY, setStartY] = useState(0);
    const [currentY, setCurrentY] = useState(0);

    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
        return () => {
            document.body.style.overflow = '';
        };
    }, [isOpen]);

    const handleTouchStart = (e: React.TouchEvent) => {
        setStartY(e.touches[0].clientY);
    };

    const handleTouchMove = (e: React.TouchEvent) => {
        setCurrentY(e.touches[0].clientY);
    };

    const handleTouchEnd = () => {
        const deltaY = currentY - startY;
        if (deltaY > 50) {
            // Swipe down significantly - close
            onClose();
        } else if (deltaY < -50 && currentSnap < snapPoints.length - 1) {
            // Swipe up - expand to next snap point
            setCurrentSnap(currentSnap + 1);
        }
        setStartY(0);
        setCurrentY(0);
    };

    if (!isOpen) return null;

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/50 z-40 transition-opacity"
                onClick={onClose}
            />

            {/* Bottom Sheet */}
            <div
                className={cn(
                    'fixed bottom-0 left-0 right-0 z-50',
                    'bg-white rounded-t-3xl shadow-2xl',
                    'transition-transform duration-300 ease-out',
                    'safe-area-inset-bottom'
                )}
                style={{
                    height: `${snapPoints[currentSnap] * 100}vh`,
                    transform: isOpen ? 'translateY(0)' : 'translateY(100%)'
                }}
                onTouchStart={handleTouchStart}
                onTouchMove={handleTouchMove}
                onTouchEnd={handleTouchEnd}
            >
                {/* Drag Handle */}
                <div className="flex justify-center pt-3 pb-2">
                    <div className="w-12 h-1.5 bg-gray-300 rounded-full" />
                </div>

                {/* Header */}
                {title && (
                    <div className="flex items-center justify-between px-6 pb-4 border-b">
                        <h2 className="text-xl font-bold">{title}</h2>
                        <TouchTarget size={44} onClick={onClose}>
                            <X className="w-6 h-6" />
                        </TouchTarget>
                    </div>
                )}

                {/* Content */}
                <div className="overflow-y-auto h-full pb-8">
                    {children}
                </div>
            </div>
        </>
    );
};

