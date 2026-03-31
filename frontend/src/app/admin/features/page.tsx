'use client';

import { useState } from 'react';
import { useFetch } from '@/hooks/useFetch';
import { useApi } from '@/hooks/useApi';
import { Shield, Search, ToggleLeft, ToggleRight, Loader2, AlertCircle } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import clsx from 'clsx';
import { toast } from 'sonner';

export default function AdminFeaturesPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  
  const [actionFlagName, setActionFlagName] = useState<string | null>(null);
  const [actionScope, setActionScope] = useState<string | null>(null);
  const [actionScopeValue, setActionScopeValue] = useState<string | null>(null);
  const [targetState, setTargetState] = useState<boolean>(false);
  const [reason, setReason] = useState('');

  const api = useApi();
  
  const queryParams = new URLSearchParams({
    page: page.toString(),
    per_page: '20',
  });
  if (search) queryParams.set('search', search);

  const { data, loading, refetch } = useFetch(`/api/v1/features?${queryParams.toString()}`);
  const features = data?.items || [];
  const totalPages = data?.total ? Math.ceil(data.total / 20) : 1;

  const handleToggle = async () => {
    if (!actionFlagName) return;
    try {
      await api.execute(`/api/v1/features/${actionFlagName}`, { 
          method: 'PUT',
          body: {
              is_enabled: targetState,
              scope: actionScope || 'global',
              scope_value: actionScopeValue || null,
              reason: reason
          }
      });
      toast.success(`Flag ${targetState ? 'Enabled' : 'Disabled'} Successfully!`);
      refetch();
      closeModal();
    } catch (err: any) {
      toast.error(err.message || 'Toggle modification boundary failed.');
    }
  };

  const openAction = (flag_name: string, scope: string, scope_value: string, currentState: boolean) => {
    setActionFlagName(flag_name);
    setActionScope(scope);
    setActionScopeValue(scope_value);
    setTargetState(!currentState);
    setReason('');
  };

  const closeModal = () => {
    setActionFlagName(null);
    setActionScope(null);
    setActionScopeValue(null);
    setReason('');
  }

  const isDangerous = (flag_name: string) => flag_name.startsWith('prod.') && (flag_name.includes('kill_switch') || flag_name.includes('live'));

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="animate-fade-in max-w-7xl mx-auto py-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-m3-on-surface">Runtime Feature Flags</h1>
            <p className="text-m3-on-surface-variant mt-2">Manage Namespaced Feature Flags globally applying scope resolutions explicitly across CTIS Engine Cache rules.</p>
          </div>
          <button className="px-5 py-2.5 bg-cultivax-primary hover:bg-cultivax-primary/90 text-white rounded-xl shadow-lg transition-colors flex items-center gap-2 font-medium">
            <Shield className="w-4 h-4" />
            Create Namespace Flag
          </button>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4 mb-6 bg-m3-surface-container-high/50 p-4 rounded-xl border border-m3-outline-variant/20">
          <div className="relative flex-1">
            <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-m3-on-surface-variant" />
            <input 
              type="text" 
              placeholder="Search explicitly by Namespace (e.g., prod.ml_kill_switch)..." 
              className="w-full bg-m3-surface border border-m3-outline-variant/30 rounded-lg pl-10 pr-4 py-2 text-sm text-m3-on-surface focus:ring-2 focus:ring-m3-primary/50"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        {/* Table */}
        <div className="glass-card rounded-2xl border border-m3-outline-variant/20 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[1000px]">
              <thead>
                <tr className="bg-m3-surface-container-high/40 text-m3-on-surface-variant text-xs uppercase tracking-wider">
                  <th className="p-4 font-semibold">Flag Identity (Namespace)</th>
                  <th className="p-4 font-semibold">Scope Mapping</th>
                  <th className="p-4 font-semibold">Description Context</th>
                  <th className="p-4 font-semibold">Runtime State</th>
                  <th className="p-4 font-semibold text-right">Toggle Controls</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-m3-outline-variant/10 text-sm">
                {loading ? (
                   <tr>
                     <td colSpan={5} className="p-12 text-center text-m3-on-surface-variant">
                       <Loader2 className="w-8 h-8 animate-spin mx-auto text-cultivax-primary" />
                     </td>
                   </tr>
                ) : features.length === 0 ? (
                   <tr>
                     <td colSpan={5} className="p-12 text-center text-m3-on-surface-variant">
                       <ToggleLeft className="w-10 h-10 opacity-30 mx-auto mb-3" />
                       <p className="font-medium text-lg">No Feature Flags Generated</p>
                       <p className="text-sm opacity-70">Expand search filters or initiate a payload dynamically.</p>
                     </td>
                   </tr>
                ) : (
                  features.map((flag: any) => {
                    const dangerous = isDangerous(flag.flag_name);
                    return (
                    <tr key={flag.id} className={clsx(
                      "transition-colors group",
                      !flag.is_enabled ? 'bg-m3-surface-container-low opacity-75 hover:opacity-100' : 'hover:bg-m3-surface-container-high/30',
                      dangerous && !flag.is_enabled && 'bg-red-500/10'
                    )}>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                           <div className={clsx("font-bold font-mono tracking-wide", dangerous ? "text-red-400" : "text-m3-on-surface")}>
                             {flag.flag_name}
                           </div>
                           {dangerous && (
                             <span title="CRITICAL PRODUCTION CACHE BOUNDARY">
                               <AlertCircle className="w-4 h-4 text-red-500" />
                             </span>
                           )}
                        </div>
                      </td>
                      <td className="p-4 text-m3-on-surface-variant">
                        <div className="font-medium uppercase text-xs tracking-widest">{flag.scope}</div>
                        {flag.scope_value && <div className="text-xs opacity-60 font-mono mt-1">Value: {flag.scope_value}</div>}
                      </td>
                      <td className="p-4 align-top w-1/3">
                        <p className="text-xs text-m3-on-surface-variant leading-relaxed">
                            {flag.description || "Generated without structural description limits."}
                        </p>
                      </td>
                      <td className="p-4 align-top">
                        <span className={clsx(
                          "px-3 py-1 rounded-full text-xs font-bold shadow-sm inline-flex items-center gap-1.5",
                          flag.is_enabled ? "bg-green-500/10 text-green-500 border border-green-500/20" : "bg-neutral-500/10 text-neutral-400 border border-neutral-500/20"
                        )}>
                            {flag.is_enabled ? <span className="w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0 animate-pulse"></span> : <span className="w-1.5 h-1.5 rounded-full bg-neutral-500 flex-shrink-0"></span>}
                            {flag.is_enabled ? 'ACTIVE CACHED' : 'FOCED OFF'}
                        </span>
                      </td>
                      <td className="p-4 align-top text-right whitespace-nowrap">
                         <button 
                             onClick={() => openAction(flag.flag_name, flag.scope, flag.scope_value, flag.is_enabled)}
                             className={clsx(
                               "p-2 rounded-full transition-colors",
                               flag.is_enabled ? 'text-green-500 hover:bg-green-500/10' : 'text-neutral-500 hover:text-m3-on-surface hover:bg-neutral-500/20'
                             )}
                         >
                             {flag.is_enabled ? <ToggleRight className="w-8 h-8" /> : <ToggleLeft className="w-8 h-8" />}
                         </button>
                      </td>
                    </tr>
                  )})
                )}
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          <div className="p-4 border-t border-m3-outline-variant/10 flex items-center justify-between bg-m3-surface-container-low/50">
            <span className="text-sm font-medium text-m3-on-surface-variant">Page {page} of {totalPages} ({data?.total || 0} Flags)</span>
            <div className="flex gap-2">
              <button 
                disabled={page === 1} 
                onClick={() => setPage(page - 1)}
                className="px-4 py-2 text-sm font-semibold border border-m3-outline-variant/30 text-m3-on-surface rounded-xl disabled:opacity-30 hover:bg-m3-surface-container-highest transition-all shadow-sm"
              >
                Previous
              </button>
              <button 
                disabled={page >= totalPages} 
                onClick={() => setPage(page + 1)}
                className="px-4 py-2 text-sm font-semibold border border-cultivax-primary/30 text-cultivax-primary bg-cultivax-primary/5 rounded-xl disabled:opacity-30 hover:bg-cultivax-primary/10 transition-all shadow-sm"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Action Modal */}
      {actionFlagName && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="glass-card max-w-sm w-full p-6 rounded-3xl shadow-2xl relative border border-m3-outline-variant/20">
            
            <div className="mb-4">
              <Shield className={clsx("w-10 h-10 mb-2", targetState ? 'text-green-500' : 'text-red-500')} />
              <h2 className="text-2xl font-bold text-m3-on-surface">
                {targetState ? 'Enable Feature Flag' : 'Isolate / Disable Flag'}
              </h2>
            </div>
            
            <p className="text-sm text-m3-on-surface-variant mb-4 leading-relaxed font-mono bg-m3-surface-container min-h-1 p-2 rounded">
               {actionFlagName} ({actionScope})
            </p>

            <p className="text-sm text-m3-on-surface-variant mb-6 leading-relaxed">
               Modifying this Namespace triggers an exact structural rebuild overriding the CTIS TTL mapping limits dynamically caching globally! Be explicitly clear in your rationale.
            </p>

            <textarea 
              value={reason}
              onChange={e => setReason(e.target.value)}
              placeholder="Governance Mapping Logic (ex. Escalated Issue #241)"
              className="w-full mb-6 bg-m3-surface-container-highest border border-m3-outline-variant/30 rounded-xl px-4 py-3 text-sm text-m3-on-surface min-h-[100px] resize-none focus:ring-2 focus:ring-cultivax-primary/50"
            />

            <div className="flex justify-end gap-3 mt-2">
              <button
                onClick={closeModal}
                className="px-5 py-2.5 rounded-xl font-medium text-sm text-m3-on-surface hover:bg-m3-surface-container-highest transition-colors border border-m3-outline-variant/20 shadow-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleToggle}
                disabled={api.loading || reason.trim().length === 0}
                className={clsx(
                  "px-5 py-2.5 rounded-xl font-medium text-sm flex items-center gap-2 text-white shadow-lg transition-all",
                  targetState ? 'bg-green-600 hover:bg-green-700 shadow-green-600/20 disabled:bg-green-600/50' : 
                  'bg-red-500 hover:bg-red-600 shadow-red-500/20 disabled:bg-red-500/50'
                )}
              >
                {api.loading && <Loader2 className="w-4 h-4 animate-spin" />}
                Execute Boundary {targetState ? 'Wipe' : 'Break'}
              </button>
            </div>
          </div>
        </div>
      )}
    </ProtectedRoute>
  );
}
