'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiGet } from '@/lib/api';
import ProtectedRoute from '@/components/ProtectedRoute';
import TrustRing from '@/components/TrustRing';
import { MapPin, CheckCircle2, Clock, Wrench, Sprout, Star, ArrowLeft, Send } from 'lucide-react';
import Link from 'next/link';
import Badge from '@/components/Badge';
import { useTranslation } from 'react-i18next';

export default function ProviderProfilePage() {
  const { t } = useTranslation();
  const { id } = useParams();
  const router = useRouter();
  
  const [provider, setProvider] = useState<any>(null);
  const [equipment, setEquipment] = useState<any[]>([]);
  const [reviewsData, setReviewsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadProfile() {
      try {
        const [prov, equip, revs] = await Promise.all([
          apiGet(`/api/v1/providers/${id}`),
          apiGet(`/api/v1/providers/${id}/equipment?is_available=true`),
          apiGet(`/api/v1/reviews?provider_id=${id}`)
        ]);
        
        setProvider(prov);
        setEquipment((equip as any)?.items || []);
        setReviewsData(revs);
      } catch (err: any) {
        setError(err.message || 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    }
    
    if (id) loadProfile();
  }, [id]);

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="py-12 text-center animate-pulse">
          <div className="w-16 h-16 bg-cultivax-elevated rounded-full mx-auto mb-4" />
          <div className="w-48 h-6 bg-cultivax-elevated rounded mx-auto mb-2" />
          <div className="w-32 h-4 bg-cultivax-elevated rounded mx-auto" />
        </div>
      </ProtectedRoute>
    );
  }

  if (error || !provider) {
    return (
      <ProtectedRoute>
        <div className="card text-center py-16">
          <h2 className="text-xl font-bold text-red-500 mb-2">{t('services.[id].profile_not_found')}</h2>
          <p className="text-cultivax-text-secondary mb-6">{error || 'This provider does not exist or has been removed.'}</p>
          <button onClick={() => router.push('/services')} className="btn-primary">{t('services.[id].back_to_marketplace')}</button>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="animate-fade-in max-w-4xl mx-auto space-y-6">
        {/* Back Link */}
        <Link href="/services" className="inline-flex items-center text-sm font-medium text-cultivax-text-muted hover:text-cultivax-text-primary transition-colors">
          <ArrowLeft className="w-4 h-4 mr-1" />{t('services.[id].back_to_services')}</Link>
        
        {/* Header Profile */}
        <div className="card p-6">
          <div className="flex flex-col md:flex-row gap-6 items-start md:items-center">
            <TrustRing 
              score={provider.trust_score ? provider.trust_score / 10 : 0} 
              size={100} 
              strokeWidth={8} 
              labelFormat="decimal" 
            />
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-2xl font-bold truncate">{provider.business_name || 'Independent Provider'}</h1>
                {provider.is_verified && <Badge variant="blue">{t('services.[id].verified')}</Badge>}
                {!provider.is_suspended ? (
                  <Badge variant="green" dot>{t('services.[id].active')}</Badge>
                ) : (
                  <Badge variant="red">{t('services.[id].suspended')}</Badge>
                )}
              </div>
              
              <div className="flex flex-wrap items-center gap-4 text-sm text-cultivax-text-muted mb-4">
                <span className="flex items-center gap-1"><MapPin className="w-4 h-4" /> {provider.region} ({provider.service_radius_km}km)</span>
                <span className="flex items-center gap-1 capitalize"><Wrench className="w-4 h-4" /> {provider.service_type.replace('_', ' ')}</span>
                <span className="flex items-center gap-1"><CheckCircle2 className="w-4 h-4" /> {reviewsData?.aggregates?.total_count || 0} Reviews</span>
              </div>
              
              <p className="text-cultivax-text-secondary line-clamp-3 md:line-clamp-none">{provider.description}</p>
            </div>
            
            <div className="mt-4 md:mt-0 flex-shrink-0 w-full md:w-auto">
              <Link 
                href={`/services/request?provider=${provider.id}`}
                className={`btn-primary w-full flex justify-center items-center gap-2 ${provider.is_suspended ? 'opacity-50 pointer-events-none' : ''}`}
              >
                Request Service <Send className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Equipment Section */}
            <div className="card p-6">
              <h2 className="text-lg font-bold mb-4">{t('services.[id].available_equipment')}</h2>
              {equipment.length > 0 ? (
                <div className="space-y-3">
                  {equipment.map(eq => (
                    <div key={eq.id} className="p-4 bg-cultivax-elevated/50 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 border border-cultivax-border/50">
                      <div>
                        <h4 className="font-semibold text-sm">{eq.name}</h4>
                        <p className="text-xs text-cultivax-text-muted capitalize">{eq.equipment_type} &bull; {eq.condition} condition</p>
                      </div>
                      <div className="text-sm font-medium text-cultivax-primary whitespace-nowrap">
                        {eq.hourly_rate ? `₹${eq.hourly_rate}/hr` : eq.daily_rate ? `₹${eq.daily_rate}/day` : 'Contact for rate'}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 bg-cultivax-elevated/30 rounded-lg border border-cultivax-border border-dashed">
                  <p className="text-sm text-cultivax-text-muted">{t('services.[id].no_specific_equipment_listed')}</p>
                </div>
              )}
            </div>

            {/* Reviews Section */}
            <div className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold">{t('services.[id].recent_reviews')}</h2>
                <div className="text-sm font-medium text-cultivax-text-secondary flex items-center gap-1">
                  <Star className="w-4 h-4 text-cultivax-primary fill-cultivax-primary" />
                  {reviewsData?.aggregates?.average_rating ? reviewsData.aggregates.average_rating.toFixed(1) : 'No rating'}
                </div>
              </div>
              
              {reviewsData?.reviews?.length > 0 ? (
                <div className="space-y-4">
                  {reviewsData.reviews.map((rev: any) => (
                    <div key={rev.id} className="pb-4 border-b border-cultivax-border last:border-0 last:pb-0">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="flex items-center text-cultivax-primary gap-0.5">
                          {[...Array(5)].map((_, i) => (
                            <Star key={i} className={`w-3 h-3 ${i < Math.round(rev.rating) ? 'fill-cultivax-primary' : 'text-cultivax-border'}`} />
                          ))}
                        </div>
                        <span className="text-xs text-cultivax-text-muted ml-2">
                          {new Date(rev.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-sm text-cultivax-text-secondary">{rev.comment || 'No comment provided.'}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 bg-cultivax-elevated/30 rounded-lg border border-cultivax-border border-dashed">
                  <p className="text-sm text-cultivax-text-muted">{t('services.[id].no_reviews_yet')}</p>
                </div>
              )}
            </div>

          </div>

          {/* Sidebar Area */}
          <div className="space-y-6">
            
            {/* Specializations */}
            <div className="card p-6">
              <h2 className="text-sm font-bold mb-3 flex items-center gap-2"><Sprout className="w-4 h-4 text-cultivax-primary" />{t('services.[id].crop_specializations')}</h2>
              {provider.crop_specializations && provider.crop_specializations.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {provider.crop_specializations.map((crop: string) => (
                    <span key={crop} className="px-2.5 py-1 text-xs font-medium bg-cultivax-primary/10 text-cultivax-text-primary rounded-full border border-cultivax-primary/20">
                      {crop}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-cultivax-text-muted">{t('services.[id].general_services')}</p>
              )}
            </div>
            
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
