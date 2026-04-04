'use client';

/**
 * Labor Management & Discovery Page
 * 
 * Available crews, verified workers, and labor booking for Farmers.
 * Inline Labor inventory modifications for Providers.
 */

import { useState, useEffect } from 'react';
import {
  Users, MapPin, Star, Clock, Shield, Phone, ArrowRight, X, UserPlus, CheckCircle2
} from 'lucide-react';
import clsx from 'clsx';
import ProtectedRoute from '@/components/ProtectedRoute';
import Badge from '@/components/Badge';
import TrustRing from '@/components/TrustRing';
import { useAuth } from '@/context/AuthContext';
import { useApi } from '@/hooks/useApi';
import Link from 'next/link';

interface LaborListing {
  id: string;
  provider_id: string;
  provider_name?: string;
  provider_trust_score?: number;
  labor_type: string;
  description: string;
  available_units: number;
  daily_rate: number;
  hourly_rate?: number;
  region: string;
  sub_region?: string;
  is_available: boolean;
  is_flagged: boolean;
}

export default function LaborPage() {
  const { user } = useAuth();
  const laborApi = useApi<{ items: LaborListing[]; total: number }>();
  const addLaborApi = useApi();
  const toggleApi = useApi();
  const deleteApi = useApi();
  
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    labor_type: 'harvesting_crew',
    description: '',
    available_units: 1,
    daily_rate: '',
    hourly_rate: '',
    region: 'Punjab',
    sub_region: '',
  });

  const loadData = () => {
    laborApi.execute('/api/v1/labor').catch(() => {});
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user?.id) return;
    try {
      await addLaborApi.execute('/api/v1/labor', {
        method: 'POST',
        body: {
          ...form,
          available_units: parseInt(form.available_units.toString()),
          daily_rate: form.daily_rate ? parseFloat(form.daily_rate) : 0,
          hourly_rate: form.hourly_rate ? parseFloat(form.hourly_rate) : 0,
        },
      });
      setShowForm(false);
      setForm({
        labor_type: 'harvesting_crew', description: '', available_units: 1,
        daily_rate: '', hourly_rate: '', region: 'Punjab', sub_region: ''
      });
      loadData();
    } catch {}
  };

  const toggleAvailability = async (id: string, current: boolean) => {
    try {
      await toggleApi.execute(`/api/v1/labor/${id}/availability`, {
        method: 'PATCH',
        body: { is_available: !current }
      });
      loadData();
    } catch {}
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to remove this labor listing?')) return;
    try {
      await deleteApi.execute(`/api/v1/labor/${id}`, { method: 'DELETE' });
      loadData();
    } catch {}
  };

  const isProvider = user?.role === 'provider' || user?.role === 'admin';
  const rawListings = laborApi.data?.items || [];
  
  // Providers only see their own on this page if we filter, or they see global?
  // Let's filter client-side for now for providers so they manage their own, 
  // but see all if admin. Farmers see all available.
  const displayListings = isProvider && user?.role !== 'admin' 
    ? rawListings.filter(l => l.provider_id === user.id) 
    : rawListings;

  return (
    <ProtectedRoute>
    <div className="animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Users className="w-6 h-6 text-cultivax-primary" /> {isProvider ? 'My Labor Logistics' : 'Labor Marketplace'}
          </h1>
          <p className="text-sm text-cultivax-text-muted mt-1">
            {isProvider ? 'Manage and post your active harvest crews' : 'Find and manage harvest labor crews'}
          </p>
        </div>
        {isProvider && (
           <button 
             onClick={() => setShowForm(!showForm)}
             className="btn-primary flex items-center gap-2 w-fit"
           >
             {showForm ? <X className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
             {showForm ? 'Cancel' : 'Post Labor'}
           </button>
        )}
      </div>

      {showForm && isProvider && (
        <form onSubmit={handleSubmit} className="card space-y-4 mb-6 border-cultivax-primary/30">
          <h3 className="font-semibold text-lg flex items-center gap-2"><CheckCircle2 className="w-5 h-5 text-cultivax-primary" /> New Labor Listing</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Labor Type</label>
              <select
                value={form.labor_type}
                onChange={(e) => setForm({ ...form, labor_type: e.target.value })}
                className="w-full text-sm"
              >
                <option value="harvesting_crew">Harvesting Crew</option>
                <option value="irrigation_worker">Irrigation Worker</option>
                <option value="spraying_team">Spraying Team</option>
                <option value="general_farm_labor">General Farm Labor</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Region</label>
              <input
                type="text"
                value={form.region}
                onChange={(e) => setForm({ ...form, region: e.target.value })}
                placeholder="e.g. Punjab"
                className="w-full text-sm"
                required
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Daily Rate (₹)</label>
              <input
                type="number"
                value={form.daily_rate}
                onChange={(e) => setForm({ ...form, daily_rate: e.target.value })}
                placeholder="650"
                className="w-full text-sm"
                required
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Crew Size (Workers)</label>
              <input
                type="number"
                min="1"
                value={form.available_units}
                onChange={(e) => setForm({ ...form, available_units: parseInt(e.target.value) })}
                className="w-full text-sm"
                required
              />
            </div>
            <div className="md:col-span-2">
              <label className="text-xs text-gray-400 block mb-1">Description</label>
              <input
                type="text"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Experienced crew skilled in wheat cutting..."
                className="w-full text-sm"
                required
              />
            </div>
          </div>
          <button type="submit" className="btn-primary text-sm" disabled={addLaborApi.loading}>
            {addLaborApi.loading ? 'Posting...' : 'Publish Listing'}
          </button>
        </form>
      )}

      {/* Stats Row format only for Farmers or general marketplace viewers */}
      {!isProvider && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
          <div className="card-stat">
            <p className="text-xs text-cultivax-text-muted mb-1">Available Today</p>
            <p className="text-2xl font-bold">{displayListings.length}</p>
            <p className="text-xs text-cultivax-text-muted">crews targeting you</p>
          </div>
          <div className="card-stat">
            <p className="text-xs text-cultivax-text-muted mb-1">Total Workers</p>
            <p className="text-2xl font-bold">{displayListings.reduce((acc, c) => acc + c.available_units, 0)}</p>
            <p className="text-xs text-cultivax-text-muted">active in region</p>
          </div>
        </div>
      )}

      {/* Logic Cards */}
      <div className="space-y-4">
        {laborApi.loading && (
          <div className="text-center py-12 text-cultivax-text-muted">Loading providers...</div>
        )}
        {!laborApi.loading && displayListings.length === 0 && (
          <div className="card text-center py-12 text-gray-500">
             <p className="text-5xl mb-4">🚜</p>
             <p className="text-lg font-medium">No Labor active!</p>
             <p className="text-sm mt-1">{isProvider ? 'Add your first crew' : 'Check back later for harvest teams.'}</p>
          </div>
        )}
        {!laborApi.loading && displayListings.map((crew) => (
          <div key={crew.id} className="card-interactive p-5">
            <div className="flex items-start gap-4">
              <TrustRing score={(crew.provider_trust_score || 0) / 10} size={56} strokeWidth={4} labelFormat="decimal" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-base font-semibold">{crew.provider_name || 'Independent Provider'}</h3>
                  {crew.is_available ? (
                    <Badge variant="green" size="sm" dot>Available</Badge>
                  ) : (
                    <Badge variant="gray" size="sm">Unavailable</Badge>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-cultivax-text-muted mb-3">
                  <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {crew.region}</span>
                  <span className="flex items-center gap-1"><Users className="w-3 h-3" /> {crew.available_units} workers</span>
                  <span className="flex items-center gap-1 uppercase bg-cultivax-elevated px-2 py-0.5 rounded-full"><Clock className="w-3 h-3" /> {crew.labor_type.replace('_', ' ')}</span>
                </div>

                <div className="text-sm text-cultivax-text-secondary mb-3">
                  "{crew.description}"
                </div>

                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pt-3 border-t border-cultivax-border gap-3">
                  <span className="text-sm font-semibold text-cultivax-primary">₹{crew.daily_rate}/day rate</span>
                  
                  {isProvider && crew.provider_id === user?.id ? (
                    <div className="flex items-center gap-2 w-full sm:w-auto">
                      <button
                        onClick={() => toggleAvailability(crew.id, crew.is_available)}
                        className="btn-secondary text-xs flex-1 sm:flex-auto whitespace-nowrap"
                      >
                        Set {crew.is_available ? 'Offline' : 'Online'}
                      </button>
                      <button
                        onClick={() => handleDelete(crew.id)}
                        className="btn-secondary !text-red-400 !border-red-500/20 hover:!bg-red-500/10 text-xs flex-1 sm:flex-auto"
                      >
                        Delete
                      </button>
                    </div>
                  ) : (
                    <Link
                      href={`/services/request?labor=${crew.id}&provider=${crew.provider_id}`}
                      className={clsx(
                        'text-xs font-medium flex items-center gap-1 transition-colors w-full sm:w-auto justify-center sm:justify-start',
                        crew.is_available ? 'text-cultivax-primary hover:text-cultivax-primary-hover' : 'text-cultivax-text-muted pointer-events-none'
                      )}
                    >
                      Request Details <ArrowRight className="w-3 h-3" />
                    </Link>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
    </ProtectedRoute>
  );
}
