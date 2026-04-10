'use client';

import { useTranslation } from 'react-i18next';

interface ActionLog {
  id: string;
  action_type: string;
  action_subtype?: string;
  effective_date?: string;
  metadata_json?: Record<string, any>;
  source?: string;
  action_impact_type?: string;
  applied_in_replay?: boolean;
  is_orphaned?: boolean;
  created_at: string;
}

interface ActionLogListProps {
  actions: ActionLog[];
}

const actionIcons: Record<string, string> = {
  irrigation: '💧',
  fertilizer: '🌿',
  pesticide: '🛡️',
  weeding: '🪴',
  inspection: '🔍',
  sowing: '🌱',
  harvest: '🌾',
};

export default function ActionLogList({ actions }: ActionLogListProps) {
  const { t } = useTranslation();

  if (actions.length === 0) {
    return (
      <div className="card text-center py-8 text-cultivax-text-muted">
        {t('common.actionLog.noActions')}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {actions.map((action) => (
        <div
          key={action.id}
          className="flex items-start gap-3 p-4 bg-cultivax-surface rounded-xl border border-cultivax-border hover:border-cultivax-border/80 hover:bg-cultivax-elevated transition-colors"
        >
          <span className="text-2xl mt-0.5">
            {actionIcons[action.action_type] || '📝'}
          </span>
          <div className="flex-1">
            <div className="flex justify-between items-start">
              <p className="font-semibold text-cultivax-text-primary capitalize">
                {action.action_type.replace('_', ' ')}
              </p>
              <p className="text-xs font-medium text-cultivax-text-muted">
                {new Date(action.effective_date || action.created_at).toLocaleDateString()}
              </p>
            </div>
            {action.action_subtype ? (
              <p className="text-sm text-cultivax-text-secondary mt-1">{t('common.actionLog.subtype')}: {action.action_subtype}</p>
            ) : null}
            <div className="text-xs mt-2 flex gap-2 items-center flex-wrap font-medium">
              {action.source && <span className="bg-cultivax-elevated px-2 py-0.5 rounded text-cultivax-text-secondary border border-cultivax-border/50">{t('common.actionLog.source')}: {action.source}</span>}
              {action.action_impact_type && <span className="bg-blue-500/10 px-2 py-0.5 rounded text-blue-400 border border-blue-500/20">{t('common.actionLog.impact')}: {action.action_impact_type.replace('_', ' ')}</span>}
              {action.applied_in_replay && (
                 <span className="bg-green-500/10 border border-green-500/20 px-2 py-0.5 rounded text-green-400">{t('common.actionLog.appliedInReplay')}</span>
              )}
              {action.is_orphaned && (
                 <span className="bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded text-red-400">{t('common.actionLog.orphaned')}</span>
              )}
            </div>
            {action.metadata_json && Object.keys(action.metadata_json).length > 0 && (
              <div className="text-xs text-cultivax-text-muted mt-3 bg-cultivax-bg/50 p-2.5 rounded-lg border border-cultivax-border font-mono overflow-x-auto">
                {Object.entries(action.metadata_json)
                  .map(([k, v]) => `${k}: ${v}`)
                  .join(' • ')}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
