'use client';

/**
 * LanguageSwitcher — Globe icon dropdown for language preference switching.
 *
 * Persists selection to the backend via PATCH /auth/me (no page reload).
 * Falls back to cookie/localStorage when user is not authenticated.
 */

import { useState, useRef, useEffect } from 'react';
import { Globe, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '@/context/AuthContext';

const LOCALES = [
  { code: 'en', label: 'English',  flag: '🇮🇳' },
  { code: 'hi', label: 'हिंदी',    flag: '🇮🇳' },
  { code: 'ta', label: 'தமிழ்',    flag: '🇮🇳' },
  { code: 'te', label: 'తెలుగు',   flag: '🇮🇳' },
  { code: 'mr', label: 'मराठी',    flag: '🇮🇳' },
];

interface LanguageSwitcherProps {
  compact?: boolean;
  className?: string;
}

export default function LanguageSwitcher({
  compact = false,
  className,
}: LanguageSwitcherProps) {
  const { user, updatePreferences } = useAuth();
  const [isOpen, setIsOpen]         = useState(false);
  const [isSaving, setIsSaving]     = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Derive current locale: backend → cookie → localStorage → default
  const currentLocale = user?.preferred_language || (() => {
    if (typeof window === 'undefined') return 'en';
    const fromCookie = document.cookie
      .split('; ')
      .find((c) => c.startsWith('locale='))
      ?.split('=')[1];
    return fromCookie || localStorage.getItem('cultivax_locale') || 'en';
  })();

  // Close dropdown on outside click
  useEffect(() => {
    const handle = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, []);

  const switchLocale = async (code: string) => {
    if (code === currentLocale) {
      setIsOpen(false);
      return;
    }

    setIsOpen(false);
    setIsSaving(true);

    try {
      if (user) {
        // Persist to backend — updatePreferences also calls hydrateSettings
        // which sets document.documentElement.lang + localStorage + cookie
        await updatePreferences({ preferred_language: code });
      } else {
        // Unauthenticated fallback — update DOM + storage only
        document.documentElement.lang = code;
        document.cookie = `locale=${code}; path=/; max-age=31536000; SameSite=Lax`;
        localStorage.setItem('cultivax_locale', code);
      }
    } catch (err) {
      console.error('Failed to update language preference:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const current = LOCALES.find((l) => l.code === currentLocale) || LOCALES[0];

  return (
    <div className={clsx('relative', className)} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={clsx(
          'flex items-center gap-2 rounded-lg transition-colors duration-200',
          compact
            ? 'btn-icon'
            : 'px-3 py-2 hover:bg-cultivax-elevated text-cultivax-text-secondary hover:text-cultivax-text-primary'
        )}
        title="Change Language / भाषा बदलें"
        disabled={isSaving}
      >
        {isSaving
          ? <Loader2 className="w-4 h-4 animate-spin" />
          : <Globe className="w-4 h-4" />
        }
        {!compact && (
          <span className="text-sm">{current.flag} {current.label}</span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-1 z-50 bg-cultivax-surface border border-cultivax-border rounded-lg shadow-elevated py-1 min-w-[180px] animate-slide-down">
          {LOCALES.map((locale) => (
            <button
              key={locale.code}
              onClick={() => switchLocale(locale.code)}
              className={clsx(
                'w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors',
                locale.code === currentLocale
                  ? 'text-cultivax-primary bg-cultivax-primary/10'
                  : 'text-cultivax-text-secondary hover:bg-cultivax-elevated hover:text-cultivax-text-primary'
              )}
            >
              <span className="text-lg">{locale.flag}</span>
              <span>{locale.label}</span>
              {locale.code === currentLocale && (
                <span className="ml-auto text-cultivax-primary">✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
