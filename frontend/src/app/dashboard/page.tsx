'use client';

/**
 * Farmer Dashboard — CultivaX
 *
 * Premium glassmorphism dashboard inspired by M3 design language.
 * Layout: Full width with responsive grid sections.
 *
 * Sections:
 *  1. Welcome header with date + Quick Actions
 *  2. Stat cards (glass-card with icon badges + tag pills)
 *  3. Weather widget (col-4) + Health chart (col-8)
 *  4. Map view with satellite overlay + pulsing markers
 *  5. Your Crops grid with image cards + SVG growth arcs
 */

import { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import {
  Sprout, AlertTriangle, ShoppingBag, Plus,
  FlaskConical, ClipboardList, Sun, Droplets, Cloud,
  ArrowRight, MapPin, TrendingUp, ChevronDown, Wind,
  Moon, Bell, BarChart3, CalendarDays, Activity,
  Wheat, Leaf, Loader2, Thermometer,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts';
import clsx from 'clsx';
import { useAuth } from '@/context/AuthContext';
import { useFetch } from '@/hooks/useFetch';
import { apiGet } from '@/lib/api';
import ProtectedRoute from '@/components/ProtectedRoute';
import type { CropRecommendation } from '@/lib/types';
import { useTranslation } from 'react-i18next';

/* ─── Weather Icon Helper ────────────────────────────────── */

function getWeatherIcon(code?: string) {
  if (!code) return <Cloud className="w-6 h-6 text-m3-secondary" />;
  if (code.includes('clear') || code.includes('sun')) return <Sun className="w-6 h-6 text-m3-secondary" />;
  if (code.includes('rain') || code.includes('drizzle')) return <Droplets className="w-6 h-6 text-m3-primary" />;
  if (code.includes('wind')) return <Wind className="w-6 h-6 text-m3-on-surface-variant" />;
  return <Cloud className="w-6 h-6 text-m3-secondary" />;
}

/* ─── SVG Growth Ring Component ──────────────────────────── */

function GrowthRing({
  percent,
  color = 'stroke-m3-primary',
  size = 48,
}: {
  percent: number;
  color?: string;
  size?: number;
}) {
  const offset = 100 - percent;
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="w-full h-full rotate-[-90deg]" viewBox="0 0 36 36">
        <circle
          className="stroke-m3-surface-container-highest"
          cx="18" cy="18" r="16"
          fill="none" strokeWidth="2"
        />
        <circle
          className={clsx('growth-arc', color)}
          cx="18" cy="18" r="16"
          fill="none" strokeWidth="2" strokeLinecap="round"
          style={{ strokeDashoffset: offset }}
        />
      </svg>
      <span className={clsx(
        'absolute inset-0 flex items-center justify-center text-[10px] font-mono',
        color === 'stroke-m3-secondary' ? 'text-m3-secondary' : 'text-m3-primary'
      )}>
        {percent}%
      </span>
    </div>
  );
}

/* ─── Stat Card (Glass) ──────────────────────────────────── */

function GlassStatCard({
  icon: Icon,
  label,
  value,
  tag,
  tagColor = 'primary',
  iconColor = 'text-m3-primary',
  iconBg = 'bg-m3-primary/10',
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  tag?: string;
  tagColor?: 'primary' | 'warning' | 'info' | 'success';
  iconColor?: string;
  iconBg?: string;
}) {
  const tagClasses: Record<string, string> = {
    primary: 'text-m3-primary bg-m3-primary/5',
    warning: 'text-m3-secondary bg-m3-secondary/5',
    info: 'text-m3-tertiary-container bg-m3-tertiary-container/5',
    success: 'text-m3-primary-container bg-m3-primary-container/5',
  };

  return (
    <div className="glass-card p-6 rounded-xl border border-m3-outline-variant/10 group hover:bg-m3-surface-container-high transition-colors duration-500">
      <div className="flex items-center justify-between mb-4">
        <span className={clsx('p-2 rounded-lg', iconBg)}>
          <Icon className={clsx('w-5 h-5', iconColor)} />
        </span>
        {tag && (
          <span className={clsx('stat-tag', tagClasses[tagColor])}>
            {tag}
          </span>
        )}
      </div>
      <p className="mono-label mb-1">{label}</p>
      <h3 className="text-4xl font-bold text-m3-on-surface font-headline tracking-tighter">
        {value}
      </h3>
    </div>
  );
}

/* ─── Dashboard Page ─────────────────────────────────────── */

export default function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [topRecommendations, setTopRecommendations] = useState<CropRecommendation[]>([]);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(false);
  const actionMenuRef = useRef<HTMLDivElement>(null);

  // Close Quick Actions menu on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (actionMenuRef.current && !actionMenuRef.current.contains(e.target as Node)) {
        setShowQuickActions(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Fetch dashboard stats (real API — returns role-specific metrics)
  const { data: stats, loading: statsLoading, error: statsError } = useFetch('/api/v1/dashboard/stats');

  // Fetch crops for the grid
  const { data: cropsData, loading: cropsLoading } = useFetch('/api/v1/crops/?per_page=6');

  // Fetch weather data (real API)
  const { data: weatherData, loading: weatherLoading } = useFetch('/api/v1/weather');
  const crops = cropsData?.items || [];

  useEffect(() => {
    const loadTopRecommendations = async () => {
      if (!crops.length || !crops[0]?.id) {
        setTopRecommendations([]);
        return;
      }

      try {
        setRecommendationsLoading(true);
        const recs = await apiGet(`/api/v1/crops/${crops[0].id}/recommendations?on_demand=true`);
        setTopRecommendations(((recs as CropRecommendation[]) || []).slice(0, 2));
      } catch (error) {
        console.error('Failed to load dashboard recommendations:', error);
        setTopRecommendations([]);
      } finally {
        setRecommendationsLoading(false);
      }
    };

    loadTopRecommendations();
  }, [crops]);

  const isNewUser = stats && (stats.active_crops === 0 || !stats.is_onboarded);

  const today = new Date().toLocaleDateString('en-IN', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).toUpperCase();

  return (
    <ProtectedRoute>
      <div className="animate-fade-in space-y-10">

      {/* ═══════ Header ═══════ */}
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h2 className="text-3xl md:text-4xl font-extrabold text-m3-on-surface tracking-tight mb-2">
            {t('dashboard.welcome')} <span className="bg-gradient-to-r from-emerald-500 to-green-600 bg-clip-text text-transparent capitalize">{user?.full_name?.split(' ')[0] || t('dashboard.farmer_default')}</span>.
          </h2>
          <p className="text-m3-on-surface-variant font-medium">
            {t('dashboard.farm_overview_for')}{' '}
            <span className="text-m3-primary font-mono tracking-tighter">{today}</span>.
          </p>
        </div>
        <div className="flex items-center gap-4 relative" ref={actionMenuRef}>
          <button 
            onClick={() => setShowQuickActions(!showQuickActions)}
            className="flex items-center gap-2 px-5 py-3 rounded-xl bg-m3-surface-container-high text-m3-on-surface border border-m3-outline-variant/15 hover:bg-m3-surface-container-highest transition-all duration-300"
          >
            <Activity className="w-4 h-4 text-m3-primary" />
            <span className="text-sm font-semibold">{t('dashboard.quick_actions')}</span>
            <ChevronDown className={clsx("w-3 h-3 transition-transform", showQuickActions && 'rotate-180')} />
          </button>
          
          {showQuickActions && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-m3-surface border border-m3-outline-variant/10 rounded-xl shadow-lg overflow-hidden z-50 animate-slide-down">
              <Link href="/crops/new" className="flex items-center gap-2 px-4 py-3 text-sm text-m3-on-surface hover:bg-m3-surface-container-high transition-colors">
                <Plus className="w-4 h-4 text-m3-primary" /> {t('dashboard.action_new_crop')}
              </Link>
              <Link href="/services" className="flex items-center gap-2 px-4 py-3 text-sm text-m3-on-surface hover:bg-m3-surface-container-high transition-colors">
                <ShoppingBag className="w-4 h-4 text-m3-secondary" /> {t('dashboard.action_request_service')}
              </Link>
            </div>
          )}
        </div>
      </header>

      {/* ═══════ New-User Onboarding Banner ═══════ */}
      {isNewUser && (
        <div className="glass-card border border-m3-primary/20 rounded-2xl p-6 sm:p-8 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-40 h-40 bg-m3-primary/10 blur-[60px] rounded-full pointer-events-none" />
          <div className="relative flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="w-14 h-14 bg-m3-primary/20 rounded-2xl flex items-center justify-center flex-shrink-0">
              <Sprout className="w-7 h-7 text-m3-primary" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-m3-on-surface mb-1">
                🌱 Welcome to CultivaX!
              </h2>
              <p className="text-sm text-m3-on-surface-variant">
                Start by adding your first crop to begin tracking, get alerts, and access all features.
              </p>
            </div>
            <Link
              href="/crops/new"
              className="btn-primary flex items-center gap-2 whitespace-nowrap onboarding-pulse"
            >
              <Plus className="w-4 h-4" /> Add Your First Crop
            </Link>
          </div>
        </div>
      )}

      {/* ═══════ Stats Grid ═══════ */}
      {statsLoading ? (
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="glass-card p-6 rounded-xl border border-m3-outline-variant/10 animate-pulse">
              <div className="h-8 w-8 rounded-lg bg-m3-surface-container-highest mb-4" />
              <div className="h-3 w-20 rounded bg-m3-surface-container-highest mb-2" />
              <div className="h-8 w-16 rounded bg-m3-surface-container-highest" />
            </div>
          ))}
        </section>
      ) : statsError ? (
        <div className="glass-card p-6 rounded-xl border border-red-500/20 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-400">Failed to load dashboard stats</p>
            <p className="text-xs text-cultivax-text-muted">{statsError}</p>
          </div>
        </div>
      ) : (
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <GlassStatCard
            icon={Sprout}
            label={t('dashboard.active_crops')}
            value={stats?.active_crops ?? 0}
            tag={stats?.active_crops > 0 ? t('dashboard.tracked', 'TRACKED') : undefined}
            tagColor="primary"
            iconColor="text-m3-primary"
            iconBg="bg-m3-primary/10"
          />
          <GlassStatCard
            icon={AlertTriangle}
            label={t('dashboard.needs_action')}
            value={stats?.crops_needing_action ?? 0}
            tag={stats?.crops_needing_action > 0 ? 'attention' : undefined}
            tagColor="warning"
            iconColor="text-m3-secondary"
            iconBg="bg-m3-secondary/10"
          />
          <GlassStatCard
            icon={Bell}
            label={t('dashboard.pending_alerts')}
            value={stats?.alerts_due_today ?? 0}
            tag={stats?.alerts_due_today > 0 ? 'pending' : undefined}
            tagColor="info"
            iconColor="text-m3-tertiary-container"
            iconBg="bg-m3-tertiary-container/10"
          />
          <GlassStatCard
            icon={CalendarDays}
            label={t('dashboard.booked_services')}
            value={stats?.services_booked ?? 0}
            tag={stats?.services_booked > 0 ? 'active' : undefined}
            tagColor="success"
            iconColor="text-m3-primary-container"
            iconBg="bg-m3-primary-container/10"
          />
        </section>
      )}

      {/* ═══════ Widgets Row: Weather + Health Chart ═══════ */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Weather Widget — Live Data */}
        <div className="lg:col-span-4 glass-card rounded-xl overflow-hidden relative border border-m3-outline-variant/10">
          <div className="p-8 relative z-10 flex flex-col h-full justify-between">
            <div>
              <div className="flex items-center justify-between mb-8">
                <p className="mono-label">{t('dashboard.weather_forecast')}</p>
                {getWeatherIcon(weatherData?.weather_data?.description)}
              </div>
              {weatherLoading ? (
                <div className="flex items-baseline gap-2">
                  <div className="h-14 w-24 rounded bg-m3-surface-container-highest animate-pulse" />
                </div>
              ) : weatherData?.weather_data?.temperature == null ? (
                <div className="flex items-center gap-2 text-m3-on-surface-variant opacity-60">
                  <Cloud className="w-8 h-8" />
                  <span className="text-lg font-medium">{t('dashboard.weather_unavailable')}</span>
                </div>
              ) : (
                <div className="flex items-baseline gap-2">
                  <h2 className="text-6xl font-black text-m3-on-surface font-headline tracking-tighter">
                    {Math.round(weatherData.weather_data.temperature)}°C
                  </h2>
                  <span className="text-xl text-m3-on-surface-variant font-light capitalize">
                    {String(t('weather.desc_' + (weatherData.weather_data.description || '').toLowerCase().replace(/ /g, '_'), weatherData.weather_data.description || '—'))}
                  </span>
                </div>
              )}
            </div>

            <div className="mt-8 pt-6 border-t border-m3-outline-variant/10 grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="mono-label mb-1">{t('dashboard.weather_humidity', 'Humidity')}</p>
                <p className="text-sm font-bold text-m3-primary">
                  {weatherData?.weather_data?.humidity != null ? `${Math.round(weatherData.weather_data.humidity)}%` : '—'}
                </p>
              </div>
              <div className="text-center">
                <p className="mono-label mb-1">{t('dashboard.weather_wind', 'Wind')}</p>
                <p className="text-sm font-bold text-m3-secondary">
                  {weatherData?.weather_data?.wind_speed_kmh != null ? `${Math.round(weatherData.weather_data.wind_speed_kmh)} km/h` : '—'}
                </p>
              </div>
              <div className="text-center">
                <p className="mono-label mb-1">{t('dashboard.weather_precip', 'Precip')}</p>
                <p className="text-sm font-bold text-m3-tertiary-container">
                  {weatherData?.weather_data?.precipitation_mm != null ? `${weatherData.weather_data.precipitation_mm}mm` : '—'}
                </p>
              </div>
            </div>
          </div>
          <div className="absolute inset-0 bg-gradient-to-br from-m3-secondary/5 to-transparent pointer-events-none" />
        </div>

        {/* Health Chart Widget — Summary from Stats */}
        <div className="lg:col-span-8 glass-card rounded-xl border border-m3-outline-variant/10 p-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <p className="mono-label">{t('dashboard.farm_overview')}</p>
              <p className="text-sm text-m3-on-surface font-medium mt-1">{t('dashboard.crop_status_summary')}</p>
            </div>
            <Link href="/crops" className="text-sm text-m3-primary font-semibold hover:underline transition-colors">
              {t('dashboard.view_all')} →
            </Link>
          </div>
          {statsLoading ? (
            <div className="h-48 flex items-center justify-center">
              <Loader2 className="w-6 h-6 text-m3-primary animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center p-4 rounded-xl bg-m3-primary/5 border border-m3-primary/10">
                <Sprout className="w-6 h-6 text-m3-primary mx-auto mb-2" />
                <p className="text-2xl font-bold text-m3-on-surface">{stats?.active_crops ?? 0}</p>
                <p className="text-sm font-medium text-m3-on-surface-variant mt-1">{t('dashboard.active_crops')}</p>
              </div>
              <div className="text-center p-4 rounded-xl bg-m3-secondary/5 border border-m3-secondary/10">
                <AlertTriangle className="w-6 h-6 text-m3-secondary mx-auto mb-2" />
                <p className="text-2xl font-bold text-m3-on-surface">{stats?.crops_needing_action ?? 0}</p>
                <p className="text-sm font-medium text-m3-on-surface-variant mt-1">{t('dashboard.needs_action')}</p>
              </div>
              <div className="text-center p-4 rounded-xl bg-m3-tertiary-container/5 border border-m3-tertiary-container/10">
                <Bell className="w-6 h-6 text-m3-tertiary-container mx-auto mb-2" />
                <p className="text-2xl font-bold text-m3-on-surface">{stats?.alerts_due_today ?? 0}</p>
                <p className="text-sm font-medium text-m3-on-surface-variant mt-1">{t('dashboard.pending_alerts')}</p>
              </div>
              <div className="text-center p-4 rounded-xl bg-m3-primary-container/5 border border-m3-primary-container/10">
                <TrendingUp className="w-6 h-6 text-m3-primary-container mx-auto mb-2" />
                <p className="text-2xl font-bold text-m3-on-surface">{stats?.services_booked ?? 0}</p>
                <p className="text-sm font-medium text-m3-on-surface-variant mt-1">{t('dashboard.booked_services')}</p>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ═══════ Weather Risk Section ═══════ */}
      {weatherData?.risk_score != null && weatherData.risk_score > 0.3 && (
        <section className="glass-card rounded-2xl border border-m3-secondary/20 overflow-hidden p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-m3-secondary/15 flex items-center justify-center flex-shrink-0">
              <AlertTriangle className="w-6 h-6 text-m3-secondary" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold text-m3-on-surface">{t('dashboard.weather_advisory', 'Weather Advisory')}</h3>
              <p className="text-sm text-m3-on-surface-variant mt-1">
                {t('dashboard.current_risk_score', 'Current risk score:')} <span className="text-m3-secondary font-bold">{Math.round(weatherData.risk_score * 100)}%</span>.
                {t('dashboard.precautionary_measures', 'Take precautionary measures for your active crops.')}
              </p>
            </div>
            <Link href="/weather" className="btn-primary text-sm px-5 whitespace-nowrap">
              {t('dashboard.view_details', 'View Details')}
            </Link>
          </div>
        </section>
      )}

      {/* ═══════ Your Crops ═══════ */}
      <section>
        <div className="flex items-center justify-between mb-8">
          <h3 className="text-2xl font-bold text-m3-on-surface tracking-tight">{t('crops.title')}</h3>
          <Link href="/crops" className="text-sm font-bold text-m3-primary hover:underline transition-all">
            {t('dashboard.view_all_crops', 'View All Crops')}
          </Link>
        </div>

        {cropsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-card rounded-2xl border border-m3-outline-variant/10 animate-pulse">
                <div className="h-40 bg-m3-surface-container-highest" />
                <div className="p-6">
                  <div className="h-5 w-32 bg-m3-surface-container-highest rounded mb-4" />
                  <div className="h-3 w-full bg-m3-surface-container-highest rounded mb-2" />
                  <div className="h-3 w-24 bg-m3-surface-container-highest rounded" />
                </div>
              </div>
            ))}
          </div>
        ) : crops.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {crops.slice(0, 3).map((crop: any) => (
              <Link
                key={crop.id}
                href={`/crops/${crop.id}`}
                className="glass-card rounded-2xl overflow-hidden border border-m3-outline-variant/10 group block"
              >
                <div className="h-40 overflow-hidden relative bg-gradient-to-br from-m3-primary/10 to-m3-surface-container flex items-center justify-center">
                  {(crop.crop_type?.toLowerCase().includes('rice') || crop.crop_type?.toLowerCase().includes('धान') || crop.crop_type?.toLowerCase().includes('chawal')) ? (
                    <Image src="/images/rice_crop.png" alt="Rice Crop" fill className="object-cover" />
                  ) : (
                    <Sprout className="w-12 h-12 text-m3-primary/30" />
                  )}
                  <div className="absolute top-4 right-4 bg-m3-primary/90 text-m3-on-primary px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest">
                    {t(`crops.state_${(crop.state || 'active').toLowerCase()}`, { defaultValue: crop.state || 'Active' }) as string}
                  </div>
                </div>
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-xl font-bold text-m3-on-surface">
                      {crop.crop_type} {crop.variety && `— ${crop.variety}`}
                    </h4>
                    <GrowthRing percent={crop.day_number ? Math.min(crop.day_number, 100) : 50} />
                  </div>
                  <div className="flex gap-4 mb-6">
                    <div className="flex-1">
                      <p className="mono-label mb-1">{t('crops.stage', 'Stage')}</p>
                      <p className="text-sm font-bold">{crop.stage || 'Germination'}</p>
                    </div>
                    <div className="flex-1">
                      <p className="mono-label mb-1">{t('crops.day', 'Day')}</p>
                      <p className="text-sm font-bold text-m3-primary">{crop.day_number || '—'}</p>
                    </div>
                  </div>
                  <button className="w-full py-3 rounded-xl bg-m3-surface-container-low border border-m3-outline-variant/10 text-sm font-bold hover:bg-m3-surface-container-highest transition-colors">
                    {t('crops.details', 'Details')}
                  </button>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="glass-card rounded-2xl border border-m3-outline-variant/10 text-center py-16">
            <Sprout className="w-12 h-12 text-m3-on-surface-variant mx-auto mb-4 opacity-40" />
            <p className="text-m3-on-surface font-semibold text-lg mb-1">{t('crops.no_crops')}</p>
            <p className="text-sm text-m3-on-surface-variant mb-6">
              Start by tracking your first farm parcel.
            </p>
            <Link href="/crops/new" className="btn-primary text-sm px-8">
              <Plus className="w-4 h-4 mr-1.5 inline" /> {t('crops.create')}
            </Link>
          </div>
        )}
      </section>

      {/* ═══════ Top Recommendations ═══════ */}
      <section className="glass-card rounded-2xl border border-m3-outline-variant/10 p-6 sm:p-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-m3-on-surface tracking-tight">{t('dashboard.top_recommendations')}</h3>
          <span className="text-xs font-mono text-m3-on-surface-variant">{t('dashboard.auto_refreshed')}</span>
        </div>
        {recommendationsLoading ? (
          <p className="text-sm text-m3-on-surface-variant">{t('dashboard.loading_recommendations', 'Loading recommendations...')}</p>
        ) : topRecommendations.length === 0 ? (
          <p className="text-sm text-m3-on-surface-variant">{t('dashboard.no_recommendations', 'No urgent recommendations available.')}</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {topRecommendations.map((rec) => (
              <div key={rec.id} className="rounded-xl border border-m3-outline-variant/15 bg-m3-surface-container-low p-4">
                <p className="text-sm font-bold text-m3-on-surface capitalize">{rec.recommendation_type.replace('_', ' ')}</p>
                <p className="text-xs text-m3-on-surface-variant mt-1">{rec.basis || rec.message_key}</p>
                <p className="text-[11px] text-m3-primary mt-3">{t('dashboard.priority', 'Priority')} {rec.priority_rank}</p>
              </div>
            ))}
          </div>
        )}
      </section>
      </div>
    </ProtectedRoute>
  );
}
