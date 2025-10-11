import React, { useState } from 'react';

interface StarRatingProps {
    recipeId: string;
    initialRating?: number;
    averageRating: number;
    totalRatings: number;
    onRate?: (recipeId: string, rating: number) => Promise<void>;
    readonly?: boolean;
    size?: 'sm' | 'md' | 'lg';
}

/**
 * StarRating - Display and interact with recipe ratings
 * 
 * Features:
 * - Interactive star rating (1-5 stars)
 * - Display average rating
 * - Hover preview
 * - Read-only mode for display
 */
const StarRating: React.FC<StarRatingProps> = ({
    recipeId,
    initialRating = 0,
    averageRating,
    totalRatings,
    onRate,
    readonly = false,
    size = 'md'
}) => {
    const [userRating, setUserRating] = useState(initialRating);
    const [hoverRating, setHoverRating] = useState(0);
    const [loading, setLoading] = useState(false);

    const sizeClasses = {
        sm: 'w-4 h-4',
        md: 'w-6 h-6',
        lg: 'w-8 h-8'
    };

    const handleRate = async (rating: number) => {
        if (readonly || loading || !onRate) return;

        setLoading(true);
        try {
            await onRate(recipeId, rating);
            setUserRating(rating);
        } catch (error) {
            console.error('Failed to rate recipe:', error);
        } finally {
            setLoading(false);
        }
    };

    const displayRating = hoverRating || userRating || Number(averageRating);

    return (
        <div className="flex flex-col gap-1">
            {/* Stars */}
            <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                    <button
                        key={star}
                        onClick={() => handleRate(star)}
                        onMouseEnter={() => !readonly && setHoverRating(star)}
                        onMouseLeave={() => !readonly && setHoverRating(0)}
                        disabled={readonly || loading}
                        className={`
                            ${readonly ? 'cursor-default' : 'cursor-pointer hover:scale-110'}
                            transition-transform duration-150
                            ${loading ? 'opacity-50' : ''}
                        `}
                    >
                        <svg
                            className={`${sizeClasses[size]} transition-colors duration-150`}
                            fill={star <= displayRating ? '#FCD34D' : 'none'}
                            stroke={star <= displayRating ? '#FCD34D' : '#D1D5DB'}
                            strokeWidth={2}
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                            />
                        </svg>
                    </button>
                ))}
            </div>

            {/* Rating info */}
            <div className="text-sm text-gray-600">
                {userRating > 0 ? (
                    <span className="font-medium text-blue-600">
                        You rated: {userRating}/5
                    </span>
                ) : (
                    <span>
                        {Number(averageRating).toFixed(1)} ({totalRatings} {totalRatings === 1 ? 'rating' : 'ratings'})
                    </span>
                )}
            </div>
        </div>
    );
};

export default StarRating;

