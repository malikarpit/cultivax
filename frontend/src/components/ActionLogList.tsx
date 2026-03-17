'use client';

interface ActionLog {
  id: string;
  action_type: string;
  action_effective_date: string;
  metadata: Record<string, any>;
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
                {new Date(action.action_effective_date).toLocaleDateString()}
              </p>
            </div>
            {action.metadata && Object.keys(action.metadata).length > 0 && (
              <p className="text-sm text-gray-500 mt-1">
                {Object.entries(action.metadata)
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
