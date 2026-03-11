'use client';

/**
 * Dashboard Page
 */

import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/context/AuthContext';
import StatsWidget from '@/components/StatsWidget';
import CropCard from '@/components/CropCard';

// Placeholder data (replaced by API calls in future phases)
const mockStats = [
  { label: 'Active Crops', value: '—', icon: '🌾', color: 'text-cultivax-primary' },
  { label: 'Stress Alerts', value: '—', icon: '⚠️', color: 'text-yellow-400' },
  { label: 'Risk Score', value: '—', icon: '📉', color: 'text-red-400' },
  { label: 'Services Booked', value: '—', icon: '🏪', color: 'text-blue-400' },
];

export default function DashboardPage() {
  const { user } = useAuth();

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
          {mockStats.map((stat) => (
            <StatsWidget key={stat.label} {...stat} />
          ))}
        </div>

        {/* Crops Section */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Your Crops</h2>
            <button className="btn-primary text-sm">+ New Crop</button>
          </div>

          <div className="card text-center py-12 text-gray-500">
            <p className="text-5xl mb-4">🌱</p>
            <p className="text-lg font-medium">No crops yet</p>
            <p className="text-sm mt-1">Create your first crop to get started</p>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
