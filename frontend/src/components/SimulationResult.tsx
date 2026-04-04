'use client';

import type { SimulationResponse } from '@/lib/types';
import { useTranslation } from 'react-i18next';

interface SimulationResultProps {
  result: SimulationResponse;
}

export default function SimulationResult({ result }: SimulationResultProps) {
  const { t } = useTranslation();
  const stressColor =
    result.projected_state.stress > 0.7
      ? 'text-red-600'
      : result.projected_state.stress > 0.4
      ? 'text-yellow-600'
      : 'text-green-600';

  const riskColor =
    result.projected_state.risk > 0.7
      ? 'text-red-600'
      : result.projected_state.risk > 0.4
      ? 'text-yellow-600'
      : 'text-green-600';

  const formatDelta = (value: number, percent = false) => {
    const n = percent ? value * 100 : value;
    const sign = n > 0 ? '+' : '';
    return `${sign}${n.toFixed(2)}${percent ? '%' : ''}`;
  };

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold mb-2">{t('simulation.results', { defaultValue: 'Simulation Results' })}</h3>
      <p className="text-sm text-cultivax-text-muted mb-4">
        {t('simulation.actionsApplied', {
          defaultValue: '{{count}} hypothetical action(s) applied. Live crop data remains unchanged.',
          count: result.actions_applied,
        })}
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-cultivax-elevated rounded-lg p-4">
          <p className="text-xs text-cultivax-text-muted uppercase tracking-wide mb-2">{t('simulation.current', { defaultValue: 'Current' })}</p>
          <div className="space-y-1 text-sm">
            <p>{t('simulation.stateLabel', { defaultValue: 'State' })}: <span className="font-medium">{result.current_state.state}</span></p>
            <p>{t('simulation.stressLabel', { defaultValue: 'Stress' })}: <span className="font-medium">{(result.current_state.stress * 100).toFixed(1)}%</span></p>
            <p>{t('simulation.riskLabel', { defaultValue: 'Risk' })}: <span className="font-medium">{(result.current_state.risk * 100).toFixed(1)}%</span></p>
            <p>{t('simulation.dayLabel', { defaultValue: 'Day' })}: <span className="font-medium">{result.current_state.day_number}</span></p>
            <p>{t('simulation.stageLabel', { defaultValue: 'Stage' })}: <span className="font-medium">{result.current_state.stage || t('simulation.notAvailable', { defaultValue: 'N/A' })}</span></p>
          </div>
        </div>

        <div className="bg-cultivax-elevated rounded-lg p-4">
          <p className="text-xs text-cultivax-text-muted uppercase tracking-wide mb-2">{t('simulation.projected', { defaultValue: 'Projected' })}</p>
          <div className="space-y-1 text-sm">
            <p>{t('simulation.stateLabel', { defaultValue: 'State' })}: <span className="font-medium">{result.projected_state.state}</span></p>
            <p>{t('simulation.stressLabel', { defaultValue: 'Stress' })}: <span className={`font-medium ${stressColor}`}>{(result.projected_state.stress * 100).toFixed(1)}%</span></p>
            <p>{t('simulation.riskLabel', { defaultValue: 'Risk' })}: <span className={`font-medium ${riskColor}`}>{(result.projected_state.risk * 100).toFixed(1)}%</span></p>
            <p>{t('simulation.dayLabel', { defaultValue: 'Day' })}: <span className="font-medium">{result.projected_state.day_number}</span></p>
            <p>{t('simulation.stageLabel', { defaultValue: 'Stage' })}: <span className="font-medium">{result.projected_state.stage || t('simulation.notAvailable', { defaultValue: 'N/A' })}</span></p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-3 bg-cultivax-elevated rounded-lg">
          <p className="text-xs text-cultivax-text-muted">{t('simulation.stressDelta', { defaultValue: 'Stress Delta' })}</p>
          <p className={`text-sm font-semibold ${result.deltas.stress > 0 ? 'text-red-500' : result.deltas.stress < 0 ? 'text-emerald-500' : 'text-cultivax-text-secondary'}`}>
            {formatDelta(result.deltas.stress, true)}
          </p>
        </div>
        <div className="text-center p-3 bg-cultivax-elevated rounded-lg">
          <p className="text-xs text-cultivax-text-muted">{t('simulation.riskDelta', { defaultValue: 'Risk Delta' })}</p>
          <p className={`text-sm font-semibold ${result.deltas.risk > 0 ? 'text-red-500' : result.deltas.risk < 0 ? 'text-emerald-500' : 'text-cultivax-text-secondary'}`}>
            {formatDelta(result.deltas.risk, true)}
          </p>
        </div>
        <div className="text-center p-3 bg-cultivax-elevated rounded-lg">
          <p className="text-xs text-cultivax-text-muted">{t('simulation.dayDelta', { defaultValue: 'Day Delta' })}</p>
          <p className="text-sm font-semibold text-cultivax-text-primary">{formatDelta(result.deltas.days)}</p>
        </div>
        <div className="text-center p-3 bg-cultivax-elevated rounded-lg">
          <p className="text-xs text-cultivax-text-muted">{t('simulation.stageChanged', { defaultValue: 'Stage Changed' })}</p>
          <p className="text-sm font-semibold text-cultivax-text-primary">{result.deltas.stage_changed ? t('common.yes', { defaultValue: 'Yes' }) : t('common.no', { defaultValue: 'No' })}</p>
        </div>
      </div>

      {result.state_transitions.length > 0 && (
        <div className="mb-6">
          <p className="text-sm font-semibold mb-2">{t('simulation.stageTransitions', { defaultValue: 'Stage Transitions' })}</p>
          <div className="space-y-2">
            {result.state_transitions.map((transition, index) => (
              <div key={index} className="text-sm bg-cultivax-elevated rounded-lg px-3 py-2">
                {t('simulation.transitionRow', {
                  defaultValue: 'Day {{day}}: {{from}} -> {{to}} (action {{action}})',
                  day: transition.at_day,
                  from: transition.from_stage || t('simulation.notAvailable', { defaultValue: 'N/A' }),
                  to: transition.to_stage || t('simulation.notAvailable', { defaultValue: 'N/A' }),
                  action: transition.at_action,
                })}
              </div>
            ))}
          </div>
        </div>
      )}

      {result.action_breakdowns.length > 0 && (
        <div className="mb-6">
          <p className="text-sm font-semibold mb-2">{t('simulation.actionBreakdown', { defaultValue: 'Action Breakdown' })}</p>
          <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {result.action_breakdowns.map((item) => (
              <details key={item.action_index} className="bg-cultivax-elevated rounded-lg p-3">
                <summary className="cursor-pointer text-sm font-medium">
                  #{item.action_index} {item.action_type} | {t('simulation.dayLabel', { defaultValue: 'Day' })} +{item.day_delta} | {t('simulation.stressLabel', { defaultValue: 'Stress' })} {formatDelta(item.stress_delta, true)} | {t('simulation.riskLabel', { defaultValue: 'Risk' })} {formatDelta(item.risk_delta, true)}
                </summary>
                <div className="mt-2 text-xs text-cultivax-text-secondary space-y-1">
                  <p>{t('simulation.dateLabel', { defaultValue: 'Date' })}: {item.action_date || t('simulation.notSpecified', { defaultValue: 'Not specified' })}</p>
                  <p>{t('simulation.dayLabel', { defaultValue: 'Day' })}: {item.day_number_before} → {item.day_number_after}</p>
                  <p>{t('simulation.stageLabel', { defaultValue: 'Stage' })}: {item.stage_before || t('simulation.notAvailable', { defaultValue: 'N/A' })} → {item.stage_after || t('simulation.notAvailable', { defaultValue: 'N/A' })}</p>
                  <p>{t('simulation.stressLabel', { defaultValue: 'Stress' })}: {(item.stress_after * 100).toFixed(2)}% | {t('simulation.riskLabel', { defaultValue: 'Risk' })}: {(item.risk_after * 100).toFixed(2)}%</p>
                  {item.details && (
                    <p>{t('simulation.detailsLabel', { defaultValue: 'Details' })}: {JSON.stringify(item.details)}</p>
                  )}
                </div>
              </details>
            ))}
          </div>
        </div>
      )}

      {result.warnings.length > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
          <p className="font-medium text-amber-300 mb-2">{t('simulation.warnings', { defaultValue: 'Warnings' })}</p>
          <ul className="list-disc list-inside text-sm text-amber-200">
            {result.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
