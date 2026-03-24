/**
 * Service Request — Create a service request for a provider.
 * Pre-fills provider if coming from marketplace (?provider=id).
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useApi } from '@/hooks/useApi';
import { apiPost } from '@/lib/api';

export default function ServiceRequestPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedProvider = searchParams.get('provider') || '';

  const [formData, setFormData] = useState({
    provider_id: preselectedProvider,
    service_type: '',
    description: '',
    preferred_date: '',
    location: '',
    urgency: 'normal',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Load providers for dropdown
  const { data: providers, execute: loadProviders } = useApi<any[]>();
  useEffect(() => {
    loadProviders('/api/v1/providers');
  }, [loadProviders]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await apiPost('/api/v1/service-requests', {
        provider_id: formData.provider_id,
        service_type: formData.service_type,
        description: formData.description,
        preferred_date: formData.preferred_date,
        location: formData.location,
        urgency: formData.urgency,
      });
      setSuccess(true);
      setTimeout(() => router.push('/services'), 2000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="card text-center max-w-md">
          <div className="text-5xl mb-4">✅</div>
          <h2 className="text-xl font-semibold mb-2">Request Submitted!</h2>
          <p className="text-gray-400 text-sm">
            Your service request has been sent. The provider will be notified shortly.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Request a Service</h1>
        <p className="text-gray-400 mt-1">
          Fill in the details below to create a service request
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="card space-y-5">
        {/* Provider Selection */}
        <div>
          <label className="text-sm text-gray-400 block mb-1.5">
            Service Provider *
          </label>
          <select
            name="provider_id"
            value={formData.provider_id}
            onChange={handleChange}
            required
            className="w-full"
          >
            <option value="">Select a provider</option>
            {(providers || []).map((p: any) => (
              <option key={p.id} value={p.id}>
                {p.business_name} — {p.region}
              </option>
            ))}
          </select>
        </div>

        {/* Service Type */}
        <div>
          <label className="text-sm text-gray-400 block mb-1.5">
            Service Type *
          </label>
          <select
            name="service_type"
            value={formData.service_type}
            onChange={handleChange}
            required
            className="w-full"
          >
            <option value="">Select service type</option>
            <option value="Equipment">Equipment Rental</option>
            <option value="Labor">Labor</option>
            <option value="Consultation">Consultation</option>
            <option value="Transport">Transport</option>
          </select>
        </div>

        {/* Description */}
        <div>
          <label className="text-sm text-gray-400 block mb-1.5">
            Description *
          </label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            required
            rows={4}
            placeholder="Describe what you need..."
            className="w-full resize-none"
          />
        </div>

        {/* Preferred Date + Location */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-400 block mb-1.5">
              Preferred Date
            </label>
            <input
              type="date"
              name="preferred_date"
              value={formData.preferred_date}
              onChange={handleChange}
              className="w-full"
            />
          </div>
          <div>
            <label className="text-sm text-gray-400 block mb-1.5">
              Location
            </label>
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleChange}
              placeholder="e.g., Village name, District"
              className="w-full"
            />
          </div>
        </div>

        {/* Urgency */}
        <div>
          <label className="text-sm text-gray-400 block mb-1.5">Urgency</label>
          <select
            name="urgency"
            value={formData.urgency}
            onChange={handleChange}
            className="w-full"
          >
            <option value="low">Low — flexible timeline</option>
            <option value="normal">Normal</option>
            <option value="high">High — needed soon</option>
            <option value="urgent">Urgent — immediate</option>
          </select>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="btn-primary flex-1 disabled:opacity-50"
          >
            {submitting ? 'Submitting...' : 'Submit Request'}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="btn-secondary"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
