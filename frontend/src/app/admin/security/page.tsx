'use client';

import React, { useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useFetch } from '@/hooks/useFetch';
import {
  ShieldAlert, RefreshCw, AlertTriangle, ShieldX, Database, Ban, Activity
} from 'lucide-react';
import clsx from 'clsx';

interface SecurityEvent {
  timestamp: number;
  type: string;
  details: string;
  request_id: string;
  path: string;
  identity: string;
}

function EventIcon({ type }: { type: string }) {
  if (type === 'RATE_LIMIT_EXCEEDED') return <Ban className="w-4 h-4 text-amber-500" />;
  if (type === 'PAYLOAD_TOO_LARGE') return <Database className="w-4 h-4 text-purple-500" />;
  if (type.startsWith('SUSPICIOUS_INPUT')) return <ShieldX className="w-4 h-4 text-red-500" />;
  return <AlertTriangle className="w-4 h-4 text-m3-on-surface-variant" />;
}

function EventRow({ event }: { event: SecurityEvent }) {
  const dateStr = new Date(event.timestamp * 1000).toLocaleString();
  
  return (
    <div className="p-4 border-b border-m3-outline-variant/10 hover:bg-m3-surface-container-highest transition-colors flex flex-col md:flex-row gap-4 justify-between group">
      <div className="flex gap-4 items-start">
        <div className="mt-1 p-2 rounded-full bg-m3-surface">
          <EventIcon type={event.type} />
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={clsx(
              "text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border",
              event.type === 'RATE_LIMIT_EXCEEDED' ? "text-amber-400 bg-amber-500/10 border-amber-500/20" :
              event.type === 'PAYLOAD_TOO_LARGE' ? "text-purple-400 bg-purple-500/10 border-purple-500/20" :
              "text-red-400 bg-red-500/10 border-red-500/20"
            )}>
              {event.type.replace(/_/g, ' ')}
            </span>
            <span className="text-xs text-m3-on-surface-variant font-mono">{dateStr}</span>
          </div>
          <p className="text-sm text-m3-on-surface font-medium mt-1.5">{event.details}</p>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-m3-on-surface-variant opacity-70 group-hover:opacity-100 transition-opacity">
            <span className="font-mono bg-m3-surface-container px-1.5 rounded">Path: {event.path}</span>
            <span className="font-mono bg-m3-surface-container px-1.5 rounded">ID: {event.identity}</span>
            <span className="font-mono bg-m3-surface-container px-1.5 rounded">Req: {event.request_id}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SecurityDashboardPage() {
  const [limit, setLimit] = useState<number>(50);
  const { data, loading, error, refetch } = useFetch<{events: SecurityEvent[], warning?: string}>(`/api/v1/admin/security-events?limit=${limit}`);

  const events = data?.events ?? [];

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="animate-fade-in max-w-6xl mx-auto py-8 space-y-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-m3-on-surface flex items-center gap-3">
              <ShieldAlert className="w-8 h-8 text-red-500" />
              Security Events
            </h1>
            <p className="text-m3-on-surface-variant mt-1 max-w-xl text-sm">
              Live operational visibility into rate limit hits, oversized payloads, and detected injection attempts.
            </p>
          </div>
          <div className="flex items-center gap-3">
             <select
                value={limit}
                onChange={e => setLimit(Number(e.target.value))}
                className="bg-m3-surface border border-m3-outline-variant/30 rounded-xl px-3 py-2 text-sm text-m3-on-surface focus:ring-2 focus:ring-red-500/50"
              >
                <option value={20}>Last 20</option>
                <option value={50}>Last 50</option>
                <option value={100}>Last 100</option>
              </select>
            <button
              onClick={refetch}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 border border-m3-outline-variant/40 rounded-xl hover:bg-m3-surface-container-highest transition-colors disabled:opacity-50"
            >
              <RefreshCw className={clsx('w-4 h-4 text-m3-on-surface', loading && 'animate-spin')} />
              <span className="text-sm font-medium">Refresh</span>
            </button>
          </div>
        </div>

        {data?.warning && (
          <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-400 text-sm flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            {data.warning}
          </div>
        )}

        {/* Console View */}
        <div className="glass-card rounded-2xl border border-m3-outline-variant/30 overflow-hidden bg-m3-surface-container-low shadow-xl">
          <div className="p-4 border-b border-m3-outline-variant/20 bg-m3-surface-container/50 flex items-center gap-2 text-sm font-medium text-m3-on-surface-variant uppercase tracking-wider">
            <Activity className="w-4 h-4 text-red-400" />
            Live Event Buffer (In-Memory)
          </div>
          
          <div className="divide-y divide-m3-outline-variant/10 max-h-[600px] overflow-y-auto">
            {loading && events.length === 0 ? (
              <div className="p-12 text-center text-m3-on-surface-variant flex flex-col items-center gap-3">
                <RefreshCw className="w-6 h-6 animate-spin opacity-50" />
                <p>Loading security stream...</p>
              </div>
            ) : error ? (
              <div className="p-12 text-center text-red-400">
                <p>Failed to load security events. Verify permissions.</p>
              </div>
            ) : events.length === 0 ? (
              <div className="p-12 text-center text-m3-on-surface-variant">
                <ShieldAlert className="w-12 h-12 mx-auto mb-3 opacity-20" />
                <p>No recent security events detected.</p>
                <p className="text-xs mt-1 opacity-60">The buffer relies on in-memory storage and resets on deployment.</p>
              </div>
            ) : (
              events.map((evt, idx) => (
                <EventRow key={`${evt.request_id}-${idx}`} event={evt} />
              ))
            )}
          </div>
        </div>

      </div>
    </ProtectedRoute>
  );
}
