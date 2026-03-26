'use client';

/**
 * Provider Equipment Management Page
 *
 * List, add, and manage equipment inventory.
 */

import { useEffect, useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import DataTable from '@/components/DataTable';
import { useApi } from '@/hooks/useApi';

interface Equipment {
  id: string;
  equipment_name: string;
  equipment_type: string;
  daily_rate: number;
  status: string;
  condition?: string;
}

export default function ProviderEquipmentPage() {
  const equipmentApi = useApi<Equipment[]>();
  const addApi = useApi<Equipment>();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    equipment_name: '',
    equipment_type: 'Tractor',
    daily_rate: '',
    condition: 'Good',
  });

  useEffect(() => {
    equipmentApi.execute('/api/v1/equipment').catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await addApi.execute('/api/v1/equipment', {
        method: 'POST',
        body: {
          ...form,
          daily_rate: parseFloat(form.daily_rate),
        },
      });
      setShowForm(false);
      setForm({ equipment_name: '', equipment_type: 'Tractor', daily_rate: '', condition: 'Good' });
      equipmentApi.execute('/api/v1/equipment').catch(() => {});
    } catch {}
  };

  const items = equipmentApi.data || [];

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Equipment Management</h1>
            <p className="text-gray-400 mt-1">Manage your equipment inventory</p>
          </div>
          <button className="btn-primary text-sm" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ Add Equipment'}
          </button>
        </div>

        {/* Add Form */}
        {showForm && (
          <form onSubmit={handleSubmit} className="card space-y-4">
            <h3 className="font-semibold">Add New Equipment</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Name</label>
                <input
                  type="text"
                  value={form.equipment_name}
                  onChange={(e) => setForm({ ...form, equipment_name: e.target.value })}
                  placeholder="e.g., John Deere 5310"
                  className="w-full text-sm"
                  required
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Type</label>
                <select
                  value={form.equipment_type}
                  onChange={(e) => setForm({ ...form, equipment_type: e.target.value })}
                  className="w-full text-sm"
                >
                  <option value="Tractor">Tractor</option>
                  <option value="Harvester">Harvester</option>
                  <option value="Sprayer">Sprayer</option>
                  <option value="Planter">Planter</option>
                  <option value="Irrigation">Irrigation System</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Daily Rate (₹)</label>
                <input
                  type="number"
                  value={form.daily_rate}
                  onChange={(e) => setForm({ ...form, daily_rate: e.target.value })}
                  placeholder="1500"
                  className="w-full text-sm"
                  required
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Condition</label>
                <select
                  value={form.condition}
                  onChange={(e) => setForm({ ...form, condition: e.target.value })}
                  className="w-full text-sm"
                >
                  <option value="Excellent">Excellent</option>
                  <option value="Good">Good</option>
                  <option value="Fair">Fair</option>
                </select>
              </div>
            </div>
            <button type="submit" className="btn-primary text-sm" disabled={addApi.loading}>
              {addApi.loading ? 'Adding...' : 'Add Equipment'}
            </button>
            {addApi.error && <p className="text-red-400 text-sm">{addApi.error}</p>}
          </form>
        )}

        {/* Equipment List */}
        {equipmentApi.loading && (
          <div className="card text-center py-8">
            <div className="inline-block w-8 h-8 border-2 border-cultivax-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!equipmentApi.loading && items.length === 0 && (
          <div className="card text-center py-12 text-gray-500">
            <p className="text-5xl mb-4">🚜</p>
            <p className="text-lg font-medium">No equipment listed</p>
            <p className="text-sm mt-1">Add your first equipment to the inventory</p>
          </div>
        )}

        {items.length > 0 && (
          <div className="space-y-3">
            {items.map((eq) => (
              <div key={eq.id} className="card flex items-center justify-between">
                <div>
                  <p className="font-medium">{eq.equipment_name}</p>
                  <p className="text-sm text-gray-400">
                    {eq.equipment_type} • {eq.condition || 'Good'} • ₹{eq.daily_rate}/day
                  </p>
                </div>
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                  eq.status === 'Available' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                }`}>
                  {eq.status || 'Available'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
