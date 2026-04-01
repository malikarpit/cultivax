'use client';

import { useMemo } from 'react';
import clsx from 'clsx';
import { MapPin, Plus } from 'lucide-react';

import { useFetch } from '@/hooks/useFetch';
import type { LandParcel, ParcelSelectorProps } from '@/lib/types';

export default function ParcelSelector({
  value,
  excludeIds = [],
  onSelect,
  onCreateNew,
  disabled = false,
  className,
}: ParcelSelectorProps) {
  const { data, loading, error } = useFetch<LandParcel[]>('/api/v1/land-parcels');

  const parcels = useMemo(() => {
    const list = data || [];
    if (!excludeIds.length) return list;
    return list.filter((p) => !excludeIds.includes(p.id));
  }, [data, excludeIds]);

  const selectedParcel = parcels.find((p) => p.id === value) || null;

  return (
    <div className={clsx('space-y-3', className)}>
      <label className="text-sm font-medium text-cultivax-text-primary block">
        Linked Field
      </label>

      {loading ? (
        <div className="text-sm text-cultivax-text-muted">Loading fields...</div>
      ) : error ? (
        <div className="space-y-2">
          <div className="text-sm text-red-400">Unable to load fields: {error}</div>
          {onCreateNew && (
            <button type="button" className="btn-secondary" onClick={onCreateNew}>
              <Plus className="w-4 h-4" /> Create New Field
            </button>
          )}
        </div>
      ) : (
        <>
          <select
            className="input w-full"
            disabled={disabled}
            value={value || ''}
            onChange={(e) => {
              const next = parcels.find((p) => p.id === e.target.value) || null;
              onSelect(next);
            }}
          >
            <option value="">No field linked</option>
            {parcels.map((parcel) => (
              <option key={parcel.id} value={parcel.id}>
                {parcel.parcel_name} - {parcel.region}
              </option>
            ))}
          </select>

          {selectedParcel && (
            <div className="rounded-xl border border-cultivax-border bg-cultivax-elevated/30 p-3 text-sm text-cultivax-text-secondary">
              <div className="flex items-center gap-2 text-cultivax-text-primary font-medium mb-1">
                <MapPin className="w-4 h-4" />
                {selectedParcel.parcel_name}
              </div>
              <div>
                {selectedParcel.region}
                {selectedParcel.sub_region ? `, ${selectedParcel.sub_region}` : ''}
              </div>
              {selectedParcel.land_area ? (
                <div>
                  Area: {selectedParcel.land_area} {selectedParcel.land_area_unit}
                </div>
              ) : null}
            </div>
          )}

          {onCreateNew && (
            <button type="button" className="btn-secondary" onClick={onCreateNew} disabled={disabled}>
              <Plus className="w-4 h-4" /> Create New Field
            </button>
          )}
        </>
      )}
    </div>
  );
}
