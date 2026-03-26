'use client';

/**
 * AccessibilityToggle Component
 *
 * Provides a dropdown/panel for toggling accessibility modes:
 * - Large Text Mode (MSDD 7.1): 1.5× base font-size
 * - High Contrast Mode (MSDD 7.2): enhanced contrast ratios
 *
 * Settings are persisted in localStorage via useAccessibility hook.
 */

import React, { useState, useRef, useEffect } from 'react';
import { useAccessibility } from '@/hooks/useAccessibility';

export default function AccessibilityToggle() {
  const { settings, toggleLargeText, toggleHighContrast } = useAccessibility();
  const [isOpen, setIsOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  // Close panel when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  return (
    <div className="relative" ref={panelRef}>
      {/* Trigger Button */}
      <button
        id="accessibility-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg
          bg-cultivax-card hover:bg-cultivax-surface border border-cultivax-card
          hover:border-cultivax-primary/40 transition-all duration-200"
        aria-label="Accessibility Settings"
        aria-expanded={isOpen}
        title="Accessibility Settings"
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="4.5" r="2.5" />
          <path d="M12 7v5m0 0l-4 7m4-7l4 7M6 11h12" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span className="hidden sm:inline">A11y</span>
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div
          className="absolute right-0 top-full mt-2 w-72 bg-cultivax-surface border
            border-cultivax-card rounded-xl shadow-2xl z-50 overflow-hidden
            animate-in fade-in slide-in-from-top-2 duration-200"
          role="dialog"
          aria-label="Accessibility options"
        >
          {/* Header */}
          <div className="px-4 py-3 border-b border-cultivax-card bg-cultivax-card/30">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <svg viewBox="0 0 24 24" className="w-4 h-4 text-cultivax-primary" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="4.5" r="2.5" />
                <path d="M12 7v5m0 0l-4 7m4-7l4 7M6 11h12" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              Accessibility
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">Adjust display for comfort</p>
          </div>

          {/* Options */}
          <div className="p-3 space-y-2">
            {/* Large Text */}
            <button
              id="toggle-large-text"
              onClick={toggleLargeText}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg
                transition-all duration-200 text-left group
                ${settings.largeText
                  ? 'bg-cultivax-primary/15 border border-cultivax-primary/40'
                  : 'bg-cultivax-card/50 border border-transparent hover:border-cultivax-card'
                }`}
              aria-pressed={settings.largeText}
            >
              <div className="flex items-center gap-3">
                <span className={`text-lg font-bold ${settings.largeText ? 'text-cultivax-primary' : 'text-gray-400'}`}>
                  Aa
                </span>
                <div>
                  <p className="text-sm font-medium text-white">Large Text</p>
                  <p className="text-xs text-gray-400">1.5× larger font size</p>
                </div>
              </div>
              <div className={`w-10 h-5 rounded-full relative transition-colors duration-200
                ${settings.largeText ? 'bg-cultivax-primary' : 'bg-gray-600'}`}>
                <div className={`absolute w-4 h-4 rounded-full bg-white top-0.5 transition-transform duration-200
                  ${settings.largeText ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </div>
            </button>

            {/* High Contrast */}
            <button
              id="toggle-high-contrast"
              onClick={toggleHighContrast}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg
                transition-all duration-200 text-left group
                ${settings.highContrast
                  ? 'bg-cultivax-primary/15 border border-cultivax-primary/40'
                  : 'bg-cultivax-card/50 border border-transparent hover:border-cultivax-card'
                }`}
              aria-pressed={settings.highContrast}
            >
              <div className="flex items-center gap-3">
                <span className={`text-lg ${settings.highContrast ? 'text-cultivax-primary' : 'text-gray-400'}`}>
                  ◐
                </span>
                <div>
                  <p className="text-sm font-medium text-white">High Contrast</p>
                  <p className="text-xs text-gray-400">Enhanced color contrast</p>
                </div>
              </div>
              <div className={`w-10 h-5 rounded-full relative transition-colors duration-200
                ${settings.highContrast ? 'bg-cultivax-primary' : 'bg-gray-600'}`}>
                <div className={`absolute w-4 h-4 rounded-full bg-white top-0.5 transition-transform duration-200
                  ${settings.highContrast ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </div>
            </button>
          </div>

          {/* Footer hint */}
          <div className="px-4 py-2 border-t border-cultivax-card/50 bg-cultivax-card/20">
            <p className="text-[10px] text-gray-500 text-center">
              Settings are saved automatically
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
