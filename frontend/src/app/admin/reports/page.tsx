'use client';

/**
 * Admin Reports Queue — OR-14
 *
 * Admins review user reports of platform abuse/fraud.
 */

import { useState } from 'react';
import { ShieldAlert, CheckCircle2, MessageSquare, Clock, Filter, AlertCircle, XCircle } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useFetch } from '@/hooks/useFetch';
import clsx from 'clsx';
import { useTranslation } from 'react-i18next';

export default function AdminReportsPage() {
  const { t } = useTranslation();
  const [filter, setFilter] = useState('');
  const { data, loading, refetch } = useFetch<any>(`/api/v1/admin/reports${filter ? '?status=' + filter : ''}`);

  const reports = data?.items || [];

  async function handleAction(id: string, action: 'review' | 'action' | 'dismiss', notes: string) {
    const token = localStorage.getItem('access_token');
    const body = action === 'dismiss' ? { reason: notes } : { review_notes: notes };
    await fetch(`/api/v1/admin/reports/${id}/${action}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify(body)
    });
    refetch();
  }

  return (
    <ProtectedRoute requiredRole={["admin"]}>
      <div className="min-h-screen bg-zinc-950 text-white p-6 sm:p-8">
        
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-rose-900/40 border border-rose-700/40 flex items-center justify-center">
              <ShieldAlert className="w-5 h-5 text-rose-400" />
            </div>
            <div>
              <h1 className="font-bold text-white text-xl">{t('admin.reports.user_reports')}</h1>
              <p className="text-xs text-zinc-500">{t('admin.reports.review_reported_fraud_abuse')}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-zinc-500" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-zinc-600"
            >
              <option value="">{t('admin.reports.all_statuses')}</option>
              <option value="open">{t('admin.reports.open')}</option>
              <option value="reviewed">{t('admin.reports.reviewed')}</option>
              <option value="actioned">{t('admin.reports.actioned')}</option>
              <option value="dismissed">{t('admin.reports.dismissed')}</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-2xl h-24 animate-pulse" />)}
          </div>
        ) : reports.length === 0 ? (
          <div className="text-center py-20">
            <CheckCircle2 className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
            <p className="text-zinc-500 text-sm">{t('admin.reports.no_reports_found')}</p>
          </div>
        ) : (
          <div className="space-y-4">
            {reports.map((r: any) => (
              <div key={r.id} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className={clsx(
                        "text-[10px] font-semibold px-2 py-0.5 rounded capitalize",
                        r.status === 'open' ? 'bg-rose-900/40 text-rose-400 border border-rose-800/40' :
                        r.status === 'reviewed' ? 'bg-amber-900/40 text-amber-400 border border-amber-800/40' :
                        r.status === 'actioned' ? 'bg-emerald-900/40 text-emerald-400 border border-emerald-800/40' :
                        'bg-zinc-800 text-zinc-400'
                      )}>{r.status}</span>
                      <span className="text-xs text-zinc-400 font-mono">ID: {r.id.split('-')[0]}</span>
                      <span className="text-xs bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded">{r.category}</span>
                    </div>
                    <p className="text-sm text-zinc-300 mt-2">{r.description || 'No description provided.'}</p>
                    <p className="text-xs text-zinc-500 mt-2">
                      Reported ID: <span className="font-mono text-zinc-400">{r.reported_id}</span>
                    </p>
                  </div>
                  
                  {r.status === 'open' && (
                    <div className="flex gap-2">
                      <button onClick={() => handleAction(r.id, 'dismiss', 'Invalid report')} className="w-8 h-8 rounded bg-zinc-800 text-zinc-400 hover:text-white flex items-center justify-center transition-colors" title="Dismiss">
                        <XCircle className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleAction(r.id, 'review', 'Requires investigation')} className="w-8 h-8 rounded bg-amber-900/40 text-amber-400 hover:text-amber-300 flex items-center justify-center transition-colors" title="Mark Reviewed">
                        <AlertCircle className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                  {r.status === 'reviewed' && (
                    <button onClick={() => handleAction(r.id, 'action', 'Account suspended')} className="px-3 py-1.5 rounded bg-emerald-900/40 text-emerald-400 hover:bg-emerald-800/40 text-xs font-semibold flex items-center gap-2 transition-colors">
                      <CheckCircle2 className="w-3.5 h-3.5" />{t('admin.reports.mark_actioned')}</button>
                  )}
                </div>
                
                {r.review_notes && (
                  <div className="mt-4 p-3 bg-zinc-950 rounded-xl border border-zinc-800 flex items-start gap-2 text-xs">
                    <MessageSquare className="w-4 h-4 text-zinc-500 shrink-0" />
                    <div>
                      <span className="text-zinc-400 font-semibold mb-0.5 block">{t('admin.reports.admin_notes')}</span>
                      <span className="text-zinc-300">{r.review_notes}</span>
                    </div>
                  </div>
                )}
                
                <p className="text-[10px] text-zinc-600 mt-4 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Filed: {new Date(r.created_at).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
