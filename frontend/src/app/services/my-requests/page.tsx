'use client';

import { useState } from 'react';
import { useFetch } from '@/hooks/useFetch';
import { useApi } from '@/hooks/useApi';
import { Clock, CheckCircle2, AlertTriangle, Loader2, Play, Check, X, MapPin, Star } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import Badge from '@/components/Badge';
import Link from 'next/link';
import clsx from 'clsx';
import { useTranslation } from 'react-i18next';

export default function FarmerMyRequestsPage() {
  const { t } = useTranslation();
  const api = useApi();
  const { data, loading, error, refetch } = useFetch('/api/v1/service-requests?per_page=50');
  const requests = data?.items || [];
  
  // Review Modal State
  const [reviewReqId, setReviewReqId] = useState<string | null>(null);
  const [rating, setRating] = useState<number>(5);
  const [comment, setComment] = useState('');
  const [complaintCategory, setComplaintCategory] = useState<string>('');

  const handleCancel = async (id: string) => {
    if (!confirm('Are you sure you want to cancel this request?')) return;
    try {
      await api.execute(`/api/v1/service-requests/${id}/cancel`, { method: 'PUT' });
      refetch();
    } catch (err) {
      console.error('Failed to cancel request:', err);
    }
  };

  const handleSubmitReview = async () => {
    if (!reviewReqId) return;
    try {
      await api.execute('/api/v1/reviews', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          request_id: reviewReqId,
          rating,
          comment: comment || null,
          complaint_category: complaintCategory || null,
        }),
      });
      setReviewReqId(null);
      setRating(5);
      setComment('');
      setComplaintCategory('');
      refetch();
    } catch (err) {
      console.error('Failed to submit review:', err);
    }
  };

  return (
    <ProtectedRoute requiredRole="farmer">
      <div className="animate-fade-in max-w-5xl mx-auto py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-m3-on-surface">{t('services.my-requests.my_service_requests')}</h1>
          <p className="text-m3-on-surface-variant mt-2">{t('services.my-requests.manage_your_requested_agricultural')}</p>
        </div>

        {error && (
          <div className="card p-5 mb-6 border border-red-500/20 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-red-400">{t('services.my-requests.failed_to_load_requests')}</p>
              <p className="text-xs text-cultivax-text-muted">{error}</p>
            </div>
          </div>
        )}

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-card p-6 border border-m3-outline-variant/10 rounded-2xl animate-pulse">
                <div className="h-6 w-48 bg-m3-surface-container-highest rounded mb-4" />
                <div className="h-4 w-32 bg-m3-surface-container-highest rounded mb-2" />
                <div className="h-4 w-24 bg-m3-surface-container-highest rounded" />
              </div>
            ))}
          </div>
        ) : requests.length === 0 ? (
          <div className="glass-card text-center py-16 rounded-2xl border border-m3-outline-variant/10">
            <Clock className="w-12 h-12 text-m3-on-surface-variant mx-auto mb-4 opacity-40" />
            <p className="text-lg font-semibold text-m3-on-surface">{t('services.my-requests.no_service_requests_found')}</p>
            <p className="text-m3-on-surface-variant text-sm mt-2 max-w-md mx-auto">{t('services.my-requests.you_haven_t_requested')}</p>
            <Link href="/services" className="btn-primary mt-6 inline-block">{t('services.my-requests.browse_providers')}</Link>
          </div>
        ) : (
          <div className="space-y-4">
            {requests.map((req: any) => (
              <div key={req.id} className="glass-card p-6 border border-m3-outline-variant/10 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-6 transition-all hover:bg-m3-surface-container-high/50">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-bold text-m3-on-surface flex items-center gap-2">
                      <span className="capitalize">{req.service_type.replace('_', ' ')}</span>
                    </h3>
                    <Badge variant={
                      req.status === 'Completed' ? 'green' : 
                      req.status === 'InProgress' ? 'blue' : 
                      req.status === 'Cancelled' ? 'red' : 'amber'
                    }>
                      {req.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-m3-on-surface-variant">
                    Targeted Region: {req.region || '—'}
                  </p>
                  <p className="text-xs text-m3-on-surface-variant/70 font-mono">
                    Requested: {new Date(req.created_at).toLocaleDateString()}
                  </p>
                </div>
                
                <div className="flex items-center gap-4">
                  {req.agreed_price && (
                    <div className="text-right">
                      <p className="text-[10px] uppercase font-bold tracking-wider text-m3-on-surface-variant">{t('services.my-requests.agreed_price')}</p>
                      <p className="font-mono font-bold text-m3-primary">{req.agreed_price} INR</p>
                    </div>
                  )}
                  {req.can_cancel && (
                    <button
                      onClick={() => handleCancel(req.id)}
                      disabled={api.loading}
                      className={clsx(
                        "px-4 py-2 text-sm font-semibold rounded-lg bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-colors flex items-center gap-2",
                        api.loading && "opacity-50 cursor-not-allowed"
                      )}
                    >
                      {api.loading && <Loader2 className="w-3 h-3 animate-spin"/>}
                      Cancel Request
                    </button>
                  )}
                  {req.status === 'Completed' && !req.has_reviewed && (
                    <button
                      onClick={() => setReviewReqId(req.id)}
                      className="px-4 py-2 text-sm font-semibold rounded-lg bg-m3-primary text-m3-on-primary hover:bg-m3-primary/90 transition-colors flex items-center gap-2"
                    >
                      <Star className="w-4 h-4" />{t('services.my-requests.leave_review')}</button>
                  )}
                  {req.status === 'Completed' && req.has_reviewed && (
                    <div className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-cultivax-primary/10 text-cultivax-primary border border-cultivax-primary/20 text-xs font-semibold">
                      <CheckCircle2 className="w-4 h-4" />{t('services.my-requests.reviewed')}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Review Modal */}
      {reviewReqId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="glass-card max-w-md w-full p-6 rounded-2xl border border-m3-outline-variant/20 shadow-2xl relative">
            <button 
              onClick={() => setReviewReqId(null)}
              className="absolute top-4 right-4 p-2 text-m3-on-surface-variant hover:text-m3-on-surface rounded-full hover:bg-m3-surface-container-highest transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <h2 className="text-xl font-bold text-m3-on-surface mb-2">{t('services.my-requests.leave_a_review')}</h2>
            <p className="text-sm text-m3-on-surface-variant mb-6">{t('services.my-requests.how_was_the_service')}</p>

            <div className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-m3-on-surface mb-2">{t('services.my-requests.rating')}</label>
                <div className="flex items-center gap-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setRating(star)}
                      className="p-1 focus:outline-none"
                    >
                      <Star
                        className={clsx(
                          "w-8 h-8 transition-colors",
                          star <= rating ? "fill-yellow-400 text-yellow-400" : "fill-transparent text-m3-outline-variant"
                        )}
                      />
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-m3-on-surface mb-2">Comment <span className="text-xs font-normal text-m3-on-surface-variant">(optional)</span></label>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder={t('services.my-requests.share_details_of_your')}
                  className="w-full bg-m3-surface-container-highest border border-m3-outline-variant/30 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-m3-primary/50 text-m3-on-surface resize-none h-24"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-m3-on-surface mb-2">Complaint Category <span className="text-xs font-normal text-m3-on-surface-variant">(optional)</span></label>
                <select
                  value={complaintCategory}
                  onChange={(e) => setComplaintCategory(e.target.value)}
                  className="w-full bg-m3-surface-container-highest border border-m3-outline-variant/30 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-m3-primary/50 text-m3-on-surface appearance-none"
                >
                  <option value="">{t('services.my-requests.no_complaint')}</option>
                  <option value="late_arrival">{t('services.my-requests.late_arrival')}</option>
                  <option value="poor_quality">{t('services.my-requests.poor_quality')}</option>
                  <option value="overcharging">{t('services.my-requests.overcharging')}</option>
                  <option value="damage">{t('services.my-requests.caused_damage')}</option>
                  <option value="no_show">{t('services.my-requests.no_show')}</option>
                  <option value="other">{t('services.my-requests.other')}</option>
                </select>
              </div>

              <div className="pt-4 flex justify-end gap-3">
                <button
                  onClick={() => setReviewReqId(null)}
                  className="px-5 py-2.5 rounded-xl font-medium text-sm border border-m3-outline-variant/30 text-m3-on-surface hover:bg-m3-surface-container-highest transition-colors"
                >{t('services.my-requests.cancel')}</button>
                <button
                  onClick={handleSubmitReview}
                  disabled={api.loading}
                  className="px-5 py-2.5 rounded-xl font-medium text-sm bg-m3-primary text-m3-on-primary hover:bg-m3-primary/90 transition-colors flex items-center gap-2 shadow-lg shadow-m3-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {api.loading && <Loader2 className="w-4 h-4 animate-spin" />}
                  Submit Review
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </ProtectedRoute>
  );
}
