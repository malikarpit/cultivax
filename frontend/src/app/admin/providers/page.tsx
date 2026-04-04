'use client';

import { useState } from 'react';
import { useFetch } from '@/hooks/useFetch';
import { useApi } from '@/hooks/useApi';
import { Users, Search, Edit3, Trash2, ShieldAlert, ShieldCheck, ShieldOff, Loader2, RefreshCw, Briefcase, MapPin } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import Badge from '@/components/Badge';
import clsx from 'clsx';

export default function AdminProvidersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [verifiedFilter, setVerifiedFilter] = useState('');
  const [suspendedFilter, setSuspendedFilter] = useState('false');
  
  const [actionProviderId, setActionProviderId] = useState<string | null>(null);
  const [actionType, setActionType] = useState<'verify' | 'suspend' | 'unverify' | 'unsuspend' | null>(null);
  const [reason, setReason] = useState('');

  const api = useApi();
  
  const queryParams = new URLSearchParams({
    page: page.toString(),
    per_page: '20',
  });
  if (search) queryParams.set('search', search);
  if (verifiedFilter !== '') queryParams.set('is_verified', verifiedFilter);
  if (suspendedFilter !== 'all') queryParams.set('is_suspended', suspendedFilter);

  const { data, loading, error, refetch } = useFetch(`/api/v1/admin/providers?${queryParams.toString()}`);
  const providers = data?.items || [];
  const totalPages = data?.total ? Math.ceil(data.total / 20) : 1;

  const handleAction = async () => {
    if (!actionProviderId || !actionType) return;
    try {
      if (actionType === 'verify') {
        await api.execute(`/api/v1/admin/providers/${actionProviderId}/verify`, { method: 'PUT' });
      } else if (actionType === 'suspend') {
        await api.execute(`/api/v1/admin/providers/${actionProviderId}/suspend`, { method: 'PUT', body: { reason } });
      } else if (actionType === 'unsuspend') {
        await api.execute(`/api/v1/admin/providers/${actionProviderId}/unsuspend`, { method: 'PUT', body: { reason } });
      } else if (actionType === 'unverify') {
        await api.execute(`/api/v1/admin/providers/${actionProviderId}/unverify`, { method: 'PUT', body: { reason } });
      }
      refetch();
      setActionType(null);
      setActionProviderId(null);
      setReason('');
    } catch (err) {
      console.error('Failed mutative action', err);
    }
  };

  const openAction = (id: string, type: 'verify' | 'suspend' | 'unverify' | 'unsuspend') => {
    setActionProviderId(id);
    setActionType(type);
    setReason('');
  };

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="animate-fade-in max-w-7xl mx-auto py-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-m3-on-surface">Provider Governance</h1>
            <p className="text-m3-on-surface-variant mt-2">Manage provider network trust, verify compliance, or restrict violating entities globally.</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4 mb-6 bg-m3-surface-container-high/50 p-4 rounded-xl border border-m3-outline-variant/20">
          <div className="relative flex-1">
            <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-m3-on-surface-variant" />
            <input 
              type="text" 
              placeholder="Search by business name or service type..." 
              className="w-full bg-m3-surface border border-m3-outline-variant/30 rounded-lg pl-10 pr-4 py-2 text-sm text-m3-on-surface focus:ring-2 focus:ring-m3-primary/50"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select 
            value={verifiedFilter} 
            onChange={e => setVerifiedFilter(e.target.value)}
            className="bg-m3-surface border border-m3-outline-variant/30 rounded-lg px-4 py-2 text-sm text-m3-on-surface appearance-none"
          >
            <option value="">Verification: All</option>
            <option value="true">Verified Only</option>
            <option value="false">Unverified Only</option>
          </select>
          <select 
            value={suspendedFilter} 
            onChange={e => setSuspendedFilter(e.target.value)}
            className="bg-m3-surface border border-m3-outline-variant/30 rounded-lg px-4 py-2 text-sm text-m3-on-surface appearance-none"
          >
            <option value="false">Active (Not Suspended)</option>
            <option value="true">Suspended Only</option>
            <option value="all">Suspend Bound: All</option>
          </select>
        </div>

        {/* Table */}
        <div className="glass-card rounded-2xl border border-m3-outline-variant/20 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[900px]">
              <thead>
                <tr className="bg-m3-surface-container-high/40 text-m3-on-surface-variant text-xs uppercase tracking-wider">
                  <th className="p-4 font-semibold">Business</th>
                  <th className="p-4 font-semibold">Service Type</th>
                  <th className="p-4 font-semibold">Territory</th>
                  <th className="p-4 font-semibold">Access State</th>
                  <th className="p-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-m3-outline-variant/10 text-sm">
                {loading ? (
                   <tr>
                     <td colSpan={5} className="p-12 text-center text-m3-on-surface-variant">
                       <Loader2 className="w-8 h-8 animate-spin mx-auto text-cultivax-primary" />
                     </td>
                   </tr>
                ) : providers.length === 0 ? (
                   <tr>
                     <td colSpan={5} className="p-12 text-center text-m3-on-surface-variant">
                       <Briefcase className="w-10 h-10 opacity-30 mx-auto mb-3" />
                       <p className="font-medium text-lg">No Providers Found</p>
                       <p className="text-sm opacity-70">Adjust active filters directly.</p>
                     </td>
                   </tr>
                ) : (
                  providers.map((provider: any) => (
                    <tr key={provider.id} className={clsx(
                      "transition-colors group",
                      provider.is_suspended ? 'bg-red-500/5 hover:bg-red-500/10' : 'hover:bg-m3-surface-container-high/30'
                    )}>
                      <td className="p-4">
                        <div className="font-bold text-m3-on-surface">{provider.business_name || 'Individual Contractor'}</div>
                        <div className="text-xs text-m3-on-surface-variant font-mono mt-1">{provider.id}</div>
                      </td>
                      <td className="p-4 text-m3-on-surface-variant capitalize">
                        {provider.service_type}
                        <div className="text-xs opacity-70 mt-1">Trust: {(provider.trust_score * 100).toFixed(0)}%</div>
                      </td>
                      <td className="p-4 text-m3-on-surface-variant">
                        <div className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" /> {provider.region}
                        </div>
                      </td>
                      <td className="p-4 align-top">
                        <div className="flex flex-col gap-2 items-start">
                          {provider.is_suspended ? (
                            <Badge variant="red">Suspended</Badge>
                          ) : (
                            <Badge variant="blue">Active</Badge>
                          )}
                          {provider.is_verified ? (
                             <Badge variant="green">Verified</Badge>
                          ) : (
                             <Badge variant="amber">Unverified</Badge>
                          )}
                        </div>
                      </td>
                      <td className="p-4 align-top text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1">
                           {/* Verify/Unverify Toggle */}
                           {provider.is_verified ? (
                             <button 
                               onClick={() => openAction(provider.id, 'unverify')} 
                               disabled={provider.is_suspended}
                               className="p-2 text-amber-500 hover:bg-amber-500/10 rounded-full transition-colors disabled:opacity-30" 
                               title="Revoke Verification"
                             >
                               <ShieldOff className="w-5 h-5" />
                             </button>
                           ) : (
                             <button 
                               onClick={() => openAction(provider.id, 'verify')} 
                               disabled={provider.is_suspended}
                               className="p-2 text-green-500 hover:bg-green-500/10 rounded-full transition-colors disabled:opacity-30" 
                               title="Grant Verification"
                             >
                               <ShieldCheck className="w-5 h-5" />
                             </button>
                           )}

                           {/* Suspend/Unsuspend Toggle */}
                           {provider.is_suspended ? (
                             <button 
                               onClick={() => openAction(provider.id, 'unsuspend')} 
                               className="p-2 text-blue-500 hover:bg-blue-500/10 rounded-full transition-colors" 
                               title="Lift Suspension"
                             >
                               <RefreshCw className="w-5 h-5" />
                             </button>
                           ) : (
                             <button 
                               onClick={() => openAction(provider.id, 'suspend')} 
                               className="p-2 text-red-500 hover:bg-red-500/10 rounded-full transition-colors" 
                               title="Suspend Provider"
                             >
                               <ShieldAlert className="w-5 h-5" />
                             </button>
                           )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          <div className="p-4 border-t border-m3-outline-variant/10 flex items-center justify-between bg-m3-surface-container-low/50">
            <span className="text-sm font-medium text-m3-on-surface-variant">Page {page} of {totalPages} ({data?.total || 0} Entities)</span>
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
      {actionType && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="glass-card max-w-sm w-full p-6 rounded-3xl shadow-2xl relative border border-m3-outline-variant/20">
            
            <div className="mb-4">
              {actionType === 'suspend' && <ShieldAlert className="w-10 h-10 text-red-500 mb-2" />}
              {actionType === 'unverify' && <ShieldOff className="w-10 h-10 text-amber-500 mb-2" />}
              {actionType === 'verify' && <ShieldCheck className="w-10 h-10 text-green-500 mb-2" />}
              {actionType === 'unsuspend' && <RefreshCw className="w-10 h-10 text-blue-500 mb-2" />}
              
              <h2 className="text-2xl font-bold text-m3-on-surface">
                {actionType === 'suspend' ? 'Suspend Provider' : 
                 actionType === 'unsuspend' ? 'Lift Suspension' : 
                 actionType === 'unverify' ? 'Revoke Verification' : 'Verify Provider'}
              </h2>
            </div>
            
            <p className="text-sm text-m3-on-surface-variant mb-6 leading-relaxed">
              {actionType === 'suspend' && 'Suspended providers are immediately stripped from the SOE marketplace lists. The provider will receive a Notice.'}
              {actionType === 'unsuspend' && 'Restoring this provider will reinstate them back into applicable network searches.'}
              {actionType === 'unverify' && 'Unverifying removes the Trusted Badge constraint natively dropping them from rigorous filters.'}
              {actionType === 'verify' && 'Verification pushes this entity back into highly trusted public ranking zones instantly.'}
            </p>

            {/* Verification does not technically require a reason, but the others do. */}
            {actionType !== 'verify' && (
              <textarea 
                value={reason}
                onChange={e => setReason(e.target.value)}
                placeholder="Required justification rationale. Visible to the provider."
                className="w-full mb-6 bg-m3-surface-container-highest border border-m3-outline-variant/30 rounded-xl px-4 py-3 text-sm text-m3-on-surface min-h-[100px] resize-none focus:ring-2 focus:ring-cultivax-primary/50"
              />
            )}

            <div className="flex justify-end gap-3 mt-2">
              <button
                onClick={() => setActionType(null)}
                className="px-5 py-2.5 rounded-xl font-medium text-sm text-m3-on-surface hover:bg-m3-surface-container-highest transition-colors border border-m3-outline-variant/20 shadow-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleAction}
                disabled={api.loading || (actionType !== 'verify' && reason.trim().length === 0)}
                className={clsx(
                  "px-5 py-2.5 rounded-xl font-medium text-sm flex items-center gap-2 text-white shadow-lg transition-all",
                  actionType === 'suspend' ? 'bg-red-500 hover:bg-red-600 shadow-red-500/20 disabled:bg-red-500/50' : 
                  actionType === 'unverify' ? 'bg-amber-500 hover:bg-amber-600 shadow-amber-500/20 disabled:bg-amber-500/50' :
                  actionType === 'unsuspend' ? 'bg-blue-500 hover:bg-blue-600 shadow-blue-500/20 disabled:bg-blue-500/50' :
                  'bg-green-600 hover:bg-green-700 shadow-green-600/20 disabled:bg-green-600/50'
                )}
              >
                {api.loading && <Loader2 className="w-4 h-4 animate-spin" />}
                Commit Action
              </button>
            </div>
          </div>
        </div>
      )}
    </ProtectedRoute>
  );
}
