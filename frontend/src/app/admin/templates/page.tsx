'use client';

/**
 * Admin — Rule Template Governance
 *
 * Template lifecycle: draft → validated → active → deprecated
 * Dual-admin approval workflow.
 * GET /api/v1/rules
 */

import { useEffect, useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/context/AuthContext';
import { useApi } from '@/hooks/useApi';
import { useTranslation } from 'react-i18next';

interface RuleTemplate {
  id: string;
  template_name: string;
  crop_type: string;
  status: string;
  version: number;
  created_by?: string;
  approved_by?: string;
  approved_at?: string;
  validation_errors?: string[];
  stage_definitions?: any[];
}

export default function TemplateGovernancePage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const rulesApi = useApi<RuleTemplate[]>();
  const actionApi = useApi();
  const [acting, setActing] = useState<string | null>(null);

  useEffect(() => {
    rulesApi.execute('/api/v1/rules').catch(() => {});
  }, []);

  const templates = rulesApi.data || [];

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      draft: 'bg-gray-500/20 text-gray-400',
      validated: 'bg-blue-500/20 text-blue-400',
      active: 'bg-green-500/20 text-green-400',
      deprecated: 'bg-red-500/20 text-red-400',
    };
    return map[status] || 'bg-gray-500/20 text-gray-400';
  };

  const statusFlow = {
    draft: { next: 'validated', label: 'Validate', icon: '✓' },
    validated: { next: 'active', label: 'Approve', icon: '✅' },
    active: { next: 'deprecated', label: 'Deprecate', icon: '⛔' },
    deprecated: null,
  };

  const handleAction = async (templateId: string, action: string) => {
    setActing(templateId);
    try {
      await actionApi.execute(`/api/v1/rules/${templateId}`, {
        method: 'PUT',
        body: { status: action },
      });
      rulesApi.execute('/api/v1/rules').catch(() => {});
    } catch {} finally {
      setActing(null);
    }
  };

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">{t('admin.templates.template_governance')}</h1>
          <p className="text-gray-400 mt-1">{t('admin.templates.manage_crop_rule_template')}</p>
        </div>

        {/* Lifecycle Legend */}
        <div className="card flex items-center gap-4 text-sm">
          <span className="text-gray-400">{t('admin.templates.lifecycle')}</span>
          <span className="bg-gray-500/20 text-gray-400 px-2 py-0.5 rounded-full">{t('admin.templates.draft')}</span>
          <span className="text-gray-500">→</span>
          <span className="bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full">{t('admin.templates.validated')}</span>
          <span className="text-gray-500">→</span>
          <span className="bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">{t('admin.templates.active')}</span>
          <span className="text-gray-500">→</span>
          <span className="bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full">{t('admin.templates.deprecated')}</span>
        </div>

        {/* Templates List */}
        {rulesApi.loading && (
          <div className="card text-center py-8">
            <div className="inline-block w-8 h-8 border-2 border-cultivax-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!rulesApi.loading && templates.length === 0 && (
          <div className="card text-center py-12 text-gray-500">
            <p className="text-5xl mb-4">📐</p>
            <p className="text-lg font-medium">{t('admin.templates.no_templates_found')}</p>
          </div>
        )}

        {templates.length > 0 && (
          <div className="space-y-3">
            {templates.map((tpl) => {
              const flow = statusFlow[tpl.status as keyof typeof statusFlow];
              const canApprove = tpl.status === 'validated' && tpl.created_by !== user?.id;

              return (
                <div key={tpl.id} className="card">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-medium">{tpl.template_name}</p>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusBadge(tpl.status)}`}>
                          {tpl.status}
                        </span>
                        <span className="text-xs text-gray-500">v{tpl.version}</span>
                      </div>
                      <p className="text-sm text-gray-400 capitalize">
                        {tpl.crop_type} • {tpl.stage_definitions?.length || 0} stages
                      </p>
                      {tpl.approved_by && tpl.approved_at && (
                        <p className="text-xs text-gray-500 mt-1">
                          Approved: {new Date(tpl.approved_at).toLocaleDateString()}
                        </p>
                      )}
                      {tpl.validation_errors && tpl.validation_errors.length > 0 && (
                        <div className="mt-2">
                          {tpl.validation_errors.map((err, i) => (
                            <p key={i} className="text-xs text-red-400">⚠ {err}</p>
                          ))}
                        </div>
                      )}
                    </div>

                    {flow && (
                      <button
                        onClick={() => handleAction(tpl.id, flow.next)}
                        disabled={acting === tpl.id || (tpl.status === 'validated' && !canApprove)}
                        className={`text-xs px-3 py-1.5 rounded-lg transition font-medium ${
                          tpl.status === 'active'
                            ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                            : 'bg-cultivax-primary/20 text-cultivax-primary hover:bg-cultivax-primary/30'
                        } disabled:opacity-40 disabled:cursor-not-allowed`}
                        title={tpl.status === 'validated' && !canApprove ? 'Cannot approve your own template' : ''}
                      >
                        {acting === tpl.id ? '...' : `${flow.icon} ${flow.label}`}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {actionApi.error && (
          <div className="card border-red-500/30 bg-red-500/10">
            <p className="text-red-400 text-sm">{actionApi.error}</p>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
