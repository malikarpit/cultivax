'use client';

/**
 * Dashboard Page — 26 March: Live API Wiring
 *
 * Replaces mock stats with real API data:
 * - Active crops count + recent crop cards
 * - Pending alerts count
 * - Average risk score
 * - Active service requests count
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/context/AuthContext';
import StatsWidget from '@/components/StatsWidget';
import CropCard from '@/components/CropCard';
import AlertBanner from '@/components/AlertBanner';
import { useApi } from '@/hooks/useApi';

interface Crop {
  id: string;
  crop_type: string;
  state: string;
  stage?: string;
  sowing_date: string;
  stress_score: number;
  risk_index: number;
  region: string;
}

interface CropsResponse {
  data: Crop[];
  meta: { total: number; page: number; per_page: number };
}

interface Alert {
  id: string;
  alert_type: string;
  severity: string;
  status: string;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();

  const cropsApi = useApi<CropsResponse>();
  const alertsApi = useApi<Alert[]>();

  const [stats, setStats] = useState([
    { label: 'Active Crops', value: '—', icon: '🌾', color: 'text-cultivax-primary' },
    { label: 'Stress Alerts', value: '—', icon: '⚠️', color: 'text-yellow-400' },
    { label: 'Avg Risk', value: '—', icon: '📉', color: 'text-red-400' },
    { label: 'Services Booked', value: '—', icon: '🏪', color: 'text-blue-400' },
  ]);

  useEffect(() => {
    cropsApi.execute('/api/v1/crops?per_page=6').catch(() => {});
    alertsApi.execute('/api/v1/alerts').catch(() => {});
  }, []);

  // Update stats when data arrives
  useEffect(() => {
    const crops = cropsApi.data;
    const alerts = alertsApi.data;

    const updatedStats = [...stats];

    // Active crops
    if (crops) {
      const total = crops.meta?.total ?? crops.data?.length ?? 0;
      updatedStats[0] = { ...updatedStats[0], value: String(total) };

      // Average risk
      if (crops.data?.length > 0) {
        const avgRisk = crops.data.reduce((sum, c) => sum + (c.risk_index || 0), 0) / crops.data.length;
        updatedStats[2] = { ...updatedStats[2], value: `${(avgRisk * 100).toFixed(0)}%` };
      } else {
        updatedStats[2] = { ...updatedStats[2], value: '0%' };
      }
    }

    // Pending alerts
    if (alerts) {
      const pending = Array.isArray(alerts)
        ? alerts.filter((a) => a.status === 'Pending').length
        : 0;
      updatedStats[1] = { ...updatedStats[1], value: String(pending) };
    }

    setStats(updatedStats);
  }, [cropsApi.data, alertsApi.data]);

  const crops = cropsApi.data?.data || [];

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        {/* Welcome */}
        <div>
          <h1 className="text-2xl font-bold">
            Welcome back, <span className="text-cultivax-primary">{user?.full_name}</span>
          </h1>
          <p className="text-gray-500 mt-1">Here&apos;s your farm overview</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <StatsWidget key={stat.label} {...stat} />
          ))}
        </div>

        {/* Recent Alert Banner */}
        {alertsApi.data && Array.isArray(alertsApi.data) && (() => {
          const pending = alertsApi.data.filter((a) => a.status === 'Pending');
          if (pending.length === 0) return null;
          const first = pending[0] as any;
          return (
            <AlertBanner
              id={first.id}
              alert_type={first.alert_type}
              severity={first.severity}
              message={first.message || 'New alert requires attention'}
              created_at={first.created_at || new Date().toISOString()}
              is_acknowledged={false}
              compact
            />
          );
        })()}

        {/* Crops Section */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Your Crops</h2>
            <button
              className="btn-primary text-sm"
              onClick={() => router.push('/crops/new')}
            >
              + New Crop
            </button>
          </div>

          {cropsApi.loading && (
            <div className="card text-center py-12">
              <div className="inline-block w-8 h-8 border-2 border-cultivax-primary border-t-transparent rounded-full animate-spin" />
              <p className="text-gray-400 mt-3">Loading crops...</p>
            </div>
          )}

          {!cropsApi.loading && crops.length === 0 && (
            <div className="card text-center py-12 text-gray-500">
              <p className="text-5xl mb-4">🌱</p>
              <p className="text-lg font-medium">No crops yet</p>
              <p className="text-sm mt-1">Create your first crop to get started</p>
            </div>
          )}

          {!cropsApi.loading && crops.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {crops.map((crop) => (
                <div key={crop.id} onClick={() => router.push(`/crops/${crop.id}`)} className="cursor-pointer">
                  <CropCard {...crop} />
                </div>
              ))}
            </div>
          )}

          {crops.length > 0 && (
            <div className="text-center mt-4">
              <button
                className="text-cultivax-primary text-sm hover:underline"
                onClick={() => router.push('/crops')}
              >
                View all crops →
              </button>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
