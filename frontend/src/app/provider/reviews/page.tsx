'use client';

/**
 * Provider Reviews Page
 *
 * Shows reviews received by the provider with ratings and feedback.
 */

import { useEffect } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/context/AuthContext';
import { useApi } from '@/hooks/useApi';
import { useTranslation } from 'react-i18next';

interface Review {
  id: string;
  rating: number;
  comment?: string;
  complaint_category?: string;
  created_at: string;
  farmer_name?: string;
}

interface ReviewData {
  aggregates: {
    average_rating: number;
    total_count: number;
  };
  reviews: Review[];
}

export default function ProviderReviewsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const reviewsApi = useApi<ReviewData>();

  useEffect(() => {
    if (user?.id) {
      reviewsApi.execute(`/api/v1/reviews?provider_id=${user.id}`).catch(() => {});
    }
  }, [user?.id]);

  const reviews = reviewsApi.data?.reviews || [];
  const aggregates = reviewsApi.data?.aggregates || { average_rating: 0, total_count: 0 };
  const avgRating = reviews.length > 0
    ? aggregates.average_rating.toFixed(1)
    : '—';

  const renderStars = (rating: number) => {
    return '★'.repeat(Math.round(rating)) + '☆'.repeat(5 - Math.round(rating));
  };

  return (
    <ProtectedRoute requiredRole={["provider", "admin"]}>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">{t('provider.reviews.my_reviews')}</h1>
          <p className="text-gray-400 mt-1">{t('provider.reviews.feedback_from_farmers_you')}</p>
        </div>

        {/* Summary */}
        <div className="card flex items-center gap-6">
          <div className="text-center">
            <p className="text-4xl font-bold text-cultivax-primary">{avgRating}</p>
            <p className="text-yellow-400 text-lg">{avgRating !== '—' ? renderStars(parseFloat(avgRating)) : ''}</p>
            <p className="text-sm text-gray-400 mt-1">{reviews.length} review{reviews.length !== 1 ? 's' : ''}</p>
          </div>
          <div className="flex-1 space-y-1">
            {[5, 4, 3, 2, 1].map((star) => {
              const count = reviews.filter((r) => Math.round(r.rating) === star).length;
              const pct = reviews.length > 0 ? (count / reviews.length) * 100 : 0;
              return (
                <div key={star} className="flex items-center gap-2 text-sm">
                  <span className="text-gray-400 w-3">{star}</span>
                  <span className="text-yellow-400">★</span>
                  <div className="flex-1 h-2 bg-cultivax-card rounded-full overflow-hidden">
                    <div
                      className="h-full bg-yellow-400 rounded-full transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-8">{count}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Reviews List */}
        {reviewsApi.loading && (
          <div className="card text-center py-8">
            <div className="inline-block w-8 h-8 border-2 border-cultivax-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!reviewsApi.loading && reviews.length === 0 && (
          <div className="card text-center py-12 text-gray-500">
            <p className="text-5xl mb-4">⭐</p>
            <p className="text-lg font-medium">{t('provider.reviews.no_reviews_yet')}</p>
            <p className="text-sm mt-1">{t('provider.reviews.reviews_will_appear_once')}</p>
          </div>
        )}

        {reviews.length > 0 && (
          <div className="space-y-3">
            {reviews.map((review) => (
              <div key={review.id} className="card">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="text-yellow-400">{renderStars(review.rating)}</p>
                    {review.farmer_name && (
                      <p className="text-sm text-gray-400 mt-1">by {review.farmer_name}</p>
                    )}
                  </div>
                  <p className="text-xs text-gray-500">{new Date(review.created_at).toLocaleDateString()}</p>
                </div>
                {review.comment && <p className="text-sm">{review.comment}</p>}
                {review.complaint_category && (
                  <span className="inline-block mt-2 text-xs px-2 py-1 rounded-full bg-red-500/20 text-red-400">
                    {review.complaint_category}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
