'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiPost } from '@/lib/api';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Briefcase, MapPin, Wrench, Sprout, ArrowRight, CheckCircle2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function ProviderOnboardingPage() {
  const { t } = useTranslation();
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
            <h1 className="text-2xl font-bold mb-2">{t('provider.onboarding.welcome_to_the_marketplace')}</h1>
            <p className="text-cultivax-text-secondary mb-6">{t('provider.onboarding.your_provider_profile_has')}</p>
          </div>
        ) : (
          <>
            <div className="mb-8 text-center">
              <h1 className="text-3xl font-bold mb-2">{t('provider.onboarding.become_a_provider')}</h1>
              <p className="text-cultivax-text-secondary">{t('provider.onboarding.join_the_cultivax_network')}</p>
            </div>

            <form onSubmit={handleSubmit} className="card p-6 space-y-6">
              {error && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              {/* Business Name */}
              <div>
                <label className="block text-sm font-medium mb-1">{t('provider.onboarding.business_name_optional')}</label>
                <div className="relative">
                  <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
                  <input
                    type="text"
                    required
                    value={formData.business_name}
                    onChange={(e) => setFormData({...formData, business_name: e.target.value})}
                    placeholder={t('provider.onboarding.e_g_green_valley')}
                    className="!pl-10 w-full"
                  />
                </div>
              </div>

              {/* Service Type */}
              <div>
                <label className="block text-sm font-medium mb-1">{t('provider.onboarding.primary_service_type')}</label>
                <div className="relative">
                  <Wrench className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
                  <select
                    required
                    value={formData.service_type}
                    onChange={(e) => setFormData({...formData, service_type: e.target.value})}
                    className="!pl-10 w-full"
                  >
                    <option value="equipment_rental">{t('provider.onboarding.equipment_rental')}</option>
                    <option value="soil_testing">{t('provider.onboarding.soil_testing')}</option>
                    <option value="drone_survey">{t('provider.onboarding.drone_survey')}</option>
                    <option value="pest_control">{t('provider.onboarding.pest_control')}</option>
                    <option value="harvest_labor">{t('provider.onboarding.harvest_labor')}</option>
                    <option value="logistics">{t('provider.onboarding.logistics_transport')}</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Region */}
                <div>
                  <label className="block text-sm font-medium mb-1">{t('provider.onboarding.region_state')}</label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
                    <input
                      type="text"
                      required
                      value={formData.region}
                      onChange={(e) => setFormData({...formData, region: e.target.value})}
                      placeholder={t('provider.onboarding.e_g_punjab')}
                      className="!pl-10 w-full"
                    />
                  </div>
                </div>

                {/* Sub Region */}
                <div>
                  <label className="block text-sm font-medium mb-1">{t('provider.onboarding.sub_region_district')}</label>
                  <input
                    type="text"
                    required
                    value={formData.sub_region}
                    onChange={(e) => setFormData({...formData, sub_region: e.target.value})}
                    placeholder={t('provider.onboarding.e_g_ludhiana')}
                    className="w-full"
                  />
                </div>
              </div>

              {/* Radius */}
              <div>
                <label className="block text-sm font-medium mb-1">{t('provider.onboarding.service_radius_km')}</label>
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
                <label className="block text-sm font-medium mb-1">{t('provider.onboarding.crop_specializations_comma_separated')}</label>
                <div className="relative">
                  <Sprout className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
                  <input
                    type="text"
                    value={formData.crop_specializations}
                    onChange={(e) => setFormData({...formData, crop_specializations: e.target.value})}
                    placeholder={t('provider.onboarding.e_g_wheat_rice')}
                    className="!pl-10 w-full"
                  />
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium mb-1">{t('provider.onboarding.business_description')}</label>
                <textarea
                  rows={4}
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder={t('provider.onboarding.describe_your_capabilities_experience')}
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
