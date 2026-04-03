import { useCallback, useEffect, useState } from 'react';
import { offlineQueue } from '@/services/offlineQueue';

export interface UseOfflineActionsOptions {
  cropId?: string;
  autoSync?: boolean;
  syncInterval?: number; // ms
}

export const useOfflineActions = (options: UseOfflineActionsOptions = {}) => {
  const {
    cropId,
    autoSync = true,
    syncInterval = 30000 // 30 seconds
  } = options;

  const [pendingCount, setPendingCount] = useState(0);
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState<string | null>(null);
  const [lastSyncError, setLastSyncError] = useState<string | null>(null);

  // Initialize queue on mount
  useEffect(() => {
    offlineQueue.init().catch(err => {
      console.error('Failed to initialize offline queue:', err);
    });
  }, []);

  // Update pending count
  const updatePendingCount = useCallback(async () => {
    try {
      const actions = await offlineQueue.getPendingActions(cropId || '*');
      setPendingCount(actions.length);
    } catch (error) {
      console.error('Failed to fetch pending count:', error);
    }
  }, [cropId]);

  // Queue action
  const queueAction = useCallback(
    async (
      crop_id: string,
      action_type: string,
      action_effective_date: string,
      metadata?: Record<string, any>
    ) => {
      try {
        const actionId = await offlineQueue.queueAction(
          crop_id,
          action_type,
          action_effective_date,
          metadata
        );

        setPendingCount(prev => prev + 1);
        setLastSyncError(null);

        return actionId;
      } catch (error) {
        const message = (error as Error).message || 'Failed to queue action';
        setLastSyncError(message);
        throw error;
      }
    },
    []
  );

  // Sync to server
  const syncActions = useCallback(async () => {
    setSyncInProgress(true);
    setLastSyncError(null);

    try {
      const authToken = localStorage.getItem('token') || '';
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || '';

      const result = await offlineQueue.syncActions(apiBaseUrl, authToken);

      if (result.failed === 0 && result.synced > 0) {
        setLastSyncTime(new Date().toISOString());
      } else if (result.failed > 0) {
        setLastSyncError(`Failed to sync ${result.failed} actions.`);
      }

      await updatePendingCount();

      return result;
    } catch (error) {
      const message = (error as Error).message || 'Sync failed';
      setLastSyncError(message);
      throw error;
    } finally {
      setSyncInProgress(false);
    }
  }, [updatePendingCount]);

  // Auto-sync on interval
  useEffect(() => {
    if (!autoSync) return;

    const interval = setInterval(() => {
        // Only auto-sync if we have pending actions to save network
        if (pendingCount > 0 && navigator.onLine) {
            syncActions();
        }
    }, syncInterval);
    return () => clearInterval(interval);
  }, [autoSync, syncInterval, syncActions, pendingCount]);

  // Update on mount
  useEffect(() => {
    updatePendingCount();
  }, [updatePendingCount]);

  return {
    pendingCount,
    syncInProgress,
    lastSyncTime,
    lastSyncError,
    queueAction,
    syncActions,
    updatePendingCount
  };
};
