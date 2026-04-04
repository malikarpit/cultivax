'use client';

import React, { useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useFetch } from '@/hooks/useFetch';
import { useApi } from '@/hooks/useApi';
import {
  BrainCircuit, Activity, Zap, Shield, Play, Square, MessageSquare, Database, LineChart, Star, Loader2, AlertTriangle
} from 'lucide-react';
import clsx from 'clsx';
import { toast } from 'sonner';

export default function MLModelsAdminPage() {
  const [activeTab, setActiveTab] = useState<'registry'|'feedback'|'training'>('registry');

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="animate-fade-in max-w-7xl mx-auto py-8 space-y-8">
        
        {/* Header Block */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-m3-on-surface flex items-center gap-3">
              <BrainCircuit className="w-8 h-8 text-cultivax-primary" />
              Machine Learning Governance
            </h1>
            <p className="text-m3-on-surface-variant mt-2 max-w-2xl">
              Control dynamic endpoints mapping Risk Analytics exactly across Versioning bounds, fallback paths, and prediction loops.
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex gap-2 border-b border-m3-outline-variant/30 pb-px overflow-x-auto custom-scrollbar">
          <button
            onClick={() => setActiveTab('registry')}
            className={clsx(
              "px-6 py-3 font-bold text-sm border-b-2 transition-all whitespace-nowrap flex items-center gap-2 flex-shrink-0",
              activeTab === 'registry' 
                ? "border-cultivax-primary text-cultivax-primary" 
                : "border-transparent text-m3-on-surface-variant hover:text-m3-on-surface hover:bg-m3-surface-container/50 rounded-t-xl"
            )}
          >
            <Activity className="w-4 h-4" /> Model Registry
          </button>
          <button
            onClick={() => setActiveTab('feedback')}
            className={clsx(
              "px-6 py-3 font-bold text-sm border-b-2 transition-all whitespace-nowrap flex items-center gap-2 flex-shrink-0",
              activeTab === 'feedback' 
                ? "border-cultivax-primary text-cultivax-primary" 
                : "border-transparent text-m3-on-surface-variant hover:text-m3-on-surface hover:bg-m3-surface-container/50 rounded-t-xl"
            )}
          >
            <MessageSquare className="w-4 h-4" /> Farmer Feedback
          </button>
          <button
            onClick={() => setActiveTab('training')}
            className={clsx(
              "px-6 py-3 font-bold text-sm border-b-2 transition-all whitespace-nowrap flex items-center gap-2 flex-shrink-0",
              activeTab === 'training' 
                ? "border-cultivax-primary text-cultivax-primary" 
                : "border-transparent text-m3-on-surface-variant hover:text-m3-on-surface hover:bg-m3-surface-container/50 rounded-t-xl"
            )}
          >
            <Database className="w-4 h-4" /> Training Audits
          </button>
        </div>

        {/* Tab Content */}
        <div className="pt-2">
          {activeTab === 'registry' && <RegistryTab />}
          {activeTab === 'feedback' && <FeedbackTab />}
          {activeTab === 'training' && <TrainingTab />}
        </div>
        
      </div>
    </ProtectedRoute>
  );
}

function RegistryTab() {
  const api = useApi();
  const { data: models, loading, refetch } = useFetch('/api/v1/ml/models?active_only=false');

  const handleToggle = async (id: string, is_active: boolean) => {
    try {
      const endpoint = is_active ? `/admin/ml/models/${id}/deactivate` : `/admin/ml/models/${id}/activate`;
      // Note: Actually the endpoint we built was /api/v1/ml/models/{id}/activate without /admin/ prefix (but secured via dependencies)
      // I will adjust to the correct route mapping
      await api.execute(`/ml/models/${id}/${is_active ? 'deactivate' : 'activate'}`, { method: 'POST' });
      toast.success(`Model successfully ${is_active ? 'deactivated' : 'activated'}`);
      refetch();
    } catch(err: any) {
      toast.error(err.message || 'Operation failed');
    }
  }

  if (loading) return <LoadingBlock text="Scanning Registry..." />

  return (
    <div className="glass-card rounded-2xl border border-m3-outline-variant/30 overflow-hidden">
      <div className="p-4 bg-m3-surface-container-low border-b border-m3-outline-variant/30 flex justify-between items-center">
        <h3 className="font-bold text-m3-on-surface flex items-center gap-2">
          <Shield className="w-5 h-5 text-cultivax-primary" /> Active Deployments
        </h3>
        <span className="text-xs font-mono text-m3-on-surface-variant bg-m3-surface-container-high px-3 py-1 rounded-full">
          Total: {models?.length || 0}
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-m3-surface-container-highest/30 text-m3-on-surface-variant text-xs uppercase tracking-wider">
              <th className="p-4 font-semibold">Registration Status</th>
              <th className="p-4 font-semibold">Model Identification</th>
              <th className="p-4 font-semibold">Evaluation Metrics</th>
              <th className="p-4 font-semibold text-right">Overrides</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-m3-outline-variant/10 text-sm">
            {models?.map((model: any) => (
              <tr key={model.id} className="hover:bg-m3-surface-container-lowest/50 group transition-colors">
                <td className="p-4">
                  {model.is_active || model.status === 'active' ? (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-green-500/10 text-green-500 text-xs font-bold uppercase tracking-wide border border-green-500/20">
                      <Zap className="w-3 h-3" /> Active
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-m3-surface-container-highest text-m3-on-surface-variant text-xs font-bold uppercase tracking-wide">
                      <Square className="w-3 h-3" /> Draft
                    </span>
                  )}
                </td>
                <td className="p-4 font-mono">
                  <div className="font-bold text-m3-on-surface text-base">{model.model_name}</div>
                  <div className="text-xs text-m3-on-surface-variant opacity-70">Type: {model.model_type} | v{model.version}</div>
                </td>
                <td className="p-4 text-xs font-mono text-m3-on-surface-variant">
                  {model.metrics ? (
                    <div className="space-y-1">
                      {Object.entries(model.metrics).map(([key, val]) => (
                        <div key={key}><span className="opacity-60">{key}:</span> <span className="text-cultivax-primary font-bold">{String(val)}</span></div>
                      ))}
                    </div>
                  ) : 'N/A'}
                </td>
                <td className="p-4 text-right">
                  <button
                    onClick={() => handleToggle(model.id, model.is_active || model.status === 'active')}
                    disabled={api.loading}
                    className={clsx(
                      "px-4 py-2 font-bold text-xs rounded-xl border transition-all inline-flex items-center gap-2",
                      (model.is_active || model.status === 'active') 
                        ? "border-red-500/30 text-red-500 hover:bg-red-500/10" 
                        : "border-cultivax-primary/50 text-cultivax-primary hover:bg-cultivax-primary/10"
                    )}
                  >
                    {model.is_active || model.status === 'active' ? <Square className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                    {model.is_active || model.status === 'active' ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
            {(!models || models.length === 0) && (
              <tr>
                <td colSpan={4} className="p-8 text-center text-m3-on-surface-variant opacity-70">
                  No models registered yet. Database fallback active.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FeedbackTab() {
  const { data: feedback, loading } = useFetch('/api/v1/ml/feedback');
  if (loading) return <LoadingBlock text="Loading field feedback..." />

  return (
    <div className="glass-card rounded-2xl border border-m3-outline-variant/30 overflow-hidden">
      <div className="p-4 bg-m3-surface-container-low border-b border-m3-outline-variant/30">
        <h3 className="font-bold text-m3-on-surface flex items-center gap-2">
          <Star className="w-5 h-5 text-cultivax-secondary" /> Field Feedback Streams
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm border-collapse">
          <thead>
            <tr className="bg-m3-surface-container-highest/30 text-m3-on-surface-variant text-xs uppercase tracking-wider">
              <th className="p-4">Crop Target</th>
              <th className="p-4">Prediction Data</th>
              <th className="p-4">Alignment</th>
              <th className="p-4">Farmer Output</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-m3-outline-variant/10">
            {feedback?.map((fb: any) => (
               <tr key={fb.id} className="hover:bg-m3-surface-container-lowest/50">
                 <td className="p-4 font-mono text-xs">{fb.crop_instance_id.split('-')[0]}</td>
                 <td className="p-4">
                    <div className="text-xs mb-1"><span className="opacity-60 font-mono text-[10px]">PRED ID:</span> {fb.prediction_id}</div>
                    <div className="text-xs"><span className="opacity-60 font-mono text-[10px]">CONF:</span> {(fb.original_confidence * 100).toFixed(1)}%</div>
                 </td>
                 <td className="p-4 font-bold uppercase text-xs tracking-wider">
                   {fb.feedback_type === 'confirmed' ? (
                     <span className="text-green-500 block">Confirmed</span>
                   ) : fb.feedback_type === 'rejected' ? (
                     <span className="text-red-500 block">Rejected</span>
                   ) : (
                     <span className="text-amber-500 block">Partial</span>
                   )}
                 </td>
                 <td className="p-4">
                   <div className="text-m3-on-surface italic text-xs mb-1">"{fb.farmer_notes || fb.reason || 'No additional notes'}"</div>
                   <div className="text-[10px] text-m3-on-surface-variant">{new Date(fb.created_at).toLocaleString()}</div>
                 </td>
               </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function TrainingTab() {
  const { data: audits, loading } = useFetch('/api/v1/ml/training-audits');
  if (loading) return <LoadingBlock text="Fetching training lineage..." />

  return (
    <div className="glass-card rounded-2xl border border-m3-outline-variant/30 overflow-hidden">
      <div className="p-4 bg-m3-surface-container-low border-b border-m3-outline-variant/30">
        <h3 className="font-bold text-m3-on-surface flex items-center gap-2">
          <LineChart className="w-5 h-5 text-blue-500" /> Training Lineage
        </h3>
      </div>
      <div className="overflow-x-auto p-0">
        <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="bg-m3-surface-container-highest/30 text-m3-on-surface-variant text-xs uppercase tracking-wider">
                <th className="p-4">Execution Target</th>
                <th className="p-4">Dataset Volumes</th>
                <th className="p-4">Final Accuracy / Loss</th>
                <th className="p-4">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-m3-outline-variant/10">
              {audits?.map((t: any) => (
                 <tr key={t.id} className="hover:bg-m3-surface-container-lowest/50">
                    <td className="p-4 font-mono text-xs">{t.model_id}</td>
                    <td className="p-4 font-bold text-cultivax-primary">{t.dataset_size.toLocaleString()} samples</td>
                    <td className="p-4 font-mono">
                      <span className="text-green-400">ACC: {t.accuracy?.toFixed(3) || 'N/A'}</span> <br/>
                      <span className="text-red-400 text-xs">LOSS: {t.loss?.toFixed(3) || 'N/A'}</span>
                    </td>
                    <td className="p-4 flex items-center gap-2 text-xs text-m3-on-surface-variant font-mono">
                       {new Date(t.created_at).toLocaleString()}
                    </td>
                 </tr>
              ))}
            </tbody>
        </table>
      </div>
    </div>
  )
}

function LoadingBlock({ text }: { text: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 opacity-60">
       <Loader2 className="w-10 h-10 animate-spin text-cultivax-primary mb-4" />
       <p className="font-mono text-sm">{text}</p>
    </div>
  )
}
