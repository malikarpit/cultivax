'use client';

/**
 * Yield Submission Page
 *
 * /crops/[id]/yield — Allows farmers to submit harvest yield data
 * for a specific crop instance. Uses YieldForm component.
 */

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import YieldForm from '@/components/YieldForm';

interface CropDetail {
  id: string;
  crop_type: string;
  variety: string;
  state: string;
  stage: string;
  region: string;
  land_area: number;
  sowing_date: string;
  current_day_number: number;
  stress_score: number;
  risk_index: number;
}

export default function YieldSubmissionPage() {
  const params = useParams();
  const router = useRouter();
  const [crop, setCrop] = useState<CropDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (params.id) {
      fetchCrop();
    }
  }, [params.id]);

  const fetchCrop = async () => {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/crops/${params.id}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      if (!res.ok) throw new Error('Crop not found');
      const data = await res.json();
      setCrop(data);
    } catch (err) {
      setError('Failed to load crop details');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitYield = async (yieldData: any) => {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/v1/crops/${params.id}/yield`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(yieldData),
      }
    );

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to submit yield');
    }

    setSubmitted(true);
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="max-w-2xl mx-auto p-6">
          <div className="card text-center py-12">
            <div className="inline-block w-8 h-8 border-2 border-cultivax-primary border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-400 mt-3">Loading crop details...</p>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  if (error || !crop) {
    return (
      <ProtectedRoute>
        <div className="max-w-2xl mx-auto p-6">
          <div className="card text-center py-12">
            <p className="text-5xl mb-4">❌</p>
            <p className="text-red-500 font-medium">{error || 'Crop not found'}</p>
            <button
              className="btn-primary mt-4"
              onClick={() => router.push('/crops')}
            >
              Back to Crops
            </button>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  if (submitted) {
    return (
      <ProtectedRoute>
        <div className="max-w-2xl mx-auto p-6">
          <div className="card text-center py-12">
            <p className="text-5xl mb-4">🎉</p>
            <h2 className="text-2xl font-bold text-green-600 mb-2">Yield Submitted!</h2>
            <p className="text-gray-500 mb-6">
              Your harvest data for{' '}
              <span className="capitalize font-medium">{crop.crop_type}</span> has been recorded
              successfully.
            </p>
            <div className="flex gap-3 justify-center">
              <button
                className="btn-primary"
                onClick={() => router.push(`/crops/${params.id}`)}
              >
                View Crop
              </button>
              <button
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                onClick={() => router.push('/dashboard')}
              >
                Dashboard
              </button>
            </div>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="max-w-2xl mx-auto p-6 space-y-6">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <button onClick={() => router.push('/crops')} className="hover:text-cultivax-primary">
            Crops
          </button>
          <span>/</span>
          <button
            onClick={() => router.push(`/crops/${params.id}`)}
            className="hover:text-cultivax-primary capitalize"
          >
            {crop.crop_type}
          </button>
          <span>/</span>
          <span className="text-gray-700 font-medium">Submit Yield</span>
        </div>

        {/* Crop Summary */}
        <div className="card bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-lg font-bold capitalize">
                {crop.crop_type} — {crop.variety}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {crop.region} · Day {crop.current_day_number} · {crop.land_area || '—'} acres
              </p>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium ${
                crop.state === 'ReadyToHarvest'
                  ? 'bg-yellow-100 text-yellow-800'
                  : crop.state === 'Harvested'
                  ? 'bg-purple-100 text-purple-800'
                  : 'bg-green-100 text-green-800'
              }`}
            >
              {crop.state}
            </span>
          </div>
        </div>

        {/* Yield Form */}
        <YieldForm
          cropId={crop.id}
          cropType={crop.crop_type}
          landArea={crop.land_area || 0}
          onSubmit={handleSubmitYield}
          onCancel={() => router.push(`/crops/${params.id}`)}
        />
      </div>
    </ProtectedRoute>
  );
}
