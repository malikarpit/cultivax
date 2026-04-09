'use client';

/**
 * Admin — System Health Dashboard
 *
 * Polls GET /api/v1/admin/health for full subsystem details.
 * Surfaces freshness decay, latency probes, error messages, and stale warnings.
 */

import { useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useFetch } from '@/hooks/useFetch';
import { useApi } from '@/hooks/useApi';
import {
  Activity, RefreshCw, CheckCircle2, AlertTriangle, XCircle,
  HelpCircle, Database, Cpu, Cloud, ImageIcon, Zap, Loader2
} from 'lucide-react';
import clsx from 'clsx';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';

const SUBSYSTEM_ICONS: Record<string, any> = {
  database: Database,
  ml: Cpu,
  weather: Cloud,
  media: ImageIcon,
  events: Zap,
};

const STATUS_CONFIG: Record<string, { label: string; icon: any; textClass: string; borderBg: string; dot: string; row: string }> = {
  Operational: {
    label: 'Operational', icon: CheckCircle2,
    textClass: 'text-green-500', borderBg: 'border-green-500/20 bg-green-500/10',
    dot: 'bg-green-500 animate-pulse', row: 'hover:bg-green-500/5',
  },
  Degraded: {
    label: 'Degraded', icon: AlertTriangle,
    textClass: 'text-amber-500', borderBg: 'border-amber-500/20 bg-amber-500/10',
    dot: 'bg-amber-500 animate-pulse', row: 'bg-amber-500/5',
  },
  Down: {
    label: 'Down', icon: XCircle,
    textClass: 'text-red-500', borderBg: 'border-red-500/20 bg-red-500/10',
    dot: 'bg-red-500', row: 'bg-red-500/10',
  },
  Unknown: {
    label: 'Unknown', icon: HelpCircle,
    textClass: 'text-neutral-400', borderBg: 'border-neutral-500/20 bg-neutral-500/10',
    dot: 'bg-neutral-400', row: 'opacity-70',
  },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.Unknown;
  return (
    <span className={clsx('px-3 py-1 rounded-full text-xs font-bold border inline-flex items-center gap-1.5 whitespace-nowrap', cfg.textClass, cfg.borderBg)}>
      <span className={clsx('w-1.5 h-1.5 rounded-full flex-shrink-0', cfg.dot)} />
      {cfg.label}
    </span>
  );
}

export default function SystemHealthPage() {
  const { t } = useTranslation();
  const api = useApi();
  const { data, loading, refetch } = useFetch('/api/v1/admin/health');
  const [triggering, setTriggering] = useState(false);

  const handleForceProbe = async () => {
    setTriggering(true);
    try {
      await api.execute('/admin/health-check', { method: 'POST' });
      toast.success(t('admin.health.toast.health_probe_triggered_refreshing'));
      refetch();
    } catch (err: any) {
      toast.error(err.message || 'Health probe trigger failed');
    } finally {
      setTriggering(false);
    }
  };

  const overall = data?.overall_status ?? 'Unknown';
  const overallCfg = STATUS_CONFIG[overall] ?? STATUS_CONFIG.Unknown;
  const OverallIcon = overallCfg.icon;
  const subsystems: Record<string, any> = data?.subsystems ?? {};
  const checkedAt = data?.checked_at;

  const bannerGradient: Record<string, string> = {
    Operational: 'from-green-500/10 to-green-500/5 border-green-500/20',
    Degraded: 'from-amber-500/10 to-amber-500/5 border-amber-500/20',
    Down: 'from-red-500/10 to-red-500/5 border-red-500/20',
    Unknown: 'from-neutral-500/10 to-neutral-500/5 border-neutral-500/20',
  };

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="animate-fade-in max-w-7xl mx-auto py-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-m3-on-surface">{t('admin.health.system_health_monitor')}</h1>
            <p className="text-m3-on-surface-variant mt-2">{t('admin.health.real_time_subsystem_telemetry')}</p>
          </div>
          <button
            onClick={handleForceProbe}
            disabled={triggering || api.loading}
            className="px-5 py-2.5 bg-cultivax-primary hover:bg-cultivax-primary/90 text-white rounded-xl shadow-lg transition-colors flex items-center gap-2 font-medium disabled:opacity-60"
          >
            {triggering ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            Force Health Probe
          </button>
        </div>

        {/* Loading state */}
        {loading ? (
          <div className="flex items-center justify-center py-32">
            <Loader2 className="w-10 h-10 animate-spin text-cultivax-primary" />
          </div>
        ) : (
          <>
            {/* Overall status banner */}
            <div className={clsx('rounded-2xl border bg-gradient-to-r p-6 mb-6 flex items-center gap-5', bannerGradient[overall])}>
              <OverallIcon className={clsx('w-12 h-12 flex-shrink-0', overallCfg.textClass)} />
              <div>
                <p className="text-xs uppercase tracking-widest text-m3-on-surface-variant font-semibold mb-1">{t('admin.health.overall_system_status')}</p>
                <h2 className={clsx('text-4xl font-extrabold', overallCfg.textClass)}>{overall}</h2>
              </div>
            </div>

            {checkedAt && (
              <p className="text-xs text-m3-on-surface-variant mb-6 font-mono">
                Last aggregated at: {new Date(checkedAt).toLocaleString()}
              </p>
            )}

            {/* Subsystem table */}
            <div className="glass-card rounded-2xl border border-m3-outline-variant/20 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[900px]">
                  <thead>
                    <tr className="bg-m3-surface-container-high/40 text-m3-on-surface-variant text-xs uppercase tracking-wider">
                      <th className="p-4 font-semibold">{t('admin.health.subsystem')}</th>
                      <th className="p-4 font-semibold">{t('admin.health.status')}</th>
                      <th className="p-4 font-semibold">{t('admin.health.last_probe')}</th>
                      <th className="p-4 font-semibold">{t('admin.health.freshness')}</th>
                      <th className="p-4 font-semibold">{t('admin.health.telemetry_details')}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-m3-outline-variant/10 text-sm">
                    {Object.keys(subsystems).length === 0 ? (
                      <tr>
                        <td colSpan={5} className="p-12 text-center text-m3-on-surface-variant">
                          <Activity className="w-10 h-10 opacity-30 mx-auto mb-3" />
                          <p className="font-medium text-lg">{t('admin.health.no_health_data_yet')}</p>
                          <p className="text-sm opacity-70">{t('admin.health.force_a_probe_or')}</p>
                        </td>
                      </tr>
                    ) : (
                      Object.entries(subsystems).map(([name, info]: [string, any]) => {
                        const cfg = STATUS_CONFIG[info.status] ?? STATUS_CONFIG.Unknown;
                        const Icon = SUBSYSTEM_ICONS[name] ?? Activity;
                        const lastChecked = info.last_checked_at;
                        const ageMs = lastChecked ? Date.now() - new Date(lastChecked).getTime() : null;
                        const ageSecs = ageMs !== null ? Math.round(ageMs / 1000) : null;

                        return (
                          <tr key={name} className={clsx('transition-colors', cfg.row)}>
                            <td className="p-4">
                              <div className="flex items-center gap-3">
                                <div className={clsx('w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0', cfg.borderBg)}>
                                  <Icon className={clsx('w-5 h-5', cfg.textClass)} />
                                </div>
                                <span className="font-bold text-m3-on-surface capitalize">{name}</span>
                              </div>
                            </td>
                            <td className="p-4">
                              <StatusBadge status={info.status} />
                            </td>
                            <td className="p-4 text-m3-on-surface-variant text-xs font-mono">
                              {lastChecked ? new Date(lastChecked).toLocaleTimeString() : '—'}
                            </td>
                            <td className="p-4">
                              {info.is_stale ? (
                                <span className="text-xs font-bold text-amber-500 flex items-center gap-1">
                                  <AlertTriangle className="w-3.5 h-3.5" />
                                  STALE {ageSecs !== null ? `(${ageSecs}s ago)` : ''}
                                </span>
                              ) : (
                                <span className="text-xs text-green-500 font-medium flex items-center gap-1">
                                  <CheckCircle2 className="w-3.5 h-3.5" />
                                  Fresh {ageSecs !== null ? `(${ageSecs}s ago)` : ''}
                                </span>
                              )}
                            </td>
                            <td className="p-4">
                              {info.details && Object.keys(info.details).length > 0 ? (
                                <div className="flex flex-wrap gap-1.5">
                                  {Object.entries(info.details)
                                    .filter(([k]) => k !== 'error')
                                    .map(([k, v]) => (
                                      <span key={k} className="text-[10px] font-mono bg-m3-surface-container-highest px-2 py-0.5 rounded-md text-m3-on-surface-variant">
                                        {k}: <span className="text-m3-on-surface font-semibold">{String(v)}</span>
                                      </span>
                                    ))}
                                </div>
                              ) : (
                                <span className="text-xs text-m3-on-surface-variant opacity-40">{t('admin.health.no_probe_data')}</span>
                              )}
                              {info.error_message && (
                                <p className="mt-1 text-xs text-red-400 font-mono break-all max-w-xs">{info.error_message}</p>
                              )}
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </ProtectedRoute>
  );
}
