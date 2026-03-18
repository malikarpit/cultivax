'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import SimulationResult from '@/components/SimulationResult';

interface SimResult {
  projected_state: string;
  projected_stress: number;
  projected_risk: number;
  projected_day_number: number;
  projected_stage: string | null;
  actions_applied: number;
  warnings: string[];
}

export default function SimulatePage() {
  const params = useParams();
  const [actions, setActions] = useState([
    { action_type: 'irrigation', action_date: '' },
  ]);
  const [result, setResult] = useState<SimResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const addAction = () => {
    setActions([...actions, { action_type: 'irrigation', action_date: '' }]);
  };

  const removeAction = (idx: number) => {
    setActions(actions.filter((_, i) => i !== idx));
  };

  const updateAction = (idx: number, field: string, value: string) => {
    const updated = [...actions];
    (updated[idx] as any)[field] = value;
    setActions(updated);
  };

  const runSimulation = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/crops/${params.id}/simulate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify({ hypothetical_actions: actions }),
        }
      );
      if (!res.ok) throw new Error('Simulation failed');
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">What-If Simulation</h1>
      <p className="text-gray-500 mb-6">
        Test hypothetical actions without affecting your actual crop data.
      </p>

      {/* Action editor */}
      <div className="space-y-3 mb-6">
        {actions.map((action, idx) => (
          <div key={idx} className="flex gap-3 items-center">
            <select
              value={action.action_type}
              onChange={(e) => updateAction(idx, 'action_type', e.target.value)}
              className="flex-1 px-3 py-2 border rounded-lg"
            >
              <option value="irrigation">Irrigation</option>
              <option value="fertilizer">Fertilizer</option>
              <option value="pesticide">Pesticide</option>
              <option value="weeding">Weeding</option>
              <option value="inspection">Inspection</option>
              <option value="delayed_action">Delayed Action</option>
            </select>
            <input
              type="date"
              value={action.action_date}
              onChange={(e) => updateAction(idx, 'action_date', e.target.value)}
              className="px-3 py-2 border rounded-lg"
            />
            {actions.length > 1 && (
              <button
                onClick={() => removeAction(idx)}
                className="text-red-500 hover:text-red-700"
              >
                ✕
              </button>
            )}
          </div>
        ))}
      </div>

      <div className="flex gap-3 mb-8">
        <button
          onClick={addAction}
          className="px-4 py-2 border rounded-lg hover:bg-gray-50"
        >
          + Add Action
        </button>
        <button
          onClick={runSimulation}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Running...' : 'Run Simulation'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4">{error}</div>
      )}

      {result && <SimulationResult result={result} />}
    </div>
  );
}
