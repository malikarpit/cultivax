/**
 * Crop Card
 */

interface CropCardProps {
  id: string;
  crop_type: string;
  state: string;
  stage?: string;
  sowing_date: string;
  stress_score: number;
  region: string;
}

const stateColors: Record<string, string> = {
  Created: 'bg-blue-500/20 text-blue-400',
  Active: 'bg-green-500/20 text-green-400',
  Delayed: 'bg-yellow-500/20 text-yellow-400',
  AtRisk: 'bg-red-500/20 text-red-400',
  Harvested: 'bg-purple-500/20 text-purple-400',
};

export default function CropCard({
  crop_type,
  state,
  stage,
  sowing_date,
  stress_score,
  region,
}: CropCardProps) {
  return (
    <div className="card hover:scale-[1.02] cursor-pointer">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-lg capitalize">{crop_type}</h3>
          <p className="text-sm text-gray-500">{region}</p>
        </div>
        <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${stateColors[state] || 'bg-gray-500/20 text-gray-400'}`}>
          {state}
        </span>
      </div>

      <div className="space-y-2 text-sm">
        {stage && (
          <div className="flex justify-between">
            <span className="text-gray-400">Stage</span>
            <span>{stage}</span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-gray-400">Sowing Date</span>
          <span>{sowing_date}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Stress</span>
          <span className={stress_score > 0.5 ? 'text-red-400' : 'text-green-400'}>
            {(stress_score * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  );
}
