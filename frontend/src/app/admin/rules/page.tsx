'use client';

import { useState } from 'react';
import { useFetch } from '@/hooks/useFetch';
import { useApi } from '@/hooks/useApi';
import { Network, Search, Edit3, Trash2, CheckCircle, ShieldAlert, BookOpen, Loader2, PlayCircle, ShieldCheck, Settings } from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import Badge from '@/components/Badge';
import clsx from 'clsx';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';

export default function AdminRulesPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  const [actionRuleId, setActionRuleId] = useState<string | null>(null);
  const [actionType, setActionType] = useState<'validate' | 'approve' | 'deprecate' | null>(null);
  const [reason, setReason] = useState('');

  const api = useApi();
  
  const queryParams = new URLSearchParams({
    page: page.toString(),
    per_page: '20',
  });
  if (search) queryParams.set('crop_type', search.toLowerCase());
  if (statusFilter !== '') queryParams.set('status', statusFilter);

  const { data, loading, refetch } = useFetch(`/api/v1/rules?${queryParams.toString()}`);
  const rules = data?.items || [];
  const totalPages = data?.total ? Math.ceil(data.total / 20) : 1;

  const handleAction = async () => {
    if (!actionRuleId || !actionType) return;
    try {
      if (actionType === 'validate') {
        const res = await api.execute(`/api/v1/rules/${actionRuleId}/validate`, { method: 'POST' });
        if (res.validation_errors?.length > 0) {
            toast.error(t('admin.rules.toast.validation_semantics_failed'));
        } else {
            toast.success(t('admin.rules.toast.template_validated_semantically'));
        }
      } else if (actionType === 'approve') {
        await api.execute(`/api/v1/rules/${actionRuleId}/approve`, { method: 'POST' });
        toast.success(t('admin.rules.toast.template_activated_previous_scoping'));
      } else if (actionType === 'deprecate') {
        await api.execute(`/api/v1/rules/${actionRuleId}/deprecate`, { method: 'POST', body: { reason } });
        toast.success(t('admin.rules.toast.template_deprecated'));
      }
      refetch();
      setActionType(null);
      setActionRuleId(null);
      setReason('');
    } catch (err: any) {
      toast.error(err.message || 'Governance Transition Failed');
    }
  };

  const openAction = (id: string, type: 'validate' | 'approve' | 'deprecate') => {
    setActionRuleId(id);
    setActionType(type);
    setReason('');
  };

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="animate-fade-in max-w-7xl mx-auto py-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-m3-on-surface">{t('admin.rules.rule_template_governance')}</h1>
            <p className="text-m3-on-surface-variant mt-2">{t('admin.rules.manage_ctis_stage_engine')}</p>
          </div>
          <button className="px-5 py-2.5 bg-cultivax-primary hover:bg-cultivax-primary/90 text-white rounded-xl shadow-lg transition-colors flex items-center gap-2 font-medium">
            <Edit3 className="w-4 h-4" />{t('admin.rules.new_draft')}</button>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4 mb-6 bg-m3-surface-container-high/50 p-4 rounded-xl border border-m3-outline-variant/20">
          <div className="relative flex-1">
            <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-m3-on-surface-variant" />
            <input 
              type="text" 
              placeholder={t('admin.rules.filter_exactly_by_crop')} 
              className="w-full bg-m3-surface border border-m3-outline-variant/30 rounded-lg pl-10 pr-4 py-2 text-sm text-m3-on-surface focus:ring-2 focus:ring-m3-primary/50"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select 
            value={statusFilter} 
            onChange={e => setStatusFilter(e.target.value)}
            className="bg-m3-surface border border-m3-outline-variant/30 rounded-lg px-4 py-2 text-sm text-m3-on-surface appearance-none min-w-[200px]"
          >
            <option value="">{t('admin.rules.status_lifecycle_all')}</option>
            <option value="draft">{t('admin.rules.drafts_only')}</option>
            <option value="validated">{t('admin.rules.validated_awaiting_approval')}</option>
            <option value="active">{t('admin.rules.active_production')}</option>
            <option value="deprecated">{t('admin.rules.deprecated')}</option>
          </select>
        </div>

        {/* Table */}
        <div className="glass-card rounded-2xl border border-m3-outline-variant/20 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[1000px]">
              <thead>
                <tr className="bg-m3-surface-container-high/40 text-m3-on-surface-variant text-xs uppercase tracking-wider">
                  <th className="p-4 font-semibold">{t('admin.rules.scope_identity')}</th>
                  <th className="p-4 font-semibold">{t('admin.rules.version_info')}</th>
                  <th className="p-4 font-semibold">{t('admin.rules.lifecycle_state')}</th>
                  <th className="p-4 font-semibold">{t('admin.rules.effective_bounds')}</th>
                  <th className="p-4 font-semibold text-right">{t('admin.rules.transitions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-m3-outline-variant/10 text-sm">
                {loading ? (
                   <tr>
                     <td colSpan={5} className="p-12 text-center text-m3-on-surface-variant">
                       <Loader2 className="w-8 h-8 animate-spin mx-auto text-cultivax-primary" />
                     </td>
                   </tr>
                ) : rules.length === 0 ? (
                   <tr>
                     <td colSpan={5} className="p-12 text-center text-m3-on-surface-variant">
                       <Network className="w-10 h-10 opacity-30 mx-auto mb-3" />
                       <p className="font-medium text-lg">{t('admin.rules.no_rules_found')}</p>
                       <p className="text-sm opacity-70">{t('admin.rules.expand_search_filters_or')}</p>
                     </td>
                   </tr>
                ) : (
                  rules.map((rule: any) => (
                    <tr key={rule.id} className={clsx(
                      "transition-colors group",
                      rule.status === 'deprecated' ? 'bg-m3-surface-container-low opacity-60' : 'hover:bg-m3-surface-container-high/30',
                      rule.status === 'active' && 'bg-green-500/5'
                    )}>
                      <td className="p-4">
                        <div className="font-bold text-m3-on-surface uppercase tracking-wide">{rule.crop_type}</div>
                        <div className="text-xs text-m3-on-surface-variant mt-1">
                          Region: {rule.region || 'Global'} | Variety: {rule.variety || 'All'}
                        </div>
                        {rule.validation_errors && rule.validation_errors.length > 0 && (
                            <div className="mt-2 text-red-500 text-xs font-medium max-w-xs break-words">
                                {rule.validation_errors.join(", ")}
                            </div>
                        )}
                      </td>
                      <td className="p-4 text-m3-on-surface-variant">
                        <div className="font-mono text-xs">v{rule.version_id}</div>
                        <div className="text-[10px] mt-1 opacity-60 font-mono">ID: {rule.id.split('-')[0]}..</div>
                      </td>
                      <td className="p-4 align-top">
                        {rule.status === 'draft' && <Badge variant="primary">{t('admin.rules.draft')}</Badge>}
                        {rule.status === 'validated' && <Badge variant="amber">{t('admin.rules.validated')}</Badge>}
                        {rule.status === 'active' && <Badge variant="green">{t('admin.rules.active')}</Badge>}
                        {rule.status === 'deprecated' && <Badge variant="neutral">{t('admin.rules.deprecated')}</Badge>}
                      </td>
                      <td className="p-4 align-top text-m3-on-surface-variant text-xs">
                        Starts: <span className="font-medium text-m3-on-surface">{rule.effective_from_date}</span>
                        {rule.approved_by && (
                           <div className="mt-2 flex flex-col gap-1 text-[10px]">
                              <span>Approved: {new Date(rule.approved_at).toLocaleDateString()}</span>
                           </div>
                        )}
                      </td>
                      <td className="p-4 align-top text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1">
                           
                           {/* Draft to Validated */}
                           {rule.status === 'draft' && (
                             <button 
                               onClick={() => openAction(rule.id, 'validate')} 
                               className="p-2 text-blue-500 hover:bg-blue-500/10 rounded-full transition-colors group-hover:opacity-100 opacity-60" 
                               title="Run Structural SEMANTICS Validation"
                             >
                               <PlayCircle className="w-5 h-5" />
                             </button>
                           )}

                           {/* Validated to Active */}
                           {rule.status === 'validated' && (
                             <button 
                               onClick={() => openAction(rule.id, 'approve')} 
                               className="p-2 text-green-500 hover:bg-green-500/10 rounded-full transition-colors group-hover:opacity-100 opacity-60" 
                               title="Approve & Deploy Template"
                             >
                               <CheckCircle className="w-5 h-5" />
                             </button>
                           )}

                           {/* Active to Deprecated */}
                           {rule.status === 'active' && (
                             <button 
                               onClick={() => openAction(rule.id, 'deprecate')} 
                               className="p-2 text-red-500 hover:bg-red-500/10 rounded-full transition-colors" 
                               title="Force Deprecate Template"
                             >
                               <ShieldAlert className="w-5 h-5" />
                             </button>
                           )}
                           
                           {/* Details Config */}
                           <button className="p-2 text-m3-on-surface-variant hover:bg-m3-surface-container-highest rounded-full transition-colors ml-2">
                             <Settings className="w-5 h-5" />
                           </button>

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
            <span className="text-sm font-medium text-m3-on-surface-variant">Page {page} of {totalPages} ({data?.total || 0} Models)</span>
            <div className="flex gap-2">
              <button 
                disabled={page === 1} 
                onClick={() => setPage(page - 1)}
                className="px-4 py-2 text-sm font-semibold border border-m3-outline-variant/30 text-m3-on-surface rounded-xl disabled:opacity-30 hover:bg-m3-surface-container-highest transition-all shadow-sm"
              >{t('admin.rules.previous')}</button>
              <button 
                disabled={page >= totalPages} 
                onClick={() => setPage(page + 1)}
                className="px-4 py-2 text-sm font-semibold border border-cultivax-primary/30 text-cultivax-primary bg-cultivax-primary/5 rounded-xl disabled:opacity-30 hover:bg-cultivax-primary/10 transition-all shadow-sm"
              >{t('admin.rules.next')}</button>
            </div>
          </div>
        </div>
      </div>

      {/* Action Modal */}
      {actionType && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="glass-card max-w-sm w-full p-6 rounded-3xl shadow-2xl relative border border-m3-outline-variant/20">
            
            <div className="mb-4">
              {actionType === 'validate' && <PlayCircle className="w-10 h-10 text-blue-500 mb-2" />}
              {actionType === 'approve' && <CheckCircle className="w-10 h-10 text-green-500 mb-2" />}
              {actionType === 'deprecate' && <ShieldAlert className="w-10 h-10 text-red-500 mb-2" />}
              
              <h2 className="text-2xl font-bold text-m3-on-surface">
                {actionType === 'validate' ? 'Validate Semantics' : 
                 actionType === 'approve' ? 'Approve Matrix' : 'Deprecate Rule Profile'}
              </h2>
            </div>
            
            <p className="text-sm text-m3-on-surface-variant mb-6 leading-relaxed">
              {actionType === 'validate' && 'Fires logical stage boundary checks and baseline metrics across the JSON payloads structurally.'}
              {actionType === 'approve' && 'Warning: Double-Approval constraint enforces the creator of the template cannot execute this function. Instantly deprecates any other active Rules intersecting exactly with this Region & Crop Type mapping.'}
              {actionType === 'deprecate' && 'Immediately decommissions the Template preventing new Crop Instances from binding to its bounds during spawn.'}
            </p>

            {actionType === 'deprecate' && (
              <textarea 
                value={reason}
                onChange={e => setReason(e.target.value)}
                placeholder={t('admin.rules.reasoning_logic_for_the')}
                className="w-full mb-6 bg-m3-surface-container-highest border border-m3-outline-variant/30 rounded-xl px-4 py-3 text-sm text-m3-on-surface min-h-[100px] resize-none focus:ring-2 focus:ring-cultivax-primary/50"
              />
            )}

            <div className="flex justify-end gap-3 mt-2">
              <button
                onClick={() => setActionType(null)}
                className="px-5 py-2.5 rounded-xl font-medium text-sm text-m3-on-surface hover:bg-m3-surface-container-highest transition-colors border border-m3-outline-variant/20 shadow-sm"
              >{t('admin.rules.cancel')}</button>
              <button
                onClick={handleAction}
                disabled={api.loading || (actionType === 'deprecate' && reason.trim().length === 0)}
                className={clsx(
                  "px-5 py-2.5 rounded-xl font-medium text-sm flex items-center gap-2 text-white shadow-lg transition-all",
                  actionType === 'deprecate' ? 'bg-red-500 hover:bg-red-600 shadow-red-500/20 disabled:bg-red-500/50' : 
                  actionType === 'validate' ? 'bg-blue-500 hover:bg-blue-600 shadow-blue-500/20 disabled:bg-blue-500/50' : 
                  'bg-green-600 hover:bg-green-700 shadow-green-600/20 disabled:bg-green-600/50'
                )}
              >
                {api.loading && <Loader2 className="w-4 h-4 animate-spin" />}
                Execute Check
              </button>
            </div>
          </div>
        </div>
      )}
    </ProtectedRoute>
  );
}
