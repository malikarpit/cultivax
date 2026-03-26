'use client';

/**
 * Labor Management Page
 *
 * CRUD for labor entries linked to crop instances.
 * GET/POST/PUT/DELETE /api/v1/labor
 */

import { useEffect, useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useApi } from '@/hooks/useApi';

interface LaborEntry {
  id: string;
  worker_name: string;
  task_type: string;
  hours_worked: number;
  daily_wage: number;
  work_date: string;
  crop_instance_id?: string;
  notes?: string;
}

interface LaborResponse {
  data: LaborEntry[];
  meta: { total: number; page: number; per_page: number };
}

export default function LaborManagementPage() {
  const laborApi = useApi<LaborResponse>();
  const addApi = useApi<LaborEntry>();
  const deleteApi = useApi();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    worker_name: '',
    task_type: 'Harvesting',
    hours_worked: '',
    daily_wage: '',
    work_date: new Date().toISOString().split('T')[0],
    notes: '',
  });

  useEffect(() => {
    laborApi.execute('/api/v1/labor').catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await addApi.execute('/api/v1/labor', {
        method: 'POST',
        body: {
          ...form,
          hours_worked: parseFloat(form.hours_worked),
          daily_wage: parseFloat(form.daily_wage),
          notes: form.notes || undefined,
        },
      });
      setShowForm(false);
      setForm({ worker_name: '', task_type: 'Harvesting', hours_worked: '', daily_wage: '', work_date: new Date().toISOString().split('T')[0], notes: '' });
      laborApi.execute('/api/v1/labor').catch(() => {});
    } catch {}
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteApi.execute(`/api/v1/labor/${id}`, { method: 'DELETE' });
      laborApi.execute('/api/v1/labor').catch(() => {});
    } catch {}
  };

  const entries = laborApi.data?.data || [];
  const totalCost = entries.reduce((sum, e) => sum + (e.daily_wage * (e.hours_worked / 8)), 0);

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Labor Management</h1>
            <p className="text-gray-400 mt-1">Track workers and expenses</p>
          </div>
          <button className="btn-primary text-sm" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ Add Entry'}
          </button>
        </div>

        {/* Cost Summary */}
        {entries.length > 0 && (
          <div className="card flex items-center gap-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-cultivax-primary">{entries.length}</p>
              <p className="text-sm text-gray-400">Entries</p>
            </div>
            <div className="w-px h-10 bg-cultivax-card" />
            <div className="text-center">
              <p className="text-3xl font-bold text-yellow-400">₹{totalCost.toFixed(0)}</p>
              <p className="text-sm text-gray-400">Total Cost</p>
            </div>
            <div className="w-px h-10 bg-cultivax-card" />
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-400">
                {entries.reduce((sum, e) => sum + e.hours_worked, 0).toFixed(1)}
              </p>
              <p className="text-sm text-gray-400">Total Hours</p>
            </div>
          </div>
        )}

        {/* Add Form */}
        {showForm && (
          <form onSubmit={handleSubmit} className="card space-y-4">
            <h3 className="font-semibold">Add Labor Entry</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Worker Name</label>
                <input
                  type="text"
                  value={form.worker_name}
                  onChange={(e) => setForm({ ...form, worker_name: e.target.value })}
                  placeholder="Ramesh Kumar"
                  className="w-full text-sm"
                  required
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Task Type</label>
                <select
                  value={form.task_type}
                  onChange={(e) => setForm({ ...form, task_type: e.target.value })}
                  className="w-full text-sm"
                >
                  <option value="Harvesting">Harvesting</option>
                  <option value="Sowing">Sowing</option>
                  <option value="Irrigation">Irrigation</option>
                  <option value="Weeding">Weeding</option>
                  <option value="Spraying">Spraying</option>
                  <option value="Transport">Transport</option>
                  <option value="General">General</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Hours Worked</label>
                <input type="number" step="0.5" value={form.hours_worked}
                  onChange={(e) => setForm({ ...form, hours_worked: e.target.value })}
                  placeholder="8" className="w-full text-sm" required />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Daily Wage (₹)</label>
                <input type="number" value={form.daily_wage}
                  onChange={(e) => setForm({ ...form, daily_wage: e.target.value })}
                  placeholder="500" className="w-full text-sm" required />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Work Date</label>
                <input type="date" value={form.work_date}
                  onChange={(e) => setForm({ ...form, work_date: e.target.value })}
                  className="w-full text-sm" required />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Notes</label>
                <input type="text" value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  placeholder="Optional notes" className="w-full text-sm" />
              </div>
            </div>
            <button type="submit" className="btn-primary text-sm" disabled={addApi.loading}>
              {addApi.loading ? 'Adding...' : 'Add Entry'}
            </button>
            {addApi.error && <p className="text-red-400 text-sm">{addApi.error}</p>}
          </form>
        )}

        {/* Entries */}
        {laborApi.loading && (
          <div className="card text-center py-8">
            <div className="inline-block w-8 h-8 border-2 border-cultivax-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!laborApi.loading && entries.length === 0 && (
          <div className="card text-center py-12 text-gray-500">
            <p className="text-5xl mb-4">👷</p>
            <p className="text-lg font-medium">No labor entries</p>
            <p className="text-sm mt-1">Start tracking your workforce</p>
          </div>
        )}

        {entries.length > 0 && (
          <div className="space-y-2">
            {entries.map((entry) => (
              <div key={entry.id} className="card flex items-center justify-between">
                <div>
                  <p className="font-medium">{entry.worker_name}</p>
                  <p className="text-sm text-gray-400">
                    {entry.task_type} • {entry.hours_worked}h • ₹{entry.daily_wage}/day •{' '}
                    {new Date(entry.work_date).toLocaleDateString()}
                  </p>
                  {entry.notes && <p className="text-xs text-gray-500 mt-1">{entry.notes}</p>}
                </div>
                <button
                  onClick={() => handleDelete(entry.id)}
                  className="text-xs text-red-400 hover:text-red-300 px-3 py-1.5 rounded-lg hover:bg-red-500/10 transition"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
