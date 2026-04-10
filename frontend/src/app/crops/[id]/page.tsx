'use client';

/**
 * Crop Detail Page — Full crop view with tabs
 *
 * Tabs: Overview | Actions | Map | Analytics
 * Overview: Stats, timeline, weather impact, recommendations
 * Actions: Action history + command panel (Log, Simulate, Yield)
 * Map: Field boundary via MapView
 * Analytics: Stress/risk charts
 */

import { useEffect, useState } from 'react';
import useSWR from 'swr';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft, Calendar, Sprout, Activity, AlertTriangle,
  Droplets, FlaskConical, ClipboardList, MapPin,
  BarChart3, Cloud, ThermometerSun, Wheat, TrendingUp,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, BarChart, Bar,
} from 'recharts';
import clsx from 'clsx';
import { apiGet, apiPatch, apiPut } from '@/lib/api';
import ProtectedRoute from '@/components/ProtectedRoute';
import Badge, { getStatusVariant } from '@/components/Badge';
import TrustRing from '@/components/TrustRing';
import ProgressBar from '@/components/ProgressBar';
import CropTimeline from '@/components/CropTimeline';
import ActionLogList from '@/components/ActionLogList';
import MapView from '@/components/MapView';
import ParcelSelector from '@/components/ParcelSelector';
import { MediaUploadForm } from '@/components/media/MediaUploadForm';
import { MediaGallery } from '@/components/media/MediaGallery';
import type { CropRecommendation, LandParcel } from '@/lib/types';
import { useTranslation } from 'react-i18next';

interface CropDetail {
  id: string;
  crop_type: string;
  variety: string;
  state: string;
  stage: string;
  region: string;
  sowing_date: string;
  stress_score: number;
  risk_index: number;
  current_day_number: number;
  seasonal_window_category: string;
  land_parcel_id?: string | null;
  field_area_acres?: number;
}

const TABS = ['Overview', 'Actions', 'Media', 'Map', 'Analytics'];

// Mock stress history for charts
const STRESS_HISTORY = [
  { day: 'D1', stress: 0.12, risk: 0.08 },
  { day: 'D5', stress: 0.18, risk: 0.11 },
  { day: 'D10', stress: 0.22, risk: 0.15 },
  { day: 'D15', stress: 0.20, risk: 0.14 },
  { day: 'D20', stress: 0.25, risk: 0.19 },
  { day: 'D25', stress: 0.23, risk: 0.17 },
  { day: 'D30', stress: 0.21, risk: 0.15 },
];

export default function CropDetailPage() {
  const { t } = useTranslation();
  const params = useParams();
  const router = useRouter();
  const [crop, setCrop] = useState<CropDetail | null>(null);
  const [parcel, setParcel] = useState<LandParcel | null>(null);
  const [recommendations, setRecommendations] = useState<CropRecommendation[]>([]);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [recommendationBusyId, setRecommendationBusyId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState('Overview');
  const [showParcelSelector, setShowParcelSelector] = useState(false);
  const [mediaRefreshKey, setMediaRefreshKey] = useState(0);

  // SWR-backed actions list — key matches the optimistic mutate in offlineQueue.ts
  const { data: actionsData } = useSWR<any[]>(
    params.id ? `/api/v1/crops/${params.id}/actions` : null,
    apiGet,
    { revalidateOnFocus: false }
  );
  const actions = Array.isArray(actionsData)
    ? actionsData
    : (actionsData as any)?.actions ?? [];

  const { data: weatherData } = useSWR<any>(
    params.id ? `/api/v1/weather/risk?crop_id=${params.id}` : null,
    apiGet,
    { revalidateOnFocus: false }
  );

  useEffect(() => {
    if (params.id) {
      fetchCropDetail();
      fetchRecommendations();
    }
  }, [params.id]);

  useEffect(() => {
    if (!crop?.land_parcel_id) {
      setParcel(null);
      return;
    }

    const fetchParcel = async () => {
      try {
        const data = await apiGet(`/api/v1/land-parcels/${crop.land_parcel_id}`);
        setParcel(data as LandParcel);
      } catch (err) {
        console.error('Failed to fetch linked parcel:', err);
        setParcel(null);
      }
    };

    fetchParcel();
  }, [crop?.land_parcel_id]);

  const fetchCropDetail = async () => {
    try {
      const data = await apiGet(`/api/v1/crops/${params.id}`);
      setCrop(data as CropDetail);
    } catch (error: any) {
      console.error('Failed to fetch crop details:', error);
      setErrorStatus(error.status || 500);
    } finally {
      setLoading(false);
    }
  };

  const fetchActions = async () => {
    // Retained as a manual refresh fallback (e.g. after parcel change)
    // Primary data is served by the useSWR hook above.
  };

  const fetchRecommendations = async (onDemand = true) => {
    try {
      setRecommendationsLoading(true);
      const data = await apiGet(`/api/v1/crops/${params.id}/recommendations?on_demand=${onDemand}`);
      setRecommendations((data || []) as CropRecommendation[]);
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
      setRecommendations([]);
    } finally {
      setRecommendationsLoading(false);
    }
  };

  const resolveRecommendation = async (recId: string, action: 'dismiss' | 'act') => {
    try {
      setRecommendationBusyId(recId);
      await apiPatch(`/api/v1/crops/${params.id}/recommendations/${recId}/${action}`, {
        reason: action === 'dismiss' ? 'dismissed_in_ui' : 'acted_in_ui',
      });
      await fetchRecommendations(false);
    } catch (error) {
      console.error(`Failed to ${action} recommendation:`, error);
    } finally {
      setRecommendationBusyId(null);
    }
  };

  const handleParcelLinkChange = async (selected: LandParcel | null) => {
    if (!crop) return;
    try {
      await apiPut(`/api/v1/crops/${crop.id}`, {
        land_parcel_id: selected?.id || null,
      });
      setShowParcelSelector(false);
      await fetchCropDetail();
      setParcel(selected);
    } catch (err) {
      console.error('Failed to update crop parcel link:', err);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="skeleton h-8 w-64 rounded-lg" />
        <div className="skeleton h-4 w-48 rounded-lg" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
          {[1,2,3,4].map(i => <div key={i} className="skeleton h-24 rounded-xl" />)}
        </div>
      </div>
    );
  }

  if (errorStatus === 404 || !crop) {
    return (
      <div className="card text-center py-16">
        <AlertTriangle className="w-10 h-10 text-cultivax-text-muted mx-auto mb-3" />
        <p className="text-lg font-semibold mb-2">Crop not found</p>
        <p className="text-sm text-cultivax-text-muted mb-6">This crop instance may have been deleted.</p>
        <Link href="/crops" className="btn-primary text-sm inline-flex items-center">Back to My Crops</Link>
      </div>
    );
  }

  if (errorStatus === 401 || errorStatus === 403) {
    return (
      <div className="card text-center py-16">
        <AlertTriangle className="w-10 h-10 text-cultivax-text-muted mx-auto mb-3" />
        <p className="text-lg font-semibold mb-2">Access Denied</p>
        <p className="text-sm text-cultivax-text-muted mb-6">You don't have permission to view this crop.</p>
        <button onClick={() => router.push('/login')} className="btn-primary text-sm inline-flex items-center">Please Log In</button>
      </div>
    );
  }

  const stressPercent = ((crop.stress_score || 0) * 100);
  const riskPercent = ((crop.risk_index || 0) * 100);
  const canSubmitYield = ['grain_filling', 'maturity'].includes(crop.stage || '');

  return (
    <ProtectedRoute requiredRole={["farmer", "admin"]}>
    <div className="animate-fade-in">
      {/* Back + Header */}
      <div className="mb-6">
        <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-cultivax-text-muted hover:text-cultivax-text-secondary mb-3 transition-colors">
          <ArrowLeft className="w-4 h-4" /> {t('yield.backToCrops')}
        </button>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Sprout className="w-6 h-6 text-cultivax-primary" />
              {crop.crop_type}
              {crop.variety && <span className="text-cultivax-text-muted font-normal">— {crop.variety}</span>}
            </h1>
            <div className="flex items-center gap-3 mt-1 text-sm text-cultivax-text-muted">
              <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {crop.region || '—'}</span>
              <span>•</span>
              <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {t('crops.sowingDate')}: {crop.sowing_date || '—'}</span>
            </div>
          </div>
          <Badge variant={getStatusVariant(crop.state)} size="md" dot>
            {crop.state}
          </Badge>
        </div>
      </div>

      {/* Replay Awareness Banner */}
      {crop.state === 'RecoveryRequired' && (
        <div className="bg-red-500/10 border border-red-500/30 p-4 rounded-xl mb-6 flex gap-3 items-start animate-fade-in">
          <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-bold text-red-500">{t('crops.recoveryRequired')}</h3>
            <p className="text-xs text-cultivax-text-muted mt-1">
              {t('crops.recoveryRequiredDesc')}
            </p>
          </div>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="card-stat flex items-center gap-3">
          <TrustRing score={1 - (crop.stress_score || 0)} size={48} strokeWidth={3} labelFormat="percentage" />
          <div>
            <p className="text-xs text-cultivax-text-muted">{t('crops.health')}</p>
            <p className="text-lg font-bold">{(100 - stressPercent).toFixed(0)}%</p>
          </div>
        </div>
        <div className="card-stat">
          <p className="text-xs text-cultivax-text-muted mb-1">{t('crops.day')}</p>
          <p className="text-2xl font-bold">{crop.current_day_number || '—'}</p>
          <p className="text-xs text-cultivax-text-muted capitalize">{t(`crops.stages.${(crop.stage || 'germination').toLowerCase()}`)}</p>
        </div>
        <div className="card-stat">
          <p className="text-xs text-cultivax-text-muted mb-1">{t('simulation.stressLabel')}</p>
          <p className="text-lg font-bold text-amber-400">{stressPercent.toFixed(1)}%</p>
          <ProgressBar value={stressPercent} color={stressPercent > 40 ? 'red' : stressPercent > 20 ? 'amber' : 'green'} size="sm" className="mt-2" />
        </div>
        <div className="card-stat">
          <p className="text-xs text-cultivax-text-muted mb-1">{t('simulation.riskLabel')}</p>
          <p className="text-lg font-bold text-red-400">{riskPercent.toFixed(1)}%</p>
          <ProgressBar value={riskPercent} color={riskPercent > 40 ? 'red' : riskPercent > 20 ? 'amber' : 'green'} size="sm" className="mt-2" />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-cultivax-border mb-6 overflow-x-auto no-scrollbar">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={clsx(
              'flex-1 pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap px-2',
              activeTab === tab
                ? 'border-cultivax-primary text-cultivax-primary'
                : 'border-transparent text-cultivax-text-muted hover:text-cultivax-text-primary hover:border-cultivax-border'
            )}
          >
            {t(`crops.${tab.toLowerCase()}`)}
          </button>
        ))}
      </div>

      {/* ─── Tab Content ────────────────────────────── */}
      {activeTab === 'Overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left (2/3) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Timeline */}
            <div className="card">
              <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4 text-cultivax-primary" /> {t('crops.growthTimeline')}
              </h3>
              <CropTimeline stage={crop.stage} dayNumber={crop.current_day_number} state={crop.state} />
            </div>

            {/* Stress Trend */}
            <div className="card">
              <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-amber-400" /> {t('crops.detail.stressRiskTrend')}
              </h3>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={STRESS_HISTORY}>
                    <defs>
                      <linearGradient id="sGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#F59E0B" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="rGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                    <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 0.5]} tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v*100).toFixed(0)}%`} />
                    <Tooltip
                      contentStyle={{ background: '#1F2937', border: '1px solid #374151', borderRadius: '8px', fontSize: '12px' }}
                      formatter={(value: any) => `${(Number(value)*100).toFixed(1)}%`}
                    />
                    <Area type="monotone" dataKey="stress" stroke="#F59E0B" fill="url(#sGrad)" strokeWidth={2} name="Stress" />
                    <Area type="monotone" dataKey="risk" stroke="#EF4444" fill="url(#rGrad)" strokeWidth={2} name="Risk" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="space-y-6">
            {/* Info Card */}
            <div className="card">
              <h3 className="text-base font-semibold mb-3">{t('crops.detail.cropInfo')}</h3>
              <div className="space-y-2.5 text-sm">
                <div className="flex justify-between"><span className="text-cultivax-text-muted">{t('crops.cropType')}</span><span className="font-medium">{crop.crop_type}</span></div>
                <div className="flex justify-between"><span className="text-cultivax-text-muted">{t('crops.variety')}</span><span className="font-medium">{crop.variety || '—'}</span></div>
                <div className="flex justify-between"><span className="text-cultivax-text-muted">{t('crops.season')}</span><Badge variant="teal" size="sm">{t(`crops.seasons.${(crop.seasonal_window_category || '').toLowerCase()}`, crop.seasonal_window_category || '—')}</Badge></div>
                <div className="flex justify-between"><span className="text-cultivax-text-muted">{t('crops.stage')}</span><span className="font-medium capitalize">{t(`crops.stages.${(crop.stage || 'germination').toLowerCase()}`)}</span></div>
                <div className="flex justify-between"><span className="text-cultivax-text-muted">{t('crops.sowingDate')}</span><span className="font-medium">{crop.sowing_date || '—'}</span></div>
                <div className="flex justify-between items-center gap-3">
                  <span className="text-cultivax-text-muted">{t('crops.detail.linkedField')}</span>
                  <button
                    className="text-xs text-cultivax-primary hover:underline"
                    onClick={() => setShowParcelSelector(true)}
                    type="button"
                  >
                    {parcel ? parcel.parcel_name : t('crops.detail.linkField')}
                  </button>
                </div>
                {crop.field_area_acres && (
                  <div className="flex justify-between"><span className="text-cultivax-text-muted">{t('crops.detail.area')}</span><span className="font-medium">{crop.field_area_acres} acres</span></div>
                )}
              </div>
            </div>

            {/* Command Panel */}
            <div className="card">
              <h3 className="text-base font-semibold mb-3">{t('crops.commandPanel')}</h3>
              <div className="space-y-2">
                <Link href={`/crops/${params.id}/log-action`} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-cultivax-text-secondary hover:bg-cultivax-elevated hover:text-cultivax-text-primary transition-all w-full">
                  <ClipboardList className="w-4 h-4" /> <span className="font-medium">{t('crops.logAction')}</span>
                </Link>
                <Link href={`/crops/${params.id}/simulate`} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-cultivax-text-secondary hover:bg-cultivax-elevated hover:text-cultivax-text-primary transition-all w-full">
                  <FlaskConical className="w-4 h-4" /> <span className="font-medium">{t('crops.simulate')}</span>
                </Link>
                <Link
                  href={canSubmitYield ? `/crops/${params.id}/yield` : '#'}
                  className={clsx(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all w-full',
                    canSubmitYield
                      ? 'text-cultivax-text-secondary hover:bg-cultivax-elevated hover:text-cultivax-text-primary'
                      : 'text-cultivax-text-muted opacity-50 cursor-not-allowed'
                  )}
                >
                  <Wheat className="w-4 h-4" /> <span className="font-medium">{t('crops.submitYield')}</span>
                </Link>
              </div>
            </div>

            {/* Weather */}
            <div className="card">
              <h3 className="text-base font-semibold mb-3 flex items-center gap-2">
                <Cloud className="w-4 h-4 text-blue-400" /> {t('crops.detail.weatherImpact')}
              </h3>
              {!weatherData ? (
                <div className="space-y-3 animate-pulse">
                  <div className="flex justify-between"><div className="h-4 w-24 bg-cultivax-elevated rounded"></div><div className="h-4 w-12 bg-cultivax-elevated rounded"></div></div>
                  <div className="flex justify-between"><div className="h-4 w-24 bg-cultivax-elevated rounded"></div><div className="h-4 w-12 bg-cultivax-elevated rounded"></div></div>
                </div>
              ) : (
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-cultivax-text-muted flex items-center gap-1.5"><ThermometerSun className="w-3 h-3" /> {t('crops.detail.temperature')}</span>
                    <span className="font-medium">{weatherData.weather_data?.temperature?.toFixed(1) || '—'}°C</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-cultivax-text-muted flex items-center gap-1.5"><Droplets className="w-3 h-3" /> {t('crops.detail.humidity')}</span>
                    <span className="font-medium">{weatherData.weather_data?.humidity?.toFixed(0) || '—'}%</span>
                  </div>
                  
                  {weatherData.alerts?.length > 0 ? (
                    <div className="mt-3 space-y-2">
                      {weatherData.alerts.map((alert: any, idx: number) => (
                        <div key={idx} className="p-2.5 bg-amber-500/10 border border-amber-500/20 rounded-lg flex gap-2">
                          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                          <p className="text-xs text-amber-400">{alert.message}</p>
                        </div>
                      ))}
                    </div>
                  ) : weatherData.crop_impact ? (
                    <div className="mt-3 p-2.5 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                      <p className="text-xs text-blue-400">{weatherData.crop_impact}</p>
                    </div>
                  ) : null}
                  
                  {weatherData.weather_data?.description && (
                    <p className="text-xs text-cultivax-text-muted text-right mt-2 italic capitalize">
                      {weatherData.weather_data.description}
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Recommendations */}
            <div className="card">
              <h3 className="text-base font-semibold mb-3">{t('crops.detail.recommendations')}</h3>
              {recommendationsLoading ? (
                <p className="text-sm text-cultivax-text-muted">{t('crops.detail.loadingRecommendations')}</p>
              ) : recommendations.length === 0 ? (
                <p className="text-sm text-cultivax-text-muted">{t('crops.detail.noRecommendations')}</p>
              ) : (
                <div className="space-y-3">
                  {recommendations.map((rec) => (
                    <div key={rec.id} className="rounded-lg border border-cultivax-border bg-cultivax-elevated p-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-cultivax-text-primary capitalize">{rec.recommendation_type.replace('_', ' ')}</p>
                          <p className="text-xs text-cultivax-text-muted mt-1">{rec.basis || rec.message_key}</p>
                        </div>
                        <span className="text-[11px] rounded-full bg-cultivax-primary/15 text-cultivax-primary px-2 py-0.5">
                          P{rec.priority_rank}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-3">
                        <button
                          className="text-xs px-2.5 py-1 rounded bg-cultivax-primary/15 text-cultivax-primary hover:bg-cultivax-primary/25 disabled:opacity-60"
                          disabled={recommendationBusyId === rec.id}
                          onClick={() => resolveRecommendation(rec.id, 'act')}
                          type="button"
                        >
                          {t('crops.detail.markActed')}
                        </button>
                        <button
                          className="text-xs px-2.5 py-1 rounded bg-cultivax-elevated text-cultivax-text-muted hover:text-cultivax-text-primary border border-cultivax-border disabled:opacity-60"
                          disabled={recommendationBusyId === rec.id}
                          onClick={() => resolveRecommendation(rec.id, 'dismiss')}
                          type="button"
                        >
                          {t('crops.detail.dismiss')}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'Actions' && (
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-base font-semibold">{t('crops.actionHistory')}</h3>
            <Link href={`/crops/${params.id}/log-action`} className="btn-primary text-sm flex items-center gap-1.5">
              <ClipboardList className="w-4 h-4" /> {t('crops.logAction')}
            </Link>
          </div>
          <ActionLogList actions={actions} />
        </div>
      )}

      {activeTab === 'Media' && (
        <div className="space-y-6">
          <MediaUploadForm 
            cropId={params.id as string} 
            onSuccess={() => setMediaRefreshKey(k => k + 1)} 
          />
          <div className="card">
            <h3 className="text-base font-semibold mb-4">{t('crops.detail.cropGallery')}</h3>
            <MediaGallery cropId={params.id as string} refreshKey={mediaRefreshKey} />
          </div>
        </div>
      )}

      {activeTab === 'Map' && (
        <div className="card">
          <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
            <MapPin className="w-4 h-4 text-cultivax-primary" /> {t('crops.detail.fieldMap')}
          </h3>
          {parcel ? (
            <MapView
              center={[parcel.gps_coordinates.lat, parcel.gps_coordinates.lng]}
              zoom={14}
              markers={[
                {
                  id: parcel.id,
                  lat: parcel.gps_coordinates.lat,
                  lng: parcel.gps_coordinates.lng,
                  label: parcel.parcel_name,
                },
              ]}
              polygons={
                parcel.gps_coordinates.boundary_polygon?.length
                  ? [
                      {
                        id: parcel.id,
                        positions: parcel.gps_coordinates.boundary_polygon,
                        label: parcel.parcel_name,
                      },
                    ]
                  : []
              }
              className="h-[380px] mt-2"
            />
          ) : (
            <div className="bg-cultivax-elevated rounded-xl h-96 flex items-center justify-center text-cultivax-text-muted text-sm">
              <div className="text-center">
                <MapPin className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>{t('crops.detail.noFieldLinked')}</p>
                <button
                  className="text-xs mt-2 text-cultivax-primary hover:underline"
                  onClick={() => setShowParcelSelector(true)}
                  type="button"
                >
                  {t('crops.detail.linkFieldNow')}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'Analytics' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-400" /> {t('crops.detail.actionDistribution')}
            </h3>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={[
                  { name: 'Irrigation', count: 8 },
                  { name: 'Fertilizer', count: 4 },
                  { name: 'Pesticide', count: 2 },
                  { name: 'Weeding', count: 3 },
                  { name: 'Observation', count: 6 },
                ]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: '#1F2937', border: '1px solid #374151', borderRadius: '8px', fontSize: '12px' }} />
                  <Bar dataKey="count" fill="#10B981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="card">
            <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-amber-400" /> {t('crops.detail.stressOverTime')}
            </h3>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={STRESS_HISTORY}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                  <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 0.5]} tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v*100).toFixed(0)}%`} />
                  <Tooltip contentStyle={{ background: '#1F2937', border: '1px solid #374151', borderRadius: '8px', fontSize: '12px' }} formatter={(value: any) => `${(Number(value)*100).toFixed(1)}%`} />
                  <Area type="monotone" dataKey="stress" stroke="#F59E0B" fill="url(#sGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {showParcelSelector ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowParcelSelector(false)} />
          <div className="relative bg-cultivax-surface border border-cultivax-border rounded-2xl p-5 max-w-lg w-full">
            <h3 className="text-base font-semibold text-cultivax-text-primary mb-3">{t('crops.detail.selectField')}</h3>
            <ParcelSelector
              value={crop.land_parcel_id || null}
              onSelect={handleParcelLinkChange}
            />
            <div className="flex justify-end mt-4">
              <button className="btn-secondary" onClick={() => setShowParcelSelector(false)} type="button">
                {t('common.close')}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
    </ProtectedRoute>
  );
}
