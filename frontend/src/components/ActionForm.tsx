'use client';

import { useState } from 'react';

interface ActionFormProps {
  onSubmit: (data: any) => void;
  loading?: boolean;
}

export default function ActionForm({ onSubmit, loading }: ActionFormProps) {
  const [formData, setFormData] = useState({
    action_type: '',
    action_effective_date: '',
    notes: '',
    metadata: {} as Record<string, string>,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Action Type
        </label>
        <select
          value={formData.action_type}
          onChange={(e) =>
            setFormData({ ...formData, action_type: e.target.value })
          }
          required
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
        >
          <option value="">Select action type</option>
          <option value="irrigation">💧 Irrigation</option>
          <option value="fertilizer">🌿 Fertilizer Application</option>
          <option value="pesticide">🛡️ Pesticide Application</option>
          <option value="weeding">🪴 Weeding</option>
          <option value="inspection">🔍 Field Inspection</option>
          <option value="sowing">🌱 Sowing</option>
          <option value="harvest">🌾 Harvest</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Date of Action
        </label>
        <input
          type="date"
          value={formData.action_effective_date}
          onChange={(e) =>
            setFormData({ ...formData, action_effective_date: e.target.value })
          }
          required
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Notes
        </label>
        <textarea
          value={formData.notes}
          onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
          rows={3}
          placeholder="Optional notes about this action..."
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50"
      >
        {loading ? 'Logging...' : 'Log Action'}
      </button>
    </form>
  );
}
