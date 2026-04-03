import React from 'react';
import { useOfflineActions } from '@/hooks/useOfflineActions';
import { useTranslations } from 'next-intl';
import { WifiOff, RefreshCcw, Activity } from 'lucide-react';

interface OfflineSyncStatusProps {
  cropId?: string;
  showActions?: boolean;
}

export const OfflineSyncStatus: React.FC<OfflineSyncStatusProps> = ({
  cropId,
  showActions = true
}) => {
  const t = useTranslations();
  const {
    pendingCount,
    syncInProgress,
    lastSyncTime,
    lastSyncError,
    syncActions
  } = useOfflineActions({ cropId });

  if (pendingCount === 0 && !lastSyncError) return null;

  return (
    <div className="glass-card mb-6 overflow-hidden border border-m3-warning/20 bg-gradient-to-r from-m3-warning/5 to-transparent">
      <div className="h-1 w-full bg-m3-warning" />
      <div className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-m3-warning/10 flex items-center justify-center text-m3-warning">
            <WifiOff className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-m3-on-surface">
              Offline Actions Queued
            </h3>
            <p className="text-sm text-m3-on-surface-variant">
              {pendingCount} action(s) waiting to sync
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-5">
          {/* Pending Count */}
          <div className="rounded-xl bg-m3-surface-container-highest p-4">
            <p className="mono-label mb-1">Queue Size</p>
            <p className="text-xl font-bold text-m3-warning font-mono tracking-tight">{pendingCount}</p>
          </div>

          {/* Last Sync */}
          {lastSyncTime && (
            <div className="rounded-xl bg-m3-surface-container-highest p-4">
              <p className="mono-label mb-1">Last Sync</p>
              <p className="text-xl font-bold text-m3-success font-mono tracking-tight text-sm">
                {new Date(lastSyncTime).toLocaleTimeString()}
              </p>
              <p className="text-[10px] text-m3-on-surface-variant uppercase tracking-widest mt-1">Successful</p>
            </div>
          )}

          {/* Sync Error */}
          {lastSyncError && (
            <div className="rounded-xl bg-m3-surface-container-highest p-4 col-span-1 sm:col-span-3 lg:col-span-1">
              <p className="mono-label mb-1">Last Error</p>
              <p className="text-sm font-bold text-m3-error">{lastSyncError}</p>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <button
            onClick={syncActions}
            disabled={syncInProgress || pendingCount === 0 || !navigator.onLine}
            className="w-full sm:w-auto px-6 py-2.5 bg-m3-primary text-m3-on-primary rounded-xl font-bold text-sm shadow flex items-center justify-center gap-2 hover:bg-m3-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {syncInProgress ? (
              <RefreshCcw className="w-4 h-4 animate-spin" />
            ) : (
              <Activity className="w-4 h-4" />
            )}
            {syncInProgress ? 'Syncing...' : 'Sync Now'}
          </button>

          {pendingCount > 0 && !navigator.onLine && (
            <p className="text-sm text-m3-on-surface-variant">
              Internet connection required to sync.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
