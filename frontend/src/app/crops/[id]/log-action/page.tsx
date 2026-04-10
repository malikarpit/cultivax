'use client';

/**
 * Log Action Form — Record agricultural entry for a crop
 * 
 * Reference: stitch_landing_page 3/log_action_form
 * Features: Crop header card, action type/date, observation notes,
 * visual evidence upload zone, and bottom stat cards
 */

import { useState, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowRight, ArrowLeft, Upload, Camera, Calendar,
  Droplets, FlaskConical, Sprout, ChevronDown,
  Thermometer, Clock, Leaf, WifiOff, CheckCircle2
} from 'lucide-react';
import clsx from 'clsx';
import ProtectedRoute from '@/components/ProtectedRoute';
import { apiPost } from '@/lib/api';
import { mutate } from 'swr';
import { useOfflineActions } from '@/hooks/useOfflineActions';
import { OfflineActionsList } from '@/components/OfflineActionsList';
import { OfflineSyncStatus } from '@/components/OfflineSyncStatus';
import React from 'react';
import { useTranslation } from 'react-i18next';

const ACTION_TYPES = [
  { value: 'irrigation', label: 'Irrigation' },
  { value: 'fertilizer', label: 'Fertilizer Application' },
  { value: 'pesticide', label: 'Pesticide Spray' },
  { value: 'weeding', label: 'Weeding' },
  { value: 'pruning', label: 'Pruning' },
  { value: 'soil_testing', label: 'Soil Testing' },
  { value: 'harvest', label: 'Harvest' },
  { value: 'seed_treatment', label: 'Seed Treatment' },
  { value: 'observation', label: 'Observation' },
  { value: 'other', label: 'Other' },
];

export default function LogActionPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const params = useParams();
  const cropId = params.id;
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [actionType, setActionType] = useState('irrigation');
  const [executionDate, setExecutionDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [notes, setNotes] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(typeof window !== 'undefined' ? navigator.onLine : true);

  const [dateError, setDateError] = useState<string | null>(null);
  const { queueAction } = useOfflineActions({ cropId: cropId as string, autoSync: true });

  React.useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files) {
      setFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleSubmit = async () => {
    if (isSubmitting) return;
    setError(null);
    setDateError(null);

    if (!executionDate) {
      setError('Execution date is required.');
      return;
    }

    setIsSubmitting(true);
    
    try {
      if (isOnline) {
        await apiPost(`/api/v1/crops/${cropId}/actions`, {
          action_type: actionType,
          effective_date: executionDate,
          category: 'Maintenance',
          metadata_json: {
            notes: notes || null,
            attachment_count: files.length,
          },
          notes: notes,
          idempotency_key: typeof crypto !== 'undefined' && crypto.randomUUID 
            ? crypto.randomUUID() 
            : `${cropId}${Date.now()}`.replace(/[^0-9a-f]/gi, '').padEnd(32, '0').slice(0, 64)
        });
        // Invalidate SWR cache so crop detail page updates instantly
        mutate(`/api/v1/crops/${cropId}/actions`);
        router.push(`/crops/${cropId}?tab=Actions`);
      } else {
        await queueAction(
          cropId as string,
          actionType,
          executionDate,
          {
            notes: notes || null,
            attachment_count: files.length,
            category: 'Maintenance'
          }
        );
        // Clear form after queuing
        setNotes('');
        setFiles([]);
        setActionType('irrigation');
        setExecutionDate(new Date().toISOString().split('T')[0]);
        // Leave user on page to see queued action
        setIsSubmitting(false);
      }
    } catch (err: any) {
      console.error('Failed to log action:', err);
      // Catch specific 422 Chronology checks if formatted natively
      if (err.message && err.message.includes("Chronology") || err.message?.includes("before")) {
         setDateError(err.message);
      } else {
         setError(err.message || 'Failed to log action');
      }
      setIsSubmitting(false);
    }
  };

  return (
    <ProtectedRoute requiredRole={["farmer", "admin"]}>
    <div className="animate-fade-in space-y-8 max-w-3xl mx-auto">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm font-mono">
        <Link href="/crops" className="text-m3-on-surface-variant hover:text-m3-primary transition-colors">{t('crops.[id].log-action.crops')}</Link>
        <span className="text-m3-outline">›</span>
        <Link href={`/crops/${cropId}`} className="text-m3-on-surface-variant hover:text-m3-primary transition-colors">
          Crop #{String(cropId).slice(0, 8)}
        </Link>
        <span className="text-m3-outline">›</span>
        <span className="text-m3-primary">{t('crops.[id].log-action.log_action')}</span>
      </nav>

      {/* Online/Offline Indicator */}
      {!isOnline && (
        <div className="glass-card mb-4 border border-m3-warning/20 bg-gradient-to-r from-m3-warning/10 to-transparent p-4 flex items-start gap-4 rounded-xl">
          <div className="w-10 h-10 rounded-full bg-m3-warning/20 flex flex-shrink-0 items-center justify-center text-m3-warning">
            <WifiOff className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-m3-on-surface">{t('crops.[id].log-action.you_are_offline')}</h3>
            <p className="text-sm text-m3-on-surface-variant mt-1">{t('crops.[id].log-action.your_actions_are_being')}</p>
          </div>
        </div>
      )}

      {/* Offline Sync Status */}
      <OfflineSyncStatus cropId={cropId as string} />

      {/* Crop Header Card */}
      <div className="glass-card rounded-xl p-6 flex items-center gap-6 border border-m3-outline-variant/10">
        <div className="w-16 h-16 rounded-xl bg-m3-primary/10 overflow-hidden flex items-center justify-center flex-shrink-0">
          <Sprout className="w-8 h-8 text-m3-primary" />
        </div>
        <div className="flex-1">
          <h2 className="text-xl font-bold text-m3-on-surface">{t('crops.[id].log-action.active_crop')}</h2>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-[11px] font-mono text-m3-primary uppercase tracking-wider">
              ID-{String(cropId).slice(0, 8)}
            </span>
          </div>
          <div className="flex items-center gap-4 mt-1 text-[11px] text-m3-on-surface-variant">
            <span className="flex items-center gap-1">
              <Thermometer className="w-3 h-3 text-m3-error" />{t('crops.[id].log-action.24_5_c')}</span>
            <span className="flex items-center gap-1">
              <Droplets className="w-3 h-3 text-m3-tertiary" /> 68%
            </span>
          </div>
        </div>
        <div className="text-right">
          <p className="mono-label">{t('crops.[id].log-action.current_health')}</p>
          <p className="text-3xl font-black text-m3-primary font-mono tracking-tighter">94%</p>
        </div>
      </div>

      {/* Form Card */}
      <div className="glass-card rounded-xl p-8 border border-m3-outline-variant/10 space-y-8">
        <div>
          <h3 className="text-xl font-bold text-m3-on-surface mb-1">{t('crops.[id].log-action.new_agricultural_entry')}</h3>
          <p className="text-sm text-m3-on-surface-variant">{t('crops.[id].log-action.record_precise_details_for')}</p>
        </div>

        {/* Action Type + Date */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">{t('crops.[id].log-action.action_type')}</label>
            <div className="relative">
              <select
                value={actionType}
                onChange={(e) => setActionType(e.target.value)}
                className="w-full bg-m3-surface-container-highest border-none rounded-lg px-4 py-3 text-m3-on-surface focus:ring-1 focus:ring-m3-primary/40 appearance-none transition-all"
                title="Select Action Type"
                aria-label="Select Action Type"
              >
                {ACTION_TYPES.map((a) => (
                  <option key={a.value} value={a.value}>{a.label}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-m3-on-surface-variant pointer-events-none" />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">{t('crops.[id].log-action.execution_date')}</label>
            <div className="relative">
              <input
                type="date"
                value={executionDate}
                onChange={(e) => setExecutionDate(e.target.value)}
                className="w-full bg-m3-surface-container-highest border-none rounded-lg px-4 py-3 text-m3-on-surface focus:ring-1 focus:ring-m3-primary/40 transition-all [color-scheme:dark]"
                title="Execution Date"
                aria-label="Execution Date"
              />
              <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-m3-on-surface-variant pointer-events-none" />
            </div>
            {dateError && <p className="text-xs text-red-400 mt-1">{dateError}</p>}
          </div>
        </div>

        {/* Observation Notes */}
        <div className="space-y-2">
          <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">{t('crops.[id].log-action.observation_notes')}</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder={t('crops.[id].log-action.describe_environmental_conditions_specific')}
            rows={5}
            className="w-full bg-m3-surface-container-highest border-none rounded-lg px-4 py-3 text-m3-on-surface focus:ring-1 focus:ring-m3-primary/40 placeholder:text-m3-on-surface-variant/30 transition-all resize-none"
          />
        </div>

        {/* Visual Evidence Upload */}
        <div className="space-y-2">
          <label className="text-[11px] font-bold uppercase tracking-widest text-m3-on-surface-variant block ml-1">{t('crops.[id].log-action.visual_evidence')}</label>
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={clsx(
              'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all',
              isDragOver
                ? 'border-m3-primary bg-m3-primary/5'
                : 'border-m3-outline-variant/20 hover:border-m3-primary/40 hover:bg-m3-surface-container-high/30'
            )}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileChange}
              className="hidden"
              title="Upload Visual Evidence"
              aria-label="Upload Visual Evidence"
            />
            <Camera className="w-8 h-8 text-m3-primary mx-auto mb-3" />
            <p className="text-sm text-m3-on-surface-variant">{t('crops.[id].log-action.click_to_upload_photos')}</p>
            <p className="text-[10px] text-m3-on-surface-variant/50 mt-1 font-mono uppercase">{t('crops.[id].log-action.png_jpg_or_raw')}</p>
            {files.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2 justify-center">
                {files.map((f, i) => (
                  <span key={i} className="stat-tag bg-m3-primary/10 text-m3-primary">
                    {f.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Submit Actions */}
        <div className="flex items-center gap-4 pt-4">
          <button
            onClick={handleSubmit}
            className={clsx(
              "flex-1 py-3.5 rounded-xl font-bold text-sm shadow-lg hover:scale-[1.01] active:scale-95 transition-all flex items-center justify-center gap-2",
              isOnline 
                ? "bg-gradient-to-br from-m3-primary to-m3-primary-container text-m3-on-primary shadow-m3-primary/20"
                : "bg-m3-warning text-m3-on-warning shadow-m3-warning/20"
            )}
          >
            {isOnline ? (
              <>Log Action <ArrowRight className="w-4 h-4" /></>
            ) : (
              <>Queue for Sync <CheckCircle2 className="w-4 h-4" /></>
            )}
          </button>
          <button
            onClick={() => router.push(`/crops/${cropId}`)}
            className="px-8 py-3.5 rounded-xl bg-m3-surface-container-highest text-m3-on-surface-variant font-bold text-sm hover:bg-m3-surface-container-high transition-colors"
          >{t('crops.[id].log-action.cancel')}</button>
        </div>
        {error ? <p className="text-sm text-red-400">{error}</p> : null}
      </div>

      {/* Queued Actions List */}
      <OfflineActionsList cropId={cropId as string} />

      {/* Bottom Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card rounded-xl p-5 border border-m3-outline-variant/10">
          <p className="mono-label mb-1">{t('crops.[id].log-action.last_irrigation')}</p>
          <p className="text-xl font-bold text-m3-on-surface font-mono tracking-tight">
            14h <span className="text-sm font-normal text-m3-on-surface-variant">{t('crops.[id].log-action.ago')}</span>
          </p>
        </div>
        <div className="glass-card rounded-xl p-5 border border-m3-outline-variant/10">
          <p className="mono-label mb-1">{t('crops.[id].log-action.ph_level')}</p>
          <p className="text-xl font-bold text-m3-on-surface font-mono tracking-tight">
            6.4 <span className="text-sm font-normal text-m3-primary">{t('crops.[id].log-action.opt')}</span>
          </p>
        </div>
        <div className="glass-card rounded-xl p-5 border border-m3-outline-variant/10">
          <p className="mono-label mb-1">{t('crops.[id].log-action.growth_cycle')}</p>
          <p className="text-xl font-bold text-m3-on-surface font-mono tracking-tight">
            Day <span className="text-m3-primary">42</span>
          </p>
        </div>
      </div>
    </div>
    </ProtectedRoute>
  );
}
