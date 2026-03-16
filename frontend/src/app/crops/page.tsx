'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import CropCard from '@/components/CropCard';

interface CropInstance {
  id: string;
  crop_type: string;
  variety: string;
  state: string;
  region: string;
  sowing_date: string;
  stress_score: number;
  risk_index: number;
  seasonal_window_category: string;
}

export default function CropsPage() {
  const [crops, setCrops] = useState<CropInstance[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ state: '', crop_type: '' });
  const router = useRouter();

  useEffect(() => {
    fetchCrops();
  }, [filter]);

  const fetchCrops = async () => {
    try {
      const params = new URLSearchParams();
      if (filter.state) params.append('state', filter.state);
      if (filter.crop_type) params.append('crop_type', filter.crop_type);

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/crops?${params}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      const data = await res.json();
      setCrops(data.items || []);
    } catch (error) {
      console.error('Failed to fetch crops:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">My Crops</h1>
        <button
          onClick={() => router.push('/crops/new')}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          + New Crop
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <select
          value={filter.state}
          onChange={(e) => setFilter({ ...filter, state: e.target.value })}
          className="px-3 py-2 border rounded-lg"
        >
          <option value="">All States</option>
          <option value="Created">Created</option>
          <option value="Active">Active</option>
          <option value="Delayed">Delayed</option>
          <option value="AtRisk">At Risk</option>
          <option value="Harvested">Harvested</option>
        </select>
        <select
          value={filter.crop_type}
          onChange={(e) => setFilter({ ...filter, crop_type: e.target.value })}
          className="px-3 py-2 border rounded-lg"
        >
          <option value="">All Crops</option>
          <option value="wheat">Wheat</option>
          <option value="rice">Rice</option>
          <option value="cotton">Cotton</option>
        </select>
      </div>

      {/* Crop Grid */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading crops...</div>
      ) : crops.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No crops found. Create your first crop to get started.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {crops.map((crop) => (
            <div
              key={crop.id}
              onClick={() => router.push(`/crops/${crop.id}`)}
              className="cursor-pointer"
            >
              <CropCard
                id={crop.id}
                crop_type={crop.crop_type}
                state={crop.state}
                region={crop.region}
                sowing_date={crop.sowing_date}
                stress_score={crop.stress_score}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
