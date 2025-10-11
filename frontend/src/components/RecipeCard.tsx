import React from 'react';
import LikeButton from './LikeButton';
import StarRating from './StarRating';

interface RecipeCardProps {
    recipe: {
        id: string;
        name: string;
        description: string;
        cuisine?: string;
        difficulty?: string;
        total_time_minutes?: number;
        servings?: number;
        diet_labels?: string[];
        source_type?: string;
        average_rating: number;
        total_ratings: number;
        total_saves: number;
        total_cooked: number;
        user_liked?: boolean;
        user_rating?: number;
        user_has_fork?: boolean;  // Keep property but don't display it
        original_creator_username?: string;
    };
    onLike: (recipeId: string) => Promise<{ user_liked: boolean; total_likes: number }>;
    onRate?: (recipeId: string, rating: number) => Promise<void>;
    onClick?: (recipeId: string) => void;
    showStats?: boolean;
}

/**
 * RecipeCard - Display canonical recipe with social features
 * 
 * Features:
 * - Recipe metadata (name, cuisine, difficulty, time)
 * - Like button with count
 * - Star rating display
 * - Diet labels
 * - Source attribution
 * - Recipe statistics
 */
const RecipeCard: React.FC<RecipeCardProps> = ({
    recipe,
    onLike,
    onRate,
    onClick,
    showStats = true
}) => {
    const difficultyColors = {
        beginner: 'bg-green-100 text-green-800',
        intermediate: 'bg-yellow-100 text-yellow-800',
        advanced: 'bg-red-100 text-red-800'
    };

    const sourceTypeIcons = {
        ai_generated: '🤖',
        user_created: '👨‍🍳',
        community_curated: '🌟',
        web_scraped: '🌐'
    };

    const sourceTypeLabels = {
        ai_generated: 'AI Generated',
        user_created: 'User Created',
        community_curated: 'Community Curated',
        web_scraped: 'From Web'
    };

    return (
        <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300 overflow-hidden">
            {/* Header with source badge */}
            <div className="relative bg-gradient-to-br from-blue-500 to-purple-600 p-6 text-white">
                {recipe.source_type && (
                    <div className="absolute top-4 right-4 bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full text-xs font-medium">
                        {sourceTypeIcons[recipe.source_type as keyof typeof sourceTypeIcons]} {sourceTypeLabels[recipe.source_type as keyof typeof sourceTypeLabels]}
                    </div>
                )}

                <h3
                    className="text-2xl font-bold mb-2 cursor-pointer hover:underline"
                    onClick={() => onClick?.(recipe.id)}
                >
                    {recipe.name}
                </h3>

                {recipe.cuisine && (
                    <span className="inline-block bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full text-sm">
                        {recipe.cuisine}
                    </span>
                )}
            </div>

            {/* Content */}
            <div className="p-6 space-y-4">
                {/* Description */}
                {recipe.description && (
                    <p className="text-gray-600 line-clamp-2">
                        {recipe.description}
                    </p>
                )}

                {/* Metadata */}
                <div className="flex flex-wrap gap-2">
                    {recipe.difficulty && (
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${difficultyColors[recipe.difficulty as keyof typeof difficultyColors] || 'bg-gray-100 text-gray-800'}`}>
                            {recipe.difficulty}
                        </span>
                    )}

                    {recipe.total_time_minutes && (
                        <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            ⏱️ {recipe.total_time_minutes} min
                        </span>
                    )}

                    {recipe.servings && (
                        <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            🍽️ {recipe.servings} servings
                        </span>
                    )}
                </div>

                {/* Diet Labels */}
                {recipe.diet_labels && recipe.diet_labels.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                        {recipe.diet_labels.slice(0, 4).map((label) => (
                            <span
                                key={label}
                                className="px-2 py-1 bg-green-50 text-green-700 rounded text-xs font-medium"
                            >
                                {label}
                            </span>
                        ))}
                        {recipe.diet_labels.length > 4 && (
                            <span className="px-2 py-1 bg-gray-50 text-gray-600 rounded text-xs font-medium">
                                +{recipe.diet_labels.length - 4} more
                            </span>
                        )}
                    </div>
                )}

                {/* Social Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    <div className="flex items-center gap-3">
                        <LikeButton
                            recipeId={recipe.id}
                            initialLiked={recipe.user_liked || false}
                            initialLikeCount={recipe.total_saves}
                            onLike={onLike}
                            size="sm"
                        />

                        <StarRating
                            recipeId={recipe.id}
                            initialRating={recipe.user_rating}
                            averageRating={recipe.average_rating}
                            totalRatings={recipe.total_ratings}
                            onRate={onRate}
                            readonly={!onRate}
                            size="sm"
                        />
                    </div>
                </div>

                {/* Statistics */}
                {showStats && (
                    <div className="flex items-center gap-4 text-sm text-gray-600 pt-2">
                        <div className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                            </svg>
                            <span>{recipe.total_saves} saved</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span>{recipe.total_cooked} cooked</span>
                        </div>
                    </div>
                )}

                {/* Attribution */}
                {recipe.original_creator_username && recipe.source_type === 'user_created' && (
                    <div className="text-xs text-gray-500 pt-2 border-t border-gray-100">
                        Created by <span className="font-medium">{recipe.original_creator_username}</span>
                    </div>
                )}
            </div>
        </div>
    );
};

export default RecipeCard;


