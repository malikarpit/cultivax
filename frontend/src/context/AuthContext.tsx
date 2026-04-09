'use client';

/**
 * Auth Context — Cookie-Based Session Management
 *
 * Provides authentication state and methods to all components.
 *
 * Security Architecture:
 * - Tokens are stored in HttpOnly cookies (immune to XSS)
 * - Session verification uses /auth/me endpoint
 * - Auto-refresh on 401 via api.ts interceptor
 * - Proper logout with server-side session revocation
 */

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';
import {
  verifySession,
  getCachedUser,
  setCachedUser,
  performLogout,
} from '@/lib/auth';
import { apiPost, apiPatch } from '@/lib/api';
import { offlineQueue } from '@/services/offlineQueue';

// ─── Types ───────────────────────────────────────────────────────────────────

export interface AccessibilitySettings {
  largeText?: boolean;
  highContrast?: boolean;
  reducedMotion?: boolean;
  theme?: 'light' | 'dark';
  sidebarPinned?: boolean;
}

export interface User {
  id: string;
  full_name: string;
  phone: string;
  email?: string;
  role: string;
  region?: string;
  is_onboarded: boolean;
  accessibility_settings: AccessibilitySettings;
  preferred_language: string;
}

export type PreferenceUpdate = {
  preferred_language?: string;
  accessibility_settings?: AccessibilitySettings;
};

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (phone: string, password: string) => Promise<User>;
  loginWithOTP: (phone: string, otp: string) => Promise<User>;
  sendOTP: (phone: string) => Promise<string | null>;
  register: (data: any) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  updatePreferences: (prefs: PreferenceUpdate) => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Hydrate accessibility & language settings from user profile into DOM/storage */
function hydrateSettings(userObj: User) {
  if (typeof window === 'undefined') return;

  const a11y = userObj.accessibility_settings || {};
  if (Object.keys(a11y).length > 0) {
    localStorage.setItem('cultivax_accessibility', JSON.stringify(a11y));
    document.documentElement.classList.toggle('large-text', !!a11y.largeText);
    document.documentElement.classList.toggle('high-contrast', !!a11y.highContrast);
    document.documentElement.classList.toggle('reduce-motion', !!a11y.reducedMotion);
    document.documentElement.classList.toggle('dark-mode', a11y.theme === 'dark');
  }

  if (userObj.preferred_language) {
    document.documentElement.lang = userObj.preferred_language;
    document.cookie = `locale=${userObj.preferred_language}; path=/; max-age=31536000; SameSite=Lax`;
    localStorage.setItem('cultivax_locale', userObj.preferred_language);
  }
}

// ─── Provider ─────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Handle Background Sync Messages from Service Worker
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === 'SYNC_OFFLINE_ACTIONS') {
        console.log('[App] Received sync trigger from Service Worker');
        offlineQueue.init().then(() => offlineQueue.syncActions()).catch(console.error);
      }
    };
    if (typeof navigator !== 'undefined' && 'serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', handleMessage);
      return () => navigator.serviceWorker.removeEventListener('message', handleMessage);
    }
  }, []);

  // Verify session on mount (reads HttpOnly cookie via /auth/me)
  useEffect(() => {
    const initSession = async () => {
      // Instant render with cached data
      const cached = getCachedUser();
      if (cached) setUser(cached);

      // Verify with server
      const serverUser = await verifySession();
      if (serverUser) {
        setUser(serverUser);
        setCachedUser(serverUser);
        hydrateSettings(serverUser);
      } else {
        setUser(null);
      }
      setIsLoading(false);
    };

    initSession();
  }, []);

  const login = useCallback(async (phone: string, password: string): Promise<User> => {
    const response = await apiPost<{ user: User }>(
      '/api/v1/auth/login',
      { phone, password }
    );
    setCachedUser(response.user);
    setUser(response.user);
    hydrateSettings(response.user);
    return response.user;
  }, []);

  const loginWithOTP = useCallback(async (phone: string, otp: string): Promise<User> => {
    const response = await apiPost<{ user: User }>(
      '/api/v1/auth/verify-otp',
      { phone, otp }
    );
    setCachedUser(response.user);
    setUser(response.user);
    hydrateSettings(response.user);
    return response.user;
  }, []);

  const sendOTP = useCallback(async (phone: string): Promise<string | null> => {
    const response = await apiPost<{ debug_otp?: string }>(
      '/api/v1/auth/send-otp',
      { phone }
    );
    return response.debug_otp || null;
  }, []);

  const register = useCallback(async (data: any): Promise<User> => {
    const response = await apiPost<{ user: User }>(
      '/api/v1/auth/register',
      data
    );
    setCachedUser(response.user);
    setUser(response.user);
    hydrateSettings(response.user);
    return response.user;
  }, []);

  const logout = useCallback(async () => {
    await performLogout();
    setUser(null);
    if (typeof document !== 'undefined') {
      document.documentElement.classList.remove(
        'large-text', 'high-contrast', 'reduce-motion', 'dark-mode'
      );
    }
  }, []);

  const refreshUser = useCallback(async () => {
    const serverUser = await verifySession();
    if (serverUser) {
      setUser(serverUser);
      setCachedUser(serverUser);
      hydrateSettings(serverUser);
    }
  }, []);

  /**
   * Update user preferences (language / accessibility) via PATCH /auth/me.
   * Updates backend, then syncs local state + DOM immediately — no page reload.
   */
  const updatePreferences = useCallback(async (prefs: PreferenceUpdate) => {
    const updated = await apiPatch<User>('/api/v1/auth/me', prefs);
    setUser((prev) => {
      if (!prev) return prev;
      const merged = { ...prev, ...updated };
      setCachedUser(merged);
      hydrateSettings(merged);
      return merged;
    });
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        loginWithOTP,
        sendOTP,
        register,
        logout,
        refreshUser,
        updatePreferences,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
