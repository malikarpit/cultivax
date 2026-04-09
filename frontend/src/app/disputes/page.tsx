'use client';

/**
 * Dispute Resolution Page — FR-33
 *
 * Farmer view: open a dispute, list own disputes with status badges.
 * Shows SLA countdown for open/investigating disputes.
 */

import { useState } from 'react';
import {
  AlertTriangle, Plus, Clock, CheckCircle2,
  XCircle, Loader2, ChevronDown, ChevronUp, Shield,
} from 'lucide-react';
import clsx from 'clsx';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useFetch } from '@/hooks/useFetch';
import { useTranslation } from 'react-i18next';

interface Dispute {
  id: string;
  category: string;
  status: 'open' | 'investigating' | 'resolved' | 'dismissed';
  description?: string;
  sla_deadline?: string;
  resolution_notes?: string;
  created_at: string;
  overdue?: boolean;
}

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  open:          { label: 'Open',          color: 'text-amber-400 bg-amber-900/30 border-amber-700',    icon: <Clock className="w-3 h-3" /> },
  investigating: { label: 'Investigating', color: 'text-blue-400 bg-blue-900/30 border-blue-700',       icon: <Shield className="w-3 h-3" /> },
  resolved:      { label: 'Resolved',      color: 'text-emerald-400 bg-emerald-900/30 border-emerald-700', icon: <CheckCircle2 className="w-3 h-3" /> },
  dismissed:     { label: 'Dismissed',     color: 'text-zinc-400 bg-zinc-800 border-zinc-600',           icon: <XCircle className="w-3 h-3" /> },
};

const CATEGORIES = ['quality', 'fraud', 'non_delivery', 'payment', 'other'];

function SLACountdown({ deadline }: { deadline: string }) {
  const diff = new Date(deadline).getTime() - Date.now();
  if (diff <= 0) return <span className="text-rose-400 text-xs font-semibold">⚠ SLA Overdue</span>;
  const hours = Math.floor(diff / 3_600_000);
  const days  = Math.floor(hours / 24);
  return (
    <span className="text-xs text-zinc-400">
      SLA: {days > 0 ? `${days}d ${hours % 24}h` : `${hours}h`} remaining
    </span>
  );
}

function DisputeCard({ dispute }: { dispute: Dispute }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = STATUS_CONFIG[dispute.status] ?? STATUS_CONFIG.open;

  return (
    <div className={clsx(
      'bg-zinc-900 border rounded-2xl p-4 transition-all',
      dispute.overdue ? 'border-rose-700/60' : 'border-zinc-800 hover:border-zinc-700',
    )}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={clsx('flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border', cfg.color)}>
              {cfg.icon}{cfg.label}
            </span>
            <span className="text-xs text-zinc-500 capitalize">{dispute.category.replace('_', ' ')}</span>
            {dispute.overdue && <span className="text-xs text-rose-400 font-semibold">{t('disputes.overdue')}</span>}
          </div>
          {dispute.description && (
            <p className={clsx('text-sm text-zinc-300 mt-2', !expanded && 'line-clamp-1')}>{dispute.description}</p>
          )}
          {dispute.sla_deadline && ['open', 'investigating'].includes(dispute.status) && (
            <div className="mt-1.5"><SLACountdown deadline={dispute.sla_deadline} /></div>
          )}
          {dispute.resolution_notes && expanded && (
            <div className="mt-2 p-3 bg-emerald-900/20 border border-emerald-800/40 rounded-xl">
              <p className="text-xs text-emerald-300 font-semibold mb-1">{t('disputes.resolution')}</p>
              <p className="text-xs text-zinc-300">{dispute.resolution_notes}</p>
            </div>
          )}
        </div>
        <button onClick={() => setExpanded(!expanded)} className="p-1.5 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors flex-shrink-0">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>
      <p className="text-xs text-zinc-600 mt-2">{new Date(dispute.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
    </div>
  );
}

function OpenDisputeForm({ onSuccess }: { onSuccess: () => void }) {
  const [category, setCategory] = useState('quality');
  const [description, setDescription] = useState('');
  const [respondentId, setRespondentId] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!respondentId.trim()) { setError('Provider ID is required'); return; }
    setSubmitting(true); setError('');
    try {
      const token = localStorage.getItem('access_token');
      const resp = await fetch('/api/v1/disputes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ respondent_id: respondentId, category, description }),
      });
      if (!resp.ok) throw new Error((await resp.json()).error ?? 'Failed');
      onSuccess();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-4">
      <h3 className="font-semibold text-white text-sm">{t('disputes.open_new_dispute')}</h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-zinc-400 mb-1">{t('disputes.provider_respondent_id')}</label>
          <input
            value={respondentId}
            onChange={(e) => setRespondentId(e.target.value)}
            placeholder={t('disputes.uuid_of_the_provider')}
            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-600"
          />
        </div>
        <div>
          <label className="block text-xs text-zinc-400 mb-1">{t('disputes.category')}</label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-600"
          >
            {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-xs text-zinc-400 mb-1">{t('disputes.description')}</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          placeholder={t('disputes.describe_the_issue')}
          className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-600 resize-none"
        />
      </div>

      {error && <p className="text-xs text-rose-400">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-sm font-semibold transition-colors disabled:opacity-60"
      >
        {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
        {submitting ? 'Submitting…' : 'Submit Dispute'}
      </button>
    </form>
  );
}

export default function DisputesPage() {
  const { t } = useTranslation();
  const [showForm, setShowForm] = useState(false);
  const { data, loading, refetch } = useFetch<{ items: Dispute[]; total: number }>('/api/v1/disputes');

  const disputes = data?.items ?? [];

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-zinc-950 text-white">
        {/* Header */}
        <div className="border-b border-zinc-800 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-900/40 border border-amber-700/40 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            </div>
            <div>
              <h1 className="font-bold text-white text-lg leading-none">{t('disputes.disputes')}</h1>
              <p className="text-xs text-zinc-500 mt-0.5">{t('disputes.track_and_manage_your')}</p>
            </div>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-amber-700 hover:bg-amber-600 text-white text-xs font-semibold transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />{t('disputes.new_dispute')}</button>
        </div>

        <div className="max-w-2xl mx-auto px-6 py-6 space-y-4">
          {showForm && <OpenDisputeForm onSuccess={() => { setShowForm(false); refetch(); }} />}

          {loading && (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-2xl h-24 animate-pulse" />
              ))}
            </div>
          )}

          {!loading && disputes.length === 0 && !showForm && (
            <div className="text-center py-16">
              <CheckCircle2 className="w-10 h-10 text-zinc-700 mx-auto mb-3" />
              <p className="text-zinc-500 text-sm">{t('disputes.no_disputes_filed_everything')}</p>
              <button onClick={() => setShowForm(true)} className="mt-4 text-xs text-amber-400 hover:underline">{t('disputes.file_a_dispute')}</button>
            </div>
          )}

          {!loading && disputes.map((d) => <DisputeCard key={d.id} dispute={d} />)}
        </div>
      </div>
    </ProtectedRoute>
  );
}
