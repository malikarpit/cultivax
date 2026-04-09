'use client';

/**
 * Admin — Dead Letter Queue Management
 *
 * View and retry failed events from the dead letter queue.
 * GET  /api/v1/admin/dead-letters
 * POST /api/v1/admin/dead-letters/{id}/retry
 */

import { useEffect, useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useApi } from '@/hooks/useApi';
import { useTranslation } from 'react-i18next';

interface DeadLetter {
  id: string;
  event_type: string;
  payload: any;
  failure_reason: string;
  retry_count: number;
  status: string;
  created_at: string;
  last_retry_at?: string;
}

export default function DeadLettersPage() {
  const { t } = useTranslation();
  const dlqApi = useApi<DeadLetter[]>();
  const retryApi = useApi();
  const [retrying, setRetrying] = useState<string | null>(null);

  useEffect(() => {
    dlqApi.execute('/api/v1/admin/dead-letters').catch(() => {});
  }, []);

  const handleRetry = async (id: string) => {
    setRetrying(id);
    try {
      await retryApi.execute(`/api/v1/admin/dead-letters/${id}/retry`, { method: 'POST' });
      dlqApi.execute('/api/v1/admin/dead-letters').catch(() => {});
    } catch {} finally {
      setRetrying(null);
    }
  };

  const items = dlqApi.data || [];

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      Failed: 'bg-red-500/20 text-red-400',
      Retry: 'bg-yellow-500/20 text-yellow-400',
      Resolved: 'bg-green-500/20 text-green-400',
    };
    return map[status] || 'bg-gray-500/20 text-gray-400';
  };

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{t('admin.dead-letters.dead_letter_queue')}</h1>
            <p className="text-gray-400 mt-1">{t('admin.dead-letters.failed_events_requiring_attention')}</p>
          </div>
          <button
            className="text-sm text-cultivax-primary hover:underline"
            onClick={() => dlqApi.execute('/api/v1/admin/dead-letters').catch(() => {})}
          >
            ↻ Refresh
          </button>
        </div>

        {dlqApi.loading && (
          <div className="card text-center py-8">
            <div className="inline-block w-8 h-8 border-2 border-cultivax-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!dlqApi.loading && items.length === 0 && (
          <div className="card text-center py-12 text-gray-500">
            <p className="text-5xl mb-4">✅</p>
            <p className="text-lg font-medium">{t('admin.dead-letters.no_dead_letters')}</p>
            <p className="text-sm mt-1">{t('admin.dead-letters.all_events_processed_successfully')}</p>
          </div>
        )}

        {items.length > 0 && (
          <div className="space-y-3">
            {items.map((dl) => (
              <div key={dl.id} className="card">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-medium text-sm font-mono">{dl.event_type}</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusBadge(dl.status)}`}>
                        {dl.status}
                      </span>
                    </div>
                    <p className="text-sm text-red-400">{dl.failure_reason}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Retries: {dl.retry_count} • Created: {new Date(dl.created_at).toLocaleString()}
                    </p>
                  </div>
                  {dl.status !== 'Resolved' && (
                    <button
                      onClick={() => handleRetry(dl.id)}
                      disabled={retrying === dl.id}
                      className="text-xs bg-cultivax-primary/20 text-cultivax-primary px-3 py-1.5 rounded-lg hover:bg-cultivax-primary/30 transition"
                    >
                      {retrying === dl.id ? 'Retrying...' : 'Retry'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
