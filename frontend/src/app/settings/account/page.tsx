'use client';

/**
 * Account Data Page — NFR-16, NFR-17
 *
 * Provides:
 * - Data export (GDPR right to portability) — downloads JSON bundle
 * - Account deletion with PII anonymisation
 *
 * Accessible from /settings/account
 */

import { useState } from 'react';
import {
  Download, Trash2, ChevronLeft, AlertTriangle,
  Loader2, CheckCircle2, Shield, FileJson,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import ProtectedRoute from '@/components/ProtectedRoute';

export default function AccountDataPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [exportLoading, setExportLoading] = useState(false);
  const [deleteStep, setDeleteStep]       = useState<'idle' | 'confirm' | 'deleting' | 'done'>('idle');
  const [confirmation, setConfirmation]   = useState('');
  const [deleteError, setDeleteError]     = useState('');

  async function handleExport() {
    setExportLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const resp  = await fetch('/api/v1/account/me/export', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error('Export failed');
      const blob     = await resp.blob();
      const url      = URL.createObjectURL(blob);
      const anchor   = document.createElement('a');
      anchor.href    = url;
      anchor.download = `cultivax_data_${Date.now()}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch {
      alert('Failed to export data. Please try again.');
    } finally {
      setExportLoading(false);
    }
  }

  async function handleDelete() {
    if (confirmation !== 'DELETE MY ACCOUNT') {
      setDeleteError('Please type exactly: DELETE MY ACCOUNT');
      return;
    }
    setDeleteStep('deleting');
    try {
      const token = localStorage.getItem('access_token');
      const resp  = await fetch('/api/v1/account/me/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ confirmation }),
      });
      if (!resp.ok) throw new Error();
      localStorage.clear();
      setDeleteStep('done');
      setTimeout(() => router.push('/login'), 2500);
    } catch {
      setDeleteError('Deletion failed. Please try again or contact support.');
      setDeleteStep('confirm');
    }
  }

  if (deleteStep === 'done') {
    return (
      <div className="min-h-screen bg-zinc-950 text-white flex items-center justify-center">
        <div className="text-center space-y-3">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
          <h2 className="text-lg font-bold">{t('account.deleted_title')}</h2>
          <p className="text-sm text-zinc-400">{t('account.deleted_desc')}</p>
        </div>
      </div>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-zinc-950 text-white">
        {/* Header */}
        <div className="border-b border-zinc-800 px-6 py-4 flex items-center gap-3">
          <button onClick={() => router.back()} className="p-1.5 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="font-bold text-white text-base leading-none">{t('account.title')}</h1>
            <p className="text-xs text-zinc-500 mt-0.5">{t('account.subtitle')}</p>
          </div>
        </div>

        <div className="max-w-xl mx-auto px-6 py-6 space-y-5">

          {/* Data Export */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-blue-900/40 border border-blue-700/40 rounded-xl flex items-center justify-center">
                <FileJson className="w-4 h-4 text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white text-sm">{t('account.export_title')}</h3>
                <p className="text-xs text-zinc-400">{t('account.export_desc')}</p>
              </div>
            </div>
            <button
              onClick={handleExport}
              disabled={exportLoading}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-700 hover:bg-blue-600 text-white text-sm font-semibold transition-colors disabled:opacity-60 w-full justify-center"
            >
              {exportLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              {exportLoading ? t('account.export_loading') : t('account.export_btn')}
            </button>
          </div>

          {/* Delete Account */}
          <div className="bg-zinc-900 border border-rose-900/40 rounded-2xl p-5 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-rose-900/40 border border-rose-700/40 rounded-xl flex items-center justify-center">
                <Trash2 className="w-4 h-4 text-rose-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white text-sm">{t('account.delete_title')}</h3>
                <p className="text-xs text-zinc-400">{t('account.delete_desc')}</p>
              </div>
            </div>

            {deleteStep === 'idle' && (
              <button
                onClick={() => setDeleteStep('confirm')}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-rose-700 text-rose-400 hover:bg-rose-900/20 text-sm font-semibold transition-colors w-full justify-center"
              >
                <Trash2 className="w-4 h-4" />{t('account.delete_request')}
              </button>
            )}

            {(deleteStep === 'confirm' || deleteStep === 'deleting') && (
              <div className="space-y-3">
                <div className="flex gap-2 bg-rose-950/40 border border-rose-800/40 rounded-xl p-3">
                  <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-rose-300 leading-relaxed">
                    {t('account.delete_warning')}
                  </p>
                </div>
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">{t('account.delete_confirm_label')}</label>
                  <input
                    value={confirmation}
                    onChange={(e) => { setConfirmation(e.target.value); setDeleteError(''); }}
                    placeholder="DELETE MY ACCOUNT"
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-sm font-mono text-white focus:outline-none focus:border-rose-600"
                  />
                </div>
                {deleteError && <p className="text-xs text-rose-400">{deleteError}</p>}
                <div className="flex gap-2">
                  <button
                    onClick={() => { setDeleteStep('idle'); setConfirmation(''); setDeleteError(''); }}
                    className="flex-1 py-2 rounded-xl border border-zinc-700 text-zinc-400 hover:text-white text-sm transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleDelete}
                    disabled={deleteStep === 'deleting'}
                    className="flex-1 py-2 rounded-xl bg-rose-700 hover:bg-rose-600 text-white text-sm font-semibold transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
                  >
                    {deleteStep === 'deleting' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                    {deleteStep === 'deleting' ? t('account.deleting') : t('account.delete_confirm_btn')}
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 justify-center text-xs text-zinc-600">
            <Shield className="w-3 h-3" />
            {t('account.legal_note')}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
