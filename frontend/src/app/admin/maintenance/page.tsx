'use client';

import React, { useState, useCallback } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useFetch } from '@/hooks/useFetch';
import { useApi } from '@/hooks/useApi';
import {
  Clock, RefreshCw, Play, CheckCircle, AlertTriangle, XCircle,
  Loader2, Zap, ChevronDown, ChevronUp, Shield, Activity
} from 'lucide-react';
import clsx from 'clsx';
import { toast } from 'sonner';

const TASK_LABELS: Record<string, { label: string; cadence: string; icon: string }> = {
  system_health:   { label: 'System Health Check',    cadence: 'Hourly (min 5 min)', icon: '🏥' },
  alert_cleanup:   { label: 'Alert Cleanup',           cadence: 'Hourly (min 30 min)', icon: '🗑️' },
  recommendations: { label: 'Recommendation Refresh', cadence: 'Daily (min 6 h)', icon: '💡' },
  log_compression: { label: 'Log Compression',        cadence: 'Daily (min 6 h)', icon: '📦' },
  trust_decay:     { label: 'Trust Decay',             cadence: 'Weekly (min 24 h)', icon: '⚖️' },
};

function StatusPill({ status }: { status: string }) {
  const base = 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider';
  if (status === 'ok' || status === 'Operational')
    return <span className={clsx(base, 'bg-green-500/15 text-green-400 border border-green-500/20')}><CheckCircle className="w-3 h-3" />{status}</span>;
  if (status === 'skipped')
    return <span className={clsx(base, 'bg-slate-500/15 text-slate-400 border border-slate-500/20')}><Clock className="w-3 h-3" />skipped</span>;
  if (status === 'error' || status === 'all_failed')
    return <span className={clsx(base, 'bg-red-500/15 text-red-400 border border-red-500/20')}><XCircle className="w-3 h-3" />{status}</span>;
  if (status === 'partial_failure')
    return <span className={clsx(base, 'bg-amber-500/15 text-amber-400 border border-amber-500/20')}><AlertTriangle className="w-3 h-3" />partial</span>;
  return <span className={clsx(base, 'bg-m3-surface-container-highest text-m3-on-surface-variant border border-m3-outline-variant/30')}>{status}</span>;
}

function OverdueBadge({ overdue }: { overdue: boolean }) {
  if (!overdue) return null;
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-red-500/10 text-red-400 border border-red-500/20 ml-2 animate-pulse">
      <AlertTriangle className="w-2.5 h-2.5" /> overdue
    </span>
  );
}

export default function AdminMaintenancePage() {
  const { data: status, loading: statusLoading, refetch: refetchStatus } = useFetch('/api/v1/admin/maintenance/status');
  const { execute, loading: triggerLoading } = useApi();

  const [lastRunResult, setLastRunResult] = useState<any>(null);
  const [expandedTask, setExpandedTask] = useState<string | null>(null);
  const [pendingCadence, setPendingCadence] = useState<string>('all');

  const handleTrigger = useCallback(async () => {
    const cadenceParam = pendingCadence === 'all' ? '' : `?cadence=${pendingCadence}`;
    const result = await execute(`/api/v1/admin/maintenance/run${cadenceParam}`, { method: 'POST' });
    if (result) {
      setLastRunResult(result);
      refetchStatus();
      toast.success(`Cron run complete — ${result.overall_status}`);
    }
  }, [pendingCadence, execute, refetchStatus]);

  const tasks = status?.tasks ?? {};
  const lockHeld = status?.lock_held ?? false;

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="animate-fade-in max-w-6xl mx-auto py-8 space-y-8">

        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-m3-on-surface flex items-center gap-3">
              <Activity className="w-8 h-8 text-cultivax-primary" />
              Scheduled Maintenance
            </h1>
            <p className="text-m3-on-surface-variant mt-1 max-w-xl text-sm">
              Operational visibility into all background cron tasks — cadences, failure counts, and live scheduling state.
            </p>
          </div>

          {/* Status Summary Chip */}
          <div className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-xl border text-sm font-medium',
            lockHeld
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
              : 'bg-green-500/10 border-green-500/30 text-green-400'
          )}>
            <Shield className="w-4 h-4" />
            {lockHeld ? 'Run In Progress...' : 'Idle — Ready'}
          </div>
        </div>

        {/* Trigger Controls */}
        <div className="glass-card rounded-2xl p-5 border border-m3-outline-variant/30 bg-m3-surface-container-low flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="flex items-center gap-2 text-m3-on-surface-variant text-sm font-medium min-w-fit">
            <Zap className="w-4 h-4 text-cultivax-primary" /> Manual Trigger
          </div>
          <select
            value={pendingCadence}
            onChange={e => setPendingCadence(e.target.value)}
            className="flex-1 bg-m3-surface border border-m3-outline-variant/30 rounded-xl px-4 py-2 text-sm text-m3-on-surface focus:ring-2 focus:ring-cultivax-primary/50"
          >
            <option value="all">All Tasks</option>
            <option value="hourly">Hourly Tasks Only</option>
            <option value="daily">Daily Tasks Only</option>
            <option value="weekly">Weekly Tasks Only</option>
          </select>
          <button
            onClick={handleTrigger}
            disabled={triggerLoading || lockHeld}
            className="flex items-center gap-2 px-5 py-2.5 bg-cultivax-primary text-white rounded-xl text-sm font-semibold hover:brightness-110 disabled:opacity-50 transition-all shadow-lg shadow-cultivax-primary/20"
          >
            {triggerLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {triggerLoading ? 'Running...' : 'Run Now'}
          </button>
          <button
            onClick={refetchStatus}
            disabled={statusLoading}
            className="p-2.5 border border-m3-outline-variant/40 rounded-xl hover:bg-m3-surface-container-highest transition-colors"
          >
            <RefreshCw className={clsx('w-4 h-4 text-m3-on-surface-variant', statusLoading && 'animate-spin')} />
          </button>
        </div>

        {/* Task Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {Object.entries(TASK_LABELS).map(([key, meta]) => {
            const taskStatus = tasks[key];
            const failures = taskStatus?.consecutive_failures ?? 0;
            const overdue = taskStatus?.overdue ?? false;
            const isExpanded = expandedTask === key;

            return (
              <div
                key={key}
                className={clsx(
                  'glass-card rounded-2xl border transition-all duration-200',
                  overdue ? 'border-red-500/30' : 'border-m3-outline-variant/30',
                  failures >= 3 ? 'bg-red-500/5' : 'bg-m3-surface-container-low'
                )}
              >
                <button
                  onClick={() => setExpandedTask(isExpanded ? null : key)}
                  className="w-full p-5 text-left flex items-start justify-between gap-4"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <span className="text-2xl">{meta.icon}</span>
                    <div className="min-w-0">
                      <div className="flex items-center flex-wrap gap-1">
                        <h3 className="font-bold text-m3-on-surface">{meta.label}</h3>
                        <OverdueBadge overdue={overdue} />
                      </div>
                      <p className="text-xs text-m3-on-surface-variant mt-0.5">{meta.cadence}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {failures > 0 && (
                      <span className="text-[10px] font-bold text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
                        {failures} fail{failures !== 1 ? 's' : ''}
                      </span>
                    )}
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-m3-on-surface-variant" /> : <ChevronDown className="w-4 h-4 text-m3-on-surface-variant" />}
                  </div>
                </button>

                {/* Expanded Detail */}
                {isExpanded && (
                  <div className="px-5 pb-5 space-y-3 border-t border-m3-outline-variant/20 pt-4">
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <p className="text-m3-on-surface-variant uppercase tracking-wider mb-1">Last Run</p>
                        <p className="font-mono text-m3-on-surface">
                          {taskStatus?.last_run
                            ? new Date(taskStatus.last_run).toLocaleString()
                            : <span className="text-m3-on-surface-variant/50 italic">never</span>}
                        </p>
                      </div>
                      <div>
                        <p className="text-m3-on-surface-variant uppercase tracking-wider mb-1">Next Eligible</p>
                        <p className={clsx('font-mono', overdue ? 'text-red-400' : 'text-m3-on-surface')}>
                          {taskStatus?.next_eligible_run
                            ? new Date(taskStatus.next_eligible_run).toLocaleString()
                            : <span className="text-green-400 italic">ready now</span>}
                        </p>
                      </div>
                      <div>
                        <p className="text-m3-on-surface-variant uppercase tracking-wider mb-1">Min Interval</p>
                        <p className="font-mono text-m3-on-surface">
                          {taskStatus?.min_interval_seconds ? `${taskStatus.min_interval_seconds}s` : '—'}
                        </p>
                      </div>
                      <div>
                        <p className="text-m3-on-surface-variant uppercase tracking-wider mb-1">Consecutive Failures</p>
                        <p className={clsx('font-bold', failures >= 3 ? 'text-red-400' : failures > 0 ? 'text-amber-400' : 'text-green-400')}>
                          {failures}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Last Run Result */}
        {lastRunResult && (
          <div className="glass-card rounded-2xl border border-m3-outline-variant/30 overflow-hidden">
            <div className="p-5 border-b border-m3-outline-variant/20 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-cultivax-primary" />
                <div>
                  <h3 className="font-bold text-m3-on-surface">Last Run Result</h3>
                  <p className="text-xs text-m3-on-surface-variant font-mono">run_id: {lastRunResult.run_id}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <StatusPill status={lastRunResult.overall_status} />
                <span className="text-xs text-m3-on-surface-variant">{lastRunResult.elapsed_seconds}s</span>
              </div>
            </div>
            <div className="divide-y divide-m3-outline-variant/10">
              {Object.entries(lastRunResult.tasks ?? {}).map(([key, result]: [string, any]) => (
                <div key={key} className="px-5 py-3 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-3">
                    <span>{TASK_LABELS[key]?.icon ?? '⚙️'}</span>
                    <span className="font-medium text-m3-on-surface">{TASK_LABELS[key]?.label ?? key}</span>
                    {result.error && (
                      <span className="text-[11px] text-red-400 font-mono truncate max-w-[200px]" title={result.error}>
                        {result.error}
                      </span>
                    )}
                    {result.reason && (
                      <span className="text-[11px] text-m3-on-surface-variant/60 italic">{result.reason}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-xs text-m3-on-surface-variant font-mono">{result.duration_ms ? `${result.duration_ms}ms` : ''}</span>
                    <StatusPill status={result.status} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Server Time Info */}
        {status?.server_time && (
          <p className="text-center text-xs text-m3-on-surface-variant/50 font-mono">
            Server time at last fetch: {new Date(status.server_time).toLocaleString()}
          </p>
        )}

      </div>
    </ProtectedRoute>
  );
}
