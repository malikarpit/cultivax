/**
 * Service Marketplace — Browse providers page.
 * Displays a searchable, filterable grid of service providers with trust scores.
 * SOE Enhancement 9: Trust Score Transparency.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProviderCard from '@/components/ProviderCard';
import { useApi } from '@/hooks/useApi';

interface Provider {
  id: string;
  business_name: string;
  region: string;
  service_types: string[];
  crop_specializations: string[];
  trust_score: number;
  is_verified: boolean;
  completed_requests: number;
  response_time_hours?: number;
}

export default function ServiceMarketplace() {
  const router = useRouter();
  const { data: providers, loading, error, execute } = useApi<Provider[]>();
  const [searchQuery, setSearchQuery] = useState('');
  const [regionFilter, setRegionFilter] = useState('');
  const [serviceFilter, setServiceFilter] = useState('');
  const [cropFilter, setCropFilter] = useState('');

  useEffect(() => {
    const params = new URLSearchParams();
    if (regionFilter) params.append('region', regionFilter);
    if (serviceFilter) params.append('service_type', serviceFilter);
    if (cropFilter) params.append('crop_type', cropFilter);

    const query = params.toString();
    execute(`/api/v1/providers${query ? `?${query}` : ''}`);
  }, [regionFilter, serviceFilter, cropFilter, execute]);

  const filteredProviders = (providers || []).filter((p) =>
    p.business_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleRequestService = (providerId: string) => {
    router.push(`/services/request?provider=${providerId}`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Service Marketplace</h1>
        <p className="text-gray-400 mt-1">
          Find trusted service providers for your farming needs
        </p>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-xs text-gray-400 block mb-1.5">Search</label>
            <input
              type="text"
              placeholder="Search providers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-sm"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1.5">Region</label>
            <select
              value={regionFilter}
              onChange={(e) => setRegionFilter(e.target.value)}
              className="w-full text-sm"
            >
              <option value="">All Regions</option>
              <option value="North">North</option>
              <option value="South">South</option>
              <option value="East">East</option>
              <option value="West">West</option>
              <option value="Central">Central</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1.5">Service Type</label>
            <select
              value={serviceFilter}
              onChange={(e) => setServiceFilter(e.target.value)}
              className="w-full text-sm"
            >
              <option value="">All Services</option>
              <option value="Equipment">Equipment Rental</option>
              <option value="Labor">Labor</option>
              <option value="Consultation">Consultation</option>
              <option value="Transport">Transport</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1.5">Crop Specialization</label>
            <select
              value={cropFilter}
              onChange={(e) => setCropFilter(e.target.value)}
              className="w-full text-sm"
            >
              <option value="">All Crops</option>
              <option value="wheat">Wheat</option>
              <option value="rice">Rice</option>
              <option value="cotton">Cotton</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-2 border-cultivax-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400 mt-3">Loading providers...</p>
        </div>
      )}

      {error && (
        <div className="card border-red-500/30 bg-red-500/10">
          <p className="text-red-400 text-sm">Failed to load providers: {error}</p>
        </div>
      )}

      {!loading && !error && filteredProviders.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-400">No providers found matching your criteria.</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredProviders.map((provider) => (
          <ProviderCard
            key={provider.id}
            {...provider}
            onRequestService={handleRequestService}
          />
        ))}
      </div>

      {/* Trust Score Transparency Note (SOE Enhancement 9) */}
      {!loading && filteredProviders.length > 0 && (
        <div className="text-center">
          <p className="text-xs text-gray-500">
            Trust scores are calculated based on completion rate, complaint ratio,
            resolution speed, consistency, and response time.
          </p>
        </div>
      )}
    </div>
  );
}
