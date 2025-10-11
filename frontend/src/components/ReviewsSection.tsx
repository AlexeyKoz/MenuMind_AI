import React, { useState, useEffect } from 'react';
import StarRating from './StarRating';

interface Review {
    id: string;
    user_username: string;
    user_first_name: string;
    title: string;
    content: string;
    rating: number;
    helpful_count: number;
    user_marked_helpful: boolean;
    created_at: string;
}

interface ReviewsSectionProps {
    recipeId: string;
    currentUserId?: string;
    onGetReviews: (recipeId: string, params?: { ordering?: string; page?: number }) => Promise<{ results: Review[]; count: number }>;
    onAddReview: (recipeId: string, data: { title: string; content: string; rating: number }) => Promise<void>;
    onUpdateReview: (recipeId: string, reviewId: string, data: any) => Promise<void>;
    onDeleteReview: (recipeId: string, reviewId: string) => Promise<void>;
    onMarkHelpful: (recipeId: string, reviewId: string) => Promise<void>;
}

/**
 * ReviewsSection - Display and manage recipe reviews
 * 
 * Features:
 * - View all reviews with pagination
 * - Add new review with star rating
 * - Edit/delete own reviews
 * - Mark reviews as helpful
 * - Sort by helpful, recent, highest rated
 */
const ReviewsSection: React.FC<ReviewsSectionProps> = ({
    recipeId,
    currentUserId,
    onGetReviews,
    onAddReview,
    onUpdateReview,
    onDeleteReview,
    onMarkHelpful
}) => {
    const [reviews, setReviews] = useState<Review[]>([]);
    const [totalReviews, setTotalReviews] = useState(0);
    const [loading, setLoading] = useState(false);
    const [showAddReview, setShowAddReview] = useState(false);
    const [editingReview, setEditingReview] = useState<string | null>(null);
    const [sortBy, setSortBy] = useState<string>('-helpful_count');

    // Form state
    const [formData, setFormData] = useState({
        title: '',
        content: '',
        rating: 5
    });

    useEffect(() => {
        loadReviews();
    }, [recipeId, sortBy]);

    const loadReviews = async () => {
        setLoading(true);
        try {
            const result = await onGetReviews(recipeId, { ordering: sortBy });
            setReviews(result.results);
            setTotalReviews(result.count);
        } catch (error) {
            console.error('Failed to load reviews:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmitReview = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.title.trim() || !formData.content.trim()) return;

        try {
            if (editingReview) {
                await onUpdateReview(recipeId, editingReview, formData);
            } else {
                await onAddReview(recipeId, formData);
            }

            setFormData({ title: '', content: '', rating: 5 });
            setShowAddReview(false);
            setEditingReview(null);
            await loadReviews();
        } catch (error: any) {
            alert(error.message || 'Failed to submit review');
        }
    };

    const handleDeleteReview = async (reviewId: string) => {
        if (!window.confirm('Are you sure you want to delete this review?')) return;

        try {
            await onDeleteReview(recipeId, reviewId);
            await loadReviews();
        } catch (error) {
            console.error('Failed to delete review:', error);
        }
    };

    const handleMarkHelpful = async (reviewId: string) => {
        try {
            await onMarkHelpful(recipeId, reviewId);
            // Update local state optimistically
            setReviews(reviews.map(review =>
                review.id === reviewId
                    ? {
                        ...review,
                        user_marked_helpful: !review.user_marked_helpful,
                        helpful_count: review.user_marked_helpful
                            ? review.helpful_count - 1
                            : review.helpful_count + 1
                    }
                    : review
            ));
        } catch (error) {
            console.error('Failed to mark helpful:', error);
        }
    };

    const startEdit = (review: Review) => {
        setFormData({
            title: review.title,
            content: review.content,
            rating: review.rating
        });
        setEditingReview(review.id);
        setShowAddReview(true);
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <h3 className="text-2xl font-bold text-gray-900">
                    Reviews ({totalReviews})
                </h3>
                <button
                    onClick={() => setShowAddReview(!showAddReview)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    {showAddReview ? 'Cancel' : 'Write Review'}
                </button>
            </div>

            {/* Add/Edit Review Form */}
            {showAddReview && (
                <form onSubmit={handleSubmitReview} className="bg-gray-50 rounded-lg p-6 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Rating
                        </label>
                        <div className="flex gap-2">
                            {[1, 2, 3, 4, 5].map((star) => (
                                <button
                                    key={star}
                                    type="button"
                                    onClick={() => setFormData({ ...formData, rating: star })}
                                    className="focus:outline-none"
                                >
                                    <svg
                                        className="w-8 h-8"
                                        fill={star <= formData.rating ? '#FCD34D' : 'none'}
                                        stroke={star <= formData.rating ? '#FCD34D' : '#D1D5DB'}
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
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Title
                        </label>
                        <input
                            type="text"
                            value={formData.title}
                            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                            placeholder="Sum up your review"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Review
                        </label>
                        <textarea
                            value={formData.content}
                            onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                            placeholder="Share your thoughts about this recipe"
                            rows={4}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                    >
                        {editingReview ? 'Update Review' : 'Submit Review'}
                    </button>
                </form>
            )}

            {/* Sort Options */}
            <div className="flex gap-2">
                <button
                    onClick={() => setSortBy('-helpful_count')}
                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${sortBy === '-helpful_count'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                >
                    Most Helpful
                </button>
                <button
                    onClick={() => setSortBy('-created_at')}
                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${sortBy === '-created_at'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                >
                    Most Recent
                </button>
                <button
                    onClick={() => setSortBy('-rating')}
                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${sortBy === '-rating'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                >
                    Highest Rated
                </button>
            </div>

            {/* Reviews List */}
            {loading ? (
                <div className="text-center py-8 text-gray-500">Loading reviews...</div>
            ) : reviews.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                    No reviews yet. Be the first to review!
                </div>
            ) : (
                <div className="space-y-4">
                    {reviews.map((review) => (
                        <div key={review.id} className="bg-white rounded-lg border border-gray-200 p-6">
                            {/* Review Header */}
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="font-semibold text-gray-900">
                                            {review.user_first_name || review.user_username}
                                        </span>
                                        <div className="flex items-center">
                                            {[...Array(5)].map((_, i) => (
                                                <svg
                                                    key={i}
                                                    className="w-4 h-4"
                                                    fill={i < review.rating ? '#FCD34D' : 'none'}
                                                    stroke={i < review.rating ? '#FCD34D' : '#D1D5DB'}
                                                    strokeWidth={2}
                                                    viewBox="0 0 24 24"
                                                >
                                                    <path
                                                        strokeLinecap="round"
                                                        strokeLinejoin="round"
                                                        d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                                                    />
                                                </svg>
                                            ))}
                                        </div>
                                    </div>
                                    <h4 className="font-semibold text-lg text-gray-900 mb-1">
                                        {review.title}
                                    </h4>
                                    <p className="text-sm text-gray-500">
                                        {new Date(review.created_at).toLocaleDateString()}
                                    </p>
                                </div>

                                {/* Edit/Delete buttons for own reviews */}
                                {review.user_username === currentUserId && (
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => startEdit(review)}
                                            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                                        >
                                            Edit
                                        </button>
                                        <button
                                            onClick={() => handleDeleteReview(review.id)}
                                            className="text-red-600 hover:text-red-700 text-sm font-medium"
                                        >
                                            Delete
                                        </button>
                                    </div>
                                )}
                            </div>

                            {/* Review Content */}
                            <p className="text-gray-700 mb-4">{review.content}</p>

                            {/* Helpful Button */}
                            <button
                                onClick={() => handleMarkHelpful(review.id)}
                                className={`flex items-center gap-2 px-3 py-1 rounded-lg text-sm transition-colors ${review.user_marked_helpful
                                    ? 'bg-blue-50 text-blue-600'
                                    : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                                    }`}
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                                </svg>
                                Helpful ({review.helpful_count})
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ReviewsSection;

