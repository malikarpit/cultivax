'use client';

/**
 * Alerts & Notifications Page
 *
 * Severity-filtered alert list with action recommendations.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Bell, AlertTriangle, AlertCircle, Info,
  CheckCircle2, Sprout,
} from 'lucide-react';
import clsx from 'clsx';
import ProtectedRoute from '@/components/ProtectedRoute';
import Badge from '@/components/Badge';
import FilterChips from '@/components/FilterChips';
import { apiGet, apiPost, apiPut } from '@/lib/api';
import { useTranslation } from 'react-i18next';

const SEVERITY_FILTERS = [
  { label: 'All', value: 'all' },
  { label: 'Critical', value: 'critical' },
  { label: 'High', value: 'high' },
  { label: 'Medium', value: 'medium' },
  { label: 'Low', value: 'low' },
];

const URGENCY_FILTERS = [
  { label: 'All Urgency', value: 'all' },
  { label: 'Immediate', value: 'immediate' },
  { label: 'Soon', value: 'soon' },
  { label: 'Routine', value: 'routine' },
];

const PAGE_SIZE = 20;

interface AlertItem {
  id: string;
  user_id: string | null;
  crop_instance_id: string | null;
  alert_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | string;
  urgency_level: string | null;
  message: string;
  details: Record<string, unknown> | null;
  source_event_id: string | null;
  expires_at: string | null;
  is_acknowledged: boolean;
  acknowledged_at: string | null;
  created_at: string;
}

interface BulkAcknowledgeResponse {
  acknowledged_count: number;
}

const alertTypeTitles: Record<string, string> = {
  weather_alert: 'Weather Alert',
  stress_alert: 'Crop Stress Alert',
  pest_alert: 'Pest Risk Alert',
  action_reminder: 'Action Reminder',
  market_alert: 'Market Alert',
  harvest_approaching: 'Harvest Approaching',
  risk_alert: 'Risk Alert',
};

const severityConfig: Record<string, { icon: any; color: string; bg: string; border: string }> = {
  critical: { icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
  high: { icon: AlertCircle, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
  medium: { icon: Info, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
  low: { icon: Info, color: 'text-gray-400', bg: 'bg-gray-500/10', border: 'border-gray-500/20' },
};

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);

  if (diffMinutes < 1) return 'just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}

function getRecommendedAction(details: Record<string, unknown> | null): string | null {
  if (!details) return null;
  const value = details.recommended_action;
  return typeof value === 'string' && value.trim() ? value : null;
}

function getAlertTitle(alert: AlertItem): string {
  const baseTitle = alertTypeTitles[alert.alert_type] || 'Alert';
  if (!alert.crop_instance_id) return baseTitle;
  return `${baseTitle} - Crop ${alert.crop_instance_id.slice(0, 8)}`;
}

export default function AlertsPage() {
  const { t } = useTranslation();
  const [severityFilter, setSeverityFilter] = useState('all');
  const [urgencyFilter, setUrgencyFilter] = useState('all');
  const [showHandled, setShowHandled] = useState(false);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [skip, setSkip] = useState(0);
  const [acknowledgingIds, setAcknowledgingIds] = useState<Record<string, boolean>>({});
  const [bulkLoading, setBulkLoading] = useState(false);

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        unacknowledged_only: showHandled ? 'false' : 'true',
        skip: String(skip),
        limit: String(PAGE_SIZE),
      });

      if (severityFilter !== 'all') {
        params.set('severity', severityFilter);
      }
      if (urgencyFilter !== 'all') {
        params.set('urgency_level', urgencyFilter);
      }

      const response = await apiGet<AlertItem[]>(`/api/v1/alerts?${params.toString()}`);
      setAlerts(response);
    } catch (err: any) {
      setError(err.message || 'Failed to load alerts');
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  }, [severityFilter, urgencyFilter, showHandled, skip]);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  useEffect(() => {
    setSkip(0);
  }, [severityFilter, urgencyFilter, showHandled]);

  const unhandledCount = useMemo(
    () => alerts.filter((alert) => !alert.is_acknowledged).length,
    [alerts]
  );

  const hasNextPage = alerts.length === PAGE_SIZE;

  const handleAcknowledge = async (alertId: string) => {
    setAcknowledgingIds((prev) => ({ ...prev, [alertId]: true }));
    try {
      await apiPut(`/api/v1/alerts/${alertId}/acknowledge`, {});
      await loadAlerts();
    } catch (err: any) {
      setError(err.message || 'Failed to acknowledge alert');
    } finally {
      setAcknowledgingIds((prev) => {
        const next = { ...prev };
        delete next[alertId];
        return next;
      });
    }
  };

  const handleBulkAcknowledge = async () => {
    const unacknowledgedIds = alerts
      .filter((alert) => !alert.is_acknowledged)
      .map((alert) => alert.id);

    if (unacknowledgedIds.length === 0) return;

    setBulkLoading(true);
    try {
      await apiPost<BulkAcknowledgeResponse>('/api/v1/alerts/acknowledge-bulk', {
        alert_ids: unacknowledgedIds,
      });
      await loadAlerts();
    } catch (err: any) {
      setError(err.message || 'Failed to acknowledge alerts');
    } finally {
      setBulkLoading(false);
    }
  };

  const filtered = alerts;

  return (
    <ProtectedRoute>
    <div className="animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bell className="w-6 h-6 text-cultivax-primary" />{t('alerts.alerts_notifications')}</h1>
          <p className="text-sm text-cultivax-text-muted mt-1">
            {unhandledCount} unhandled alerts on this page
          </p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-cultivax-text-secondary cursor-pointer">
            <input
              type="checkbox"
              checked={showHandled}
              onChange={(e) => setShowHandled(e.target.checked)}
              className="w-4 h-4 rounded border-cultivax-border bg-cultivax-elevated text-cultivax-primary"
            />{t('alerts.show_handled')}</label>
          <button
            onClick={handleBulkAcknowledge}
            disabled={bulkLoading || unhandledCount === 0}
            className="px-3 py-2 text-xs font-medium rounded-lg border border-cultivax-border text-cultivax-text-secondary hover:bg-cultivax-elevated disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {bulkLoading ? 'Acknowledging...' : 'Acknowledge visible'}
          </button>
        </div>
      </div>

      <FilterChips options={SEVERITY_FILTERS} selected={severityFilter} onChange={setSeverityFilter} className="mb-3" />
      <FilterChips options={URGENCY_FILTERS} selected={urgencyFilter} onChange={setUrgencyFilter} className="mb-6" />

      {error && (
        <div className="card mb-4 p-3 border border-red-500/30 bg-red-500/10 text-red-300 text-sm">
          {error}
        </div>
      )}

      {loading && (
        <div className="space-y-3 mb-4">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="card p-4 animate-pulse">
              <div className="h-4 w-2/5 bg-cultivax-elevated rounded mb-3" />
              <div className="h-3 w-4/5 bg-cultivax-elevated rounded" />
            </div>
          ))}
        </div>
      )}

      <div className="space-y-3">
        {filtered.map((alert) => {
          const config = severityConfig[alert.severity];
          const Icon = (config || severityConfig.low).icon;
          const recommendedAction = getRecommendedAction(alert.details);

          return (
            <div
              key={alert.id}
              className={clsx(
                'card p-4 transition-all',
                alert.is_acknowledged && 'opacity-60',
                !alert.is_acknowledged && config?.border && `border-l-4 ${config.border}`
              )}
            >
              <div className="flex items-start gap-3">
                <div className={clsx('p-2 rounded-lg flex-shrink-0', (config || severityConfig.low).bg)}>
                  <Icon className={clsx('w-4 h-4', (config || severityConfig.low).color)} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-semibold truncate">{getAlertTitle(alert)}</h3>
                    <Badge
                      variant={
                        alert.severity === 'critical' ? 'red' :
                        alert.severity === 'high' ? 'amber' :
                        alert.severity === 'medium' ? 'blue' : 'gray'
                      }
                      size="sm"
                    >
                      {alert.severity}
                    </Badge>
                    {alert.is_acknowledged && (
                      <Badge variant="green" size="sm" dot>{t('alerts.handled')}</Badge>
                    )}
                  </div>
                  <p className="text-xs text-cultivax-text-secondary mb-2">{alert.message}</p>

                  {alert.urgency_level && (
                    <p className="text-xs text-cultivax-text-muted mb-2 capitalize">
                      Urgency: {alert.urgency_level}
                    </p>
                  )}

                  {alert.crop_instance_id && (
                    <p className="text-xs text-cultivax-text-muted flex items-center gap-1 mb-2">
                      <Sprout className="w-3 h-3" /> Crop ID: {alert.crop_instance_id.slice(0, 8)}
                    </p>
                  )}

                  {/* Recommended Action */}
                  {!alert.is_acknowledged && recommendedAction && (
                    <div className="bg-cultivax-elevated rounded-lg px-3 py-2 text-xs text-cultivax-text-secondary mt-2">
                      <span className="font-semibold text-cultivax-primary">{t('alerts.recommended')}</span> {recommendedAction}
                    </div>
                  )}

                  <div className="flex items-center justify-between mt-3">
                    <span className="text-xs text-cultivax-text-muted">{formatTimeAgo(alert.created_at)}</span>
                    {!alert.is_acknowledged && (
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        disabled={!!acknowledgingIds[alert.id]}
                        className="text-xs font-medium text-cultivax-primary hover:text-cultivax-primary-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {acknowledgingIds[alert.id] ? 'Saving...' : 'Mark Handled'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {!loading && filtered.length === 0 && (
        <div className="card text-center py-12">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-3" />
          <p className="text-cultivax-text-secondary">{t('alerts.all_clear_no_alerts')}</p>
        </div>
      )}

      <div className="mt-6 flex items-center justify-end gap-2">
        <button
          onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
          disabled={skip === 0 || loading}
          className="px-3 py-2 text-xs rounded-lg border border-cultivax-border text-cultivax-text-secondary hover:bg-cultivax-elevated disabled:opacity-50 disabled:cursor-not-allowed"
        >{t('alerts.previous')}</button>
        <button
          onClick={() => setSkip(skip + PAGE_SIZE)}
          disabled={!hasNextPage || loading}
          className="px-3 py-2 text-xs rounded-lg border border-cultivax-border text-cultivax-text-secondary hover:bg-cultivax-elevated disabled:opacity-50 disabled:cursor-not-allowed"
        >{t('alerts.next')}</button>
      </div>
    </div>
    </ProtectedRoute>
  );
}
