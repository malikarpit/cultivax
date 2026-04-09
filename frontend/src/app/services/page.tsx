'use client';

/**
 * Service Marketplace — Find and book agricultural services
 *
 * Search + category filter chips + provider cards with trust rings
 */

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Search, MapPin, Star, Clock, CheckCircle2,
  Beaker, Plane, Droplets, Bug, Users, Wrench,
  ArrowRight, SlidersHorizontal,
} from 'lucide-react';
import clsx from 'clsx';
import ProtectedRoute from '@/components/ProtectedRoute';
import TrustRing from '@/components/TrustRing';
import FilterChips from '@/components/FilterChips';
import Badge from '@/components/Badge';
import { useFetch } from '@/hooks/useFetch';
import { useTranslation } from 'react-i18next';

const CATEGORIES = [
  { label: 'All', value: 'all' },
  { label: 'Soil Testing', value: 'soil_testing' },
  { label: 'Drone Survey', value: 'drone_survey' },
  { label: 'Irrigation', value: 'irrigation' },
  { label: 'Pest Control', value: 'pest_control' },
  { label: 'Harvest Labor', value: 'harvest_labor' },
  { label: 'Equipment Rental', value: 'equipment_rental' },
];

export default function ServicesPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');

  const [debouncedSearch, setDebouncedSearch] = useState(search);

  // Debounce search input map
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
    }, 300);
    return () => clearTimeout(handler);
  }, [search]);

  // Build query sting
  const queryParams = new URLSearchParams();
  if (category !== 'all') {
    queryParams.append('service_type', category);
  }
  if (debouncedSearch) {
    queryParams.append('search', debouncedSearch);
  }
  
  const { data, loading, error } = useFetch(`/api/v1/providers/search?${queryParams.toString()}`);
  const providers = data?.items || [];

  return (
    <ProtectedRoute>
    <div className="animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">{t('services.title')}</h1>
        <p className="text-sm text-cultivax-text-muted mt-1">Find trusted agricultural service providers</p>
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search for tractor rental, soil testing, drone survey..."
          className="!pl-10"
        />
      </div>

      {/* Category Chips */}
      <FilterChips options={CATEGORIES} selected={category} onChange={setCategory} className="mb-6" />

      {/* Provider Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {loading && (
           <div className="col-span-1 md:col-span-2 py-12 text-center text-cultivax-text-muted">Loading providers...</div>
        )}
        {!loading && providers.length === 0 && (
          <div className="card text-center py-12 col-span-1 md:col-span-2">
            <SlidersHorizontal className="w-8 h-8 text-cultivax-text-muted mx-auto mb-3" />
            <p className="text-cultivax-text-secondary">No ranked providers match your search</p>
            <p className="text-xs text-cultivax-text-muted mt-1">Try expanding your parameters or search keywords.</p>
          </div>
        )}
        
        {!loading && providers.map((provider: any) => (
          <div key={provider.id} className="card-interactive p-5">
            <div className="flex items-start gap-4">
              <TrustRing score={provider.trust_score ? provider.trust_score / 10 : 0} size={56} strokeWidth={4} labelFormat="decimal" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-semibold truncate">{provider.business_name || 'Independent Provider'}</h3>
                  {!provider.is_suspended ? (
                    <Badge variant="green" size="sm" dot>Active</Badge>
                  ) : (
                    <Badge variant="red" size="sm">Suspended</Badge>
                  )}
                  {provider.is_verified && (
                    <Badge variant="blue" size="sm">Verified</Badge>
                  )}
                  {provider.ranking_flags?.includes('FAIRNESS_BOOST') && (
                    <Badge variant="purple" size="sm">✨ Fairness Boosted</Badge>
                  )}
                </div>
                <p className="text-xs text-cultivax-text-muted mb-2 line-clamp-2">{provider.description}</p>

                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-cultivax-text-muted">
                  <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {provider.region} ({provider.service_radius_km}km)</span>
                  <span className="flex items-center gap-1 capitalize"><Wrench className="w-3 h-3" /> {provider.service_type.replace('_', ' ')}</span>
                </div>

                <div className="flex items-center justify-between mt-3 pt-3 border-t border-cultivax-border">
                  <Link
                    href={`/services/${provider.id}`}
                    className="text-xs font-medium text-cultivax-text-muted hover:text-cultivax-text-primary transition-colors"
                  >
                    View Details
                  </Link>
                  <Link
                    href={`/services/request?provider=${provider.id}`}
                    className={clsx(
                      'text-xs font-medium flex items-center gap-1 transition-colors',
                      !provider.is_suspended
                        ? 'text-cultivax-primary hover:text-cultivax-primary-hover'
                        : 'text-cultivax-text-muted pointer-events-none'
                    )}
                  >
                    {t('services.request')} <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
    </ProtectedRoute>
  );
}
