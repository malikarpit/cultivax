'use client';

/**
 * useOnlineSync — Global online/offline sync coordinator.
 *
 * Responsibilities:
 * - Listens to browser online/offline events globally.
 * - When connectivity is restored, waits 2 s then auto-triggers
 *   offlineQueue.syncActions() if there are pending actions.
 * - Listens for the SYNC_OFFLINE_ACTIONS postMessage from the custom
 *   service worker (background sync path).
 * - Shows sonner toasts for sync start / success / failure.
 *
 * Usage: mount once inside <LayoutShell> (authenticated shell only).
 */

import { useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { offlineQueue } from '@/services/offlineQueue';

export function useOnlineSync() {
  const syncInFlight = useRef(false);

  /**
   * Core sync runner — deduplicates concurrent calls.
   */
  const runSync = async (source: 'online-event' | 'sw-message' | 'manual') => {
    if (syncInFlight.current) return;
    syncInFlight.current = true;

    let toastId: string | number | undefined;
    try {
      // Ensure queue is initialised (idempotent)
      await offlineQueue.init();

      const pending = await offlineQueue.getPendingActions('*');
      if (pending.length === 0) {
        syncInFlight.current = false;
        return;
      }

      toastId = toast.loading(
        `Syncing ${pending.length} queued action${pending.length > 1 ? 's' : ''}…`,
        { id: 'cultivax-sync' }
      );

      const result = await offlineQueue.syncActions();

      if (result.synced > 0 && result.failed === 0) {
        toast.success(
          `✅ ${result.synced} action${result.synced > 1 ? 's' : ''} synced successfully`,
          { id: 'cultivax-sync', duration: 4000 }
        );
      } else if (result.failed > 0) {
        toast.warning(
          `⚡ Synced ${result.synced}, failed ${result.failed}. Will retry automatically.`,
          { id: 'cultivax-sync', duration: 5000 }
        );
      }
    } catch (err) {
      console.error('[useOnlineSync] Sync error:', err);
      if (toastId) {
        toast.error('Sync failed. Will retry when online.', {
          id: 'cultivax-sync',
          duration: 4000,
        });
      }
    } finally {
      syncInFlight.current = false;
    }
  };

  useEffect(() => {
    if (typeof window === 'undefined') return;

    // ── 1. Online event: connection restored ────────────────────────
    const handleOnline = () => {
      // Small delay so the network stack is fully up
      setTimeout(() => {
        if (navigator.onLine) runSync('online-event');
      }, 2000);
    };

    // ── 2. Service Worker postMessage (background sync path) ────────
    const handleSwMessage = (event: MessageEvent) => {
      if (event.data?.type === 'SYNC_OFFLINE_ACTIONS') {
        runSync('sw-message');
      }
    };

    window.addEventListener('online', handleOnline);
    navigator.serviceWorker?.addEventListener('message', handleSwMessage);

    // ── 3. Initial check on mount (e.g. came back online before load) ─
    if (navigator.onLine) {
      // Fire after a tick so the UI renders first
      setTimeout(() => runSync('online-event'), 500);
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      navigator.serviceWorker?.removeEventListener('message', handleSwMessage);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
