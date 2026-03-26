'use client';

/**
 * Admin — System Health Dashboard
 *
 * Real-time subsystem health monitoring.
 * GET /health
 */

import { useEffect, useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useApi } from '@/hooks/useApi';

interface SubsystemHealth {
  name: string;
  status: string;
  last_check: string;
  details?: string;
}

interface HealthResponse {
  status: string;
  subsystems: SubsystemHealth[];
}

export default function SystemHealthPage() {
  const healthApi = useApi<HealthResponse>();
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchHealth = () => {
    healthApi.execute('/health').catch(() => {});
  };

  useEffect(() => {
    fetchHealth();
    if (!autoRefresh) return;
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const statusConfig: Record<string, { color: string; bg: string; icon: string }> = {
    Operational: { color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/30', icon: '🟢' },
    Degraded: { color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/30', icon: '🟡' },
    Down: { color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/30', icon: '🔴' },
  };

  const subsystems = healthApi.data?.subsystems || [];
  const overallStatus = healthApi.data?.status || 'Loading...';
  const overallConfig = statusConfig[overallStatus] || statusConfig.Operational;

  const subsystemIcons: Record<string, string> = {
    database: '🗄️',
    ml_service: '🤖',
    weather_api: '🌦️',
    media_storage: '📸',
    event_processor: '⚡',
  };

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">System Health</h1>
            <p className="text-gray-400 mt-1">Real-time subsystem monitoring</p>
          </div>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-400">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="accent-cultivax-primary"
              />
              Auto-refresh (30s)
            </label>
            <button
              className="text-sm text-cultivax-primary hover:underline"
              onClick={fetchHealth}
            >
              ↻ Refresh
            </button>
          </div>
        </div>

        {/* Overall Status */}
        <div className={`card border ${overallConfig.bg} text-center py-6`}>
          <p className="text-4xl mb-2">{overallConfig.icon}</p>
          <p className={`text-2xl font-bold ${overallConfig.color}`}>{overallStatus}</p>
          <p className="text-sm text-gray-400 mt-1">Overall System Status</p>
        </div>

        {/* Subsystem Grid */}
        {healthApi.loading && subsystems.length === 0 && (
          <div className="card text-center py-8">
            <div className="inline-block w-8 h-8 border-2 border-cultivax-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {subsystems.map((sub) => {
            const cfg = statusConfig[sub.status] || statusConfig.Operational;
            return (
              <div key={sub.name} className={`card border ${cfg.bg}`}>
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-2xl">{subsystemIcons[sub.name] || '📦'}</span>
                  <div>
                    <p className="font-medium capitalize">{sub.name.replace(/_/g, ' ')}</p>
                    <p className={`text-sm font-medium ${cfg.color}`}>{sub.status}</p>
                  </div>
                </div>
                {sub.details && (
                  <p className="text-xs text-gray-500">{sub.details}</p>
                )}
                <p className="text-xs text-gray-500 mt-2">
                  Last check: {sub.last_check ? new Date(sub.last_check).toLocaleTimeString() : '—'}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </ProtectedRoute>
  );
}
