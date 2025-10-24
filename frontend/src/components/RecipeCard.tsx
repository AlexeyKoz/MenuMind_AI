import React from 'react';
import { useTranslation } from 'react-i18next';
import LikeButton from './LikeButton';
import StarRating from './StarRating';
import AllergenWarning from './AllergenWarning';
import { useAuth } from '../contexts/AuthContext';

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
        allergens?: string[];
        source_type?: string;
        average_rating: number;
        total_ratings: number;
        total_saves: number;
        total_cooked: number;
        user_liked?: boolean;
        user_rating?: number;
        user_has_fork?: boolean;  // Keep property but don't display it
        original_creator_username?: string;
        original_creator_first_name?: string;
        original_creator_last_name?: string;
        original_creator_color?: string;
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
    const { t } = useTranslation();

    // Helper function to convert snake_case to camelCase for translation keys
    const toCamelCase = (str: string) => {
        return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
    };

    const difficultyColors = {
        beginner: 'bg-green-100 text-green-800',
        intermediate: 'bg-yellow-100 text-yellow-800',
        advanced: 'bg-red-100 text-red-800'
    };

    const sourceTypeIcons = {
        ai_generated: '🤖',
        user_created: '👨‍🍳',
        community_curated: '🌟'
    };

    const sourceTypeLabels = {
        ai_generated: t('discover.recipeCard.sourceTypes.aiGenerated'),
        user_created: t('discover.recipeCard.sourceTypes.userCreated'),
        community_curated: t('discover.recipeCard.sourceTypes.communityCurated')
    };

    return (
        <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300 overflow-hidden flex flex-col h-full">
            {/* Header with source badge */}
            <div className="relative bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                {/* Top section - invisible space for badge */}
                <div className="h-10 flex items-center justify-end px-6 pt-3">
                    {/* Source badge - show user info for user_created, else show source type */}
                    {recipe.source_type === 'user_created' && recipe.original_creator_username ? (
                        <div className="flex items-center gap-2 bg-white/20 backdrop-blur-sm px-3 py-1.5 rounded-full text-xs font-medium max-w-[220px]">
                            {/* User avatar circle */}
                            <div
                                className="w-6 h-6 rounded-full flex items-center justify-center text-white font-semibold text-xs flex-shrink-0"
                                style={{ backgroundColor: recipe.original_creator_color || '#4F46E5' }}
                            >
                                {(recipe.original_creator_first_name?.[0] || recipe.original_creator_username?.[0] || '?').toUpperCase()}
                            </div>
                            {/* User name */}
                            <span className="truncate">
                                {recipe.original_creator_first_name || recipe.original_creator_username}
                            </span>
                        </div>
                    ) : recipe.source_type && (
                        <div className="bg-white/20 backdrop-blur-sm px-3 py-1.5 rounded-full text-xs font-medium max-w-[220px] whitespace-nowrap overflow-hidden">
                            <div className="flex items-center gap-1.5">
                                <span className="flex-shrink-0">{sourceTypeIcons[recipe.source_type as keyof typeof sourceTypeIcons]}</span>
                                <span className="truncate">{sourceTypeLabels[recipe.source_type as keyof typeof sourceTypeLabels]}</span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Bottom section - recipe name and cuisine */}
                <div className="px-6 pb-6 pt-2">
                    <h3
                        className="text-xl font-bold mb-2 cursor-pointer hover:underline leading-snug"
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
            </div>

            {/* Content */}
            <div className="p-6 space-y-4 flex-1 flex flex-col">
                {/* Description */}
                {recipe.description && (
                    <p className="text-gray-600 line-clamp-2 h-10">
                        {recipe.description}
                    </p>
                )}

                {/* Metadata */}
                <div className="flex flex-wrap gap-2 min-h-[32px]">
                    {recipe.difficulty && (
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${difficultyColors[recipe.difficulty as keyof typeof difficultyColors] || 'bg-gray-100 text-gray-800'}`}>
                            {t(`discover.difficulties.${recipe.difficulty}`, { defaultValue: recipe.difficulty })}
                        </span>
                    )}

                    {recipe.total_time_minutes && (
                        <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            ⏱️ {recipe.total_time_minutes} {t('discover.recipeCard.min')}
                        </span>
                    )}

                    {recipe.servings && (
                        <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            🍽️ {recipe.servings} {t('discover.recipeCard.servings')}
                        </span>
                    )}
                </div>

                {/* Diet Labels */}
                {recipe.diet_labels && recipe.diet_labels.length > 0 && (
                    <div className="flex flex-wrap gap-2 min-h-[28px]">
                        {recipe.diet_labels.slice(0, 4).map((label) => {
                            // Convert snake_case to camelCase (e.g., dairy_free -> dairyFree)
                            const translationKey = toCamelCase(label);
                            return (
                                <span
                                    key={label}
                                    className="px-2 py-1 bg-green-50 text-green-700 rounded text-xs font-medium"
                                >
                                    {t(`discover.dietLabels.${translationKey}`, { defaultValue: label })}
                                </span>
                            );
                        })}
                        {recipe.diet_labels.length > 4 && (
                            <span className="px-2 py-1 bg-gray-50 text-gray-600 rounded text-xs font-medium">
                                +{recipe.diet_labels.length - 4} {t('discover.recipeCard.more')}
                            </span>
                        )}
                    </div>
                )}

                {/* Allergen Warning */}
                {recipe.allergens && recipe.allergens.length > 0 && (
                    <AllergenWarning
                        allergens={recipe.allergens}
                        userAllergies={[]} // Will be populated from user context
                        className="mt-3"
                    />
                )}

                {/* Spacer to push content to bottom */}
                <div className="flex-1"></div>

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
                            <span>{recipe.total_saves} {t('discover.recipeCard.saved')}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span>{recipe.total_cooked} {t('discover.recipeCard.cooked')}</span>
                        </div>
                    </div>
                )}

                {/* Attribution */}
                {recipe.original_creator_username && recipe.source_type === 'user_created' && (
                    <div className="text-xs text-gray-500 pt-2 border-t border-gray-100">
                        {t('discover.recipeCard.createdBy')} <span className="font-medium">{recipe.original_creator_username}</span>
                    </div>
                )}
            </div>
        </div>
    );
};

export default RecipeCard;


