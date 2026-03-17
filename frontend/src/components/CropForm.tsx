'use client';

import { useState } from 'react';

interface CropFormProps {
  onSubmit: (data: any) => void;
  loading?: boolean;
}

export default function CropForm({ onSubmit, loading }: CropFormProps) {
  const [formData, setFormData] = useState({
    crop_type: '',
    variety: '',
    sowing_date: '',
    region: '',
    sub_region: '',
    land_area: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      land_area: parseFloat(formData.land_area) || 0,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Crop Type
        </label>
        <select
          name="crop_type"
          value={formData.crop_type}
          onChange={handleChange}
          required
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
        >
          <option value="">Select crop type</option>
          <option value="wheat">Wheat</option>
          <option value="rice">Rice</option>
          <option value="cotton">Cotton</option>
          <option value="maize">Maize</option>
          <option value="soybean">Soybean</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Variety
        </label>
        <input
          type="text"
          name="variety"
          value={formData.variety}
          onChange={handleChange}
          required
          placeholder="e.g., HD-2967"
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Sowing Date
        </label>
        <input
          type="date"
          name="sowing_date"
          value={formData.sowing_date}
          onChange={handleChange}
          required
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Region
          </label>
          <input
            type="text"
            name="region"
            value={formData.region}
            onChange={handleChange}
            required
            placeholder="e.g., Punjab"
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Sub-Region
          </label>
          <input
            type="text"
            name="sub_region"
            value={formData.sub_region}
            onChange={handleChange}
            placeholder="e.g., Ludhiana"
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Land Area (hectares)
        </label>
        <input
          type="number"
          name="land_area"
          value={formData.land_area}
          onChange={handleChange}
          required
          step="0.01"
          placeholder="e.g., 2.5"
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Creating...' : 'Create Crop Instance'}
      </button>
    </form>
  );
}
