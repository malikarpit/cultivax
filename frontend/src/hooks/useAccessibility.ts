'use client';

/**
 * useAccessibility Hook
 *
 * Reads and saves accessibility settings from user profile
 * and localStorage. Supports large text mode and high contrast
 * mode per MSDD Section 7.1-7.2.
 *
 * Settings are persisted in localStorage and applied via
 * CSS class names on the <html> element.
 */

import { useState, useEffect, useCallback } from 'react';

export interface AccessibilitySettings {
  largeText: boolean;
  highContrast: boolean;
}

const STORAGE_KEY = 'cultivax_accessibility';

const DEFAULT_SETTINGS: AccessibilitySettings = {
  largeText: false,
  highContrast: false,
};

function loadSettings(): AccessibilitySettings {
  if (typeof window === 'undefined') return DEFAULT_SETTINGS;
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
    }
  } catch {
    // Ignore parse errors
  }
  return DEFAULT_SETTINGS;
}

function applyToDOM(settings: AccessibilitySettings) {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;

  // Large text mode — increase base font-size by 1.5×
  if (settings.largeText) {
    root.classList.add('large-text');
  } else {
    root.classList.remove('large-text');
  }

  // High contrast mode — enhanced contrast ratios
  if (settings.highContrast) {
    root.classList.add('high-contrast');
  } else {
    root.classList.remove('high-contrast');
  }
}

export function useAccessibility() {
  const [settings, setSettings] = useState<AccessibilitySettings>(DEFAULT_SETTINGS);

  // Load on mount
  useEffect(() => {
    const loaded = loadSettings();
    setSettings(loaded);
    applyToDOM(loaded);
  }, []);

  const updateSettings = useCallback((partial: Partial<AccessibilitySettings>) => {
    setSettings((prev) => {
      const next = { ...prev, ...partial };
      // Persist
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      // Apply
      applyToDOM(next);
      return next;
    });
  }, []);

  const toggleLargeText = useCallback(() => {
    updateSettings({ largeText: !settings.largeText });
  }, [settings.largeText, updateSettings]);

  const toggleHighContrast = useCallback(() => {
    updateSettings({ highContrast: !settings.highContrast });
  }, [settings.highContrast, updateSettings]);

  const resetDefaults = useCallback(() => {
    updateSettings(DEFAULT_SETTINGS);
  }, [updateSettings]);

  return {
    settings,
    updateSettings,
    toggleLargeText,
    toggleHighContrast,
    resetDefaults,
  };
}
