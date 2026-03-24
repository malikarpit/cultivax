/**
 * Alert Banner — Notification/alert display component.
 * Supports severity levels, alert types, timestamps, and acknowledge actions.
 */

'use client';

interface AlertBannerProps {
  id: string;
  alert_type: string;
  severity: string;
  message: string;
  created_at: string;
  is_acknowledged: boolean;
  crop_type?: string;
  onAcknowledge?: (alertId: string) => void;
  compact?: boolean;
}

const severityConfig: Record<string, { icon: string; bg: string; border: string; text: string }> = {
  critical: {
    icon: '🔴',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    text: 'text-red-400',
  },
  high: {
    icon: '🟠',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
    text: 'text-orange-400',
  },
  medium: {
    icon: '🟡',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
    text: 'text-yellow-400',
  },
  low: {
    icon: '🔵',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    text: 'text-blue-400',
  },
};

const alertTypeLabels: Record<string, string> = {
  weather_alert: '🌦 Weather',
  stress_alert: '⚡ Stress',
  pest_alert: '🐛 Pest',
  action_reminder: '📋 Reminder',
  market_alert: '📊 Market',
  harvest_approaching: '🌾 Harvest',
};

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

export default function AlertBanner({
  id,
  alert_type,
  severity,
  message,
  created_at,
  is_acknowledged,
  crop_type,
  onAcknowledge,
  compact = false,
}: AlertBannerProps) {
  const config = severityConfig[severity] || severityConfig.low;
  const typeLabel = alertTypeLabels[alert_type] || alert_type;

  if (compact) {
    return (
      <div
        className={`flex items-center gap-3 px-3 py-2 rounded-lg border ${config.bg} ${config.border} ${
          is_acknowledged ? 'opacity-50' : ''
        }`}
      >
        <span className="text-sm">{config.icon}</span>
        <span className="text-sm flex-1 truncate">{message}</span>
        <span className="text-xs text-gray-500">{formatTimeAgo(created_at)}</span>
      </div>
    );
  }

  return (
    <div
      className={`rounded-xl border p-4 transition-all duration-200 ${config.bg} ${config.border} ${
        is_acknowledged ? 'opacity-60' : 'hover:scale-[1.01]'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        {/* Left: Icon + Content */}
        <div className="flex gap-3 flex-1 min-w-0">
          <span className="text-xl flex-shrink-0 mt-0.5">{config.icon}</span>
          <div className="flex-1 min-w-0">
            {/* Type + Severity badges */}
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs bg-cultivax-card px-2 py-0.5 rounded-full">
                {typeLabel}
              </span>
              <span className={`text-xs font-medium uppercase ${config.text}`}>
                {severity}
              </span>
              {crop_type && (
                <span className="text-xs bg-cultivax-primary/15 text-cultivax-primary px-2 py-0.5 rounded-full capitalize">
                  {crop_type}
                </span>
              )}
            </div>

            {/* Message */}
            <p className="text-sm leading-relaxed">{message}</p>

            {/* Timestamp */}
            <p className="text-xs text-gray-500 mt-1.5">{formatTimeAgo(created_at)}</p>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex-shrink-0">
          {!is_acknowledged && onAcknowledge ? (
            <button
              onClick={() => onAcknowledge(id)}
              className="text-xs bg-cultivax-card hover:bg-cultivax-surface px-3 py-1.5 rounded-lg transition-colors border border-cultivax-card hover:border-cultivax-primary/30"
            >
              Acknowledge
            </button>
          ) : is_acknowledged ? (
            <span className="text-xs text-gray-500 italic">Acknowledged</span>
          ) : null}
        </div>
      </div>
    </div>
  );
}
