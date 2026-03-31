'use client';

/**
 * useAccessibility Hook
 *
 * Manages accessibility settings with a three-layer priority:
 *   1. Backend (user.accessibility_settings via AuthContext) — source of truth
 *   2. localStorage — offline / unauthenticated fallback
 *   3. Defaults — safe baseline
 *
 * Updating settings saves to both backend (via updatePreferences) and
 * localStorage as an offline fallback. CSS classes are applied to <html>.
 *
 * MSDD Section 7.1–7.2 compliance.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth, type AccessibilitySettings } from '@/context/AuthContext';

const STORAGE_KEY = 'cultivax_accessibility';

const DEFAULT_SETTINGS: AccessibilitySettings = {
  largeText: false,
  highContrast: false,
  reducedMotion: false,
  theme: 'light',
  sidebarPinned: false,
};

function loadFromStorage(): AccessibilitySettings {
  if (typeof window === 'undefined') return DEFAULT_SETTINGS;
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
  } catch {
    // Ignore parse errors
  }
  return DEFAULT_SETTINGS;
}

function applyToDOM(settings: AccessibilitySettings) {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  root.classList.toggle('large-text',    !!settings.largeText);
  root.classList.toggle('high-contrast', !!settings.highContrast);
  root.classList.toggle('reduce-motion', !!settings.reducedMotion);
  root.classList.toggle('dark-mode',     settings.theme === 'dark');
}

export function useAccessibility() {
  const { user, updatePreferences } = useAuth();
  const hydrated = useRef(false);

  // Initialize from localStorage (instant, no flash)
  const [settings, setSettings] = useState<AccessibilitySettings>(loadFromStorage);

  // Hydrate from backend once user loads — backend is source of truth
  useEffect(() => {
    if (user && !hydrated.current) {
      hydrated.current = true;
      const backendSettings = user.accessibility_settings || {};
      if (Object.keys(backendSettings).length > 0) {
        const merged = { ...DEFAULT_SETTINGS, ...backendSettings };
        setSettings(merged);
        applyToDOM(merged);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
      }
    }
  }, [user]);

  // Apply to DOM whenever settings change
  useEffect(() => {
    applyToDOM(settings);
  }, [settings]);

  /**
   * Update a single or multiple accessibility settings.
   * Saves to backend (if authed) and localStorage.
   */
  const updateSettings = useCallback(async (partial: Partial<AccessibilitySettings>) => {
    const next = { ...settings, ...partial };
    setSettings(next);
    applyToDOM(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));

    if (user) {
      try {
        await updatePreferences({ accessibility_settings: next });
      } catch (err) {
        console.error('Failed to save accessibility settings to backend:', err);
        // Still kept in localStorage as fallback
      }
    }
  }, [settings, user, updatePreferences]);

  // Convenience toggles
  const toggleLargeText = useCallback(
    () => updateSettings({ largeText: !settings.largeText }),
    [settings.largeText, updateSettings]
  );

  const toggleHighContrast = useCallback(
    () => updateSettings({ highContrast: !settings.highContrast }),
    [settings.highContrast, updateSettings]
  );

  const toggleReducedMotion = useCallback(
    () => updateSettings({ reducedMotion: !settings.reducedMotion }),
    [settings.reducedMotion, updateSettings]
  );

  const toggleTheme = useCallback(
    () => updateSettings({ theme: settings.theme === 'dark' ? 'light' : 'dark' }),
    [settings.theme, updateSettings]
  );

  const toggleSidebarPinned = useCallback(
    () => updateSettings({ sidebarPinned: !settings.sidebarPinned }),
    [settings.sidebarPinned, updateSettings]
  );

  const resetDefaults = useCallback(
    () => updateSettings(DEFAULT_SETTINGS),
    [updateSettings]
  );

  return {
    settings,
    updateSettings,
    toggleLargeText,
    toggleHighContrast,
    toggleReducedMotion,
    toggleTheme,
    toggleSidebarPinned,
    resetDefaults,
  };
}
