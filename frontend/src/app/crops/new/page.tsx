'use client';

/**
 * New Crop Record — Multi-step wizard form
 * 
 * Reference: stitch_landing_page 3/new_crop_form
 * 3-step wizard: Identity → Environment → Review
 * Glass card form container with protocol overview preview
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft, ArrowRight, Sprout, MapPin, Calendar,
  Droplets, Leaf, Check, ChevronDown,
} from 'lucide-react';
import clsx from 'clsx';
import ProtectedRoute from '@/components/ProtectedRoute';
import ParcelSelector from '@/components/ParcelSelector';
import { apiPost } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import type { LandParcel } from '@/lib/types';

const CROP_TYPES = [
  'Wheat', 'Rice', 'Maize', 'Cotton', 'Sugarcane',
  'Mustard', 'Soybean', 'Groundnut', 'Bajra', 'Jowar',
];

const REGIONS = [
  'Punjab - North', 'Haryana - North', 'UP - Central',
  'Maharashtra - West', 'Karnataka - South', 'Tamil Nadu - South',
  'Rajasthan - West', 'Gujarat - West', 'MP - Central', 'Bihar - East',
];

type StepId = 1 | 2 | 3;

export default function NewCropPage() {
  const router = useRouter();
  const { refreshUser } = useAuth();
  const [step, setStep] = useState<StepId>(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [cropType, setCropType] = useState('');
  const [variety, setVariety] = useState('');
  const [sowingDate, setSowingDate] = useState('');
  const [region, setRegion] = useState('');
  const [landArea, setLandArea] = useState('');
  const [soilType, setSoilType] = useState('');
  const [irrigationType, setIrrigationType] = useState('');
  const [notes, setNotes] = useState('');
  const [selectedParcelId, setSelectedParcelId] = useState<string | null>(null);
  const [selectedParcelName, setSelectedParcelName] = useState<string | null>(null);

  const steps: { id: StepId; label: string }[] = [
    { id: 1, label: 'Identity' },
    { id: 2, label: 'Environment' },
    { id: 3, label: 'Review' },
  ];

  const canAdvance = () => {
    if (step === 1) return cropType && sowingDate && region;
    if (step === 2) return true;
    return true;
  };

  const handleSubmit = async () => {
    if (submitting) return;
    setSubmitting(true);
    setError(null);

    try {
      const payload = {
        crop_type: cropType,
        variety: variety || null,
        sowing_date: sowingDate,
        region,
        sub_region: null,
        land_area: landArea ? parseFloat(landArea) : null,
        land_parcel_id: selectedParcelId,
        metadata_extra: {
          soil_type: soilType || undefined,
          irrigation_type: irrigationType || undefined,
          notes: notes || undefined,
          source: 'new_crop_wizard',
          onboarding: true,
        },
      };

      await apiPost('/api/v1/crops', payload);
      await refreshUser();
      router.push('/crops');
    } catch (err: any) {
      setError(err.message || 'Failed to create crop. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="animate-fade-in flex flex-col items-center">
      {/* Hero Header */}
      <div className="w-full max-w-4xl mb-10 text-center">
        <span className="inline-block px-4 py-1.5 bg-m3-primary/10 text-m3-primary text-[10px] font-bold tracking-[0.2em] uppercase rounded-full mb-4">
          Cultivation Protocol
        </span>
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tighter text-m3-on-surface mb-3">
          New Crop Record
        </h1>
        <p className="text-m3-on-surface-variant max-w-lg mx-auto">
          Initiate a new growth cycle by defining your seed variety and environmental parameters.
        </p>
      </div>

      {/* Stepper */}
      <div className="w-full max-w-2xl mb-10 flex items-center justify-between relative px-4">
        {/* Connection line */}
        <div className="absolute top-5 left-[15%] right-[15%] h-[2px] bg-m3-surface-container-highest z-0" />
        <div
          className="absolute top-5 left-[15%] h-[2px] bg-m3-primary z-0 transition-all duration-500"
          style={{ width: step === 1 ? '0%' : step === 2 ? '35%' : '70%' }}
        />

        {steps.map((s) => (
          <div key={s.id} className="relative z-10 flex flex-col items-center gap-2">
            <div
              className={clsx(
                'w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all duration-300',
                step >= s.id
                  ? 'bg-m3-primary text-m3-on-primary shadow-[0_0_15px_rgba(90,240,179,0.3)]'
                  : 'bg-m3-surface-container-highest text-m3-on-surface-variant'
              )}
            >
              {step > s.id ? <Check className="w-4 h-4" /> : s.id}
            </div>
            <span
              className={clsx(
                'text-[10px] font-bold uppercase tracking-wider',
                step >= s.id ? 'text-m3-primary' : 'text-m3-on-surface-variant'
              )}
            >
              {s.label}
            </span>
          </div>
        ))}
      </div>

      {/* Form Container — Glass Card */}
      <div className="w-full max-w-2xl glass-card rounded-xl p-8 shadow-2xl relative overflow-hidden">
        {/* Decorative glow */}
        <div className="absolute -top-24 -right-24 w-64 h-64 bg-m3-primary/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-8">
          {/* ═══ Step 1: Identity ═══ */}
          {step === 1 && (
            <div className="space-y-6 animate-fade-in">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Crop Type */}
                <div className="space-y-2">
                  <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">
                    Crop Type
                  </label>
                  <div className="relative">
                    <select
                      value={cropType}
                      onChange={(e) => setCropType(e.target.value)}
                      className="w-full bg-m3-surface-container-highest border-none rounded-lg px-4 py-3 text-m3-on-surface focus:ring-1 focus:ring-m3-primary/40 appearance-none transition-all"
                    >
                      <option value="" disabled>Select species...</option>
                      {CROP_TYPES.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-m3-on-surface-variant pointer-events-none" />
                  </div>
                </div>

                {/* Variety */}
                <div className="space-y-2">
                  <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">
                    Variety
                  </label>
                  <input
                    type="text"
                    value={variety}
                    onChange={(e) => setVariety(e.target.value)}
                    placeholder="e.g. HD-2967, Pusa Bold"
                    className="w-full bg-m3-surface-container-highest border-none rounded-lg px-4 py-3 text-m3-on-surface focus:ring-1 focus:ring-m3-primary/40 placeholder:text-m3-on-surface-variant/30 transition-all"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Sowing Date */}
                <div className="space-y-2">
                  <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">
                    Sowing Date
                  </label>
                  <div className="relative">
                    <input
                      type="date"
                      value={sowingDate}
                      onChange={(e) => setSowingDate(e.target.value)}
                      className="w-full bg-m3-surface-container-highest border-none rounded-lg px-4 py-3 text-m3-on-surface focus:ring-1 focus:ring-m3-primary/40 transition-all [color-scheme:dark]"
                    />
                    <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-m3-on-surface-variant pointer-events-none" />
                  </div>
                </div>

                {/* Region */}
                <div className="space-y-2">
                  <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">
                    Region
                  </label>
                  <div className="relative">
                    <select
                      value={region}
                      onChange={(e) => setRegion(e.target.value)}
                      className="w-full bg-m3-surface-container-highest border-none rounded-lg px-4 py-3 text-m3-on-surface focus:ring-1 focus:ring-m3-primary/40 appearance-none transition-all"
                    >
                      <option value="" disabled>Select zone...</option>
                      {REGIONS.map((r) => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>
                    <MapPin className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-m3-on-surface-variant pointer-events-none" />
                  </div>
                </div>
              </div>

              {/* Land Area */}
              <div className="space-y-2">
                <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">
                  Land Area (Square Meters)
                </label>
                <div className="relative">
                  <input
                    type="number"
                    value={landArea}
                    onChange={(e) => setLandArea(e.target.value)}
                    placeholder="0.00"
                    step="0.01"
                    className="w-full bg-m3-surface-container-highest border-none rounded-lg px-4 py-4 text-m3-on-surface font-mono focus:ring-1 focus:ring-m3-primary/40 transition-all"
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[10px] font-mono font-bold text-m3-primary">
                    M²
                  </span>
                </div>
                <p className="text-[10px] text-m3-on-surface-variant/60 italic mt-1">
                  Numerical precision required for biomass calculation.
                </p>
              </div>

              <ParcelSelector
                value={selectedParcelId}
                onSelect={(parcel: LandParcel | null) => {
                  setSelectedParcelId(parcel?.id || null);
                  setSelectedParcelName(parcel?.parcel_name || null);
                }}
              />
            </div>
          )}

          {/* ═══ Step 2: Environment ═══ */}
          {step === 2 && (
            <div className="space-y-6 animate-fade-in">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">
                    Soil Type
                  </label>
                  <select
                    value={soilType}
                    onChange={(e) => setSoilType(e.target.value)}
                    className="w-full bg-m3-surface-container-highest border-none rounded-lg px-4 py-3 text-m3-on-surface focus:ring-1 focus:ring-m3-primary/40 appearance-none transition-all"
                  >
                    <option value="">Select soil type...</option>
                    <option value="alluvial">Alluvial Soil</option>
                    <option value="black">Black Cotton Soil</option>
                    <option value="red">Red Soil</option>
                    <option value="laterite">Laterite Soil</option>
                    <option value="sandy">Sandy Loam</option>
                    <option value="clay">Clay Soil</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">
                    Irrigation Method
                  </label>
                  <select
                    value={irrigationType}
                    onChange={(e) => setIrrigationType(e.target.value)}
                    className="w-full bg-m3-surface-container-highest border-none rounded-lg px-4 py-3 text-m3-on-surface focus:ring-1 focus:ring-m3-primary/40 appearance-none transition-all"
                  >
                    <option value="">Select method...</option>
                    <option value="drip">Drip Irrigation</option>
                    <option value="sprinkler">Sprinkler</option>
                    <option value="flood">Flood / Basin</option>
                    <option value="canal">Canal Irrigation</option>
                    <option value="rainfed">Rain-fed</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">
                  Additional Notes
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Any observations about soil condition, previous crop, etc..."
                  rows={4}
                  className="w-full bg-m3-surface-container-highest border-none rounded-lg px-4 py-3 text-m3-on-surface focus:ring-1 focus:ring-m3-primary/40 placeholder:text-m3-on-surface-variant/30 transition-all resize-none"
                />
              </div>
            </div>
          )}

          {/* ═══ Step 3: Review ═══ */}
          {step === 3 && (
            <div className="space-y-6 animate-fade-in">
              <h3 className="text-lg font-bold text-m3-on-surface">Review Your Crop Record</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  { label: 'Crop Type', value: cropType || '—' },
                  { label: 'Variety', value: variety || '—' },
                  { label: 'Sowing Date', value: sowingDate || '—' },
                  { label: 'Region', value: region || '—' },
                  { label: 'Land Area', value: landArea ? `${landArea} m²` : '—' },
                  { label: 'Linked Field', value: selectedParcelName || '—' },
                  { label: 'Soil Type', value: soilType || '—' },
                  { label: 'Irrigation', value: irrigationType || '—' },
                ].map((item) => (
                  <div key={item.label} className="bg-m3-surface-container-low rounded-lg p-4">
                    <p className="mono-label mb-1">{item.label}</p>
                    <p className="text-sm font-bold text-m3-on-surface">{item.value}</p>
                  </div>
                ))}
              </div>

              {notes && (
                <div className="bg-m3-surface-container-low rounded-lg p-4">
                  <p className="mono-label mb-1">Notes</p>
                  <p className="text-sm text-m3-on-surface-variant">{notes}</p>
                </div>
              )}
            </div>
          )}

          {/* Protocol Overview (Step 1 only) */}
          {step === 1 && (
            <div className="bg-m3-surface-container-low rounded-lg p-6 flex items-center gap-6 border border-m3-outline-variant/5">
              <div className="w-16 h-16 rounded-xl bg-m3-primary/10 flex items-center justify-center flex-shrink-0">
                <Sprout className="w-8 h-8 text-m3-primary" />
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-m3-on-surface uppercase tracking-wider">
                  Protocol Overview
                </h4>
                <div className="flex flex-wrap gap-4 text-[11px] font-mono text-m3-primary">
                  <span className="flex items-center gap-1">
                    <Droplets className="w-3.5 h-3.5" /> AUTO_PH_SYNC
                  </span>
                  <span className="flex items-center gap-1">
                    <Leaf className="w-3.5 h-3.5" /> OPTIMAL_H2O
                  </span>
                </div>
                <p className="text-[11px] text-m3-on-surface-variant leading-relaxed">
                  System will automatically calibrate irrigation cycles based on the selected variety and land area parameters.
                </p>
              </div>
            </div>
          )}

          {/* Form Actions */}
          {error && (
            <div className="rounded-lg border border-red-500/20 bg-red-500/10 text-red-100 px-4 py-3 text-sm">
              {error}
            </div>
          )}
          <div className="flex items-center justify-between pt-6">
            <button
              onClick={() => step === 1 ? router.push('/crops') : setStep((step - 1) as StepId)}
              className="px-6 py-3 rounded-lg text-m3-on-surface-variant hover:text-m3-on-surface transition-colors flex items-center gap-2 group"
              type="button"
            >
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
              <span className="text-sm font-bold uppercase tracking-widest">
                {step === 1 ? 'Cancel' : 'Back'}
              </span>
            </button>

            <button
              onClick={() => step === 3 ? handleSubmit() : setStep((step + 1) as StepId)}
              disabled={!canAdvance() || submitting}
              className={clsx(
                'px-8 py-3 rounded-lg font-bold uppercase tracking-widest text-sm flex items-center gap-2 transition-all',
                'bg-gradient-to-br from-m3-primary to-m3-primary-container text-m3-on-primary',
                'shadow-lg shadow-m3-primary/20 hover:scale-[1.02] active:scale-95',
                'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100'
              )}
            >
              {step === 3 ? (submitting ? 'Creating…' : 'Create Crop') : 'Next Sequence'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
      </div>
    </ProtectedRoute>
  );
}
