'use client';

import React, { useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useFetch } from '@/hooks/useFetch';
import { useApi } from '@/hooks/useApi';
import {
  Skull, RefreshCw, AlertTriangle, Play, ChevronRight, Activity, Filter, PackageOpen, Loader2
} from 'lucide-react';
import clsx from 'clsx';
import { toast } from 'sonner';

export default function DLQAdminPage() {
  const [page, setPage] = useState(1);
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [bulkReason, setBulkReason] = useState('');
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const api = useApi();
  const { data, loading, refetch } = useFetch(
    `/api/v1/admin/dead-letters?page=${page}&per_page=50${eventTypeFilter ? `&event_type=${eventTypeFilter}` : ''}`
  );

  const handleSingleRetry = async (eventId: string) => {
    try {
      await api.execute(`/admin/dead-letters/${eventId}/retry`, { method: 'POST' });
      toast.success('Event recovered and placed back in queue');
      refetch();
    } catch (err: any) {
      toast.error(err.message || 'Failed to retry event');
    }
  };

  const handleBulkRetry = async () => {
    if (!bulkReason.trim()) {
      toast.error('A recovery reason is required');
      return;
    }
    
    try {
      const payload: any = {
        reason: bulkReason,
        limit: 100, // Safe batch size
      };
      if (eventTypeFilter) payload.event_type = eventTypeFilter;

      const res = await api.execute('/admin/dead-letters/bulk-retry', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      toast.success(`Bulk recovery successful. Retried: ${res.retried}`);
      setShowBulkModal(false);
      setBulkReason('');
      refetch();
    } catch (err: any) {
      toast.error(err.message || 'Bulk recovery failed');
    }
  };

  const deadLetters = data?.items || [];
  const total = data?.total || 0;

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="animate-fade-in max-w-7xl mx-auto py-8">
        
        {/* Header & Controls */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-m3-on-surface flex items-center gap-3">
              <Skull className="w-8 h-8 text-red-500" />
              Dead Letter Queue
            </h1>
            <p className="text-m3-on-surface-variant mt-2 max-w-2xl">
              Inspect and recover exhausted system events. Events in the DLQ have failed all retry attempts or exceeded their survival TTL.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Filter className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-m3-on-surface-variant" />
              <select
                value={eventTypeFilter}
                onChange={(e) => {
                  setEventTypeFilter(e.target.value);
                  setPage(1);
                }}
                className="pl-9 pr-8 py-2.5 rounded-xl border border-m3-outline-variant/30 bg-m3-surface-container-low text-sm font-medium focus:ring-2 focus:ring-cultivax-primary outline-none appearance-none"
              >
                <option value="">All Event Types</option>
                <option value="RiskAssessment">RiskAssessment</option>
                <option value="WeatherUpdated">WeatherUpdated</option>
                <option value="MediaAnalyzed">MediaAnalyzed</option>
                <option value="YieldSubmitted">YieldSubmitted</option>
              </select>
            </div>

            <button
              onClick={() => refetch()}
              className="p-2.5 rounded-xl border border-m3-outline-variant/30 hover:bg-m3-surface-container-high transition-colors text-m3-on-surface-variant"
              title="Refresh Queue"
            >
              <RefreshCw className={clsx("w-5 h-5", loading && "animate-spin")} />
            </button>

            <button
              onClick={() => setShowBulkModal(true)}
              disabled={deadLetters.length === 0}
              className="px-5 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl shadow-lg transition-colors flex items-center gap-2 font-medium disabled:opacity-50"
            >
              <Activity className="w-4 h-4" />
              Bulk Recovery
            </button>
          </div>
        </div>

        {/* Data Area */}
        {loading && deadLetters.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 opacity-60">
            <Loader2 className="w-12 h-12 animate-spin text-cultivax-primary mb-4" />
            <p className="text-m3-on-surface-variant font-medium">Scanning graves...</p>
          </div>
        ) : deadLetters.length === 0 ? (
          <div className="glass-card rounded-2xl border border-dashed border-m3-outline-variant/40 py-24 flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mb-4">
              <PackageOpen className="w-8 h-8 text-green-500" />
            </div>
            <h3 className="text-xl font-bold text-m3-on-surface mb-2">The Queue is Empty</h3>
            <p className="text-m3-on-surface-variant max-w-md">
              There are no exhausted events waiting for recovery. All backend processes are healthy and executing normally.
            </p>
          </div>
        ) : (
          <div className="glass-card rounded-2xl border border-m3-outline-variant/20 overflow-hidden">
            <div className="bg-red-500/10 border-b border-red-500/20 p-4 flex items-center justify-between">
              <div className="flex items-center gap-2 text-red-500 font-bold">
                <AlertTriangle className="w-5 h-5" />
                {total} Critical Failures Detected
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse min-w-[1000px]">
                <thead>
                  <tr className="bg-m3-surface-container-highest/30 text-m3-on-surface-variant text-xs uppercase tracking-wider">
                    <th className="p-4 font-semibold w-10"></th>
                    <th className="p-4 font-semibold">Event Target</th>
                    <th className="p-4 font-semibold">Decay / Age</th>
                    <th className="p-4 font-semibold">Status Limits</th>
                    <th className="p-4 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-m3-outline-variant/10 text-sm">
                  {deadLetters.map((event: any) => {
                    const isExpanded = expandedRow === event.id;
                    return (
                      <React.Fragment key={event.id}>
                        <tr className={clsx("hover:bg-m3-surface-container-lowest/50 transition-colors group cursor-pointer", isExpanded && "bg-m3-surface-container-lowest")} onClick={() => setExpandedRow(isExpanded ? null : event.id)}>
                          <td className="p-4 text-center">
                            <ChevronRight className={clsx("w-4 h-4 text-m3-on-surface-variant transition-transform", isExpanded && "rotate-90")} />
                          </td>
                          <td className="p-4">
                            <div className="font-bold text-m3-on-surface mb-1 flex items-center gap-2">
                              {event.event_type}
                              <span className="text-[10px] bg-red-500/10 text-red-500 px-2 py-0.5 rounded-full uppercase">DeadLetter</span>
                            </div>
                            <div className="text-xs text-m3-on-surface-variant font-mono">
                              {event.entity_type} : {event.entity_id.split('-')[0]}...
                            </div>
                          </td>
                          <td className="p-4 font-mono text-m3-on-surface-variant">
                            {event.age_seconds > 3600 
                              ? `${(event.age_seconds/3600).toFixed(1)} hrs` 
                              : `${Math.round(event.age_seconds/60)} mins`}
                            <div className="text-[10px] opacity-60 mt-1 uppercase">Stuck in queue</div>
                          </td>
                          <td className="p-4">
                            <div className="text-xs mb-1 font-mono">
                              <span className="text-red-400 font-bold">{event.retry_count}</span> / {event.max_retries} Retries
                            </div>
                            <div className="w-24 h-1.5 bg-m3-surface-container-highest rounded-full overflow-hidden">
                              <div className="h-full bg-red-500 w-full" />
                            </div>
                          </td>
                          <td className="p-4 text-right">
                            <button
                              onClick={(e) => { e.stopPropagation(); handleSingleRetry(event.id); }}
                              disabled={api.loading}
                              className="px-4 py-2 bg-m3-surface-container-high hover:bg-cultivax-primary/20 hover:text-cultivax-primary hover:border-cultivax-primary/50 border border-transparent rounded-xl transition-all text-xs font-bold inline-flex items-center gap-2 disabled:opacity-50"
                            >
                              <Play className="w-3 h-3" />
                              Force Retry
                            </button>
                          </td>
                        </tr>
                        
                        {/* Expanded Details Row */}
                        {isExpanded && (
                          <tr className="bg-m3-surface-container-lowest/50 border-b-0">
                            <td colSpan={5} className="p-0 border-b border-m3-outline-variant/10">
                              <div className="p-6 pt-2 pl-14">
                                <div className="grid grid-cols-2 gap-6 mb-4">
                                  <div>
                                    <h4 className="text-xs uppercase tracking-wider text-m3-on-surface-variant font-bold mb-2">Failure Reason</h4>
                                    <p className="text-sm border-l-2 border-amber-500 pl-3 py-1 bg-amber-500/5 rounded-r-md">
                                      {event.failure_reason || 'Unknown fatal termination'}
                                    </p>
                                  </div>
                                  <div>
                                    <h4 className="text-xs uppercase tracking-wider text-m3-on-surface-variant font-bold mb-2">Timestamps</h4>
                                    <div className="text-xs font-mono text-m3-on-surface-variant space-y-1">
                                      <p>Created: {new Date(event.created_at).toLocaleString()}</p>
                                      <p>Last Misfire: {event.last_failed_at ? new Date(event.last_failed_at).toLocaleString() : 'N/A'}</p>
                                    </div>
                                  </div>
                                </div>
                                {event.last_error && (
                                  <div className="mt-4">
                                    <h4 className="text-xs uppercase tracking-wider text-m3-on-surface-variant font-bold mb-2">Internal Stack Trace</h4>
                                    <pre className="text-[10px] font-mono text-red-400 bg-black/80 p-4 rounded-xl overflow-x-auto border border-red-500/20 whitespace-pre-wrap max-h-64 overflow-y-auto custom-scrollbar">
                                      {event.last_error}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination block */}
            <div className="p-4 border-t border-m3-outline-variant/10 flex items-center justify-between text-sm text-m3-on-surface-variant">
              <span>Showing {deadLetters.length} of {total} records</span>
              <div className="flex items-center gap-2">
                <button
                  disabled={page === 1}
                  onClick={() => setPage(p => p - 1)}
                  className="px-3 py-1 bg-m3-surface-container-high rounded disabled:opacity-30 hover:text-white"
                >
                  Prev
                </button>
                <span className="font-mono">{page}</span>
                <button
                  disabled={deadLetters.length < 50}
                  onClick={() => setPage(p => p + 1)}
                  className="px-3 py-1 bg-m3-surface-container-high rounded disabled:opacity-30 hover:text-white"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}

      </div>

      {/* Bulk Recovery Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="glass-card max-w-md w-full rounded-2xl p-6 shadow-2xl border border-red-500/30">
            <h2 className="text-xl font-bold text-red-500 flex items-center gap-2 mb-2">
              <AlertTriangle className="w-6 h-6" />
              Mass Queue Recovery
            </h2>
            <p className="text-sm text-m3-on-surface-variant mb-6">
              You are about to force retry up to 100 DeadLetter events. {eventTypeFilter ? `Filtered to: ${eventTypeFilter}` : 'No filters applied.'} This will bypass normal throttles and dump them directly into the dispatcher.
            </p>
            
            <div className="mb-6">
              <label className="block text-sm font-bold text-m3-on-surface-variant mb-2">Override Reason (Required)</label>
              <textarea 
                value={bulkReason}
                onChange={e => setBulkReason(e.target.value)}
                placeholder="e.g. Services restored, forcing batch replay"
                className="w-full bg-m3-surface-container-lowest border border-m3-outline-variant/30 rounded-xl p-3 text-sm focus:ring-2 focus:ring-red-500 outline-none resize-none h-24"
              />
            </div>

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowBulkModal(false)}
                className="px-5 py-2.5 rounded-xl font-medium hover:bg-m3-surface-container-high transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleBulkRetry}
                disabled={api.loading || !bulkReason.trim()}
                className="px-5 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl font-bold shadow-lg transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {api.loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                Execute Bulk Recovery
              </button>
            </div>
          </div>
        </div>
      )}
    </ProtectedRoute>
  );
}
