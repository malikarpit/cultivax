'use client';

import React, { useState, useEffect } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useFetch } from '@/hooks/useFetch';
import { useApi } from '@/hooks/useApi';
import {
  FileText, Search, Loader2, ArrowRight, Clock, ShieldAlert, Key, Filter, ChevronLeft, ChevronRight, List
} from 'lucide-react';
import clsx from 'clsx';
import { toast } from 'sonner';

export default function AdminAuditLogPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    action: '',
    entity_type: '',
    admin_id: '',
  });

  const queryParams = new URLSearchParams({
    page: page.toString(),
    per_page: '20',
  });
  
  if (filters.action) queryParams.append('action', filters.action);
  if (filters.entity_type) queryParams.append('entity_type', filters.entity_type);
  if (filters.admin_id) queryParams.append('admin_id', filters.admin_id);

  const { data, loading, refetch } = useFetch(`/api/v1/admin/audit?${queryParams.toString()}`);
  
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  // Trigger refetch whenever page or filter changes
  useEffect(() => {
    refetch();
  }, [page, filters]);

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFilters(prev => ({ ...prev, [e.target.name]: e.target.value }));
    setPage(1); // Reset to first page
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="animate-fade-in max-w-7xl mx-auto py-8 space-y-8">
        
        {/* Header Block */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-m3-on-surface flex items-center gap-3">
              <FileText className="w-8 h-8 text-cultivax-primary" />
              Admin Audit Logs
            </h1>
            <p className="text-m3-on-surface-variant mt-2 max-w-2xl">
              Compliance-ready footprints tracing explicit system changes organically without omission.
            </p>
          </div>
        </div>

        {/* Filter Toolbar */}
        <div className="glass-card rounded-2xl p-4 flex flex-col md:flex-row gap-4 border border-m3-outline-variant/30 bg-m3-surface-container-low">
          <div className="flex items-center gap-2 text-m3-on-surface-variant px-2">
            <Filter className="w-4 h-4" /> Filters
          </div>
          <input 
            type="text"
            name="action"
            placeholder="Filter by Action..."
            className="flex-1 bg-m3-surface shadow-sm focus:ring-2 focus:ring-cultivax-primary/50 text-m3-on-surface rounded-xl px-4 py-2 border border-m3-outline-variant/30 text-sm"
            value={filters.action}
            onChange={handleFilterChange}
          />
          <input 
            type="text"
            name="entity_type"
            placeholder="Entity Type (e.g., user, service_provider)..."
            className="flex-1 bg-m3-surface shadow-sm focus:ring-2 focus:ring-cultivax-primary/50 text-m3-on-surface rounded-xl px-4 py-2 border border-m3-outline-variant/30 text-sm"
            value={filters.entity_type}
            onChange={handleFilterChange}
          />
          <input 
            type="text"
            name="admin_id"
            placeholder="Exact Admin UUID..."
            className="flex-1 bg-m3-surface shadow-sm focus:ring-2 focus:ring-cultivax-primary/50 text-m3-on-surface rounded-xl px-4 py-2 border border-m3-outline-variant/30 text-sm"
            value={filters.admin_id}
            onChange={handleFilterChange}
          />
        </div>

        {/* Audit Table */}
        <div className="glass-card rounded-2xl border border-m3-outline-variant/30 overflow-hidden relative min-h-[400px]">
          
          {loading && (
             <div className="absolute inset-0 bg-m3-surface-container/50 backdrop-blur-sm flex items-center justify-center z-10">
               <Loader2 className="w-8 h-8 animate-spin text-cultivax-primary" />
             </div>
          )}

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-m3-surface-container-highest/30 text-m3-on-surface-variant text-xs uppercase tracking-wider">
                  <th className="p-4 font-semibold w-56">Timestamp</th>
                  <th className="p-4 font-semibold w-40">Actor (Admin View)</th>
                  <th className="p-4 font-semibold w-48">Action</th>
                  <th className="p-4 font-semibold">Entity Mappings</th>
                  <th className="p-4 font-semibold w-24">Trace</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-m3-outline-variant/10 text-sm">
                {data?.items?.length === 0 && !loading && (
                   <tr>
                     <td colSpan={5} className="p-8 text-center text-m3-on-surface-variant/60">
                        No auditable records bound to this filter state.
                     </td>
                   </tr>
                )}
                {data?.items?.map((log: any) => (
                  <React.Fragment key={log.id}>
                    <tr className="hover:bg-m3-surface-container-lowest/50 group transition-colors">
                      <td className="p-4">
                        <div className="flex items-center gap-2 text-xs font-mono text-m3-on-surface-variant">
                          <Clock className="w-3 h-3" />
                          {new Date(log.created_at).toLocaleString()}
                        </div>
                      </td>
                      <td className="p-4 font-mono text-xs truncate max-w-[150px]" title={log.admin_id}>
                        {log.admin_id.split('-')[0]}...
                      </td>
                      <td className="p-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wide bg-m3-surface-container-highest text-cultivax-primary border border-cultivax-primary/10">
                          {log.action.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="p-4 font-mono text-xs">
                         <span className="text-m3-on-surface opacity-60">[{log.entity_type}]</span> {log.entity_id}
                         {log.reason && (
                           <div className="text-[10px] mt-1 text-red-400 italic">" {log.reason} "</div>
                         )}
                      </td>
                      <td className="p-4">
                        <button 
                          onClick={() => setExpandedLogId(expandedLogId === log.id ? null : log.id)}
                          className="px-3 py-1.5 text-xs font-semibold rounded-lg hover:bg-m3-surface-container-highest transition-colors border border-m3-outline-variant/40"
                        >
                          Payload
                        </button>
                      </td>
                    </tr>

                    {/* Expandable Trace Payload View */}
                    {expandedLogId === log.id && (
                      <tr className="bg-black/20">
                        <td colSpan={5} className="p-0">
                           <div className="p-4 border-l-4 border-cultivax-primary overflow-x-auto text-xs grid grid-cols-1 md:grid-cols-2 gap-4">
                              
                              <div className="space-y-2">
                                <h4 className="font-bold text-m3-on-surface-variant uppercase tracking-wider flex items-center gap-2">
                                   <List className="w-3 h-3" /> Before State
                                </h4>
                                <pre className="bg-m3-surface-container p-3 rounded-lg border border-m3-outline-variant/20 custom-scrollbar overflow-x-auto font-mono text-[10px] text-m3-on-surface opacity-80">
                                  {log.before_value ? JSON.stringify(log.before_value, null, 2) : "Null / Unavailable"}
                                </pre>
                              </div>

                              <div className="space-y-2">
                                <h4 className="font-bold text-cultivax-primary uppercase tracking-wider flex items-center gap-2">
                                   <ArrowRight className="w-3 h-3" /> After Delta
                                </h4>
                                <pre className="bg-m3-surface-container p-3 rounded-lg border border-cultivax-primary/20 custom-scrollbar overflow-x-auto font-mono text-[10px] text-green-400 opacity-90">
                                  {log.after_value ? JSON.stringify(log.after_value, null, 2) : "Null / Process executed purely"}
                                </pre>
                              </div>
                              
                           </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data?.total_pages > 1 && (
            <div className="p-4 border-t border-m3-outline-variant/30 flex items-center justify-between text-sm bg-m3-surface-container-low">
               <span className="text-m3-on-surface-variant font-medium">
                 Viewing {(page - 1) * data.per_page + 1} to {Math.min(page * data.per_page, data.total)} of {data.total}
               </span>
               <div className="flex gap-2">
                 <button 
                   onClick={() => setPage(p => Math.max(1, p - 1))}
                   disabled={page === 1}
                   className="p-2 rounded-xl border border-m3-outline-variant/30 hover:bg-m3-surface disabled:opacity-30 transition-all font-mono"
                 >
                   <ChevronLeft className="w-4 h-4" />
                 </button>
                 <button 
                   onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
                   disabled={page === data.total_pages}
                   className="p-2 rounded-xl border border-m3-outline-variant/30 hover:bg-m3-surface disabled:opacity-30 transition-all font-mono"
                 >
                   <ChevronRight className="w-4 h-4" />
                 </button>
               </div>
            </div>
          )}
        </div>
        
      </div>
    </ProtectedRoute>
  );
}
