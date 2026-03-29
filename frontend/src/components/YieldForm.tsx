'use client';

/**
 * Yield Form Component
 *
 * Form for farmers to submit harvest yield data.
 * Fields from MSDD 1.12 — Yield Verification:
 * - Yield quantity (kg/acre)
 * - Quality grade
 * - Harvest date
 * - Moisture content
 * - Notes
 */

import { useState } from 'react';

interface YieldFormProps {
  cropId: string;
  cropType: string;
  landArea: number;
  onSubmit: (data: YieldData) => Promise<void>;
  onCancel: () => void;
}

interface YieldData {
  yield_quantity_kg: number;
  quality_grade: string;
  harvest_date: string;
  moisture_content_pct: number;
  notes: string;
}

const QUALITY_GRADES = [
  { value: 'A', label: 'Grade A — Premium (Export Quality)' },
  { value: 'B', label: 'Grade B — Standard (Market Quality)' },
  { value: 'C', label: 'Grade C — Below Average' },
  { value: 'D', label: 'Grade D — Poor / Damaged' },
];

export default function YieldForm({ cropId, cropType, landArea, onSubmit, onCancel }: YieldFormProps) {
  const [formData, setFormData] = useState<YieldData>({
    yield_quantity_kg: 0,
    quality_grade: 'B',
    harvest_date: new Date().toISOString().split('T')[0],
    moisture_content_pct: 12,
    notes: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const yieldPerAcre = landArea > 0 ? (formData.yield_quantity_kg / landArea).toFixed(0) : '—';

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: ['yield_quantity_kg', 'moisture_content_pct'].includes(name) ? Number(value) : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.yield_quantity_kg <= 0) {
      setError('Yield quantity must be greater than 0');
      return;
    }
    if (formData.moisture_content_pct < 0 || formData.moisture_content_pct > 100) {
      setError('Moisture content must be between 0% and 100%');
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit(formData);
    } catch (err: any) {
      setError(err.message || 'Failed to submit yield');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="card space-y-6">
      <div>
        <h3 className="text-lg font-semibold">🌾 Submit Harvest Yield</h3>
        <p className="text-sm text-gray-500 mt-1">
          Crop: <span className="capitalize font-medium text-gray-700">{cropType}</span>
          {landArea > 0 && <> · {landArea} acres</>}
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          ⚠️ {error}
        </div>
      )}

      {/* Yield Quantity */}
      <div>
        <label htmlFor="yield_quantity_kg" className="block text-sm font-medium text-gray-700 mb-1">
          Total Yield (kg) *
        </label>
        <input
          type="number"
          id="yield_quantity_kg"
          name="yield_quantity_kg"
          value={formData.yield_quantity_kg || ''}
          onChange={handleChange}
          placeholder="Enter total yield in kilograms"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cultivax-primary focus:border-transparent"
          min="0"
          step="0.1"
          required
        />
        {formData.yield_quantity_kg > 0 && landArea > 0 && (
          <p className="text-xs text-gray-500 mt-1">
            ≈ {yieldPerAcre} kg/acre
          </p>
        )}
      </div>

      {/* Quality Grade */}
      <div>
        <label htmlFor="quality_grade" className="block text-sm font-medium text-gray-700 mb-1">
          Quality Grade *
        </label>
        <select
          id="quality_grade"
          name="quality_grade"
          value={formData.quality_grade}
          onChange={handleChange}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cultivax-primary focus:border-transparent"
        >
          {QUALITY_GRADES.map((g) => (
            <option key={g.value} value={g.value}>
              {g.label}
            </option>
          ))}
        </select>
      </div>

      {/* Harvest Date */}
      <div>
        <label htmlFor="harvest_date" className="block text-sm font-medium text-gray-700 mb-1">
          Harvest Date *
        </label>
        <input
          type="date"
          id="harvest_date"
          name="harvest_date"
          value={formData.harvest_date}
          onChange={handleChange}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cultivax-primary focus:border-transparent"
          required
        />
      </div>

      {/* Moisture Content */}
      <div>
        <label htmlFor="moisture_content_pct" className="block text-sm font-medium text-gray-700 mb-1">
          Moisture Content (%)
        </label>
        <input
          type="number"
          id="moisture_content_pct"
          name="moisture_content_pct"
          value={formData.moisture_content_pct}
          onChange={handleChange}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cultivax-primary focus:border-transparent"
          min="0"
          max="100"
          step="0.1"
        />
        <p className="text-xs text-gray-500 mt-1">
          Optimal: Wheat 12%, Rice 14-20%, Cotton 8%
        </p>
      </div>

      {/* Notes */}
      <div>
        <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
          Notes (optional)
        </label>
        <textarea
          id="notes"
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          rows={3}
          placeholder="Any observations about the harvest..."
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cultivax-primary focus:border-transparent resize-none"
        />
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          disabled={submitting}
          className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Submitting...
            </span>
          ) : (
            '✅ Submit Yield'
          )}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
