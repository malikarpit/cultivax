'use client';

interface SimResult {
  projected_state: string;
  projected_stress: number;
  projected_risk: number;
  projected_day_number: number;
  projected_stage: string | null;
  actions_applied: number;
  warnings: string[];
}

interface SimulationResultProps {
  result: SimResult;
}

export default function SimulationResult({ result }: SimulationResultProps) {
  const stressColor =
    result.projected_stress > 0.7
      ? 'text-red-600'
      : result.projected_stress > 0.4
      ? 'text-yellow-600'
      : 'text-green-600';

  const riskColor =
    result.projected_risk > 0.7
      ? 'text-red-600'
      : result.projected_risk > 0.4
      ? 'text-yellow-600'
      : 'text-green-600';

  return (
    <div className="bg-white border rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Simulation Results</h3>
      <p className="text-sm text-gray-500 mb-4">
        {result.actions_applied} hypothetical action(s) applied — no live data was modified.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-500">Projected State</p>
          <p className="text-lg font-bold">{result.projected_state}</p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-500">Stress Score</p>
          <p className={`text-lg font-bold ${stressColor}`}>
            {(result.projected_stress * 100).toFixed(1)}%
          </p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-500">Risk Index</p>
          <p className={`text-lg font-bold ${riskColor}`}>
            {(result.projected_risk * 100).toFixed(1)}%
          </p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-500">Day Number</p>
          <p className="text-lg font-bold">{result.projected_day_number}</p>
        </div>
      </div>

      {result.warnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="font-medium text-yellow-800 mb-2">⚠️ Warnings</p>
          <ul className="list-disc list-inside text-sm text-yellow-700">
            {result.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
