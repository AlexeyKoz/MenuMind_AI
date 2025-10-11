import React, { useState } from 'react';

interface LikeButtonProps {
    recipeId: string;
    initialLiked: boolean;
    initialLikeCount: number;
    onLike: (recipeId: string) => Promise<{ user_liked: boolean; total_likes: number }>;
    size?: 'sm' | 'md' | 'lg';
}

/**
 * LikeButton - Toggle like/unlike for canonical recipes
 * 
 * Features:
 * - Optimistic UI updates
 * - Heart animation on like
 * - Like count display
 */
const LikeButton: React.FC<LikeButtonProps> = ({
    recipeId,
    initialLiked,
    initialLikeCount,
    onLike,
    size = 'md'
}) => {
    const [liked, setLiked] = useState(initialLiked);
    const [likeCount, setLikeCount] = useState(initialLikeCount);
    const [loading, setLoading] = useState(false);
    const [animating, setAnimating] = useState(false);

    const sizeClasses = {
        sm: 'text-lg px-2 py-1',
        md: 'text-xl px-3 py-2',
        lg: 'text-2xl px-4 py-3'
    };

    const handleLike = async () => {
        if (loading) return;

        // Optimistic update
        const previousLiked = liked;
        const previousCount = likeCount;
        setLiked(!liked);
        setLikeCount(liked ? likeCount - 1 : likeCount + 1);

        if (!liked) {
            setAnimating(true);
            setTimeout(() => setAnimating(false), 600);
        }

        setLoading(true);

        try {
            const result = await onLike(recipeId);
            setLiked(result.user_liked);
            setLikeCount(result.total_likes);
        } catch (error) {
            console.error('Failed to toggle like:', error);
            // Revert on error
            setLiked(previousLiked);
            setLikeCount(previousCount);
        } finally {
            setLoading(false);
        }
    };

    return (
        <button
            onClick={handleLike}
            disabled={loading}
            className={`
                ${sizeClasses[size]}
                flex items-center gap-2 rounded-lg
                transition-all duration-200
                ${liked
                    ? 'bg-red-50 text-red-600 hover:bg-red-100'
                    : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                }
                ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                ${animating ? 'animate-bounce' : ''}
            `}
        >
            <svg
                className={`w-5 h-5 transition-transform ${animating ? 'scale-125' : ''}`}
                fill={liked ? 'currentColor' : 'none'}
                stroke="currentColor"
                strokeWidth={liked ? 0 : 2}
                viewBox="0 0 24 24"
            >
                <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                />
            </svg>
            <span className="font-medium">{likeCount}</span>
        </button>
    );
};

export default LikeButton;


