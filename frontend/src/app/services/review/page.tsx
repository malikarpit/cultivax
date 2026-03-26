'use client';

/**
 * Service Review Submission Page
 *
 * After completing a service, farmers can leave a review.
 * POST /api/v1/reviews
 */

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useApi } from '@/hooks/useApi';

export default function ReviewSubmissionPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const providerId = searchParams.get('provider') || '';
  const requestId = searchParams.get('request') || '';
  const submitApi = useApi();

  const [form, setForm] = useState({
    rating: 5,
    comment: '',
    complaint_category: '',
  });
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await submitApi.execute('/api/v1/reviews', {
        method: 'POST',
        body: {
          provider_id: providerId,
          service_request_id: requestId || undefined,
          rating: form.rating,
          comment: form.comment || undefined,
          complaint_category: form.complaint_category || undefined,
        },
      });
      setSubmitted(true);
    } catch {}
  };

  if (submitted) {
    return (
      <ProtectedRoute>
        <div className="max-w-lg mx-auto text-center py-16">
          <p className="text-6xl mb-4">✅</p>
          <h1 className="text-2xl font-bold mb-2">Review Submitted</h1>
          <p className="text-gray-400 mb-6">Thank you for your feedback!</p>
          <button className="btn-primary" onClick={() => router.push('/services')}>
            Back to Services
          </button>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="max-w-lg mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Submit Review</h1>
          <p className="text-gray-400 mt-1">Rate the service you received</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-5">
          {/* Star Rating */}
          <div>
            <label className="text-sm text-gray-400 block mb-2">Rating</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setForm({ ...form, rating: star })}
                  className={`text-3xl transition-transform hover:scale-110 ${
                    star <= form.rating ? 'text-yellow-400' : 'text-gray-600'
                  }`}
                >
                  ★
                </button>
              ))}
            </div>
          </div>

          {/* Comment */}
          <div>
            <label className="text-sm text-gray-400 block mb-1">Feedback (optional)</label>
            <textarea
              value={form.comment}
              onChange={(e) => setForm({ ...form, comment: e.target.value })}
              placeholder="How was the service?"
              rows={4}
              className="w-full text-sm"
            />
          </div>

          {/* Complaint Category */}
          {form.rating <= 2 && (
            <div>
              <label className="text-sm text-gray-400 block mb-1">Issue Category</label>
              <select
                value={form.complaint_category}
                onChange={(e) => setForm({ ...form, complaint_category: e.target.value })}
                className="w-full text-sm"
              >
                <option value="">Select an issue...</option>
                <option value="Late Arrival">Late Arrival</option>
                <option value="Poor Quality">Poor Quality</option>
                <option value="Incomplete Work">Incomplete Work</option>
                <option value="Equipment Damage">Equipment Damage</option>
                <option value="Overcharging">Overcharging</option>
                <option value="Unprofessional">Unprofessional Behavior</option>
                <option value="Other">Other</option>
              </select>
            </div>
          )}

          {submitApi.error && (
            <p className="text-red-400 text-sm">{submitApi.error}</p>
          )}

          <button
            type="submit"
            className="btn-primary w-full"
            disabled={submitApi.loading}
          >
            {submitApi.loading ? 'Submitting...' : 'Submit Review'}
          </button>
        </form>
      </div>
    </ProtectedRoute>
  );
}
