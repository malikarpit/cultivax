'use client';

/**
 * Dashboard Stats Component
 *
 * Displays aggregate farm statistics:
 * - Total crops
 * - Active crops
 * - At-risk crops
 * - Harvested count
 * - Average stress score
 * - Pending alerts
 */

import { useEffect, useState } from 'react';
import { useApi } from '@/hooks/useApi';

interface Crop {
  id: string;
  state: string;
  stress_score: number;
  risk_index: number;
}

interface CropsResponse {
  data: Crop[];
  meta: { total: number; page: number; per_page: number };
}

interface StatItem {
  label: string;
  value: string | number;
  icon: string;
  color: string;
  bgColor: string;
  trend?: string;
}

export default function DashboardStats() {
  const cropsApi = useApi<CropsResponse>();
  const [stats, setStats] = useState<StatItem[]>([]);

  useEffect(() => {
    cropsApi.execute('/api/v1/crops?per_page=100').catch(() => {});
  }, []);

  useEffect(() => {
    if (!cropsApi.data?.data) return;

    const crops = cropsApi.data.data;
    const total = cropsApi.data.meta?.total ?? crops.length;
    const active = crops.filter((c) => c.state === 'Active').length;
    const atRisk = crops.filter((c) => c.state === 'AtRisk' || c.state === 'Delayed').length;
    const harvested = crops.filter((c) => c.state === 'Harvested').length;
    const avgStress = crops.length > 0
      ? crops.reduce((sum, c) => sum + (c.stress_score || 0), 0) / crops.length
      : 0;
    const highRisk = crops.filter((c) => (c.risk_index || 0) > 0.6).length;

    setStats([
      {
        label: 'Total Crops',
        value: total,
        icon: '🌾',
        color: 'text-emerald-600',
        bgColor: 'bg-emerald-50 border-emerald-200',
      },
      {
        label: 'Active',
        value: active,
        icon: '🟢',
        color: 'text-green-600',
        bgColor: 'bg-green-50 border-green-200',
        trend: total > 0 ? `${((active / total) * 100).toFixed(0)}%` : undefined,
      },
      {
        label: 'At Risk / Delayed',
        value: atRisk,
        icon: '⚠️',
        color: atRisk > 0 ? 'text-red-600' : 'text-gray-500',
        bgColor: atRisk > 0 ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200',
      },
      {
        label: 'Harvested',
        value: harvested,
        icon: '🌻',
        color: 'text-purple-600',
        bgColor: 'bg-purple-50 border-purple-200',
      },
      {
        label: 'Avg Stress',
        value: `${(avgStress * 100).toFixed(1)}%`,
        icon: '📊',
        color: avgStress > 0.5 ? 'text-red-600' : 'text-blue-600',
        bgColor: avgStress > 0.5 ? 'bg-red-50 border-red-200' : 'bg-blue-50 border-blue-200',
      },
      {
        label: 'High Risk',
        value: highRisk,
        icon: '🔴',
        color: highRisk > 0 ? 'text-red-700' : 'text-gray-500',
        bgColor: highRisk > 0 ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200',
      },
    ]);
  }, [cropsApi.data]);

  if (cropsApi.loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="bg-white border rounded-xl p-4 animate-pulse"
          >
            <div className="h-4 bg-gray-200 rounded w-16 mb-2" />
            <div className="h-8 bg-gray-200 rounded w-12" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className={`border rounded-xl p-4 transition-all hover:shadow-md ${stat.bgColor}`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">{stat.icon}</span>
            {stat.trend && (
              <span className="text-xs text-gray-500 bg-white px-2 py-0.5 rounded-full">
                {stat.trend}
              </span>
            )}
          </div>
          <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
          <p className="text-xs text-gray-600 mt-1">{stat.label}</p>
        </div>
      ))}
    </div>
  );
}
