'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import { FlaskConical, Plus, Trash2, Play, AlertTriangle, Loader2 } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import SimulationResult from '@/components/SimulationResult';
import { simulateCrop } from '@/lib/api';
import type {
  HypotheticalAction,
  SimulationActionType,
  SimulationResponse,
} from '@/lib/types';

const ACTION_TYPES: { value: SimulationActionType; label: string }[] = [
  { value: 'irrigation', label: 'Irrigation' },
  { value: 'fertilizer', label: 'Fertilizer' },
  { value: 'pesticide', label: 'Pesticide' },
  { value: 'weeding', label: 'Weeding' },
  { value: 'inspection', label: 'Inspection' },
  { value: 'delayed_action', label: 'Delayed Action' },
];

export default function SimulatePage() {
  const params = useParams();
  const { t } = useTranslation();
  const [actions, setActions] = useState<HypotheticalAction[]>([
    { action_type: 'irrigation', action_date: '' },
  ]);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const addAction = () => {
    setActions([...actions, { action_type: 'irrigation', action_date: '' }]);
  };

  const removeAction = (idx: number) => {
    setActions(actions.filter((_, i) => i !== idx));
  };

  const updateAction = (idx: number, field: 'action_type' | 'action_date', value: string) => {
    const updated = [...actions];
    if (field === 'action_type') {
      updated[idx] = { ...updated[idx], action_type: value as SimulationActionType };
    } else {
      updated[idx] = { ...updated[idx], action_date: value };
    }
    setActions(updated);
  };

  const runSimulation = async () => {
    setLoading(true);
    setError('');
    try {
      const normalizedActions: HypotheticalAction[] = actions.map((action) => ({
        ...action,
        action_date: action.action_date?.trim() ? action.action_date : undefined,
      }));
      const data = await simulateCrop(String(params.id), {
        hypothetical_actions: normalizedActions,
      });
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Simulation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute requiredRole="farmer">
      <div className="animate-fade-in space-y-8">
        {/* Header */}
        <header>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-m3-primary/15 flex items-center justify-center">
              <FlaskConical className="w-5 h-5 text-m3-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-m3-on-surface tracking-tight">
                {t('simulation.title', { defaultValue: 'What-If Simulation' })}
              </h1>
              <p className="text-sm text-m3-on-surface-variant">
                {t('simulation.subtitle', { defaultValue: 'Test hypothetical actions without affecting your actual crop data.' })}
              </p>
            </div>
          </div>
        </header>

        {/* Action Editor */}
        <section className="glass-card rounded-2xl border border-m3-outline-variant/10 p-6">
          <p className="mono-label mb-4">Hypothetical Actions</p>

          <div className="space-y-3 mb-6">
            {actions.map((action, idx) => (
              <div
                key={idx}
                className="flex gap-3 items-center p-3 rounded-xl bg-m3-surface-container-low border border-m3-outline-variant/10"
              >
                <select
                  value={action.action_type}
                  onChange={(e) => updateAction(idx, 'action_type', e.target.value)}
                  className="flex-1 px-3 py-2 rounded-lg bg-m3-surface-container border border-m3-outline-variant/20 text-m3-on-surface text-sm font-medium focus:outline-none focus:ring-2 focus:ring-m3-primary/40"
                  aria-label={`Action type ${idx + 1}`}
                >
                  {ACTION_TYPES.map((at) => (
                    <option key={at.value} value={at.value}>
                      {t(`simulation.actionTypes.${at.value}`, { defaultValue: at.label })}
                    </option>
                  ))}
                </select>
                <input
                  type="date"
                  value={action.action_date}
                  onChange={(e) => updateAction(idx, 'action_date', e.target.value)}
                  className="px-3 py-2 rounded-lg bg-m3-surface-container border border-m3-outline-variant/20 text-m3-on-surface text-sm focus:outline-none focus:ring-2 focus:ring-m3-primary/40"
                  aria-label={`Action date ${idx + 1}`}
                />
                {actions.length > 1 && (
                  <button
                    onClick={() => removeAction(idx)}
                    className="p-2 rounded-lg text-m3-error hover:bg-m3-error/10 transition-colors"
                    aria-label={t('simulation.removeAction', { defaultValue: 'Remove action' })}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>

          <div className="flex gap-3">
            <button
              onClick={addAction}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-m3-outline-variant/20 bg-m3-surface-container-low text-sm font-semibold text-m3-on-surface hover:bg-m3-surface-container-high transition-colors"
            >
              <Plus className="w-4 h-4" />
              {t('simulation.addAction', { defaultValue: 'Add Action' })}
            </button>
            <button
              onClick={runSimulation}
              disabled={loading}
              className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              {loading
                ? t('simulation.running', { defaultValue: 'Running...' })
                : t('simulation.runSimulation', { defaultValue: 'Run Simulation' })}
            </button>
          </div>
        </section>

        {/* Error */}
        {error && (
          <div className="glass-card rounded-xl border border-m3-error/20 p-4 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-m3-error flex-shrink-0" />
            <p className="text-sm font-medium text-m3-error">{error}</p>
          </div>
        )}

        {/* Results */}
        {result && (
          <section className="glass-card rounded-2xl border border-m3-outline-variant/10 p-6">
            <p className="mono-label mb-4">Simulation Results</p>
            <SimulationResult result={result} />
          </section>
        )}
      </div>
    </ProtectedRoute>
  );
}
