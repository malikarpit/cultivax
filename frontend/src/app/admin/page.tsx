'use client';

/**
 * Admin Dashboard — CultivaX Obsidian Console
 *
 * System overview with real platform metrics from /dashboard/admin-stats.
 * Shows total users, active crops, providers, pending issues, region breakdown.
 */

import Link from 'next/link';
import {
  Users, Sprout, Shield, AlertTriangle, Activity,
  UserCheck, FileText, Skull, Heart, TrendingUp,
  ArrowRight, CheckCircle2, XCircle, Minus, MapPin,
  Loader2, BarChart3,
} from 'lucide-react';
import clsx from 'clsx';
import ProtectedRoute from '@/components/ProtectedRoute';
import StatCard from '@/components/StatCard';
import Badge from '@/components/Badge';

import { useFetch } from '@/hooks/useFetch';

export default function AdminDashboardPage() {
  // Fetch real admin stats from API
  const { data: stats, loading, error } = useFetch('/api/v1/dashboard/admin-stats');

  return (
    <ProtectedRoute requiredRole="admin">
    <div className="animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">CultivaX Obsidian — Admin Console</h1>
        <p className="text-sm text-cultivax-text-muted mt-1">System overview and management</p>
      </div>

      {/* Stats */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="h-4 w-24 bg-cultivax-elevated rounded mb-3" />
              <div className="h-8 w-16 bg-cultivax-elevated rounded" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="card p-5 mb-6 border border-red-500/20 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-400">Failed to load admin stats</p>
            <p className="text-xs text-cultivax-text-muted">{error}</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <StatCard
            icon={Users}
            label="Total Users"
            value={stats?.total_users?.toLocaleString() ?? '0'}
            trend={stats?.total_users > 0 ? 'live' : undefined}
            trendDirection="up"
            color="blue"
          />
          <StatCard
            icon={Sprout}
            label="Active Crops"
            value={stats?.active_crops?.toLocaleString() ?? '0'}
            color="green"
          />
          <StatCard
            icon={Shield}
            label="Providers"
            value={`${stats?.verified_providers ?? 0} / ${stats?.total_providers ?? 0}`}
            color="default"
          />
          <StatCard
            icon={AlertTriangle}
            label="Pending Issues"
            value={stats?.pending_issues ?? 0}
            color={(stats?.pending_issues ?? 0) > 0 ? 'red' : 'default'}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Region Breakdown (Real Data) */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-cultivax-primary" /> Farmers by Region
              </h3>
              <span className="text-xs text-cultivax-text-muted">Top 5 regions</span>
            </div>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-10 bg-cultivax-elevated rounded animate-pulse" />
                ))}
              </div>
            ) : stats?.region_breakdown?.length > 0 ? (
              <div className="space-y-3">
                {stats.region_breakdown.map((item: { region: string; count: number }, index: number) => {
                  const maxCount = stats.region_breakdown[0]?.count || 1;
                  const widthPct = Math.max(10, (item.count / maxCount) * 100);
                  return (
                    <div key={item.region} className="flex items-center gap-3">
                      <div className="w-8 text-xs text-cultivax-text-muted text-right">
                        #{index + 1}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-cultivax-text-primary flex items-center gap-1.5">
                            <MapPin className="w-3 h-3 text-cultivax-primary" />
                            {item.region}
                          </span>
                          <span className="text-sm font-semibold text-cultivax-primary">
                            {item.count.toLocaleString()}
                          </span>
                        </div>
                        <div className="h-2 bg-cultivax-elevated rounded-full overflow-hidden">
                          <div
                            className="h-full bg-cultivax-primary/60 rounded-full transition-all duration-500"
                            style={{ width: `${widthPct}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8">
                <MapPin className="w-8 h-8 text-cultivax-text-muted mx-auto mb-2 opacity-40" />
                <p className="text-sm text-cultivax-text-muted">No regional data available</p>
              </div>
            )}
          </div>

          {/* System Health Link */}
          <div className="card mt-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold flex items-center gap-2">
                <Activity className="w-4 h-4 text-cultivax-primary" /> System Health
              </h3>
              <Link href="/admin/health" className="text-xs text-cultivax-primary font-semibold hover:underline">
                View Details →
              </Link>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded-lg bg-green-500/10 text-center">
                <CheckCircle2 className="w-5 h-5 text-green-400 mx-auto mb-1" />
                <p className="text-xs text-cultivax-text-muted">API</p>
              </div>
              <div className="p-3 rounded-lg bg-green-500/10 text-center">
                <CheckCircle2 className="w-5 h-5 text-green-400 mx-auto mb-1" />
                <p className="text-xs text-cultivax-text-muted">Database</p>
              </div>
              <div className="p-3 rounded-lg bg-green-500/10 text-center">
                <CheckCircle2 className="w-5 h-5 text-green-400 mx-auto mb-1" />
                <p className="text-xs text-cultivax-text-muted">Events</p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-base font-semibold mb-3">Quick Actions</h3>
            <div className="space-y-2">
              {[
                { label: 'User Management', href: '/admin/users', icon: UserCheck },
                { label: 'Provider Management', href: '/admin/providers', icon: Shield },
                { label: 'Rule Templates', href: '/admin/templates', icon: FileText },
                { label: 'Dead Letter Queue', href: '/admin/dead-letters', icon: Skull },
                { label: 'System Health', href: '/admin/health', icon: Activity },
              ].map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-cultivax-text-secondary hover:bg-cultivax-elevated hover:text-cultivax-text-primary transition-all"
                >
                  <item.icon className="w-4 h-4" />
                  <span className="font-medium">{item.label}</span>
                  <ArrowRight className="w-3 h-3 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
              ))}
            </div>
          </div>

          {/* Platform Summary Card */}
          {!loading && stats && (
            <div className="card">
              <h3 className="text-base font-semibold mb-3">Platform Summary</h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-cultivax-text-muted">Total Crops</span>
                  <span className="font-semibold text-cultivax-text-primary">
                    {stats.total_crops?.toLocaleString() ?? '0'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-cultivax-text-muted">Active Crops</span>
                  <span className="font-semibold text-cultivax-primary">
                    {stats.active_crops?.toLocaleString() ?? '0'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-cultivax-text-muted">Verified Providers</span>
                  <span className="font-semibold text-cultivax-text-primary">
                    {stats.verified_providers ?? 0} / {stats.total_providers ?? 0}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-cultivax-text-muted">Regions Active</span>
                  <span className="font-semibold text-cultivax-text-primary">
                    {stats.region_breakdown?.length ?? 0}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recent Admin Actions */}
      <div className="card mt-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold">Recent Admin Actions</h3>
          <Link href="/admin/audit" className="text-xs text-cultivax-primary font-semibold hover:underline">
            Full Audit Log →
          </Link>
        </div>
        <p className="text-sm text-cultivax-text-muted">
          View the complete audit trail of all administrative actions from the audit log.
        </p>
      </div>
    </div>
    </ProtectedRoute>
  );
}
