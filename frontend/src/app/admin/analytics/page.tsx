'use client';

/**
 * Admin Analytics Dashboard — FR-35, NFR-15
 *
 * Displays platform overview KPIs, activity charts, and regional demand.
 */

import { useState } from 'react';
import {
  BarChart3, Users, Sprout, AlertTriangle, Activity, Map, PieChart
} from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useFetch } from '@/hooks/useFetch';
import clsx from 'clsx';
import { useTranslation } from 'react-i18next';

export default function AnalyticsDashboard() {
  const { t } = useTranslation();
  const { data: overview, loading: l1 } = useFetch<any>('/api/v1/analytics/overview');
  const { data: activity, loading: l2 } = useFetch<any>('/api/v1/analytics/activity?days=14');
  const { data: distribution, loading: l3 } = useFetch<any>('/api/v1/analytics/crops/distribution');
  const { data: demand, loading: l4 } = useFetch<any>('/api/v1/analytics/regions/demand');

  const loading = l1 || l2 || l3 || l4;

  if (loading) {
    return (
      <ProtectedRoute requiredRole={["admin"]}>
        <div className="p-8 animate-pulse text-zinc-400">{t('admin.analytics.loading_analytics')}</div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute requiredRole={["admin"]}>
      <div className="min-h-screen bg-zinc-950 text-white p-6 sm:p-8 space-y-8">
        
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-blue-900/40 border border-blue-700/40 flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="font-bold text-white text-xl">{t('admin.analytics.platform_analytics')}</h1>
            <p className="text-xs text-zinc-500">{t('admin.analytics.live_platform_metrics_and')}</p>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
            <div className="flex items-center gap-2 text-zinc-400 mb-2">
              <Users className="w-4 h-4" /> <span className="text-xs font-semibold">{t('admin.analytics.total_users')}</span>
            </div>
            <p className="text-2xl font-bold text-white">{overview?.users?.total || 0}</p>
            <p className="text-[10px] text-zinc-500 mt-1">{overview?.users?.farmers || 0} farmers, {overview?.users?.providers || 0} providers</p>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
            <div className="flex items-center gap-2 text-emerald-400 mb-2">
              <Sprout className="w-4 h-4" /> <span className="text-xs font-semibold">{t('admin.analytics.active_crops')}</span>
            </div>
            <p className="text-2xl font-bold text-white">{overview?.crops?.active || 0}</p>
            <p className="text-[10px] text-emerald-500/70 mt-1">{overview?.crops?.health_rate || 0}% healthy</p>
          </div>

          <div className="bg-zinc-900 border border-rose-900/40 rounded-2xl p-5">
            <div className="flex items-center gap-2 text-rose-400 mb-2">
              <AlertTriangle className="w-4 h-4" /> <span className="text-xs font-semibold">{t('admin.analytics.at_risk')}</span>
            </div>
            <p className="text-2xl font-bold text-white">{overview?.crops?.at_risk || 0}</p>
            <p className="text-[10px] text-rose-500/70 mt-1">{t('admin.analytics.require_immediate_attention')}</p>
          </div>

          <div className="bg-zinc-900 border border-amber-900/40 rounded-2xl p-5">
            <div className="flex items-center gap-2 text-amber-400 mb-2">
              <Activity className="w-4 h-4" /> <span className="text-xs font-semibold">{t('admin.analytics.open_alerts')}</span>
            </div>
            <p className="text-2xl font-bold text-white">{overview?.alerts?.unacknowledged || 0}</p>
            <p className="text-[10px] text-amber-500/70 mt-1">{t('admin.analytics.pending_user_acknowledgment')}</p>
          </div>
        </div>

        {/* Charts & Data */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Region Demand */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
            <h3 className="flex items-center gap-2 font-semibold text-white text-sm mb-4">
              <Map className="w-4 h-4 text-purple-400" />{t('admin.analytics.regional_distribution')}</h3>
            <div className="space-y-3">
              {(demand?.regions || []).map((r: any) => (
                <div key={r.region} className="flex items-center justify-between">
                  <span className="text-sm text-zinc-300">{r.region}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-zinc-500">{r.total_crops} crops</span>
                    <span className={clsx(
                      "text-[10px] px-1.5 py-0.5 rounded font-mono",
                      r.risk_rate > 20 ? "bg-rose-900/40 text-rose-400" : "bg-emerald-900/40 text-emerald-400"
                    )}>{r.risk_rate}% risk</span>
                  </div>
                </div>
              ))}
              {(!demand?.regions || demand.regions.length === 0) && (
                <p className="text-xs text-zinc-500">{t('admin.analytics.no_regional_data_available')}</p>
              )}
            </div>
          </div>

          {/* Crop Types */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
            <h3 className="flex items-center gap-2 font-semibold text-white text-sm mb-4">
              <PieChart className="w-4 h-4 text-indigo-400" />{t('admin.analytics.crop_distribution')}</h3>
            <div className="space-y-3">
              {(distribution?.by_type || []).map((t: any) => (
                <div key={t.label} className="flex items-center justify-between">
                  <span className="text-sm text-zinc-300 capitalize">{t.label}</span>
                  <span className="text-xs text-zinc-500">{t.count} registered</span>
                </div>
              ))}
              {(!distribution?.by_type || distribution.by_type.length === 0) && (
                <p className="text-xs text-zinc-500">{t('admin.analytics.no_crop_data_available')}</p>
              )}
            </div>
          </div>

        </div>

      </div>
    </ProtectedRoute>
  );
}
