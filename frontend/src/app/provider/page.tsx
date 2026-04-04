'use client';

/**
 * Provider Dashboard — CultivaX
 *
 * Stats, incoming requests, quarterly revenue chart, trust score.
 * Now wired to real API data via /api/v1/dashboard/stats (provider role).
 */

import { useFetch } from '@/hooks/useFetch';
import { useApi } from '@/hooks/useApi';
import {
  ShoppingBag, Clock, CheckCircle2, Star,
  TrendingUp, Users, MapPin, ArrowRight, AlertTriangle,
  Loader2, Check, X, Play, CopyCheck
} from 'lucide-react';
import StatCard from '@/components/StatCard';
import Badge from '@/components/Badge';
import TrustRing from '@/components/TrustRing';
import ProtectedRoute from '@/components/ProtectedRoute';

export default function ProviderDashboardPage() {
  const api = useApi();
  // Fetch real provider stats from API
  const { data: stats, loading, error } = useFetch('/api/v1/dashboard/stats');

  // Fetch pending service requests for the provider
  const { data: requestsData, loading: reqLoading, refetch } = useFetch(
    '/api/v1/service-requests?per_page=5'
  );
  const requests = requestsData?.items || [];

  const handleAction = async (id: string, action: 'accept' | 'decline' | 'start' | 'complete') => {
    try {
      await api.execute(`/api/v1/service-requests/${id}/${action}`, { method: 'PUT' });
      refetch();
    } catch (err) {
      console.error('Failed to ' + action + ' request:', err);
    }
  };

  return (
    <ProtectedRoute requiredRole={["provider", "admin"]}>
    <div className="animate-fade-in">
      <h1 className="text-2xl font-bold mb-6">Provider Dashboard</h1>

      {/* Stats */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="h-4 w-20 bg-cultivax-elevated rounded mb-3" />
              <div className="h-8 w-12 bg-cultivax-elevated rounded" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="card p-5 mb-6 border border-red-500/20 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-400">Failed to load provider stats</p>
            <p className="text-xs text-cultivax-text-muted">{error}</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <StatCard
            icon={Clock}
            label="Pending Requests"
            value={stats?.pending_requests ?? 0}
            color={stats?.pending_requests > 0 ? 'amber' : 'default'}
          />
          <StatCard
            icon={ShoppingBag}
            label="Active Jobs"
            value={stats?.active_jobs ?? 0}
            color="blue"
          />
          <StatCard
            icon={CheckCircle2}
            label="Completed"
            value={stats?.completed_jobs ?? 0}
            trend={stats?.completed_jobs > 0 ? `${stats.completed_jobs} total` : undefined}
            trendDirection="up"
            color="green"
          />
          <StatCard
            icon={Star}
            label="Trust Score"
            value={stats?.trust_score ? stats.trust_score.toFixed(1) : '—'}
            color="green"
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left (2/3) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Incoming Requests */}
          <div className="card">
            <h3 className="text-base font-semibold mb-4">Incoming Service Requests</h3>
            {reqLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center gap-3 px-3 py-3 rounded-lg bg-cultivax-elevated/50 animate-pulse">
                    <div className="w-9 h-9 rounded-full bg-cultivax-elevated" />
                    <div className="flex-1">
                      <div className="h-3 w-32 bg-cultivax-elevated rounded mb-1" />
                      <div className="h-2 w-48 bg-cultivax-elevated rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : requests.length > 0 ? (
              <div className="space-y-3">
                {requests.map((req: any) => (
                  <div key={req.id} className="flex items-center justify-between px-3 py-3 rounded-lg bg-cultivax-elevated/50 hover:bg-cultivax-elevated transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-cultivax-primary/20 flex items-center justify-center text-cultivax-primary font-semibold text-sm">
                        {(req.farmer_name || 'F').charAt(0)}
                      </div>
                      <div>
                        <p className="text-sm font-medium">{req.farmer_name || 'Farmer'}</p>
                        <p className="text-xs text-cultivax-text-muted">
                          {req.service_type} • <MapPin className="w-3 h-3 inline" /> {req.region || '—'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={req.urgency === 'high' ? 'red' : req.urgency === 'normal' ? 'amber' : 'gray'}
                        size="sm"
                      >
                        {req.status}
                      </Badge>
                      
                      {/* Action Buttons based on generated constraints from backend */}
                      {req.can_accept && (
                        <button onClick={() => handleAction(req.id, 'accept')} className="p-1.5 rounded bg-green-500/10 text-green-500 hover:bg-green-500/20" title="Accept">
                          <Check className="w-4 h-4" />
                        </button>
                      )}
                      {req.can_decline && (
                        <button onClick={() => handleAction(req.id, 'decline')} className="p-1.5 rounded bg-red-500/10 text-red-500 hover:bg-red-500/20" title="Decline">
                          <X className="w-4 h-4" />
                        </button>
                      )}
                      {req.can_start && (
                        <button onClick={() => handleAction(req.id, 'start')} className="p-1.5 rounded bg-blue-500/10 text-blue-500 hover:bg-blue-500/20" title="Start Service">
                          <Play className="w-4 h-4" />
                        </button>
                      )}
                      {req.can_complete && (
                        <button onClick={() => handleAction(req.id, 'complete')} className="p-1.5 rounded bg-cultivax-primary/10 text-cultivax-primary hover:bg-cultivax-primary/20" title="Finish Task">
                          <CopyCheck className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <CheckCircle2 className="w-8 h-8 text-cultivax-text-muted mx-auto mb-2 opacity-40" />
                <p className="text-sm text-cultivax-text-muted">No pending requests</p>
              </div>
            )}
          </div>

          {/* Revenue Summary */}
          <div className="card">
            <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cultivax-primary" /> Performance
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-cultivax-elevated/50 text-center">
                <p className="text-2xl font-bold text-cultivax-text-primary">{stats?.completed_jobs ?? 0}</p>
                <p className="text-xs text-cultivax-text-muted mt-1">Jobs Completed</p>
              </div>
              <div className="p-4 rounded-xl bg-cultivax-elevated/50 text-center">
                <p className="text-2xl font-bold text-cultivax-text-primary">{stats?.active_jobs ?? 0}</p>
                <p className="text-xs text-cultivax-text-muted mt-1">Active Now</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right (1/3) */}
        <div className="space-y-6">
          <div className="card text-center">
            <h3 className="text-base font-semibold mb-4">Your Trust Score</h3>
            <TrustRing
              score={stats?.trust_score ? stats.trust_score / 10 : 0}
              size={120}
              strokeWidth={8}
              labelFormat="outOf10"
              className="mx-auto mb-3"
            />
            <p className="text-sm text-cultivax-text-secondary">
              {stats?.is_verified ? 'Verified Provider ✓' : 'Verification Pending'}
            </p>
          </div>

          {/* Service Regions */}
          <div className="card">
            <h3 className="text-base font-semibold mb-3">Service Coverage</h3>
            <p className="text-sm text-cultivax-text-secondary">
              {stats?.region || 'Coverage area not set'}
            </p>
            <p className="text-xs text-cultivax-text-muted mt-2">
              Manage your service area from Settings
            </p>
          </div>
        </div>
      </div>
    </div>
    </ProtectedRoute>
  );
}
