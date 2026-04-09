'use client';

/**
 * Profile Page — User Profile Dashboard
 *
 * Displays the authenticated user's profile information:
 * name, phone, email, role, region, onboarding status,
 * preferred language, and account creation date.
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  User, Phone, Mail, MapPin, Globe, Shield, Calendar,
  CheckCircle2, Clock, ChevronRight, Settings, Sprout,
} from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/context/AuthContext';
import { useTranslation } from 'react-i18next';

const LANGUAGE_LABELS: Record<string, string> = {
  en: 'English',
  hi: 'हिन्दी (Hindi)',
  ta: 'தமிழ் (Tamil)',
  te: 'తెలుగు (Telugu)',
  mr: 'मराठी (Marathi)',
};

const ROLE_LABELS: Record<string, { label: string; color: string }> = {
  farmer: { label: 'Farmer', color: 'bg-green-500/15 text-green-400' },
  provider: { label: 'Service Provider', color: 'bg-blue-500/15 text-blue-400' },
  admin: { label: 'Administrator', color: 'bg-purple-500/15 text-purple-400' },
};

export default function ProfilePage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const router = useRouter();

  if (!user) return null;

  const roleInfo = ROLE_LABELS[user.role] || ROLE_LABELS.farmer;

  const InfoRow = ({
    icon: Icon,
    label,
    value,
    id,
  }: {
    icon: React.ElementType;
    label: string;
    value: string | React.ReactNode;
    id: string;
  }) => (
    <div id={id} className="flex items-start gap-4 py-4 border-b border-cultivax-border last:border-0">
      <div className="w-10 h-10 rounded-lg bg-cultivax-elevated flex items-center justify-center flex-shrink-0">
        <Icon className="w-5 h-5 text-cultivax-text-muted" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-cultivax-text-muted uppercase tracking-wider mb-0.5">{label}</p>
        <p className="text-sm text-cultivax-text-primary">{value || '—'}</p>
      </div>
    </div>
  );

  return (
    <ProtectedRoute>
      <div className="max-w-2xl mx-auto">
        {/* Page header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-cultivax-text-primary">{t('profile.my_profile')}</h1>
          <p className="text-sm text-cultivax-text-muted mt-1">{t('profile.view_and_manage_your')}</p>
        </div>

        {/* Avatar + name card */}
        <div className="card mb-6">
          <div className="flex items-center gap-5">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-cultivax-primary/30 to-cultivax-primary/10 flex items-center justify-center text-cultivax-primary text-3xl font-bold">
              {(user.full_name || user.phone || 'U').charAt(0).toUpperCase()}
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-cultivax-text-primary">
                {user.full_name || 'CultivaX User'}
              </h2>
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium mt-2 ${roleInfo.color}`}>
                <Shield className="w-3 h-3" />
                {roleInfo.label}
              </span>
            </div>
            <button
              onClick={() => router.push('/settings')}
              className="btn-icon"
              title="Edit settings"
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Info card */}
        <div className="card mb-6">
          <h3 className="text-sm font-semibold text-cultivax-text-muted uppercase tracking-wider mb-2">{t('profile.account_details')}</h3>
          <InfoRow icon={Phone} label={t('profile.label.phone')} value={user.phone} id="profile-phone" />
          <InfoRow icon={Mail} label={t('profile.label.email')} value={user.email || 'Not set'} id="profile-email" />
          <InfoRow icon={MapPin} label={t('profile.label.region')} value={user.region || 'Not set'} id="profile-region" />
          <InfoRow
            icon={Globe}
            label={t('profile.label.language')}
            value={LANGUAGE_LABELS[user.preferred_language || 'en'] || user.preferred_language}
            id="profile-language"
          />
          <InfoRow
            icon={Sprout}
            label={t('profile.label.onboarding')}
            value={
              <span className={`inline-flex items-center gap-1 ${user.is_onboarded ? 'text-green-400' : 'text-amber-400'}`}>
                {user.is_onboarded ? <CheckCircle2 className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
                {user.is_onboarded ? 'Complete' : 'In Progress'}
              </span>
            }
            id="profile-onboarding"
          />
        </div>

        {/* Quick actions */}
        <div className="card">
          <h3 className="text-sm font-semibold text-cultivax-text-muted uppercase tracking-wider mb-2">{t('profile.quick_actions')}</h3>
          <button
            onClick={() => router.push('/settings')}
            className="w-full flex items-center justify-between py-3 text-sm text-cultivax-text-secondary hover:text-cultivax-text-primary transition-colors border-b border-cultivax-border"
          >
            <span className="flex items-center gap-3">
              <Settings className="w-4 h-4" />{t('profile.language_accessibility')}</span>
            <ChevronRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => router.push('/crops')}
            className="w-full flex items-center justify-between py-3 text-sm text-cultivax-text-secondary hover:text-cultivax-text-primary transition-colors"
          >
            <span className="flex items-center gap-3">
              <Sprout className="w-4 h-4" />{t('profile.my_crops')}</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </ProtectedRoute>
  );
}
