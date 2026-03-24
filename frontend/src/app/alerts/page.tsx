/**
 * Alerts Page — Lists all alerts with filtering and acknowledge actions.
 * Fetches from GET /api/v1/alerts, acknowledges via PUT /api/v1/alerts/{id}/acknowledge.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import AlertBanner from '@/components/AlertBanner';
import { useApi } from '@/hooks/useApi';
import { apiPut } from '@/lib/api';

interface Alert {
  id: string;
  alert_type: string;
  severity: string;
  message: string;
  created_at: string;
  is_acknowledged: boolean;
  crop_type?: string;
}

export default function AlertsPage() {
  const { data: alerts, loading, error, execute } = useApi<Alert[]>();
  const [typeFilter, setTypeFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [showAcknowledged, setShowAcknowledged] = useState(false);

  const loadAlerts = useCallback(() => {
    execute('/api/v1/alerts');
  }, [execute]);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  const handleAcknowledge = async (alertId: string) => {
    try {
      await apiPut(`/api/v1/alerts/${alertId}/acknowledge`, {});
      loadAlerts(); // Refresh
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  // Filter logic
  const filteredAlerts = (alerts || []).filter((a) => {
    if (typeFilter && a.alert_type !== typeFilter) return false;
    if (severityFilter && a.severity !== severityFilter) return false;
    if (!showAcknowledged && a.is_acknowledged) return false;
    return true;
  });

  const unacknowledgedCount = (alerts || []).filter((a) => !a.is_acknowledged).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Alerts & Notifications</h1>
          <p className="text-gray-400 mt-1">
            Stay informed about your crops and services
          </p>
        </div>
        {unacknowledgedCount > 0 && (
          <div className="bg-red-500/20 text-red-400 text-sm font-semibold px-4 py-2 rounded-full">
            {unacknowledgedCount} unread
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="text-xs text-gray-400 block mb-1.5">Alert Type</label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full text-sm"
            >
              <option value="">All Types</option>
              <option value="weather_alert">🌦 Weather</option>
              <option value="stress_alert">⚡ Stress</option>
              <option value="pest_alert">🐛 Pest</option>
              <option value="action_reminder">📋 Reminder</option>
              <option value="market_alert">📊 Market</option>
              <option value="harvest_approaching">🌾 Harvest</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1.5">Severity</label>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="w-full text-sm"
            >
              <option value="">All Severities</option>
              <option value="critical">🔴 Critical</option>
              <option value="high">🟠 High</option>
              <option value="medium">🟡 Medium</option>
              <option value="low">🔵 Low</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="showAcknowledged"
              checked={showAcknowledged}
              onChange={(e) => setShowAcknowledged(e.target.checked)}
              className="w-4 h-4 rounded border-cultivax-card"
            />
            <label htmlFor="showAcknowledged" className="text-sm text-gray-400 cursor-pointer">
              Show acknowledged
            </label>
          </div>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-2 border-cultivax-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400 mt-3">Loading alerts...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card border-red-500/30 bg-red-500/10">
          <p className="text-red-400 text-sm">Failed to load alerts: {error}</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && filteredAlerts.length === 0 && (
        <div className="text-center py-16">
          <div className="text-5xl mb-4">🔔</div>
          <p className="text-gray-400 text-lg">No alerts to show</p>
          <p className="text-gray-500 text-sm mt-1">
            {showAcknowledged
              ? 'No alerts match your current filters.'
              : 'All caught up! Try enabling "Show acknowledged" to see past alerts.'}
          </p>
        </div>
      )}

      {/* Alert List */}
      <div className="space-y-3">
        {filteredAlerts.map((alert) => (
          <AlertBanner
            key={alert.id}
            {...alert}
            onAcknowledge={handleAcknowledge}
          />
        ))}
      </div>
    </div>
  );
}
