'use client';

/**
 * Crop Lifecycle History Timeline
 * 
 * Reference: stitch_landing_page 3/crop_history_timeline
 * Sections:
 *  1. Hero header with crop name + image background
 *  2. Stat cards: Growth Index, Logged Actions, Hydration Avg
 *  3. Vertical timeline with alternating left/right cards
 *  4. Related Intelligence section at bottom
 */

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  ArrowRight, TrendingUp, ClipboardList, Droplets,
  ChevronDown, Sprout, Bug, Beaker, Pipette,
  Leaf, Calendar, Download, AlertTriangle, BarChart3,
} from 'lucide-react';
import clsx from 'clsx';
import ProtectedRoute from '@/components/ProtectedRoute';
import { apiGet } from '@/lib/api';

/* ─── Page Component ─────────────────────────────────────── */

const getActionIcon = (type: string) => {
  if (type.includes('Irrig')) return Droplets;
  if (type.includes('Pest')) return Bug;
  if (type.includes('Fert')) return Beaker;
  if (type.includes('Seed')) return Sprout;
  return ClipboardList;
};

const getActionColor = (type: string) => {
  if (type.includes('Irrig')) return 'text-m3-tertiary';
  if (type.includes('Pest')) return 'text-m3-error';
  if (type.includes('Fert')) return 'text-m3-secondary';
  return 'text-m3-primary';
};

/* ─── Page Component ─────────────────────────────────────── */

export default function CropHistoryPage() {
  const params = useParams();
  const cropId = params.id;
  const [showMore, setShowMore] = useState(false);
  const [actions, setActions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadActions = async () => {
      try {
        const data = await apiGet(`/api/v1/crops/${cropId}/actions`);
        const payload = data as any;
        setActions(Array.isArray(payload) ? payload : payload?.actions || []);
      } catch (err) {
        console.error('Failed to load actions', err);
      } finally {
        setLoading(false);
      }
    };
    if (cropId) loadActions();
  }, [cropId]);

  return (
    <ProtectedRoute requiredRole={["farmer", "admin"]}>
    <div className="animate-fade-in space-y-10">
      {/* ═══ Hero Header ═══ */}
      <section className="glass-card rounded-3xl overflow-hidden relative">
        {/* Background image */}
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=1200&h=400&fit=crop"
            alt="Crop field"
            className="w-full h-full object-cover opacity-20 filter grayscale contrast-150"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-m3-surface-dim via-m3-surface-dim/90 to-transparent" />
        </div>

        <div className="relative z-10 p-8 md:p-12">
          {/* Breadcrumb */}
          <nav className="flex items-center gap-2 text-[11px] font-mono text-m3-on-surface-variant mb-4">
            <Link href="/crops" className="hover:text-m3-primary transition-colors">CROPS</Link>
            <span>/</span>
            <span className="text-m3-on-surface-variant">HD-2967</span>
            <span>/</span>
            <span className="text-m3-primary">Lifecycle History</span>
          </nav>

          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tighter">
            <span className="text-m3-on-surface">Wheat </span>
            <span className="text-m3-primary">HD-2967</span>
          </h1>
          <p className="text-m3-on-surface-variant mt-2 max-w-xl">
            Deep-dive technical timeline. Monitoring biological progress and manual intervention records since planting.
          </p>

          <div className="flex flex-wrap gap-3 mt-4">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-m3-primary/10 text-m3-primary text-[10px] font-bold uppercase tracking-widest rounded-full">
              <span className="w-1.5 h-1.5 bg-m3-primary rounded-full" /> Active Growth
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-m3-secondary/10 text-m3-secondary text-[10px] font-bold uppercase tracking-widest rounded-full">
              📍 Sector 04B
            </span>
          </div>
        </div>
      </section>

      {/* ═══ Stat Cards ═══ */}
      <section className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="glass-card rounded-xl p-6 border-l-2 border-m3-primary border border-m3-outline-variant/10">
          <div className="flex items-center justify-between mb-3">
            <p className="mono-label font-bold">Growth Index</p>
            <TrendingUp className="w-5 h-5 text-m3-primary" />
          </div>
          <p className="font-mono text-3xl font-black tracking-tighter">
            84.2 <span className="text-sm font-normal text-m3-primary">%</span>
          </p>
          <div className="w-full h-1 bg-m3-surface-container-highest rounded-full mt-3 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-m3-primary to-m3-primary-container rounded-full" style={{ width: '84%' }} />
          </div>
        </div>

        <div className="glass-card rounded-xl p-6 border border-m3-outline-variant/10">
          <div className="flex items-center justify-between mb-3">
            <p className="mono-label font-bold">Logged Actions</p>
            <ClipboardList className="w-5 h-5 text-m3-primary" />
          </div>
          <p className="font-mono text-3xl font-black tracking-tighter">
            {actions.length} <span className="text-sm font-normal text-m3-primary">Items</span>
          </p>
          <p className="text-[10px] text-m3-on-surface-variant mt-2">Overall history</p>
        </div>

        <div className="glass-card rounded-xl p-6 border border-m3-outline-variant/10">
          <div className="flex items-center justify-between mb-3">
            <p className="mono-label font-bold">Hydration Avg</p>
            <Droplets className="w-5 h-5 text-m3-tertiary" />
          </div>
          <p className="font-mono text-3xl font-black tracking-tighter">
            620 <span className="text-sm font-normal text-m3-on-surface-variant">mL/day</span>
          </p>
          <p className="text-[10px] text-m3-on-surface-variant mt-2">Stable for 14 days</p>
        </div>
      </section>

      {/* ═══ Timeline ═══ */}
      <section className="relative">
        {/* Central vertical line */}
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-m3-outline-variant/20 -translate-x-1/2 hidden md:block" />

        <div className="space-y-12 md:space-y-16">
          {actions.length === 0 && !loading && (
            <div className="text-center py-10 text-m3-on-surface-variant">
              No actions logged for this crop yet.
            </div>
          )}
          {actions.map((action, index) => {
            const Icon = getActionIcon(action.action_type || '');
            const iconColor = getActionColor(action.action_type || '');
            const isLeft = index % 2 === 0;

            return (
              <div key={action.id} className="relative">
                {/* Center dot */}
                <div className="absolute left-1/2 -translate-x-1/2 w-10 h-10 rounded-full bg-m3-surface-container-high border border-m3-outline-variant/20 flex items-center justify-center z-10 hidden md:flex">
                  <Icon className={clsx('w-4 h-4', iconColor)} />
                </div>

                <div className={clsx(
                  'grid grid-cols-1 md:grid-cols-2 gap-8 items-center',
                  !isLeft && 'md:direction-rtl'
                )}>
                  {/* Event Card */}
                  <div className={clsx(
                    isLeft ? 'md:pr-16' : 'md:pl-16 md:order-2',
                  )}>
                    <div className="glass-card rounded-2xl p-6 border border-m3-outline-variant/10 hover:bg-m3-surface-container-high transition-colors">
                      <span className="inline-block stat-tag bg-m3-primary/10 text-m3-primary mb-3">
                        {new Date(action.action_effective_date || action.effective_date).toLocaleDateString()}
                      </span>
                      <div className="flex items-start justify-between">
                        <h4 className="text-lg font-bold text-m3-on-surface">{action.action_type}</h4>
                        <Icon className={clsx('w-5 h-5 flex-shrink-0 md:hidden', iconColor)} />
                      </div>
                      <p className="text-sm text-m3-on-surface-variant mt-2 leading-relaxed">
                        {action.notes || 'No notes provided. Task completed as per schedule.'}
                      </p>
                      <button className="mt-4 text-sm font-bold text-m3-primary hover:underline flex items-center gap-1 uppercase tracking-wider">
                        View Analysis <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  {/* Side Label */}
                  <div className={clsx(
                    'hidden md:block',
                    isLeft ? 'md:pl-16 md:order-2' : 'md:pr-16',
                  )}>
                    <p className="mono-label">{action.category || 'Maintenance'}</p>
                    <p className="text-sm font-mono text-m3-on-surface-variant mt-1">Operator: You</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Load More */}
        <div className="text-center mt-12">
          <button
            onClick={() => setShowMore(!showMore)}
            className="px-8 py-3 rounded-xl bg-m3-surface-container-high text-m3-on-surface font-bold text-sm hover:bg-m3-surface-container-highest transition-colors inline-flex items-center gap-2"
          >
            Load Older History <ChevronDown className="w-4 h-4" />
          </button>
        </div>
      </section>

      {/* ═══ Related Intelligence ═══ */}
      <section>
        <h3 className="text-2xl font-bold text-m3-on-surface mb-6">Related Intelligence</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-card rounded-2xl p-6 border border-m3-outline-variant/10 md:row-span-2 flex flex-col justify-between">
            <div>
              <Beaker className="w-8 h-8 text-m3-primary mb-4" />
              <h4 className="text-lg font-bold text-m3-on-surface">Biological Analysis</h4>
              <p className="text-sm text-m3-on-surface-variant mt-2">
                Review full chemical and microbial breakdown for this crop batch.
              </p>
            </div>
            <button className="mt-4 text-sm font-bold text-m3-primary hover:underline flex items-center gap-1">
              Open Report <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="glass-card rounded-2xl p-6 border border-m3-outline-variant/10">
            <AlertTriangle className="w-6 h-6 text-m3-secondary mb-3" />
            <h4 className="font-bold text-m3-on-surface">Climate Overlay</h4>
            <p className="text-xs text-m3-on-surface-variant mt-1">Environmental impact data correlations.</p>
          </div>

          <div className="glass-card rounded-2xl p-6 border border-m3-outline-variant/10">
            <Download className="w-6 h-6 text-m3-primary mb-3" />
            <h4 className="font-bold text-m3-on-surface">Export Report</h4>
            <p className="text-xs text-m3-on-surface-variant mt-1">PDF / CSV Formats</p>
          </div>
        </div>
      </section>
    </div>
    </ProtectedRoute>
  );
}
