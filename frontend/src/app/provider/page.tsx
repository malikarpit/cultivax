'use client';

/**
 * Provider Dashboard — Home Page
 *
 * Shows provider stats, incoming service requests, and quick actions.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/context/AuthContext';
import StatsWidget from '@/components/StatsWidget';
import { useApi } from '@/hooks/useApi';

interface ServiceRequest {
  id: string;
  farmer_name?: string;
  crop_type?: string;
  service_type: string;
  status: string;
  created_at: string;
  notes?: string;
}

export default function ProviderDashboard() {
  const { user } = useAuth();
  const router = useRouter();
  const requestsApi = useApi<ServiceRequest[]>();

  useEffect(() => {
    requestsApi.execute('/api/v1/service-requests').catch(() => {});
  }, []);

  const requests = requestsApi.data || [];
  const pending = requests.filter((r) => r.status === 'Pending');
  const active = requests.filter((r) => r.status === 'Accepted');
  const completed = requests.filter((r) => r.status === 'Completed');

  const stats = [
    { label: 'Pending Requests', value: String(pending.length), icon: '📥', color: 'text-yellow-400' },
    { label: 'Active Jobs', value: String(active.length), icon: '🔨', color: 'text-blue-400' },
    { label: 'Completed', value: String(completed.length), icon: '✅', color: 'text-cultivax-primary' },
    { label: 'Total Requests', value: String(requests.length), icon: '📋', color: 'text-purple-400' },
  ];

  const handleAccept = async (id: string) => {
    try {
      await requestsApi.execute(`/api/v1/service-requests/${id}/accept`, { method: 'PUT' });
      requestsApi.execute('/api/v1/service-requests').catch(() => {});
    } catch {}
  };

  const handleComplete = async (id: string) => {
    try {
      await requestsApi.execute(`/api/v1/service-requests/${id}/complete`, { method: 'PUT' });
      requestsApi.execute('/api/v1/service-requests').catch(() => {});
    } catch {}
  };

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">
            Provider Dashboard
          </h1>
          <p className="text-gray-500 mt-1">
            Welcome, <span className="text-cultivax-primary">{user?.full_name}</span>
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <StatsWidget key={stat.label} {...stat} />
          ))}
        </div>

        {/* Pending Requests */}
        <div>
          <h2 className="text-lg font-semibold mb-4">📥 Incoming Requests</h2>
          {pending.length === 0 ? (
            <div className="card text-center py-8 text-gray-500">
              <p className="text-4xl mb-3">📭</p>
              <p>No pending requests right now</p>
            </div>
          ) : (
            <div className="space-y-3">
              {pending.map((req) => (
                <div key={req.id} className="card flex items-center justify-between">
                  <div>
                    <p className="font-medium">{req.service_type}</p>
                    <p className="text-sm text-gray-400">
                      {req.crop_type && `${req.crop_type} • `}
                      {new Date(req.created_at).toLocaleDateString()}
                    </p>
                    {req.notes && <p className="text-xs text-gray-500 mt-1">{req.notes}</p>}
                  </div>
                  <button
                    onClick={() => handleAccept(req.id)}
                    className="btn-primary text-sm"
                  >
                    Accept
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Active Jobs */}
        {active.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">🔨 Active Jobs</h2>
            <div className="space-y-3">
              {active.map((req) => (
                <div key={req.id} className="card flex items-center justify-between">
                  <div>
                    <p className="font-medium">{req.service_type}</p>
                    <p className="text-sm text-gray-400">
                      {req.crop_type && `${req.crop_type} • `}Accepted
                    </p>
                  </div>
                  <button
                    onClick={() => handleComplete(req.id)}
                    className="bg-cultivax-primary/20 text-cultivax-primary px-4 py-2 rounded-lg text-sm font-medium hover:bg-cultivax-primary/30 transition"
                  >
                    Mark Complete
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
