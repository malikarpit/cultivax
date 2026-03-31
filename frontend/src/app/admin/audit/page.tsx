'use client';

import { useState } from 'react';
import { useFetch } from '@/hooks/useFetch';
import { Shield, Clock, Search, Filter, Loader2 } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import Badge from '@/components/Badge';

export default function AdminAuditPage() {
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState('');
  
  const queryParams = new URLSearchParams({
    page: page.toString(),
    per_page: '20',
  });
  if (actionFilter) queryParams.set('action', actionFilter);

  const { data, loading, error } = useFetch(`/api/v1/admin/audit?${queryParams.toString()}`);
  const logs = data?.items || [];
  const totalPages = data?.total ? Math.ceil(data.total / 20) : 1;

  const actionColors: Record<string, 'red' | 'blue' | 'green' | 'amber' | 'slate'> = {
    'role_change': 'blue',
    'user_deleted': 'red',
    'user_restored': 'green',
    'provider_verified': 'green',
    'provider_suspended': 'red',
    'abuse_flag_reviewed': 'amber',
  };

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="animate-fade-in max-w-6xl mx-auto py-8">
        <div className="flex items-center gap-3 mb-8">
          <div className="p-3 bg-m3-surface-container-high rounded-xl border border-m3-outline-variant/20 shadow-inner">
             <Shield className="w-8 h-8 text-cultivax-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold text-m3-on-surface">Audit Trail</h1>
            <p className="text-m3-on-surface-variant mt-1">Immutable ledger tracing governance execution policies and security boundaries.</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6 bg-m3-surface-container-high/50 p-4 rounded-xl border border-m3-outline-variant/20">
          <div className="flex items-center gap-2 flex-1 relative">
            <Filter className="w-5 h-5 text-m3-on-surface-variant absolute left-3" />
            <select 
              value={actionFilter} 
              onChange={e => { setActionFilter(e.target.value); setPage(1); }}
              className="w-full bg-m3-surface border border-m3-outline-variant/30 rounded-lg pl-10 pr-4 py-2.5 text-sm text-m3-on-surface appearance-none focus:ring-2 focus:ring-cultivax-primary/50"
            >
              <option value="">All Actions</option>
              <option value="role_change">Role Changes</option>
              <option value="user_deleted">Deletions</option>
              <option value="user_restored">Restorations</option>
              <option value="provider_verified">Provider Verification</option>
              <option value="provider_suspended">Provider Suspensions</option>
              <option value="dead_letter_retry">Dead Letter Retries</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="glass-card rounded-2xl border border-m3-outline-variant/20 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[800px]">
              <thead>
                <tr className="bg-m3-surface-container-high/40 text-m3-on-surface-variant text-xs uppercase tracking-wider">
                  <th className="p-4 font-semibold w-56">Action</th>
                  <th className="p-4 font-semibold w-48">Admin ID</th>
                  <th className="p-4 font-semibold w-48">Target Type</th>
                  <th className="p-4 font-semibold w-64">Details</th>
                  <th className="p-4 font-semibold text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-m3-outline-variant/10 text-sm">
                {loading ? (
                   <tr>
                     <td colSpan={5} className="p-12 text-center">
                       <Loader2 className="w-8 h-8 animate-spin mx-auto text-cultivax-primary" />
                     </td>
                   </tr>
                ) : logs.length === 0 ? (
                   <tr>
                     <td colSpan={5} className="p-12 text-center text-m3-on-surface-variant">
                       <Clock className="w-10 h-10 opacity-30 mx-auto mb-3" />
                       <p className="text-lg font-medium">No Audit Trace Found</p>
                       <p className="text-sm opacity-70">Adjust filters to see chronological governance actions.</p>
                     </td>
                   </tr>
                ) : (
                  logs.map((log: any) => (
                    <tr key={log.id} className="hover:bg-m3-surface-container-highest/20 transition-colors group">
                      <td className="p-4 align-top">
                        <Badge variant={actionColors[log.action] || 'slate'}>
                          {log.action.replace(/_/g, ' ').toUpperCase()}
                        </Badge>
                      </td>
                      <td className="p-4 align-top text-xs font-mono text-m3-on-surface-variant break-all">
                        {log.admin_id}
                      </td>
                      <td className="p-4 align-top">
                        <span className="capitalize font-medium text-m3-on-surface mr-1">{log.target_type.replace('_', ' ')}</span>
                        <div className="text-[10px] uppercase font-mono text-m3-on-surface-variant mt-1">{log.target_id}</div>
                      </td>
                      <td className="p-4 align-top">
                        {log.details ? (
                          <pre className="text-xs bg-m3-surface-container-high p-2 rounded border border-m3-outline-variant/10 whitespace-pre-wrap font-mono text-m3-on-surface-variant group-hover:bg-m3-surface-container-highest transition-colors">
                            {JSON.stringify(log.details, null, 2)}
                          </pre>
                        ) : (
                          <span className="text-xs text-m3-on-surface-variant italic">—</span>
                        )}
                      </td>
                      <td className="p-4 align-top text-right whitespace-nowrap">
                        <div className="font-medium text-m3-on-surface">
                          {new Date(log.created_at).toLocaleDateString()}
                        </div>
                        <div className="text-xs text-m3-on-surface-variant mt-0.5">
                          {new Date(log.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          
          {/* Pagination */}
          {logs.length > 0 && (
            <div className="p-4 border-t border-m3-outline-variant/10 flex flex-col sm:flex-row items-center justify-between gap-4 bg-m3-surface-container-low/50">
              <span className="text-sm font-medium text-m3-on-surface-variant">
                Displaying Trace {((page - 1) * 20) + 1}-{Math.min(page * 20, data?.total || 0)} of {data?.total || 0}
              </span>
              <div className="flex gap-2">
                <button 
                  disabled={page === 1} 
                  onClick={() => setPage(p => p - 1)}
                  className="px-4 py-2 text-sm font-semibold border border-m3-outline-variant/30 text-m3-on-surface rounded-xl disabled:opacity-30 hover:bg-m3-surface-container-highest transition-all shadow-sm"
                >
                  Previous
                </button>
                <button 
                  disabled={page >= totalPages} 
                  onClick={() => setPage(p => p + 1)}
                  className="px-4 py-2 text-sm font-semibold border border-cultivax-primary/30 text-cultivax-primary bg-cultivax-primary/5 rounded-xl disabled:opacity-30 hover:bg-cultivax-primary/10 transition-all shadow-sm"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
