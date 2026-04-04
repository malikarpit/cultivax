'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiPost } from '@/lib/api';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Briefcase, MapPin, Wrench, Sprout, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function ProviderOnboardingPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const [formData, setFormData] = useState({
    business_name: '',
    service_type: 'equipment_rental',
    region: '',
    sub_region: '',
    service_radius_km: 50,
    crop_specializations: '',
    description: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Convert comma separated string to array for backend
      const payload = {
        ...formData,
        crop_specializations: formData.crop_specializations
          ? formData.crop_specializations.split(',').map(s => s.trim())
          : []
      };

      await apiPost('/api/v1/providers/onboard', payload);
      setSuccess(true);
      
      // Navigate to dashboard after short delay
      setTimeout(() => {
        router.push('/provider');
        router.refresh();
      }, 2000);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit application');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="max-w-2xl mx-auto py-8 animate-fade-in">
        
        {success ? (
          <div className="card text-center py-16 px-6">
            <CheckCircle2 className="w-16 h-16 text-cultivax-green mx-auto mb-4" />
            <h1 className="text-2xl font-bold mb-2">Welcome to the Marketplace!</h1>
            <p className="text-cultivax-text-secondary mb-6">Your provider profile has been created successfully. Redirecting to your new dashboard...</p>
          </div>
        ) : (
          <>
            <div className="mb-8 text-center">
              <h1 className="text-3xl font-bold mb-2">Become a Provider</h1>
              <p className="text-cultivax-text-secondary">Join the CultivaX network and offer your services to farmers.</p>
            </div>

            <form onSubmit={handleSubmit} className="card p-6 space-y-6">
              {error && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              {/* Business Name */}
              <div>
                <label className="block text-sm font-medium mb-1">Business Name (Optional)</label>
                <div className="relative">
                  <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
                  <input
                    type="text"
                    required
                    value={formData.business_name}
                    onChange={(e) => setFormData({...formData, business_name: e.target.value})}
                    placeholder="E.g., Green Valley Tech"
                    className="!pl-10 w-full"
                  />
                </div>
              </div>

              {/* Service Type */}
              <div>
                <label className="block text-sm font-medium mb-1">Primary Service Type</label>
                <div className="relative">
                  <Wrench className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
                  <select
                    required
                    value={formData.service_type}
                    onChange={(e) => setFormData({...formData, service_type: e.target.value})}
                    className="!pl-10 w-full"
                  >
                    <option value="equipment_rental">Equipment Rental</option>
                    <option value="soil_testing">Soil Testing</option>
                    <option value="drone_survey">Drone Survey</option>
                    <option value="pest_control">Pest Control</option>
                    <option value="harvest_labor">Harvest Labor</option>
                    <option value="logistics">Logistics & Transport</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Region */}
                <div>
                  <label className="block text-sm font-medium mb-1">Region (State)</label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
                    <input
                      type="text"
                      required
                      value={formData.region}
                      onChange={(e) => setFormData({...formData, region: e.target.value})}
                      placeholder="e.g., Punjab"
                      className="!pl-10 w-full"
                    />
                  </div>
                </div>

                {/* Sub Region */}
                <div>
                  <label className="block text-sm font-medium mb-1">Sub Region (District)</label>
                  <input
                    type="text"
                    required
                    value={formData.sub_region}
                    onChange={(e) => setFormData({...formData, sub_region: e.target.value})}
                    placeholder="e.g., Ludhiana"
                    className="w-full"
                  />
                </div>
              </div>

              {/* Radius */}
              <div>
                <label className="block text-sm font-medium mb-1">Service Radius (km)</label>
                <input
                  type="number"
                  min="1"
                  required
                  value={formData.service_radius_km}
                  onChange={(e) => setFormData({...formData, service_radius_km: Number(e.target.value)})}
                  className="w-full"
                />
              </div>

              {/* Crop Specializations */}
              <div>
                <label className="block text-sm font-medium mb-1">Crop Specializations (Comma separated)</label>
                <div className="relative">
                  <Sprout className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
                  <input
                    type="text"
                    value={formData.crop_specializations}
                    onChange={(e) => setFormData({...formData, crop_specializations: e.target.value})}
                    placeholder="e.g., Wheat, Rice, Sugarcane"
                    className="!pl-10 w-full"
                  />
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium mb-1">Business Description</label>
                <textarea
                  rows={4}
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Describe your capabilities, experience, and equipment..."
                  className="w-full"
                />
              </div>

              <button type="submit" disabled={loading} className="btn-primary w-full">
                {loading ? 'Submitting...' : (
                  <>Register as Provider <ArrowRight className="w-4 h-4 ml-2" /></>
                )}
              </button>
            </form>
          </>
        )}
      </div>
    </ProtectedRoute>
  );
}
