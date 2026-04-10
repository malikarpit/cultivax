'use client';

/**
 * Login Page — Dual Authentication
 *
 * Supports two login methods:
 * 1. Password-based login (phone + password)
 * 2. OTP-based login (phone + 6-digit code)
 *
 * Security Features:
 * - Account lockout messaging (429 errors)
 * - OTP rate limiting feedback
 * - No token exposure in JavaScript
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Leaf, Eye, EyeOff, Phone, Lock, Loader2, MessageSquare, ArrowRight, Shield } from 'lucide-react';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import Footer from '@/components/Footer';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/context/AuthContext';

type AuthTab = 'password' | 'otp';

export default function LoginPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const { login, loginWithOTP, sendOTP } = useAuth();

  // Role-based post-login routing
  const getPostLoginRoute = (role: string): string => {
    const routes: Record<string, string> = {
      farmer: '/dashboard',
      provider: '/provider',
      admin: '/admin',
    };
    return routes[role] || '/dashboard';
  };

  // Shared state
  const [activeTab, setActiveTab] = useState<AuthTab>('password');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Password tab
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // OTP tab
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState('');
  const [otpCooldown, setOtpCooldown] = useState(0);
  const [debugOtp, setDebugOtp] = useState<string | null>(null);

  // OTP cooldown timer
  const startCooldown = () => {
    setOtpCooldown(60);
    const interval = setInterval(() => {
      setOtpCooldown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  // Password login
  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const loggedInUser = await login(phone, password);
      router.push(getPostLoginRoute(loggedInUser.role));
    } catch (err: any) {
      const status = err?.status;
      const code = err?.code;
      const rawMessage = typeof err?.message === 'string' ? err.message : '';

      let msg = rawMessage || 'Sign in failed. Please try again.';
      if (code === 'network' || /failed to fetch|network request failed|load failed/i.test(rawMessage)) {
        msg = 'Unable to reach server. Please ensure backend is running on http://localhost:8000.';
      } else if (status === 401 || /invalid phone number or password/i.test(rawMessage)) {
        msg = 'Invalid phone number or password';
      }

      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  // Send OTP
  const handleSendOTP = async () => {
    if (!phone || phone.length < 10) {
      setError('Please enter a valid phone number');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const devOtp = await sendOTP(phone);
      setOtpSent(true);
      setDebugOtp(devOtp);
      startCooldown();
    } catch (err: any) {
      const rawMessage = typeof err?.message === 'string' ? err.message : '';
      if (err?.code === 'network' || /failed to fetch|network request failed|load failed/i.test(rawMessage)) {
        setError('Unable to reach server. Please ensure backend is running on http://localhost:8000.');
      } else {
        setError(rawMessage || 'Failed to send OTP');
      }
    } finally {
      setLoading(false);
    }
  };

  // Verify OTP
  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const loggedInUser = await loginWithOTP(phone, otp);
      router.push(getPostLoginRoute(loggedInUser.role));
    } catch (err: any) {
      const rawMessage = typeof err?.message === 'string' ? err.message : '';
      if (err?.code === 'network' || /failed to fetch|network request failed|load failed/i.test(rawMessage)) {
        setError('Unable to reach server. Please ensure backend is running on http://localhost:8000.');
      } else {
        setError(rawMessage || 'Invalid OTP');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cultivax-bg flex flex-col">
      {/* Subtle grid background */}
      <div className="fixed inset-0 opacity-[0.015] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(rgba(16,185,129,0.4) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(16,185,129,0.4) 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
        }}
      />

      {/* Centered card */}
      <div className="flex-1 flex items-center justify-center px-4 py-12 relative">
        <div className="w-full max-w-md">
          {/* Language switcher */}
          <div className="flex justify-end mb-4">
            <LanguageSwitcher />
          </div>

          <div className="card p-8 animate-fade-in">
            {/* Logo */}
            <div className="text-center mb-8">
              <div className="w-14 h-14 bg-cultivax-primary/15 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Leaf className="w-8 h-8 text-cultivax-primary" />
              </div>
              <h1 className="text-2xl font-bold text-cultivax-text-primary">
                {t('auth.login')}
              </h1>
              <p className="text-sm text-cultivax-text-secondary mt-1">
                {t('auth.welcome_back')}
              </p>
            </div>

            {/* Auth method tabs */}
            <div className="flex bg-cultivax-bg/50 rounded-lg p-1 mb-6 border border-cultivax-border/50">
              <button
                onClick={() => { setActiveTab('password'); setError(''); }}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-md text-sm font-medium transition-all ${
                  activeTab === 'password'
                    ? 'bg-cultivax-primary/15 text-cultivax-primary shadow-sm'
                    : 'text-cultivax-text-muted hover:text-cultivax-text-secondary'
                }`}
              >
                <Lock className="w-3.5 h-3.5" />
                {t('auth.password_tab')}
              </button>
              <button
                onClick={() => { setActiveTab('otp'); setError(''); setOtpSent(false); }}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-md text-sm font-medium transition-all ${
                  activeTab === 'otp'
                    ? 'bg-cultivax-primary/15 text-cultivax-primary shadow-sm'
                    : 'text-cultivax-text-muted hover:text-cultivax-text-secondary'
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5" />
                {t('auth.otp_tab')}
              </button>
            </div>

            {/* Error */}
            {error && (
              <div className={`rounded-lg px-4 py-3 mb-6 text-sm ${
                error.includes('locked') || error.includes('Too many')
                  ? 'bg-orange-500/10 border border-orange-500/20 text-orange-400'
                  : 'bg-red-500/10 border border-red-500/20 text-red-400'
              }`}>
                {error.includes('locked') && <Shield className="w-4 h-4 inline mr-1.5" />}
                {error}
              </div>
            )}

            {/* --- PASSWORD TAB --- */}
            {activeTab === 'password' && (
              <form onSubmit={handlePasswordLogin} className="space-y-5">
                {/* Phone field */}
                <div>
                  <label className="form-label">{t('auth.phone')}</label>
                  <div className="relative">
                    <div className="absolute left-0 top-0 bottom-0 flex items-center pl-3 pr-2 border-r border-cultivax-border text-sm text-cultivax-text-muted">
                      <Phone className="w-4 h-4 mr-1.5" />
                      +91
                    </div>
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="9876543210"
                      className="!pl-20"
                      required
                      autoFocus
                    />
                  </div>
                </div>

                {/* Password field */}
                <div>
                  <label className="form-label">{t('auth.password')}</label>
                  <div className="relative">
                    <div className="absolute left-3 top-1/2 -translate-y-1/2 text-cultivax-text-muted">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
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
                </div>

                {/* Forgot password + OTP hint */}
                <div className="flex justify-between items-center">
                  <button
                    type="button"
                    onClick={() => { setActiveTab('otp'); setError(''); }}
                    className="text-sm text-cultivax-text-muted hover:text-cultivax-primary transition-colors"
                  >
                    {t('auth.use_otp')}
                  </button>
                  <Link
                    href="#"
                    className="text-sm text-cultivax-primary hover:text-cultivax-primary-hover transition-colors"
                  >
                    {t('auth.forgot_password')}
                  </Link>
                </div>

                {/* Submit */}
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary w-full flex items-center justify-center gap-2 py-3"
                >
                  {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                  {loading ? t('btn.loading') : t('auth.login')}
                </button>
              </form>
            )}

            {/* --- OTP TAB --- */}
            {activeTab === 'otp' && (
              <div className="space-y-5">
                {/* Phone field */}
                <div>
                  <label className="form-label">{t('auth.phone')}</label>
                  <div className="relative">
                    <div className="absolute left-0 top-0 bottom-0 flex items-center pl-3 pr-2 border-r border-cultivax-border text-sm text-cultivax-text-muted">
                      <Phone className="w-4 h-4 mr-1.5" />
                      +91
                    </div>
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="9876543210"
                      className="!pl-20"
                      required
                      disabled={otpSent}
                    />
                  </div>
                </div>

                {!otpSent ? (
                  /* Send OTP button */
                  <button
                    onClick={handleSendOTP}
                    disabled={loading || !phone || phone.length < 10}
                    className="btn-primary w-full flex items-center justify-center gap-2 py-3"
                  >
                    {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                    <MessageSquare className="w-4 h-4" />
                    {t('auth.send_otp')}
                  </button>
                ) : (
                  /* OTP verification form */
                  <form onSubmit={handleVerifyOTP} className="space-y-5">
                    {/* Dev mode OTP display */}
                    {debugOtp && (
                      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg px-4 py-3 text-sm text-blue-400">
                        <span className="font-mono font-bold text-base">{debugOtp}</span>
                        <span className="ml-2 text-blue-400/60">{t('auth.dev_otp_hint')}</span>
                      </div>
                    )}

                    {/* OTP input */}
                    <div>
                      <label className="form-label">{t('auth.otp')}</label>
                      <input
                        type="text"
                        inputMode="numeric"
                        maxLength={6}
                        value={otp}
                        onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        placeholder="000000"
                        className="text-center text-2xl tracking-[0.5em] font-mono"
                        autoFocus
                        required
                      />
                    </div>

                    {/* Verify button */}
                    <button
                      type="submit"
                      disabled={loading || otp.length !== 6}
                      className="btn-primary w-full flex items-center justify-center gap-2 py-3"
                    >
                      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                      <ArrowRight className="w-4 h-4" />
                      {t('auth.verify_sign_in')}
                    </button>

                    {/* Resend */}
                    <div className="text-center">
                      <button
                        type="button"
                        onClick={handleSendOTP}
                        disabled={otpCooldown > 0 || loading}
                        className="text-sm text-cultivax-text-muted hover:text-cultivax-primary transition-colors disabled:opacity-50"
                      >
                        {otpCooldown > 0
                          ? t('auth.resend_in', { count: otpCooldown })
                          : t('auth.resend_otp')}
                      </button>
                    </div>
                  </form>
                )}
              </div>
            )}

            {/* Divider */}
            <div className="divider" />

            {/* Security badge */}
            <div className="flex items-center justify-center gap-2 text-xs text-cultivax-text-muted mb-4">
              <Shield className="w-3.5 h-3.5" />
              {t('auth.secure_badge')}
            </div>

            {/* Register link */}
            <div className="text-center">
              <p className="text-sm text-cultivax-text-secondary mb-3">
                {t('auth.no_account')}
              </p>
              <Link
                href="/register"
                className="btn-secondary w-full inline-flex items-center justify-center"
              >
                {t('auth.register')}
              </Link>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
