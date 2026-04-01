'use client';

import { useMemo, useState } from 'react';
import { Loader2 } from 'lucide-react';

import MapView from '@/components/MapView';
import { createLandParcel, updateLandParcel } from '@/lib/land-parcels';
import type { LandParcel, LandParcelCreate, LandParcelUpdate, SoilInfo } from '@/lib/types';

interface ParcelFormProps {
  initialData?: LandParcel | null;
  onSuccess: (parcel: LandParcel) => void;
  onCancel: () => void;
}

const IRRIGATION_OPTIONS = ['canal', 'tubewell', 'rainfed', 'drip', 'sprinkler', 'mixed'];
const SOIL_PRIMARY_OPTIONS = ['alluvial', 'black', 'red', 'laterite', 'sandy', 'clay'];
const SOIL_ORGANIC_OPTIONS = ['low', 'medium', 'high'];

export default function ParcelForm({ initialData, onSuccess, onCancel }: ParcelFormProps) {
  const isEdit = !!initialData;
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [parcelName, setParcelName] = useState(initialData?.parcel_name || '');
  const [region, setRegion] = useState(initialData?.region || '');
  const [subRegion, setSubRegion] = useState(initialData?.sub_region || '');
  const [landArea, setLandArea] = useState(initialData?.land_area?.toString() || '');
  const [landAreaUnit, setLandAreaUnit] = useState<'acres' | 'hectares' | 'bigha'>(
    initialData?.land_area_unit || 'acres'
  );
  const [irrigationSource, setIrrigationSource] = useState(initialData?.irrigation_source || '');

  const [lat, setLat] = useState((initialData?.gps_coordinates?.lat ?? 22.5).toString());
  const [lng, setLng] = useState((initialData?.gps_coordinates?.lng ?? 78.9).toString());
  const [polygon, setPolygon] = useState<[number, number][]>(
    initialData?.gps_coordinates?.boundary_polygon || []
  );

  const [soilPrimary, setSoilPrimary] = useState(initialData?.soil_type?.primary || '');
  const [soilPh, setSoilPh] = useState(initialData?.soil_type?.ph?.toString() || '');
  const [soilOrganic, setSoilOrganic] = useState(initialData?.soil_type?.organic_matter || '');

  const mapCenter = useMemo<[number, number]>(() => {
    const parsedLat = Number(lat);
    const parsedLng = Number(lng);
    if (!Number.isFinite(parsedLat) || !Number.isFinite(parsedLng)) return [22.5, 78.9];
    return [parsedLat, parsedLng];
  }, [lat, lng]);

  const canSubmit = parcelName.trim() && region.trim() && Number.isFinite(Number(lat)) && Number.isFinite(Number(lng));

  const handleSubmit = async () => {
    if (!canSubmit || submitting) return;
    setSubmitting(true);
    setError(null);

    const soilType: SoilInfo | undefined =
      soilPrimary || soilPh || soilOrganic
        ? {
            primary: soilPrimary || undefined,
            ph: soilPh ? Number(soilPh) : undefined,
            organic_matter: soilOrganic || undefined,
          }
        : undefined;

    const payloadBase: LandParcelCreate = {
      parcel_name: parcelName.trim(),
      region: region.trim(),
      sub_region: subRegion.trim() || undefined,
      land_area: landArea ? Number(landArea) : undefined,
      land_area_unit: landAreaUnit as 'acres' | 'hectares' | 'bigha',
      irrigation_source: irrigationSource || undefined,
      soil_type: soilType,
      gps_coordinates: {
        lat: Number(lat),
        lng: Number(lng),
        boundary_polygon: polygon.length >= 3 ? polygon : undefined,
      },
    };

    try {
      const saved = isEdit
        ? await updateLandParcel(initialData.id, payloadBase as LandParcelUpdate)
        : await createLandParcel(payloadBase);
      onSuccess(saved);
    } catch (err: any) {
      setError(err.message || 'Failed to save field');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <input
          className="input"
          placeholder="Field name"
          value={parcelName}
          onChange={(e) => setParcelName(e.target.value)}
        />
        <input
          className="input"
          placeholder="Region"
          value={region}
          onChange={(e) => setRegion(e.target.value)}
        />
        <input
          className="input"
          placeholder="Sub-region"
          value={subRegion}
          onChange={(e) => setSubRegion(e.target.value)}
        />
        <div className="grid grid-cols-2 gap-2">
          <input
            className="input"
            type="number"
            step="0.01"
            placeholder="Area"
            value={landArea}
            onChange={(e) => setLandArea(e.target.value)}
          />
          <select
            className="input"
            value={landAreaUnit}
            onChange={(e) => setLandAreaUnit(e.target.value as 'acres' | 'hectares' | 'bigha')}
          >
            <option value="acres">acres</option>
            <option value="hectares">hectares</option>
            <option value="bigha">bigha</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <input
          className="input"
          type="number"
          step="0.000001"
          placeholder="Latitude"
          value={lat}
          onChange={(e) => setLat(e.target.value)}
        />
        <input
          className="input"
          type="number"
          step="0.000001"
          placeholder="Longitude"
          value={lng}
          onChange={(e) => setLng(e.target.value)}
        />
        <select
          className="input"
          value={irrigationSource}
          onChange={(e) => setIrrigationSource(e.target.value)}
        >
          <option value="">Irrigation source</option>
          {IRRIGATION_OPTIONS.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <select className="input" value={soilPrimary} onChange={(e) => setSoilPrimary(e.target.value)}>
          <option value="">Soil type</option>
          {SOIL_PRIMARY_OPTIONS.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
        <input
          className="input"
          type="number"
          step="0.1"
          min="0"
          max="14"
          placeholder="Soil pH"
          value={soilPh}
          onChange={(e) => setSoilPh(e.target.value)}
        />
        <select className="input" value={soilOrganic} onChange={(e) => setSoilOrganic(e.target.value)}>
          <option value="">Organic matter</option>
          {SOIL_ORGANIC_OPTIONS.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      </div>

      <MapView
        center={mapCenter}
        zoom={13}
        editable
        polygons={polygon.length >= 3 ? [{ id: 'draft', positions: polygon, label: 'Boundary' }] : []}
        markers={[{ id: 'center', lat: mapCenter[0], lng: mapCenter[1], label: parcelName || 'Field center' }]}
        onPolygonComplete={(points) => setPolygon(points)}
        height="300px"
      />

      <p className="text-xs text-cultivax-text-muted">
        Click on map to draw boundary, then double-click to finish.
      </p>

      {error && <div className="text-sm text-red-400">{error}</div>}

      <div className="flex items-center justify-end gap-2">
        <button className="btn-secondary" onClick={onCancel} type="button" disabled={submitting}>
          Cancel
        </button>
        <button className="btn-primary" onClick={handleSubmit} type="button" disabled={!canSubmit || submitting}>
          {submitting ? (
            <span className="inline-flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Saving...</span>
          ) : isEdit ? 'Update Field' : 'Create Field'}
        </button>
      </div>
    </div>
  );
}
