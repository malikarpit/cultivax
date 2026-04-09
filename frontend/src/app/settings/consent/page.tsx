'use client';

/**
 * Consent Settings Page — NFR-13
 *
 * Allows users to view and manage their data-processing consent per purpose.
 * Each toggle fires a PATCH to the backend consent API.
 * Linked from /settings and footer privacy links.
 */

import { useState, useEffect } from 'react';
import {
  Shield, ToggleLeft, ToggleRight, ChevronLeft,
  Lock, BarChart3, Brain, MessageSquare, Users, FlaskConical,
  CheckCircle2, AlertCircle,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useFetch } from '@/hooks/useFetch';
import clsx from 'clsx';
import { useTranslation } from 'react-i18next';

interface ConsentItem {
  purpose: string;
  granted: boolean;
  granted_at: string | null;
  revoked_at: string | null;
}

const PURPOSE_META: Record<string, { label: string; description: string; icon: React.ReactNode; risk: 'low' | 'medium' | 'high' }> = {
  analytics:   { label: 'Platform Analytics', description: 'Helps us improve app performance and reliability using aggregated usage data. No personal data leaves CultivaX.', icon: <BarChart3 className="w-4 h-4" />, risk: 'low' },
  ml_training: { label: 'ML Model Training', description: 'Your anonymised crop data may improve AI risk predictions for all farmers. Data is scrubbed of all identifiers before use.', icon: <Brain className="w-4 h-4" />, risk: 'medium' },
  sms_alerts:  { label: 'SMS Notifications', description: 'Receive critical crop alerts and weather warnings via SMS when you are offline.', icon: <MessageSquare className="w-4 h-4" />, risk: 'low' },
  third_party: { label: 'Partner Sharing', description: 'Share anonymised agricultural patterns with certified partner organisations (NGOs, seed companies). Never sold.', icon: <Users className="w-4 h-4" />, risk: 'high' },
  research:    { label: 'Research Use', description: 'Allow government agencies or academic institutions to use anonymised data for agricultural research.', icon: <FlaskConical className="w-4 h-4" />, risk: 'medium' },
};

const RISK_BADGE: Record<string, string> = {
  low:    'text-emerald-400 bg-emerald-900/30 border-emerald-700',
  medium: 'text-amber-400 bg-amber-900/30 border-amber-700',
  high:   'text-rose-400 bg-rose-900/30 border-rose-700',
};

function ConsentToggle({ item, onToggle }: { item: ConsentItem; onToggle: (p: string, grant: boolean) => void }) {
  const meta = PURPOSE_META[item.purpose];
  if (!meta) return null;

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 flex items-start gap-4 hover:border-zinc-700 transition-all">
      <div className="w-9 h-9 rounded-xl bg-zinc-800 flex items-center justify-center text-zinc-400 flex-shrink-0">
        {meta.icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-white text-sm">{meta.label}</span>
          <span className={clsx('text-[10px] font-semibold px-1.5 py-0.5 rounded border capitalize', RISK_BADGE[meta.risk])}>
            {meta.risk} risk
          </span>
        </div>
        <p className="text-xs text-zinc-400 mt-1 leading-relaxed">{meta.description}</p>
        {item.granted && item.granted_at && (
          <p className="text-[10px] text-zinc-600 mt-1">Granted {new Date(item.granted_at).toLocaleDateString()}</p>
        )}
        {!item.granted && item.revoked_at && (
          <p className="text-[10px] text-zinc-600 mt-1">Revoked {new Date(item.revoked_at).toLocaleDateString()}</p>
        )}
      </div>
      <button
        onClick={() => onToggle(item.purpose, !item.granted)}
        className="flex-shrink-0 transition-colors"
        aria-label={item.granted ? 'Revoke consent' : 'Grant consent'}
      >
        {item.granted
          ? <ToggleRight className="w-8 h-8 text-emerald-400 hover:text-emerald-300" />
          : <ToggleLeft className="w-8 h-8 text-zinc-600 hover:text-zinc-400" />}
      </button>
    </div>
  );
}

export default function ConsentPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { data, loading, refetch } = useFetch<{ consents: ConsentItem[] }>('/api/v1/consent/me');
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);

  async function handleToggle(purpose: string, grant: boolean) {
    const token = localStorage.getItem('access_token');
    const method = grant ? 'POST' : 'DELETE';
    try {
      const resp = await fetch(`/api/v1/consent/me/${purpose}`, {
        method,
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error();
      setToast({ msg: `${grant ? 'Granted' : 'Revoked'} consent for ${PURPOSE_META[purpose]?.label ?? purpose}`, ok: true });
      refetch();
    } catch {
      setToast({ msg: 'Failed to update consent. Please try again.', ok: false });
    }
    setTimeout(() => setToast(null), 3000);
  }

  const consents = data?.consents ?? [];

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-zinc-950 text-white">
        {/* Header */}
        <div className="border-b border-zinc-800 px-6 py-4 flex items-center gap-3">
          <button onClick={() => router.back()} className="p-1.5 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-emerald-400" />
            <div>
              <h1 className="font-bold text-white text-base leading-none">{t('settings.consent.data_privacy_amp_consent')}</h1>
              <p className="text-xs text-zinc-500 mt-0.5">{t('settings.consent.control_how_your_data')}</p>
            </div>
          </div>
        </div>

        <div className="max-w-xl mx-auto px-6 py-6 space-y-4">
          {/* Info banner */}
          <div className="bg-blue-900/20 border border-blue-800/40 rounded-2xl p-4 flex gap-3">
            <Lock className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-blue-300 leading-relaxed">{t('settings.consent.your_privacy_matters_you')}</p>
          </div>

          {loading && Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-2xl h-20 animate-pulse" />
          ))}

          {!loading && consents.map((item) => (
            <ConsentToggle key={item.purpose} item={item} onToggle={handleToggle} />
          ))}

          <p className="text-xs text-zinc-600 text-center pt-2">{t('settings.consent.cultivax_processes_data_under')}</p>
        </div>

        {/* Toast */}
        {toast && (
          <div className={clsx(
            'fixed bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium shadow-xl transition-all',
            toast.ok ? 'bg-emerald-800 text-white' : 'bg-rose-800 text-white',
          )}>
            {toast.ok ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
            {toast.msg}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
