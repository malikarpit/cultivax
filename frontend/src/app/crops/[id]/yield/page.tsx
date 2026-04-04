'use client';

/**
 * Yield Submission Page
 *
 * /crops/[id]/yield — Allows farmers to submit harvest yield data
 * for a specific crop instance. Uses YieldForm component.
 */

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import ProtectedRoute from '@/components/ProtectedRoute';
import YieldForm, { type YieldFormData } from '@/components/YieldForm';
import { apiGet, apiPost, getLatestYield, getYieldHistory } from '@/lib/api';
import type { YieldRecord } from '@/lib/types';

interface CropDetail {
  id: string;
  crop_type: string;
  variety: string;
  state: string;
  stage: string;
  region: string;
  land_area: number;
  sowing_date: string;
  current_day_number: number;
  stress_score: number;
  risk_index: number;
}

export default function YieldSubmissionPage() {
  const params = useParams();
  const router = useRouter();
  const { t } = useTranslation();
  const [crop, setCrop] = useState<CropDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitted, setSubmitted] = useState(false);
  const [yieldResult, setYieldResult] = useState<YieldRecord | null>(null);
  const [yieldHistory, setYieldHistory] = useState<YieldRecord[]>([]);
  const [error, setError] = useState('');
  const canSubmitYield = crop?.state === 'ReadyToHarvest';

  useEffect(() => {
    if (params.id) {
      fetchCrop();
    }
  }, [params.id]);

  const fetchCrop = async () => {
    try {
      const [cropData, latestYield, history] = await Promise.all([
        apiGet<CropDetail>(`/api/v1/crops/${params.id}`),
        getLatestYield(String(params.id)).catch(() => null),
        getYieldHistory(String(params.id)).catch(() => []),
      ]);
      setCrop(cropData);
      setYieldResult(latestYield);
      setYieldHistory(history);
    } catch (err) {
      setError('Failed to load crop details');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitYield = async (yieldData: YieldFormData) => {
    const payload = {
      reported_yield: yieldData.yield_quantity_kg,
      yield_unit: 'kg',
      harvest_date: yieldData.harvest_date,
      quality_grade: yieldData.quality_grade,
      moisture_pct: yieldData.moisture_content_pct,
      notes: yieldData.notes,
    };
    const result = await apiPost<YieldRecord>(`/api/v1/crops/${params.id}/yield`, payload);
    setYieldResult(result);
    setYieldHistory((current) => [result, ...current.filter((item) => item.id !== result.id)]);

    setSubmitted(true);
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="max-w-2xl mx-auto p-6">
          <div className="card text-center py-12">
            <div className="inline-block w-8 h-8 border-2 border-cultivax-primary border-t-transparent rounded-full animate-spin" />
            <p className="text-cultivax-text-muted mt-3">{t('yield.loadingCrop', { defaultValue: 'Loading crop details...' })}</p>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  if (error || !crop) {
    return (
      <ProtectedRoute>
        <div className="max-w-2xl mx-auto p-6">
          <div className="card text-center py-12">
            <p className="text-5xl mb-4">❌</p>
            <p className="text-red-500 font-medium">{error || 'Crop not found'}</p>
            <button
              className="btn-primary mt-4"
              onClick={() => router.push('/crops')}
            >
              {t('yield.backToCrops', { defaultValue: 'Back to Crops' })}
            </button>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  if (submitted) {
    return (
      <ProtectedRoute>
        <div className="max-w-2xl mx-auto p-6">
          <div className="card text-center py-12">
            <p className="text-5xl mb-4">🎉</p>
            <h2 className="text-2xl font-bold text-green-400 mb-2">{t('yield.submittedTitle', { defaultValue: 'Yield Submitted!' })}</h2>
            <p className="text-cultivax-text-muted mb-6">
              {t('yield.submittedMessage', {
                defaultValue: 'Your harvest data for {{crop}} has been recorded successfully.',
                crop: crop.crop_type,
              })}
            </p>

            {yieldResult && (
              <div className="text-left bg-cultivax-elevated border border-cultivax-border rounded-lg p-4 mb-6 space-y-2">
                <p className="text-sm font-semibold text-cultivax-text-primary">{t('yield.verificationSummary', { defaultValue: 'Verification Summary' })}</p>
                <p className="text-sm text-cultivax-text-secondary">
                  {t('yield.reportedLabel', { defaultValue: 'Reported' })}: <span className="font-medium">{yieldResult.reported_yield} {yieldResult.yield_unit}</span>
                </p>
                <p className="text-sm text-cultivax-text-secondary">
                  {t('yield.mlYieldLabel', { defaultValue: 'ML Yield' })}: <span className="font-medium">{yieldResult.ml_yield_value ?? t('yield.notAvailable', { defaultValue: 'N/A' })}</span>
                </p>
                <p className="text-sm text-cultivax-text-secondary">
                  {t('yield.biologicalCapLabel', { defaultValue: 'Biological Cap' })}: <span className="font-medium">{yieldResult.biological_cap ?? t('yield.notAvailable', { defaultValue: 'N/A' })}</span>
                </p>
                <p className="text-sm text-cultivax-text-secondary">
                  {t('yield.capAppliedLabel', { defaultValue: 'Cap Applied' })}: <span className="font-medium">{yieldResult.bio_cap_applied ? t('common.yes', { defaultValue: 'Yes' }) : t('common.no', { defaultValue: 'No' })}</span>
                </p>
                <p className="text-sm text-cultivax-text-secondary">
                  {t('yield.verificationScoreLabel', { defaultValue: 'Verification Score' })}: <span className="font-medium">{yieldResult.yield_verification_score ?? t('yield.notAvailable', { defaultValue: 'N/A' })}</span>
                </p>
              </div>
            )}

            {yieldHistory.length > 0 && (
              <div className="text-left bg-cultivax-surface border border-cultivax-border rounded-lg p-4 mb-6">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-semibold text-cultivax-text-primary">{t('yield.historyTitle', { defaultValue: 'Yield History' })}</p>
                  <span className="text-xs text-cultivax-text-muted">{yieldHistory.length} {t('yield.records', { defaultValue: 'records' })}</span>
                </div>
                <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                  {yieldHistory.map((record) => (
                    <div key={record.id} className="rounded-lg border border-cultivax-border/60 bg-cultivax-elevated px-3 py-2">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-medium text-cultivax-text-primary">
                            {record.reported_yield} {record.yield_unit}
                          </p>
                          <p className="text-xs text-cultivax-text-muted">
                            {record.created_at.slice(0, 10)} · {record.quality_grade || t('yield.notAvailable', { defaultValue: 'N/A' })}
                          </p>
                        </div>
                        <span className={`text-xs px-2 py-1 rounded-full ${record.bio_cap_applied ? 'bg-amber-500/15 text-amber-200' : 'bg-emerald-500/15 text-emerald-200'}`}>
                          {record.bio_cap_applied ? t('yield.capAppliedLabel', { defaultValue: 'Cap Applied' }) : t('yield.withinCapLabel', { defaultValue: 'Within Cap' })}
                        </span>
                      </div>
                      <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-cultivax-text-secondary">
                        <p>{t('yield.verificationScoreLabel', { defaultValue: 'Verification Score' })}: {record.yield_verification_score ?? t('yield.notAvailable', { defaultValue: 'N/A' })}</p>
                        <p>{t('yield.biologicalCapLabel', { defaultValue: 'Biological Cap' })}: {record.biological_cap ?? t('yield.notAvailable', { defaultValue: 'N/A' })}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-3 justify-center">
              <button
                className="btn-primary"
                onClick={() => router.push(`/crops/${params.id}`)}
              >
                {t('yield.viewCrop', { defaultValue: 'View Crop' })}
              </button>
              <button
                className="px-4 py-2 border border-cultivax-border rounded-lg text-cultivax-text-primary hover:bg-cultivax-elevated transition"
                onClick={() => router.push('/dashboard')}
              >
                {t('yield.dashboard', { defaultValue: 'Dashboard' })}
              </button>
            </div>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="max-w-2xl mx-auto p-6 space-y-6 animate-fade-in">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-cultivax-text-muted">
          <button onClick={() => router.push('/crops')} className="hover:text-cultivax-primary">
            {t('crops.title', { defaultValue: 'Crops' })}
          </button>
          <span>/</span>
          <button
            onClick={() => router.push(`/crops/${params.id}`)}
            className="hover:text-cultivax-primary capitalize"
          >
            {crop.crop_type}
          </button>
          <span>/</span>
          <span className="text-cultivax-text-primary font-medium">{t('yield.title', { defaultValue: 'Submit Yield' })}</span>
        </div>

        {/* Crop Summary */}
        <div className="card bg-gradient-to-r from-cultivax-primary/10 to-cultivax-primary/5 border-cultivax-primary/20">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-lg font-bold capitalize">
                {crop.crop_type} — {crop.variety}
              </h2>
              <p className="text-sm text-cultivax-text-secondary mt-1">
                {crop.region} · Day {crop.current_day_number} · {crop.land_area || '—'} acres
              </p>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium ${
                crop.state === 'ReadyToHarvest'
                  ? 'bg-yellow-100 text-yellow-800'
                  : crop.state === 'Harvested'
                  ? 'bg-purple-100 text-purple-800'
                  : 'bg-green-100 text-green-800'
              }`}
            >
              {crop.state}
            </span>
          </div>
        </div>

        {/* Yield Form */}
        {!canSubmitYield ? (
          <div className="card border border-amber-500/40 bg-amber-500/10">
            <p className="text-sm text-amber-200">
              {t('yield.readyToHarvestRequired', { defaultValue: 'Yield submission is enabled only when crop state is ReadyToHarvest.' })}
            </p>
          </div>
        ) : (
          <>
            {yieldResult && (
              <div className="card border border-cultivax-border bg-cultivax-surface/70">
                <p className="text-sm font-semibold text-cultivax-text-primary mb-2">{t('yield.latestSubmission', { defaultValue: 'Latest Submission' })}</p>
                <p className="text-sm text-cultivax-text-secondary">
                  {yieldResult.reported_yield} {yieldResult.yield_unit} · {t('yield.verificationScoreLabel', { defaultValue: 'Verification Score' })}: {yieldResult.yield_verification_score ?? t('yield.notAvailable', { defaultValue: 'N/A' })}
                </p>
              </div>
            )}
            <YieldForm
              cropId={crop.id}
              cropType={crop.crop_type}
              landArea={crop.land_area || 0}
              onSubmit={handleSubmitYield}
              onCancel={() => router.push(`/crops/${params.id}`)}
            />
          </>
        )}
      </div>
    </ProtectedRoute>
  );
}
