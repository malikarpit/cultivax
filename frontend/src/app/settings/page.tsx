'use client';

/**
 * Settings Page — User Preferences
 *
 * Central hub for user preferences:
 * - Language selection (5 Indian languages)
 * - Accessibility toggles (large text, high contrast, reduced motion, theme)
 * - Account info display
 *
 * Reuses Feature 3 components: LanguageSwitcher, useAccessibility hook.
 */

import { useState } from 'react';
import {
  Settings as SettingsIcon,
  Globe,
  Eye,
  Type,
  Wind,
  Moon,
  Sun,
  Check,
  ChevronLeft,
  User,
  Shield,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import clsx from 'clsx';
import { useTranslation } from 'react-i18next';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/context/AuthContext';
import { useAccessibility } from '@/hooks/useAccessibility';

const LANGUAGES = [
  { code: 'en', label: 'English', native: 'English' },
  { code: 'hi', label: 'Hindi', native: 'हिन्दी' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்' },
  { code: 'te', label: 'Telugu', native: 'తెలుగు' },
  { code: 'mr', label: 'Marathi', native: 'मराठी' },
];

export default function SettingsPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { user, updatePreferences } = useAuth();
  const {
    settings,
    toggleLargeText,
    toggleHighContrast,
    toggleReducedMotion,
    toggleTheme,
  } = useAccessibility();

  const [savingLang, setSavingLang] = useState<string | null>(null);

  const currentLang = user?.preferred_language || 'en';

  const handleLanguageChange = async (langCode: string) => {
    if (langCode === currentLang) return;
    setSavingLang(langCode);
    try {
      await updatePreferences({ preferred_language: langCode });
    } catch {
      // Graceful fallback — user sees no change
    } finally {
      setSavingLang(null);
    }
  };

  const ToggleRow = ({
    icon: Icon,
    label,
    description,
    active,
    onToggle,
    id,
  }: {
    icon: React.ElementType;
    label: string;
    description: string;
    active: boolean;
    onToggle: () => void;
    id: string;
  }) => (
    <button
      id={id}
      onClick={onToggle}
      aria-pressed={active}
      className="w-full flex items-center gap-4 p-4 rounded-xl hover:bg-cultivax-elevated/50 transition-colors group"
    >
      <div className={clsx(
        'w-10 h-10 rounded-lg flex items-center justify-center transition-colors',
        active ? 'bg-cultivax-primary/15' : 'bg-cultivax-elevated'
      )}>
        <Icon className={clsx('w-5 h-5', active ? 'text-cultivax-primary' : 'text-cultivax-text-muted')} />
      </div>
      <div className="flex-1 text-left">
        <p className="text-sm font-medium text-cultivax-text-primary">{label}</p>
        <p className="text-xs text-cultivax-text-muted">{description}</p>
      </div>
      <div
        className={clsx(
          'w-11 h-6 rounded-full transition-colors flex-shrink-0 relative',
          active ? 'bg-cultivax-primary' : 'bg-cultivax-border'
        )}
      >
        <span
          className={clsx(
            'absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform',
            active ? 'translate-x-[22px]' : 'translate-x-0.5'
          )}
        />
      </div>
    </button>
  );

  return (
    <ProtectedRoute>
      <div className="max-w-2xl mx-auto">
        {/* Page header */}
        <div className="flex items-center gap-3 mb-8">
          <button
            onClick={() => router.back()}
            className="btn-icon"
            aria-label="Go back"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-cultivax-text-primary flex items-center gap-2">
              <SettingsIcon className="w-6 h-6 text-cultivax-primary" />
              {t('settings.title')}
            </h1>
            <p className="text-sm text-cultivax-text-muted mt-0.5">
              {t('settings.subtitle')}
            </p>
          </div>
        </div>

        {/* Language Selection */}
        <div className="card mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-5 h-5 text-cultivax-primary" />
            <h2 className="text-base font-semibold text-cultivax-text-primary">{t('settings.language')}</h2>
          </div>
          <p className="text-xs text-cultivax-text-muted mb-4">
            {t('settings.language_desc')}
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {LANGUAGES.map((lang) => {
              const isActive = currentLang === lang.code;
              const isSaving = savingLang === lang.code;

              return (
                <button
                  key={lang.code}
                  id={`settings-lang-${lang.code}`}
                  onClick={() => handleLanguageChange(lang.code)}
                  disabled={isSaving}
                  className={clsx(
                    'flex items-center justify-between p-3 rounded-xl border transition-all',
                    isActive
                      ? 'border-cultivax-primary bg-cultivax-primary/5'
                      : 'border-cultivax-border hover:border-cultivax-border-highlight hover:bg-cultivax-elevated/30'
                  )}
                >
                  <div className="text-left">
                    <p className={clsx(
                      'text-sm font-medium',
                      isActive ? 'text-cultivax-primary' : 'text-cultivax-text-primary'
                    )}>
                      {lang.native}
                    </p>
                    <p className="text-xs text-cultivax-text-muted">{lang.label}</p>
                  </div>
                  {isActive && <Check className="w-4 h-4 text-cultivax-primary" />}
                  {isSaving && (
                    <div className="w-4 h-4 border-2 border-cultivax-primary border-t-transparent rounded-full animate-spin" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Accessibility */}
        <div className="card mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Eye className="w-5 h-5 text-cultivax-primary" />
            <h2 className="text-base font-semibold text-cultivax-text-primary">{t('settings.accessibility')}</h2>
          </div>
          <p className="text-xs text-cultivax-text-muted mb-3">
            {t('settings.accessibility_desc')}
          </p>

          <div className="space-y-1">
            <ToggleRow
              id="settings-large-text"
              icon={Type}
              label={t('a11y.large_text')}
              description={t('settings.large_text_desc')}
              active={!!settings.largeText}
              onToggle={toggleLargeText}
            />
            <ToggleRow
              id="settings-high-contrast"
              icon={Eye}
              label={t('a11y.high_contrast')}
              description={t('settings.high_contrast_desc')}
              active={!!settings.highContrast}
              onToggle={toggleHighContrast}
            />
            <ToggleRow
              id="settings-reduced-motion"
              icon={Wind}
              label={t('a11y.reduce_motion')}
              description={t('settings.reduce_motion_desc')}
              active={!!settings.reducedMotion}
              onToggle={toggleReducedMotion}
            />
            <ToggleRow
              id="settings-dark-mode"
              icon={settings.theme === 'dark' ? Sun : Moon}
              label={settings.theme === 'dark' ? t('a11y.light_mode') : t('a11y.dark_mode')}
              description={t('settings.theme_desc')}
              active={settings.theme === 'dark'}
              onToggle={toggleTheme}
            />
          </div>
        </div>

        {/* Account Info */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <User className="w-5 h-5 text-cultivax-primary" />
            <h2 className="text-base font-semibold text-cultivax-text-primary">{t('settings.account')}</h2>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-cultivax-text-muted">{t('settings.field_name')}</span>
              <span className="text-cultivax-text-primary font-medium">{user?.full_name || '—'}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-cultivax-text-muted">{t('settings.field_phone')}</span>
              <span className="text-cultivax-text-primary font-medium">{user?.phone || '—'}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-cultivax-text-muted">{t('settings.field_role')}</span>
              <span className="inline-flex items-center gap-1 text-cultivax-primary">
                <Shield className="w-3 h-3" />
                <span className="capitalize font-medium">{user?.role}</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
