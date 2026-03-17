'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import CropTimeline from '@/components/CropTimeline';
import ActionLogList from '@/components/ActionLogList';

interface CropDetail {
  id: string;
  crop_type: string;
  variety: string;
  state: string;
  stage: string;
  region: string;
  sowing_date: string;
  stress_score: number;
  risk_index: number;
  current_day_number: number;
  seasonal_window_category: string;
}

interface ActionLog {
  id: string;
  action_type: string;
  action_effective_date: string;
  metadata: Record<string, any>;
  created_at: string;
}

export default function CropDetailPage() {
  const params = useParams();
  const [crop, setCrop] = useState<CropDetail | null>(null);
  const [actions, setActions] = useState<ActionLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) {
      fetchCropDetail();
      fetchActions();
    }
  }, [params.id]);

  const fetchCropDetail = async () => {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/crops/${params.id}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      const data = await res.json();
      setCrop(data);
    } catch (error) {
      console.error('Failed to fetch crop details:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchActions = async () => {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/crops/${params.id}/actions`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      const data = await res.json();
      setActions(data || []);
    } catch (error) {
      console.error('Failed to fetch actions:', error);
    }
  };

  if (loading) {
    return <div className="p-6 text-center text-gray-500">Loading...</div>;
  }

  if (!crop) {
    return <div className="p-6 text-center text-red-500">Crop not found</div>;
  }

  const stateColors: Record<string, string> = {
    Created: 'bg-blue-100 text-blue-800',
    Active: 'bg-green-100 text-green-800',
    Delayed: 'bg-yellow-100 text-yellow-800',
    AtRisk: 'bg-red-100 text-red-800',
    Harvested: 'bg-purple-100 text-purple-800',
    Closed: 'bg-gray-100 text-gray-800',
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold capitalize">
            {crop.crop_type} — {crop.variety}
          </h1>
          <p className="text-gray-500">{crop.region}</p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium ${
            stateColors[crop.state] || 'bg-gray-100'
          }`}
        >
          {crop.state}
        </span>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <p className="text-sm text-gray-500">Day</p>
          <p className="text-2xl font-bold">{crop.current_day_number}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <p className="text-sm text-gray-500">Stress Score</p>
          <p className="text-2xl font-bold">{(crop.stress_score * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <p className="text-sm text-gray-500">Risk Index</p>
          <p className="text-2xl font-bold">{(crop.risk_index * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <p className="text-sm text-gray-500">Season</p>
          <p className="text-2xl font-bold">{crop.seasonal_window_category}</p>
        </div>
      </div>

      {/* Timeline */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4">Growth Timeline</h2>
        <CropTimeline
          stage={crop.stage}
          dayNumber={crop.current_day_number}
          state={crop.state}
        />
      </div>

      {/* Action History */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Action History</h2>
        <ActionLogList actions={actions} />
      </div>
    </div>
  );
}
