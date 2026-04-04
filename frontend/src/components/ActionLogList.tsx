'use client';

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
  if (actions.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No actions logged yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {actions.map((action) => (
        <div
          key={action.id}
          className="flex items-start gap-3 p-4 bg-white rounded-lg border hover:shadow-sm transition-shadow"
        >
          <span className="text-2xl">
            {actionIcons[action.action_type] || '📝'}
          </span>
          <div className="flex-1">
            <div className="flex justify-between items-start">
              <p className="font-medium capitalize">
                {action.action_type.replace('_', ' ')}
              </p>
              <p className="text-sm text-gray-400">
                {new Date(action.effective_date || action.created_at).toLocaleDateString()}
              </p>
            </div>
            {action.action_subtype ? (
              <p className="text-sm text-gray-500 mt-1">Subtype: {action.action_subtype}</p>
            ) : null}
            <div className="text-xs mt-1 flex gap-2 items-center flex-wrap">
              {action.source && <span className="bg-gray-100 px-2 py-0.5 rounded text-gray-600">Source: {action.source}</span>}
              {action.action_impact_type && <span className="bg-blue-50 px-2 py-0.5 rounded text-blue-600">Impact: {action.action_impact_type.replace('_', ' ')}</span>}
              {action.applied_in_replay && (
                 <span className="bg-green-50/20 border border-green-500/30 px-2 py-0.5 rounded text-green-500 font-medium">✨ Applied in Replay</span>
              )}
              {action.is_orphaned && (
                 <span className="bg-red-50/20 border border-red-500/30 px-2 py-0.5 rounded text-red-500 font-medium">⚠️ Orphaned</span>
              )}
            </div>
            {action.metadata_json && Object.keys(action.metadata_json).length > 0 && (
              <p className="text-sm text-gray-500 mt-2 bg-gray-50/50 p-2 rounded border border-gray-100">
                {Object.entries(action.metadata_json)
                  .map(([k, v]) => `${k}: ${v}`)
                  .join(' • ')}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
