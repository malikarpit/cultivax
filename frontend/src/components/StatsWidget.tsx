/**
 * Stats Widget
 */

interface StatsWidgetProps {
  label: string;
  value: string;
  icon: string;
  color: string;
}

export default function StatsWidget({ label, value, icon, color }: StatsWidgetProps) {
  return (
    <div className="card flex items-center gap-4">
      <div className="text-3xl">{icon}</div>
      <div>
        <p className={`text-2xl font-bold ${color}`}>{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  );
}
