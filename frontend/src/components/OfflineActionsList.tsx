import React, { useEffect, useState } from 'react';
import { offlineQueue } from '@/services/offlineQueue';
import { useTranslations } from 'next-intl';

interface QueuedAction {
  id: string;
  crop_id: string;
  action_type: string;
  action_effective_date: string;
  local_seq_no: number;
  status: 'pending' | 'syncing' | 'synced' | 'failed';
  error?: string;
  attempts: number;
}

interface OfflineActionsListProps {
  cropId?: string;
}

export const OfflineActionsList: React.FC<OfflineActionsListProps> = ({
  cropId
}) => {
  const t = useTranslations();
  const [actions, setActions] = useState<QueuedAction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadActions = async () => {
      try {
        let allActions = await offlineQueue.getAllQueuedActions();
        if (cropId) {
          allActions = allActions.filter(a => a.crop_id === cropId);
        }
        setActions(allActions);
      } catch (error) {
        console.error('Failed to load actions:', error);
      } finally {
        setLoading(false);
      }
    };

    loadActions();
    // Refresh every 2 seconds
    const interval = setInterval(loadActions, 2000);
    return () => clearInterval(interval);
  }, [cropId]);

  if (loading) return <div className="loading loading-spinner"></div>;
  if (actions.length === 0) return null; // Dont show if empty

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return 'badge-warning';
      case 'syncing':
        return 'badge-info';
      case 'synced':
        return 'badge-success';
      case 'failed':
        return 'badge-error';
      default:
        return 'badge';
    }
  };

  return (
    <div className="glass-card rounded-xl p-8 border border-m3-outline-variant/10 shadow mt-6">
      <div className="">
        <h3 className="text-lg font-bold text-m3-on-surface mb-4">Queued Actions ({actions.length})</h3>

        <div className="overflow-x-auto rounded-lg border border-m3-outline-variant/20">
          <table className="table w-full text-sm">
            <thead>
              <tr className="bg-m3-surface-container-highest text-m3-on-surface-variant font-mono text-[11px] uppercase tracking-wider">
                <th className="py-3 px-4">#</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Attempts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-m3-outline-variant/10 text-m3-on-surface">
              {actions.map((action, idx) => (
                <tr key={action.id} className="hover:bg-m3-surface-container-high transition-colors">
                  <td className="py-3 px-4">{idx + 1}</td>
                  <td className="py-3 px-4 font-semibold capitalize">{action.action_type.replace('_', ' ')}</td>
                  <td className="py-3 px-4 text-xs font-mono text-m3-on-surface-variant">{new Date(action.action_effective_date).toLocaleDateString()}</td>
                  <td className="py-3 px-4">
                    <span className={`badge badge-sm font-mono uppercase tracking-wider ${getStatusBadge(action.status)}`}>
                      {action.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">{action.attempts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {actions.some(a => a.status === 'failed') && (
          <div className="bg-m3-error/10 text-m3-error rounded-xl p-4 flex items-center gap-3 mt-4 text-sm font-medium">
            ⚠️ Some actions failed to sync. Review the list and try again.
          </div>
        )}
      </div>
    </div>
  );
};
