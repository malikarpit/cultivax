'use client';

/**
 * Register Page
 *
 * Multi-field registration with Indian-specific data,
 * role segmented control, password strength indicator,
 * and post-registration redirect to dashboard.
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Leaf, Eye, EyeOff, Phone, Lock, User, Mail, MapPin,
  Loader2, Sprout, Wrench, Check, X,
} from 'lucide-react';
import clsx from 'clsx';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import Footer from '@/components/Footer';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/context/AuthContext';

const INDIAN_STATES = [
  'Andhra Pradesh', 'Bihar', 'Chhattisgarh', 'Gujarat', 'Haryana',
  'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala',
  'Madhya Pradesh', 'Maharashtra', 'Odisha', 'Punjab', 'Rajasthan',
  'Tamil Nadu', 'Telangana', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
];

function PasswordStrength({ password }: { password: string }) {
  const checks = [
    { label: 'At least 8 characters', met: password.length >= 8 },
    { label: 'One uppercase letter', met: /[A-Z]/.test(password) },
    { label: 'One number', met: /\d/.test(password) },
  ];
  const strength = checks.filter((c) => c.met).length;

  return (
    <div className="mt-2 space-y-1.5">
      {/* Strength bar */}
      <div className="flex gap-1">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className={clsx(
              'h-1 flex-1 rounded-full transition-colors',
              strength >= i
                ? strength === 1 ? 'bg-red-500' : strength === 2 ? 'bg-amber-500' : 'bg-emerald-500'
                : 'bg-cultivax-elevated'
            )}
          />
        ))}
      </div>
      {/* Rules */}
      <div className="space-y-0.5">
        {checks.map((c) => (
          <div key={c.label} className="flex items-center gap-1.5 text-xs">
            {c.met ? (
              <Check className="w-3 h-3 text-emerald-400" />
            ) : (
              <X className="w-3 h-3 text-cultivax-text-muted" />
            )}
            <span className={c.met ? 'text-emerald-400' : 'text-cultivax-text-muted'}>
              {c.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function RegisterPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { register } = useAuth();

  // Role-based post-registration routing
  const getPostLoginRoute = (role: string): string => {
    const routes: Record<string, string> = {
      farmer: '/dashboard',
      provider: '/provider',
      admin: '/admin',
    };
    return routes[role] || '/dashboard';
  };

  const [form, setForm] = useState({
    fullName: '',
    phone: '',
    email: '',
    region: '',
    preferredLanguage: 'en',
    role: 'farmer',
    password: '',
    confirmPassword: '',
    agreedTerms: false,
  });

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const passwordMismatch = form.confirmPassword && form.password !== form.confirmPassword;

  const handleChange = (field: string, value: any) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      const registeredUser = await register({
        full_name: form.fullName,
        phone: form.phone,
        email: form.email || undefined,
        region: form.region,
        preferred_language: form.preferredLanguage,
        role: form.role,
        password: form.password,
      });
      router.push(getPostLoginRoute(registeredUser.role));
    } catch (err: any) {
      setError(err?.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cultivax-bg flex flex-col">
      {/* Grid background */}
      <div className="fixed inset-0 opacity-[0.015] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(rgba(16,185,129,0.4) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(16,185,129,0.4) 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
        }}
      />

      <div className="flex-1 flex items-center justify-center px-4 py-12 relative">
        <div className="w-full max-w-lg">
          <div className="flex justify-end mb-4">
            <LanguageSwitcher />
          </div>

          <div className="card p-8 animate-fade-in">
            {/* Logo */}
            <div className="text-center mb-8">
              <div className="w-14 h-14 bg-cultivax-primary/15 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Leaf className="w-8 h-8 text-cultivax-primary" />
              </div>
              <h1 className="text-2xl font-bold">{t('auth.register')}</h1>
              <p className="text-sm text-cultivax-text-secondary mt-1">
                {t('auth.create_account')}
              </p>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 mb-6 text-sm text-red-400">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Full Name */}
              <div>
                <label className="form-label">{t('auth.full_name')}</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
                  <input
                    type="text"
                    value={form.fullName}
                    onChange={(e) => handleChange('fullName', e.target.value)}
                    placeholder="Enter your full name"
                    className="!pl-10"
                    required
                  />
                </div>
              </div>

              {/* Phone */}
              <div>
                <label className="form-label">{t('auth.phone')}</label>
                <div className="relative">
                  <div className="absolute left-0 top-0 bottom-0 flex items-center pl-3 pr-2 border-r border-cultivax-border text-sm text-cultivax-text-muted">
                    <Phone className="w-4 h-4 mr-1.5" />
                    +91
                  </div>
                  <input
                    type="tel"
                    value={form.phone}
                    onChange={(e) => handleChange('phone', e.target.value)}
                    placeholder="9876543210"
                    className="!pl-20"
                    required
                  />
                </div>
              </div>

              {/* Email (optional) */}
              <div>
                <label className="form-label">{t('auth.email_optional')}</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => handleChange('email', e.target.value)}
                    placeholder="email@example.com"
                    className="!pl-10"
                  />
                </div>
              </div>

              {/* Region */}
              <div>
                <label className="form-label">{t('auth.region')}</label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
                  <select
                    value={form.region}
                    onChange={(e) => handleChange('region', e.target.value)}
                    className="!pl-10"
                    required
                  >
                    <option value="">{t('auth.select_region')}</option>
                    {INDIAN_STATES.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Preferred Language */}
              <div>
                <label className="form-label">{t('auth.preferred_language')}</label>
                <div className="flex gap-3">
                  {[
                    { code: 'en', label: 'English' },
                    { code: 'hi', label: 'हिंदी' },
                  ].map((lang) => (
                    <button
                      key={lang.code}
                      type="button"
                      onClick={() => handleChange('preferredLanguage', lang.code)}
                      className={clsx(
                        'flex-1 py-2.5 rounded-lg text-sm font-medium border transition-all',
                        form.preferredLanguage === lang.code
                          ? 'border-cultivax-primary bg-cultivax-primary/10 text-cultivax-primary'
                          : 'border-cultivax-border text-cultivax-text-secondary hover:border-cultivax-border-highlight'
                      )}
                    >
                      {lang.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Role segmented control */}
              <div>
                <label className="form-label">{t('auth.i_am_a')}</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => handleChange('role', 'farmer')}
                    className={clsx(
                      'p-4 rounded-xl border text-left transition-all',
                      form.role === 'farmer'
                        ? 'border-cultivax-primary bg-cultivax-primary/10'
                        : 'border-cultivax-border hover:border-cultivax-border-highlight'
                    )}
                  >
                    <Sprout className={clsx('w-5 h-5 mb-2', form.role === 'farmer' ? 'text-cultivax-primary' : 'text-cultivax-text-muted')} />
                    <p className="text-sm font-semibold">{t('auth.farmer_label')}</p>
                    <p className="text-xs text-cultivax-text-muted mt-0.5">{t('auth.farmer_desc')}</p>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleChange('role', 'provider')}
                    className={clsx(
                      'p-4 rounded-xl border text-left transition-all',
                      form.role === 'provider'
                        ? 'border-cultivax-primary bg-cultivax-primary/10'
                        : 'border-cultivax-border hover:border-cultivax-border-highlight'
                    )}
                  >
                    <Wrench className={clsx('w-5 h-5 mb-2', form.role === 'provider' ? 'text-cultivax-primary' : 'text-cultivax-text-muted')} />
                    <p className="text-sm font-semibold">{t('auth.provider_label')}</p>
                    <p className="text-xs text-cultivax-text-muted mt-0.5">{t('auth.provider_desc')}</p>
                  </button>
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="form-label">{t('auth.password')}</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={form.password}
                    onChange={(e) => handleChange('password', e.target.value)}
                    placeholder="Create a password"
                    className="!pl-10 !pr-10"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-cultivax-text-muted hover:text-cultivax-text-secondary"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {form.password && <PasswordStrength password={form.password} />}
              </div>

              {/* Confirm Password */}
              <div>
                <label className="form-label">{t('auth.confirm_password')}</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cultivax-text-muted" />
                  <input
                    type="password"
                    value={form.confirmPassword}
                    onChange={(e) => handleChange('confirmPassword', e.target.value)}
                    placeholder={t('auth.reenter_password')}
                    className={clsx('!pl-10', passwordMismatch && '!border-red-500')}
                    required
                  />
                </div>
                {passwordMismatch && (
                  <p className="text-xs text-red-400 mt-1">{t('auth.passwords_mismatch')}</p>
                )}
              </div>

              {/* Terms */}
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.agreedTerms}
                  onChange={(e) => handleChange('agreedTerms', e.target.checked)}
                  className="mt-1 w-4 h-4 rounded border-cultivax-border bg-cultivax-elevated text-cultivax-primary focus:ring-cultivax-primary"
                  required
                />
                <span className="text-sm text-cultivax-text-secondary leading-relaxed">
                  {t('auth.agree_terms')}{' '}
                  <Link href="#" className="text-cultivax-primary hover:underline">{t('auth.terms_of_service')}</Link>
                  {' '}{t('auth.and')}{' '}
                  <Link href="#" className="text-cultivax-primary hover:underline">{t('auth.privacy_policy')}</Link>
                </span>
              </label>

              {/* Submit */}
              <button
                type="submit"
                disabled={loading || passwordMismatch as boolean}
                className="btn-primary w-full flex items-center justify-center gap-2 py-3"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {loading ? t('btn.loading') : t('auth.register')}
              </button>
            </form>

            <div className="divider" />

            <div className="text-center">
              <p className="text-sm text-cultivax-text-secondary">
                {t('auth.already_have_account')}{' '}
                <Link href="/login" className="text-cultivax-primary hover:underline font-medium">
                  {t('auth.sign_in_here')}
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
