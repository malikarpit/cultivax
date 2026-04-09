'use client';

/**
 * Government Schemes Browser — FR-31
 *
 * Allows farmers to discover and access official government schemes.
 * Filters by region and category; logs redirect audit via backend.
 * Data freshness indicator shown when fetched (offline-safe).
 */

import { useState } from 'react';
import {
  ExternalLink, Search, Filter, BookOpen,
  Landmark, ChevronRight, Tag, MapPin, RefreshCw,
} from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useFetch } from '@/hooks/useFetch';
import clsx from 'clsx';
import { useTranslation } from 'react-i18next';

const CATEGORIES = ['All', 'subsidy', 'insurance', 'advisory', 'loan', 'other'];
const REGIONS    = ['All', 'Punjab', 'Haryana', 'Rajasthan', 'UP', 'MP', 'Maharashtra', 'Karnataka'];

interface Scheme {
  id: string;
  name: string;
  description: string;
  portal_url: string;
  category: string;
  region: string;
  crop_type?: string;
  tags?: string[];
}

function SchemeCard({ scheme }: { scheme: Scheme }) {
  const [redirecting, setRedirecting] = useState(false);

  async function handleVisit() {
    setRedirecting(true);
    try {
      const token = localStorage.getItem('access_token');
      await fetch(`/api/v1/schemes/${scheme.id}/redirect`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch (_) {
      // non-fatal — still open the portal
    }
    window.open(scheme.portal_url, '_blank', 'noopener,noreferrer');
    setRedirecting(false);
  }

  const catColor: Record<string, string> = {
    subsidy:   'bg-emerald-900/40 text-emerald-300 border-emerald-700',
    insurance: 'bg-blue-900/40 text-blue-300 border-blue-700',
    advisory:  'bg-amber-900/40 text-amber-300 border-amber-700',
    loan:      'bg-purple-900/40 text-purple-300 border-purple-700',
    other:     'bg-zinc-800 text-zinc-300 border-zinc-600',
  };

  return (
    <div className="bg-cultivax-surface border border-cultivax-border rounded-2xl p-5 flex flex-col gap-3 hover:border-cultivax-primary/60 transition-all group">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-cultivax-primary/20 border border-cultivax-primary/40 flex items-center justify-center">
            <Landmark className="w-4 h-4 text-cultivax-primary" />
          </div>
          <span className={clsx(
            'text-xs font-semibold px-2 py-0.5 rounded-full border capitalize',
            catColor[scheme.category] ?? catColor.other,
          )}>
            {scheme.category}
          </span>
        </div>
        {scheme.region && (
          <span className="flex items-center gap-1 text-xs text-cultivax-text-muted">
            <MapPin className="w-3 h-3" />{scheme.region}
          </span>
        )}
      </div>

      <div>
        <h3 className="font-semibold text-cultivax-text-primary text-sm leading-snug group-hover:text-cultivax-primary transition-colors">
          {scheme.name}
        </h3>
        {scheme.description && (
          <p className="text-xs text-cultivax-text-muted mt-1 line-clamp-2">{scheme.description}</p>
        )}
      </div>

      {scheme.tags && scheme.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {scheme.tags.slice(0, 3).map((t) => (
            <span key={t} className="flex items-center gap-1 text-[10px] text-cultivax-text-muted bg-cultivax-background rounded px-1.5 py-0.5 border border-cultivax-border">
              <Tag className="w-2.5 h-2.5" />{t}
            </span>
          ))}
        </div>
      )}

      <button
        onClick={handleVisit}
        disabled={redirecting}
        className="mt-auto flex items-center justify-center gap-2 w-full py-2 rounded-xl bg-cultivax-primary hover:bg-cultivax-primary-hover text-cultivax-surface text-xs font-semibold transition-colors disabled:opacity-60"
      >
        {redirecting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <ExternalLink className="w-3.5 h-3.5" />}
        {redirecting ? 'Opening…' : 'Visit Portal'}
      </button>
    </div>
  );
}

export default function SchemesPage() {
  const { t } = useTranslation();
  const [search, setSearch]     = useState('');
  const [category, setCategory] = useState('All');
  const [region, setRegion]     = useState('All');

  const params = new URLSearchParams();
  if (category !== 'All') params.set('category', category);
  if (region   !== 'All') params.set('region', region);

  const { data, loading, error, refetch } = useFetch<{ items: Scheme[]; total: number }>(
    `/api/v1/schemes?${params.toString()}`,
  );

  const schemes = (data?.items ?? []).filter((s) =>
    search ? s.name.toLowerCase().includes(search.toLowerCase()) : true,
  );

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-cultivax-background text-cultivax-text-primary">
        {/* Header */}
        <div className="border-b border-cultivax-border px-6 py-4 flex items-center justify-between bg-cultivax-surface">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-cultivax-primary/10 border border-cultivax-primary/40 flex items-center justify-center">
              <BookOpen className="w-4 h-4 text-cultivax-primary" />
            </div>
            <div>
              <h1 className="font-bold text-cultivax-text-primary text-lg leading-none">{t('schemes.government_schemes')}</h1>
              <p className="text-xs text-cultivax-text-muted mt-0.5">{t('schemes.browse_amp_access_official')}</p>
            </div>
          </div>
          <button onClick={() => refetch()} title="Refresh schemes" aria-label="Refresh schemes" className="p-2 rounded-lg hover:bg-cultivax-elevated hover:text-cultivax-text-primary text-cultivax-text-muted transition-colors">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <div className="max-w-5xl mx-auto px-6 py-6 space-y-5">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
              <input
                type="text"
                placeholder={t('schemes.search_schemes')}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-cultivax-surface border border-cultivax-border rounded-xl pl-9 pr-4 py-2.5 text-sm text-cultivax-text-primary placeholder:text-cultivax-text-muted focus:outline-none focus:border-cultivax-primary"
              />
            </div>
            <select title="Filter by category" aria-label="Filter by category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="bg-cultivax-surface border border-cultivax-border rounded-xl px-3 py-2.5 text-sm text-cultivax-text-primary focus:outline-none focus:border-cultivax-primary"
            >
              {CATEGORIES.map((c) => <option key={c} value={c}>{c === 'All' ? 'All Categories' : c}</option>)}
            </select>
            <select title="Filter by region" aria-label="Filter by region"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="bg-cultivax-surface border border-cultivax-border rounded-xl px-3 py-2.5 text-sm text-cultivax-text-primary focus:outline-none focus:border-cultivax-primary"
            >
              {REGIONS.map((r) => <option key={r} value={r}>{r === 'All' ? 'All Regions' : r}</option>)}
            </select>
          </div>

          {/* Results */}
          {loading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="bg-cultivax-surface border border-cultivax-border rounded-2xl p-5 h-44 animate-pulse" />
              ))}
            </div>
          )}

          {error && (
            <div className="text-center py-12 text-cultivax-danger text-sm">{error}</div>
          )}

          {!loading && !error && schemes.length === 0 && (
            <div className="text-center py-16">
              <Landmark className="w-10 h-10 text-cultivax-text-muted mx-auto mb-3 opacity-30" />
              <p className="text-cultivax-text-muted text-sm">{t('schemes.no_schemes_found_matching')}</p>
            </div>
          )}

          {!loading && schemes.length > 0 && (
            <>
              <p className="text-xs text-cultivax-text-muted">{schemes.length} scheme{schemes.length !== 1 ? 's' : ''} found</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {schemes.map((s) => <SchemeCard key={s.id} scheme={s} />)}
              </div>
            </>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
