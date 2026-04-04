import { useCallback, useEffect, useState } from 'react';
import { apiGet } from '@/lib/api';

interface AlertSummaryItem {
  id: string;
}

interface UseUnreadAlertsCountOptions {
  enabled?: boolean;
  pollIntervalMs?: number;
}

export function useUnreadAlertsCount(options: UseUnreadAlertsCountOptions = {}) {
  const { enabled = true, pollIntervalMs = 60000 } = options;
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!enabled) {
      setCount(0);
      return;
    }

    setLoading(true);
    try {
      const alerts = await apiGet<AlertSummaryItem[]>(
        '/api/v1/alerts?unacknowledged_only=true&skip=0&limit=100'
      );
      setCount(Array.isArray(alerts) ? alerts.length : 0);
    } catch {
      // Keep notification UI non-blocking if alerts endpoint is unavailable.
      setCount(0);
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!enabled || pollIntervalMs <= 0) return;
    const intervalId = window.setInterval(() => {
      refresh();
    }, pollIntervalMs);
    return () => window.clearInterval(intervalId);
  }, [enabled, pollIntervalMs, refresh]);

  return { count, loading, refresh };
}
