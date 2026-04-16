'use client';

/**
 * Crops List Page
 *
 * Enhanced filter bar, circular health indicator,
 * grid/list toggle, pagination, responsive cards.
 */

import { useState, useMemo } from 'react';
import Link from 'next/link';
import {
  Plus, Search, Grid3X3, List, Sprout,
  Calendar, MapPin, ArrowUpDown,
} from 'lucide-react';
import clsx from 'clsx';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useFetch } from '@/hooks/useFetch';
import Badge, { getStatusVariant } from '@/components/Badge';
import FilterChips from '@/components/FilterChips';
import TrustRing from '@/components/TrustRing';
import DisclaimerBanner from '@/components/DisclaimerBanner';
import { useTranslation } from 'react-i18next';

const STATE_FILTERS = [
  { label: 'crops.filter_all_states', fallback: 'All States', value: 'all' },
  { label: 'crops.filter_active', fallback: 'Active', value: 'Active' },
  { label: 'crops.filter_at_risk', fallback: 'At Risk', value: 'AtRisk' },
  { label: 'crops.filter_delayed', fallback: 'Delayed', value: 'Delayed' },
  { label: 'crops.filter_harvested', fallback: 'Harvested', value: 'Harvested' },
  { label: 'crops.filter_closed', fallback: 'Closed', value: 'Closed' },
];

const SEASON_FILTERS = [
  { label: 'crops.filter_all_seasons', fallback: 'All Seasons', value: 'all' },
  { label: 'crops.filter_rabi', fallback: 'Rabi', value: 'rabi' },
  { label: 'crops.filter_kharif', fallback: 'Kharif', value: 'kharif' },
  { label: 'crops.filter_zaid', fallback: 'Zaid', value: 'zaid' },
];

export default function CropsPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const [stateFilter, setStateFilter] = useState('all');
  const [seasonFilter, setSeasonFilter] = useState('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [page, setPage] = useState(1);
  const perPage = 12;

  // Fetch crops
  const queryParams = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
    ...(stateFilter !== 'all' ? { state: stateFilter } : {}),
    ...(seasonFilter !== 'all' ? { seasonal_window_category: seasonFilter } : {}),
    ...(search ? { search } : {}),
  });
  const { data, loading } = useFetch(`/api/v1/crops/?${queryParams}`);
  const crops = data?.items || [];
  const totalPages = data?.total_pages || 1;
  const total = data?.total || 0;

  return (
    <ProtectedRoute requiredRole={["farmer", "admin"]}>
    <DisclaimerBanner context="crops" />
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cultivax-text-primary">{t('crops.title')}</h1>
          <p className="text-sm text-cultivax-text-muted mt-0.5">
            {total} {total !== 1 ? t('crops.crop_total_plural', 'crops total') : t('crops.crop_total_singular', '1 crop total').replace('1 ', '')}
          </p>
        </div>
        <Link href="/crops/new" className="btn-primary flex items-center gap-2 w-fit">
          <Plus className="w-4 h-4" /> {t('crops.create_crop', 'Create Crop')}
        </Link>
      </div>

      {/* Search + Filters */}
      <div className="space-y-3 mb-6">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search crops by type, variety, region..."
              className="!pl-10"
            />
          </div>
          <div className="flex bg-cultivax-elevated rounded-lg p-0.5 gap-0.5">
            <button
              onClick={() => setViewMode('grid')}
              title={t('crops.view_grid', 'Grid view')}
              aria-label={t('crops.view_grid', 'Grid view')}
              className={clsx(
                'p-2 rounded-md transition-colors',
                viewMode === 'grid' ? 'bg-cultivax-primary/15 text-cultivax-primary' : 'text-cultivax-text-muted'
              )}
            >
              <Grid3X3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              title={t('crops.view_list', 'List view')}
              aria-label={t('crops.view_list', 'List view')}
              className={clsx(
                'p-2 rounded-md transition-colors',
                viewMode === 'list' ? 'bg-cultivax-primary/15 text-cultivax-primary' : 'text-cultivax-text-muted'
              )}
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <FilterChips options={STATE_FILTERS.map(f => ({ ...f, label: t(f.label, f.fallback) }))} selected={stateFilter} onChange={setStateFilter} />
          <FilterChips options={SEASON_FILTERS.map(f => ({ ...f, label: t(f.label, f.fallback) }))} selected={seasonFilter} onChange={setSeasonFilter} />
        </div>
      </div>

      {/* Crops Grid/List */}
      {loading ? (
        <div className={clsx(
          viewMode === 'grid'
            ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4'
            : 'space-y-3'
        )}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="skeleton h-40 rounded-xl" />
          ))}
        </div>
      ) : crops.length === 0 ? (
        <div className="card text-center py-16">
          <Sprout className="w-12 h-12 text-cultivax-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">{t('crops.no_crops')}</h3>
          <p className="text-sm text-cultivax-text-muted mb-6">Create your first crop to get started</p>
          <Link href="/crops/new" className="btn-primary inline-flex items-center gap-2">
            <Plus className="w-4 h-4" /> {t('crops.create_crop', 'Create Crop')}
          </Link>
        </div>
      ) : (
        <div className={clsx(
          viewMode === 'grid'
            ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4'
            : 'space-y-3'
        )}>
          {crops.map((crop: any) => (
            <Link
              key={crop.id}
              href={`/crops/${crop.id}`}
              className="card-interactive p-5 block"
            >
              <div className="flex items-start gap-4">
                {/* Health ring */}
                <TrustRing
                  score={1 - (crop.stress_score || 0.2)}
                  size={48}
                  strokeWidth={3}
                  showLabel
                  labelFormat="percentage"
                />

                <div className="flex-1 min-w-0">
                  {/* Title + Badge */}
                  <div className="flex items-center gap-2 mb-1.5">
                    <h3 className="text-sm font-semibold truncate">
                      {crop.crop_type}
                      {crop.variety && (
                        <span className="font-normal text-cultivax-text-muted"> — {crop.variety}</span>
                      )}
                    </h3>
                    <Badge variant={getStatusVariant(crop.state)} size="sm">
                      {crop.state}
                    </Badge>
                  </div>

                  {/* Meta row */}
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-cultivax-text-muted">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {t('crops.day', 'Day')} {crop.current_day_number || '0'}
                    </span>
                    <span>{crop.stage || 'Germination'}</span>
                    {crop.region && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {crop.region}
                      </span>
                    )}
                  </div>

                  {/* Season */}
                  {crop.seasonal_window_category && (
                    <div className="mt-2">
                      <Badge variant="teal" size="sm">
                        {String(t('crops.season_' + (crop.seasonal_window_category || 'unknown').toLowerCase(), crop.seasonal_window_category))}
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-6">
          <p className="text-sm text-cultivax-text-muted">
            Showing {(page - 1) * perPage + 1}–{Math.min(page * perPage, total)} of {total}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="btn-secondary text-sm px-3 py-1.5"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="btn-secondary text-sm px-3 py-1.5"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
    </ProtectedRoute>
  );
}
