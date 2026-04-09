'use client';

/**
 * Service Request Form — Book agricultural services
 * 
 * Reference: stitch_landing_page 3/service_request_form
 * Layout: 2-column (form left, summary right)
 * Features: Provider card, service type, crop selector, 
 * request summary with pricing, yield lift projection
 */

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowRight, Star, MapPin, Calendar, Zap,
  ChevronDown, Sprout, HelpCircle, Info,
  CheckCircle, Leaf,
} from 'lucide-react';
import clsx from 'clsx';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useApi } from '@/hooks/useApi';
import { useTranslation } from 'react-i18next';

/* ─── Mock Data ──────────────────────────────────────────── */

const SERVICES = [
  'Automated Nutrient Infusion',
  'Drone Crop Survey',
  'Soil Analysis & Report',
  'Pest Management Spray',
  'Irrigation System Setup',
  'Harvest Labor Assistance',
];

const CROPS = [
  { id: '1', name: 'Wheat HD-2967', code: 'GH-S7-01', icon: '🌾', selected: true },
  { id: '2', name: 'Basmati Rice', code: 'GH-S7-04', icon: '🌿', selected: false },
  { id: '3', name: 'Pima Cotton', code: 'GH-S7-09', icon: '🌱', selected: false },
];

export default function ServiceRequestPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const searchParams = useSearchParams();
  const providerId = searchParams.get('provider') || '00000000-0000-0000-0000-000000000000';
  const api = useApi();

  const [serviceType, setServiceType] = useState(SERVICES[0]);
  const [preferredDate, setPreferredDate] = useState('');
  const [selectedCrops, setSelectedCrops] = useState<string[]>(['1']);
  const [notes, setNotes] = useState('');

  const toggleCrop = (id: string) => {
    setSelectedCrops(prev =>
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    );
  };

  const baseFee = 125;
  const droneCalibration = 45;
  const priorityDispatch = 15;
  const total = baseFee + droneCalibration + priorityDispatch;

  const handleSubmit = async () => {
    try {
      await api.execute('/api/v1/service-requests', {
        method: 'POST',
        body: {
          provider_id: providerId,
          service_type: serviceType,
          description: notes,
          preferred_date: preferredDate ? new Date(preferredDate).toISOString() : undefined,
          agreed_price: total
        }
      });
      router.push('/services');
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <ProtectedRoute requiredRole="farmer">
    <div className="animate-fade-in space-y-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-[11px] font-mono text-m3-on-surface-variant">
        <Link href="/services" className="hover:text-m3-primary transition-colors">{t('services.request.marketplace')}</Link>
        <span>›</span>
        <span className="text-m3-primary">{t('services.request.request_service')}</span>
      </nav>

      {/* Page Title */}
      <div>
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tighter text-m3-on-surface">{t('services.request.request_service')}</h1>
        <p className="text-m3-on-surface-variant mt-2 max-w-xl">{t('services.request.customize_your_technical_request')}</p>
      </div>

      {/* ═══ Main Grid ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Form */}
        <div className="lg:col-span-8 space-y-8">
          {/* Provider Card */}
          <div className="glass-card rounded-2xl p-6 border border-m3-outline-variant/10 flex flex-col sm:flex-row items-start sm:items-center gap-6">
            <div className="w-16 h-16 rounded-full bg-m3-surface-container-highest flex items-center justify-center flex-shrink-0 overflow-hidden">
              <Sprout className="w-8 h-8 text-m3-primary" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-m3-on-surface">{t('services.request.dr_aris_thorne')}</h3>
              <div className="flex items-center gap-3 mt-1">
                <span className="flex items-center gap-1 text-sm">
                  <Star className="w-4 h-4 fill-m3-secondary text-m3-secondary" />
                  <span className="font-bold">4.9</span>
                  <span className="text-m3-on-surface-variant text-xs">(128 reviews)</span>
                </span>
                <span className="flex items-center gap-1 text-xs text-m3-on-surface-variant">
                  <MapPin className="w-3 h-3" />{t('services.request.northern_region')}</span>
              </div>
            </div>
            <div className="flex gap-2">
              <span className="stat-tag bg-m3-primary/10 text-m3-primary border border-m3-primary/20 px-3 py-1.5">{t('services.request.precision_drone')}</span>
              <span className="stat-tag bg-m3-secondary/10 text-m3-secondary border border-m3-secondary/20 px-3 py-1.5">{t('services.request.soil_analytics')}</span>
            </div>
          </div>

          {/* Service Type + Date */}
          <div className="glass-card rounded-2xl p-8 border border-m3-outline-variant/10 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">{t('services.request.service_type')}</label>
                <div className="relative">
                  <select
                    value={serviceType}
                    onChange={(e) => setServiceType(e.target.value)}
                    className="w-full bg-m3-surface-container-highest border-none rounded-lg px-4 py-3.5 text-m3-on-surface focus:ring-1 focus:ring-m3-primary/40 appearance-none transition-all"
                  >
                    {SERVICES.map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-m3-on-surface-variant pointer-events-none" />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">{t('services.request.preferred_date')}</label>
                <div className="relative">
                  <input
                    type="date"
                    value={preferredDate}
                    onChange={(e) => setPreferredDate(e.target.value)}
                    className="w-full bg-m3-surface-container-highest border-none rounded-lg px-4 py-3.5 text-m3-on-surface focus:ring-1 focus:ring-m3-primary/40 transition-all [color-scheme:dark]"
                  />
                  <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-m3-on-surface-variant pointer-events-none" />
                </div>
              </div>
            </div>

            {/* Target Crop Selection */}
            <div className="space-y-3">
              <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">{t('services.request.target_crop_environment')}</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {CROPS.map(crop => (
                  <button
                    key={crop.id}
                    onClick={() => toggleCrop(crop.id)}
                    className={clsx(
                      'p-4 rounded-xl border transition-all text-left flex items-center gap-3',
                      selectedCrops.includes(crop.id)
                        ? 'bg-m3-primary/10 border-m3-primary/30 text-m3-primary'
                        : 'bg-m3-surface-container-high border-m3-outline-variant/10 text-m3-on-surface-variant hover:border-m3-outline/30'
                    )}
                  >
                    <span className="text-2xl">{crop.icon}</span>
                    <div>
                      <p className="text-sm font-bold">{crop.name}</p>
                      <p className="text-[10px] font-mono opacity-70">{crop.code}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Notes */}
            <div className="space-y-2">
              <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">{t('services.request.logistical_specifications')}</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder={t('services.request.include_any_specific_sensor')}
                rows={4}
                className="w-full bg-m3-surface-container-highest border-none rounded-lg px-4 py-3 text-m3-on-surface focus:ring-1 focus:ring-m3-primary/40 placeholder:text-m3-on-surface-variant/30 transition-all resize-none"
              />
            </div>
          </div>

          {/* Info Banner */}
          <div className="glass-card rounded-xl p-4 border border-m3-outline-variant/10 flex items-start gap-3">
            <Info className="w-5 h-5 text-m3-tertiary flex-shrink-0 mt-0.5" />
            <p className="text-sm text-m3-on-surface-variant">{t('services.request.requests_are_subject_to')}</p>
          </div>
        </div>

        {/* Right: Summary Sidebar */}
        <div className="lg:col-span-4 space-y-6">
          {/* Request Summary */}
          <div className="glass-card rounded-2xl p-6 border border-m3-outline-variant/10 space-y-5 sticky top-24">
            <h4 className="text-sm font-bold uppercase tracking-widest text-m3-on-surface-variant">{t('services.request.request_summary')}</h4>

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-m3-on-surface-variant">{t('services.request.base_service_fee')}</span>
                <span className="text-sm font-bold font-mono text-m3-on-surface">
                  {baseFee.toFixed(2)} <span className="text-m3-primary text-[10px]">{t('services.request.inr')}</span>
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-m3-on-surface-variant">{t('services.request.drone_calibration')}</span>
                <span className="text-sm font-bold font-mono text-m3-on-surface">
                  {droneCalibration.toFixed(2)} <span className="text-m3-primary text-[10px]">{t('services.request.inr')}</span>
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-m3-on-surface-variant">{t('services.request.priority_dispatch')}</span>
                <span className="text-sm font-bold font-mono text-m3-primary">
                  +{priorityDispatch.toFixed(2)} <span className="text-[10px]">{t('services.request.inr')}</span>
                </span>
              </div>
            </div>

            <div className="border-t border-m3-outline-variant/10 pt-4">
              <p className="mono-label mb-1">{t('services.request.total_impact')}</p>
              <p className="text-4xl font-black font-mono tracking-tighter text-m3-on-surface">
                {total.toFixed(2)}{' '}
                <span className="text-sm font-normal text-m3-primary">{t('services.request.inr')}</span>
              </p>
            </div>

            <button
              onClick={handleSubmit}
              disabled={api.loading}
              className="w-full bg-gradient-to-br from-m3-primary to-m3-primary-container text-m3-on-primary py-3.5 rounded-xl font-bold text-sm shadow-lg shadow-m3-primary/20 hover:scale-[1.01] active:scale-95 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Zap className="w-4 h-4" /> {api.loading ? 'Submitting...' : 'Submit Request'}
            </button>
            {api.error && <p className="text-red-400 text-xs mt-2">{api.error}</p>}

            <p className="text-[10px] text-m3-on-surface-variant text-center leading-relaxed">{t('services.request.by_submitting_you_agree')}</p>
          </div>

          {/* Estimated Yield Lift */}
          <div className="glass-card rounded-2xl p-6 border border-m3-outline-variant/10">
            <div className="flex items-center justify-between mb-4">
              <p className="mono-label font-bold">{t('services.request.estimated_yield_lift')}</p>
              <span className="stat-tag bg-m3-primary/10 text-m3-primary">+12.4%</span>
            </div>
            <div>
              <span className="stat-tag bg-m3-secondary/10 text-m3-secondary mb-2 inline-block">{t('services.request.projected_growth')}</span>
              <div className="w-full bg-m3-surface-container-highest h-2 rounded-full overflow-hidden mt-2">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-m3-secondary to-m3-primary transition-all duration-700"
                  style={{ width: '68%' }}
                />
              </div>
              <div className="flex justify-between mt-2">
                <span className="text-[10px] text-m3-on-surface-variant font-mono">{t('services.request.current_68')}</span>
                <span className="text-[10px] text-m3-on-surface-variant font-mono">{t('services.request.target_92')}</span>
              </div>
            </div>
          </div>

          {/* Help Card */}
          <div className="glass-card rounded-2xl p-6 border border-m3-outline-variant/10 flex items-center gap-4">
            <HelpCircle className="w-8 h-8 text-m3-on-surface-variant flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-m3-on-surface">{t('services.request.need_help_deciding')}</p>
              <p className="text-xs text-m3-on-surface-variant">{t('services.request.chat_with_an_ai')}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    </ProtectedRoute>
  );
}
