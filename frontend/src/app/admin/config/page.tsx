'use client';

/**
 * Admin Region Config Extensibility — FR-38
 *
 * Manage dynamic agricultural regions without code changes.
 */

import { useState } from 'react';
import { Settings, Plus, MapPin, CheckCircle2, Save, Trash2, Edit2, Loader2, AlertTriangle } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useFetch } from '@/hooks/useFetch';
import clsx from 'clsx';
import { useTranslation } from 'react-i18next';

export default function AdminConfigPage() {
  const { t } = useTranslation();
  const { data, loading, refetch } = useFetch<any>('/api/v1/config/regions');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({ region_name: '', is_active: true, parameters: '{}' });
  const [submitLoading, setSubmitLoading] = useState(false);
  const [error, setError] = useState('');

  const regions = data?.items || [];

  function handleEdit(r: any) {
    setEditingId(r.id);
    setFormData({
      region_name: r.region_name,
      is_active: r.is_active,
      parameters: JSON.stringify(r.parameters, null, 2)
    });
    setError('');
  }

  function handleNew() {
    setEditingId('new');
    setFormData({
      region_name: '',
      is_active: true,
      parameters: '{\n  "supported_crops": ["wheat", "rice"],\n  "ph_thresholds": {"wheat": {"min": 6.0, "max": 7.5}}\n}'
    });
    setError('');
  }

  async function handleSave() {
    setSubmitLoading(true);
    setError('');
    try {
      let parsedParams;
      try {
        parsedParams = JSON.parse(formData.parameters);
      } catch (e) {
        throw new Error('Invalid JSON in parameters');
      }

      const token = localStorage.getItem('access_token');
      const url = editingId === 'new' ? '/api/v1/config/regions' : `/api/v1/config/regions/${editingId}`;
      const method = editingId === 'new' ? 'POST' : 'PUT';

      const resp = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          region_name: formData.region_name,
          is_active: formData.is_active,
          parameters: parsedParams
        })
      });

      if (!resp.ok) throw new Error((await resp.json()).error || 'Save failed');
      
      setEditingId(null);
      refetch();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Are you sure you want to delete this region configuration?')) return;
    const token = localStorage.getItem('access_token');
    await fetch(`/api/v1/config/regions/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` }
    });
    refetch();
  }

  return (
    <ProtectedRoute requiredRole={["admin"]}>
      <div className="min-h-screen bg-zinc-950 text-white p-6 sm:p-8">
        
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-900/40 border border-purple-700/40 flex items-center justify-center">
              <Settings className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h1 className="font-bold text-white text-xl">{t('admin.config.region_extensibility')}</h1>
              <p className="text-xs text-zinc-500">{t('admin.config.dynamically_add_or_configure')}</p>
            </div>
          </div>
          <button onClick={handleNew} disabled={editingId !== null} className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-purple-700 hover:bg-purple-600 text-white text-sm font-semibold transition-colors disabled:opacity-50">
            <Plus className="w-4 h-4" />{t('admin.config.new_region')}</button>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-rose-950/40 border border-rose-800/40 rounded-xl text-xs text-rose-300 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400" /> {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* List */}
          <div className="space-y-4">
            {loading ? (
              <div className="p-8 animate-pulse text-zinc-400">{t('admin.config.loading_configurations')}</div>
            ) : regions.map((r: any) => (
              <div key={r.id} className={clsx(
                "bg-zinc-900 border rounded-2xl p-4 transition-all",
                editingId === r.id ? "border-purple-600" : "border-zinc-800"
              )}>
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-bold text-white text-lg flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-zinc-400" /> {r.region_name}
                      {!r.is_active && <span className="text-[10px] bg-rose-900/40 text-rose-400 px-1.5 py-0.5 rounded">{t('admin.config.disabled')}</span>}
                    </h3>
                    <div className="mt-3">
                      <span className="text-xs text-zinc-500 font-semibold mb-1 block">{t('admin.config.supported_crops')}</span>
                      <div className="flex gap-1.5 flex-wrap">
                        {(r.parameters?.supported_crops || []).map((c: string) => (
                          <span key={c} className="text-[10px] bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded capitalize">{c}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleEdit(r)} disabled={editingId !== null} className="p-1.5 text-zinc-400 hover:text-white disabled:opacity-50"><Edit2 className="w-4 h-4" /></button>
                    <button onClick={() => handleDelete(r.id)} disabled={editingId !== null} className="p-1.5 text-zinc-400 hover:text-rose-400 disabled:opacity-50"><Trash2 className="w-4 h-4" /></button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Editor */}
          {editingId && (
            <div className="bg-zinc-900 border border-purple-800/40 rounded-2xl p-5 h-fit sticky top-6">
              <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                {editingId === 'new' ? 'Create New Region' : 'Edit Region'}
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">{t('admin.config.region_name_unique_key')}</label>
                  <input
                    value={formData.region_name}
                    onChange={e => setFormData({...formData, region_name: e.target.value})}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-600"
                    placeholder={t('admin.config.e_g_maharashtra')}
                  />
                </div>
                
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={e => setFormData({...formData, is_active: e.target.checked})}
                    id="isActive"
                    className="accent-purple-600"
                  />
                  <label htmlFor="isActive" className="text-sm text-zinc-300">{t('admin.config.region_is_active')}</label>
                </div>

                <div>
                  <label className="block text-xs text-zinc-400 mb-1 flex items-center justify-between">
                    <span>{t('admin.config.json_parameters')}</span>
                    <span className="text-[10px] text-zinc-600">{t('admin.config.must_be_valid_json')}</span>
                  </label>
                  <textarea
                    value={formData.parameters}
                    onChange={e => setFormData({...formData, parameters: e.target.value})}
                    rows={12}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm font-mono text-emerald-400 focus:outline-none focus:border-purple-600"
                  />
                </div>

                <div className="flex gap-3 pt-2">
                  <button onClick={() => { setEditingId(null); setError(''); }} className="flex-1 py-2 rounded-xl border border-zinc-700 text-zinc-400 hover:text-white text-sm transition-colors">{t('admin.config.cancel')}</button>
                  <button onClick={handleSave} disabled={submitLoading || !formData.region_name.trim()} className="flex-1 py-2 rounded-xl bg-purple-700 hover:bg-purple-600 text-white text-sm font-semibold transition-colors flex items-center justify-center gap-2 disabled:opacity-50">
                    {submitLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    Save Config
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

      </div>
    </ProtectedRoute>
  );
}
