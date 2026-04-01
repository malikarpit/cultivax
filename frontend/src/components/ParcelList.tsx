'use client';

import { MapPin, Pencil, RotateCcw, Trash2 } from 'lucide-react';

import type { LandParcel } from '@/lib/types';

interface ParcelListProps {
  parcels: LandParcel[];
  onEdit: (parcel: LandParcel) => void;
  onDelete: (parcel: LandParcel) => void;
  onRestore?: (parcel: LandParcel) => void;
  onOpen?: (parcel: LandParcel) => void;
}

export default function ParcelList({ parcels, onEdit, onDelete, onRestore, onOpen }: ParcelListProps) {
  if (!parcels.length) {
    return (
      <div className="card text-center py-10 text-cultivax-text-muted">
        No fields yet. Create your first field to link it with crops.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {parcels.map((parcel) => (
        <div key={parcel.id} className="card space-y-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold text-cultivax-text-primary">
                {parcel.parcel_name}
                {parcel.is_deleted ? (
                  <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-yellow-500/10 text-yellow-300 border border-yellow-500/30">
                    Deleted
                  </span>
                ) : null}
              </h3>
              <p className="text-sm text-cultivax-text-muted inline-flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {parcel.region}
                {parcel.sub_region ? `, ${parcel.sub_region}` : ''}
              </p>
            </div>
            {parcel.land_area ? (
              <span className="text-xs px-2 py-1 rounded-full bg-cultivax-primary/10 text-cultivax-primary">
                {parcel.land_area} {parcel.land_area_unit}
              </span>
            ) : null}
          </div>

          <div className="text-sm text-cultivax-text-secondary space-y-1">
            {parcel.irrigation_source ? <p>Irrigation: {parcel.irrigation_source}</p> : null}
            {parcel.soil_type?.primary ? <p>Soil: {parcel.soil_type.primary}</p> : null}
          </div>

          <div className="flex items-center gap-2 pt-1">
            {onOpen ? (
              <button className="btn-secondary text-sm" onClick={() => onOpen(parcel)} type="button">
                Open
              </button>
            ) : null}
            {!parcel.is_deleted ? (
              <>
                <button className="btn-secondary text-sm" onClick={() => onEdit(parcel)} type="button">
                  <Pencil className="w-4 h-4" /> Edit
                </button>
                <button className="btn-danger text-sm" onClick={() => onDelete(parcel)} type="button">
                  <Trash2 className="w-4 h-4" /> Delete
                </button>
              </>
            ) : onRestore ? (
              <button className="btn-secondary text-sm" onClick={() => onRestore(parcel)} type="button">
                <RotateCcw className="w-4 h-4" /> Restore
              </button>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}
