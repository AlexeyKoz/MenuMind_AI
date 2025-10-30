import { useState, useCallback } from 'react';

interface SwipeState {
    startX: number;
    currentX: number;
    isDragging: boolean;
}

export const useSwipeGestures = (
    itemId: string,
    onSwipeRight: () => void,
    onSwipeLeft: () => void,
    threshold: number = 100
) => {
    const [swipeState, setSwipeState] = useState<SwipeState>({
        startX: 0,
        currentX: 0,
        isDragging: false
    });

    const handleTouchStart = useCallback((e: React.TouchEvent) => {
        setSwipeState({
            startX: e.touches[0].clientX,
            currentX: 0,
            isDragging: true
        });
    }, []);

    const handleTouchMove = useCallback((e: React.TouchEvent) => {
        if (!swipeState.isDragging) return;

        const deltaX = e.touches[0].clientX - swipeState.startX;
        setSwipeState(prev => ({ ...prev, currentX: deltaX }));
    }, [swipeState.isDragging, swipeState.startX]);

    const handleTouchEnd = useCallback(() => {
        if (!swipeState.isDragging) return;

        if (swipeState.currentX > threshold) {
            onSwipeRight();
        } else if (swipeState.currentX < -threshold) {
            onSwipeLeft();
        }

        setSwipeState({ startX: 0, currentX: 0, isDragging: false });
    }, [swipeState, threshold, onSwipeRight, onSwipeLeft]);

    return {
        swipeState,
        handlers: {
            onTouchStart: handleTouchStart,
            onTouchMove: handleTouchMove,
            onTouchEnd: handleTouchEnd
        }
    };
};

