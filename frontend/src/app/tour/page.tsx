'use client';

/**
 * Tour Page — Interactive product walkthrough
 *
 * 5-step guided tour with:
 * - Step cards with icons and descriptions
 * - Progress indicator + animated transitions
 * - Telemetry: records tour_seen, completion step, timestamp
 * - Repeat-visitor detection: auto-redirects if tour already seen
 * - Skip + navigation
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Sprout, MapPin, ClipboardList, FlaskConical,
  ShoppingBag, ArrowRight, ArrowLeft, X, Leaf,
  Check,
} from 'lucide-react';
import clsx from 'clsx';

const TOUR_STEPS = [
  {
    icon: Sprout,
    title: 'Create Your Crop',
    desc: 'Start by adding your first crop — choose the type, variety, and sowing date. We\'ll track everything from here.',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    visual: '🌱',
  },
  {
    icon: MapPin,
    title: 'Map Your Field',
    desc: 'Draw your field boundary on the map. We use this for weather data, satellite analysis, and area calculation.',
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    visual: '🗺️',
  },
  {
    icon: ClipboardList,
    title: 'Log Actions & Get Alerts',
    desc: 'Record irrigation, fertilizer, pesticide applications. CultivaX monitors stress and sends you alerts.',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    visual: '📋',
  },
  {
    icon: FlaskConical,
    title: 'What-If Simulation',
    desc: 'Test actions before committing. See how irrigation would affect your crop\'s stress score and yield.',
    color: 'text-purple-400',
    bg: 'bg-purple-500/10',
    visual: '🧪',
  },
  {
    icon: ShoppingBag,
    title: 'Book Services',
    desc: 'Find verified providers — soil testing, drone survey, harvest labor. Trust scores help you choose right.',
    color: 'text-rose-400',
    bg: 'bg-rose-500/10',
    visual: '🤝',
  },
];

/* ─── Tour Telemetry Helpers ─────────────────────────────── */

function isTourSeen(): boolean {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem('cultivax_tour_seen') === 'true';
}

function markTourSeen(finalStep: number, completed: boolean) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('cultivax_tour_seen', 'true');
  localStorage.setItem('cultivax_tour_completed_at', new Date().toISOString());
  localStorage.setItem('cultivax_tour_final_step', String(finalStep + 1));
  localStorage.setItem('cultivax_tour_completed', String(completed));
}

/* ─── Component ──────────────────────────────────────────── */

export default function TourPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [ready, setReady] = useState(false);

  // Redirect repeat visitors — they've already seen the tour
  useEffect(() => {
    if (isTourSeen()) {
      router.replace('/register');
    } else {
      setReady(true);
    }
  }, [router]);

  const step = TOUR_STEPS[currentStep];
  const isLast = currentStep === TOUR_STEPS.length - 1;

  const handleNext = () => {
    if (isLast) {
      markTourSeen(currentStep, true); // completed = true
      router.push('/register');
    } else {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    markTourSeen(currentStep, false); // completed = false (skipped)
    router.push('/register');
  };

  // Don't render until we've checked localStorage (prevents flash)
  if (!ready) return null;

  return (
    <div className="min-h-screen bg-cultivax-bg flex flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 sm:px-6 h-16 border-b border-cultivax-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-cultivax-primary/15 rounded-lg flex items-center justify-center">
            <Leaf className="w-5 h-5 text-cultivax-primary" />
          </div>
          <span className="font-bold text-lg">CultivaX</span>
        </div>
        <button
          onClick={handleSkip}
          className="text-sm text-cultivax-text-muted hover:text-cultivax-text-secondary flex items-center gap-1 transition-colors"
        >
          Skip Tour <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="max-w-xl w-full">
          {/* Progress dots */}
          <div className="flex items-center justify-center gap-2 mb-10">
            {TOUR_STEPS.map((_, i) => (
              <button
                key={i}
                onClick={() => setCurrentStep(i)}
                className={clsx(
                  'transition-all duration-300 rounded-full',
                  i === currentStep
                    ? 'w-8 h-2 bg-cultivax-primary'
                    : i < currentStep
                    ? 'w-2 h-2 bg-cultivax-primary/50'
                    : 'w-2 h-2 bg-cultivax-elevated'
                )}
              />
            ))}
          </div>

          {/* Step card */}
          <div key={currentStep} className="card p-8 text-center animate-fade-in">
            {/* Visual */}
            <div className="text-6xl mb-6">{step.visual}</div>

            {/* Icon badge */}
            <div className={clsx('w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center', step.bg)}>
              <step.icon className={clsx('w-7 h-7', step.color)} />
            </div>

            {/* Step number */}
            <span className="text-xs font-bold text-cultivax-primary uppercase tracking-widest">
              Step {currentStep + 1} of {TOUR_STEPS.length}
            </span>

            {/* Title */}
            <h2 className="text-2xl font-bold mt-3 mb-3">{step.title}</h2>

            {/* Description */}
            <p className="text-cultivax-text-secondary leading-relaxed max-w-md mx-auto">
              {step.desc}
            </p>
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8">
            <button
              onClick={handlePrev}
              disabled={currentStep === 0}
              className={clsx(
                'btn-secondary flex items-center gap-2',
                currentStep === 0 && 'opacity-0 pointer-events-none'
              )}
            >
              <ArrowLeft className="w-4 h-4" /> Previous
            </button>

            <button
              onClick={handleNext}
              className="btn-primary flex items-center gap-2"
            >
              {isLast ? (
                <>
                  Get Started <Check className="w-4 h-4" />
                </>
              ) : (
                <>
                  Next Step <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
