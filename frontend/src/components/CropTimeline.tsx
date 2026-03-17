'use client';

interface CropTimelineProps {
  stage: string;
  dayNumber: number;
  state: string;
}

const STAGES = [
  { name: 'Germination', days: '0-14' },
  { name: 'Seedling', days: '15-30' },
  { name: 'Vegetative', days: '31-60' },
  { name: 'Flowering', days: '61-80' },
  { name: 'Fruiting', days: '81-110' },
  { name: 'Maturity', days: '111-130' },
  { name: 'Harvest', days: '131+' },
];

export default function CropTimeline({ stage, dayNumber, state }: CropTimelineProps) {
  const currentStageIdx = STAGES.findIndex(
    (s) => s.name.toLowerCase() === (stage || '').toLowerCase()
  );

  return (
    <div className="relative">
      <div className="flex items-center justify-between">
        {STAGES.map((s, idx) => {
          const isCompleted = idx < currentStageIdx;
          const isCurrent = idx === currentStageIdx;
          const isFuture = idx > currentStageIdx;

          return (
            <div key={s.name} className="flex flex-col items-center flex-1">
              {/* Connector line */}
              {idx > 0 && (
                <div
                  className={`absolute h-0.5 ${
                    isCompleted ? 'bg-green-500' : 'bg-gray-200'
                  }`}
                  style={{
                    left: `${((idx - 0.5) / STAGES.length) * 100}%`,
                    width: `${(1 / STAGES.length) * 100}%`,
                    top: '12px',
                  }}
                />
              )}

              {/* Stage marker */}
              <div
                className={`w-6 h-6 rounded-full border-2 z-10 flex items-center justify-center ${
                  isCompleted
                    ? 'bg-green-500 border-green-500'
                    : isCurrent
                    ? 'bg-blue-500 border-blue-500 ring-2 ring-blue-200'
                    : 'bg-white border-gray-300'
                }`}
              >
                {isCompleted && (
                  <span className="text-white text-xs">✓</span>
                )}
                {isCurrent && (
                  <span className="text-white text-xs">●</span>
                )}
              </div>

              {/* Label */}
              <p
                className={`text-xs mt-2 text-center ${
                  isCurrent ? 'font-bold text-blue-600' : 'text-gray-500'
                }`}
              >
                {s.name}
              </p>
              <p className="text-xs text-gray-400">{s.days}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
