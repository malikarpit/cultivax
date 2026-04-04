'use client';

/**
 * Landing Page — CultivaX Public Homepage
 *
 * Full public landing with:
 * - Top navbar with public links
 * - Hero section with farmer-specific messaging
 * - Feature grid (6 cards)
 * - Process flow (4 steps)
 * - Bottom CTA
 * - Footer
 */

import Link from 'next/link';
import {
  Leaf,
  Sprout,
  Bell,
  FlaskConical,
  WifiOff,
  Globe,
  Shield,
  ArrowRight,
  ChevronRight,
  Menu,
  X,
} from 'lucide-react';
import { useState } from 'react';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import Footer from '@/components/Footer';

const FEATURES = [
  {
    icon: Sprout,
    title: 'Crop Timeline',
    desc: 'Track every stage from sowing to harvest with day-by-day progress and growth alerts.',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
  },
  {
    icon: Bell,
    title: 'Smart Alerts',
    desc: 'Get notified when your crop needs attention — stress indicators, weather events, or missed actions.',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
  },
  {
    icon: FlaskConical,
    title: 'What-If Simulation',
    desc: 'Test hypothetical actions before committing. See how irrigation or fertilizer changes would affect outcomes.',
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
  },
  {
    icon: WifiOff,
    title: 'Offline Sync',
    desc: 'Works without internet, syncs when connected — designed for field use on any device.',
    color: 'text-purple-400',
    bg: 'bg-purple-500/10',
  },
  {
    icon: Globe,
    title: 'Local Language',
    desc: 'Full interface available in Hindi and English with more languages coming soon.',
    color: 'text-teal-400',
    bg: 'bg-teal-500/10',
  },
  {
    icon: Shield,
    title: 'Trusted Providers',
    desc: 'Find verified service providers with transparent trust scores, reviews, and fair pricing.',
    color: 'text-rose-400',
    bg: 'bg-rose-500/10',
  },
];

const PROCESS = [
  {
    step: '01',
    title: 'Create Crop',
    desc: 'Add your crop details and map your field boundaries',
    icon: '🌱',
  },
  {
    step: '02',
    title: 'Log Actions',
    desc: 'Record irrigation, fertilizer, pesticide applications',
    icon: '📝',
  },
  {
    step: '03',
    title: 'Get Alerts',
    desc: 'Receive smart notifications and AI recommendations',
    icon: '🔔',
  },
  {
    step: '04',
    title: 'Book Services',
    desc: 'Find and hire trusted agricultural service providers',
    icon: '🤝',
  },
];

export default function LandingPage() {
  const [mobileNav, setMobileNav] = useState(false);

  return (
    <div className="min-h-screen bg-cultivax-bg text-cultivax-text-primary">
      {/* ─── Navbar ─────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-cultivax-bg/80 backdrop-blur-lg border-b border-cultivax-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-cultivax-primary/15 rounded-lg flex items-center justify-center">
              <Leaf className="w-5 h-5 text-cultivax-primary" />
            </div>
            <span className="font-bold text-lg">CultivaX</span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-6">
            <a href="#features" className="text-sm text-cultivax-text-secondary hover:text-cultivax-text-primary transition-colors">
              Features
            </a>
            <a href="#how-it-works" className="text-sm text-cultivax-text-secondary hover:text-cultivax-text-primary transition-colors">
              How It Works
            </a>
            <a href="#for-farmers" className="text-sm text-cultivax-text-secondary hover:text-cultivax-text-primary transition-colors">
              For Farmers
            </a>
            <a href="#for-providers" className="text-sm text-cultivax-text-secondary hover:text-cultivax-text-primary transition-colors">
              For Providers
            </a>
          </div>

          {/* Right actions */}
          <div className="hidden md:flex items-center gap-3">
            <LanguageSwitcher compact />
            <Link href="/login" className="btn-ghost text-sm">
              Sign In
            </Link>
            <Link href="/register" className="btn-primary text-sm">
              Get Started
            </Link>
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden btn-icon"
            onClick={() => setMobileNav(!mobileNav)}
          >
            {mobileNav ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile nav dropdown */}
        {mobileNav && (
          <div className="md:hidden bg-cultivax-surface border-t border-cultivax-border animate-slide-down">
            <div className="px-4 py-4 space-y-3">
              <a href="#features" className="block text-sm text-cultivax-text-secondary py-2" onClick={() => setMobileNav(false)}>Features</a>
              <a href="#how-it-works" className="block text-sm text-cultivax-text-secondary py-2" onClick={() => setMobileNav(false)}>How It Works</a>
              <div className="flex gap-3 pt-2">
                <Link href="/login" className="btn-secondary text-sm flex-1 text-center">Sign In</Link>
                <Link href="/register" className="btn-primary text-sm flex-1 text-center">Get Started</Link>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* ─── Hero ───────────────────────────────────────── */}
      <section className="relative pt-32 pb-20 px-4" id="for-farmers">
        {/* Background grid pattern */}
        <div className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(rgba(16,185,129,0.3) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(16,185,129,0.3) 1px, transparent 1px)`,
            backgroundSize: '60px 60px',
          }}
        />
        {/* Gradient glow */}
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-cultivax-primary/5 blur-[120px] rounded-full pointer-events-none" />

        <div className="relative max-w-4xl mx-auto text-center">
          {/* Tag */}
          <div className="inline-flex items-center gap-2 bg-cultivax-primary/10 border border-cultivax-primary/20 rounded-full px-4 py-1.5 text-sm text-cultivax-primary mb-6">
            <Leaf className="w-4 h-4" />
            Intelligent Crop Management for Indian Farmers
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold leading-tight mb-6">
            <span className="gradient-text">Track Crops.</span>{' '}
            <span className="text-cultivax-text-primary">Get Alerts.</span>{' '}
            <span className="gradient-text">Book Services.</span>
          </h1>

          <p className="text-lg sm:text-xl text-cultivax-text-secondary max-w-2xl mx-auto mb-10 leading-relaxed">
            CultivaX helps Indian farmers manage crop lifecycles with smart alerts,
            what-if simulations, and a trusted service marketplace — all in your language.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/register"
              className="btn-primary text-base px-8 py-3.5 flex items-center gap-2 group"
            >
              Start Your First Crop
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/tour"
              className="btn-secondary text-base px-8 py-3.5"
            >
              See How It Works
            </Link>
          </div>
        </div>
      </section>

      {/* ─── Features ───────────────────────────────────── */}
      <section className="py-20 px-4" id="features">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold mb-4">
              Everything You Need to Grow Smarter
            </h2>
            <p className="text-cultivax-text-secondary max-w-xl mx-auto">
              From sowing to harvest, CultivaX provides the intelligence tools modern farming demands.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="card-interactive p-6 group"
              >
                <div className={`w-11 h-11 rounded-xl ${f.bg} flex items-center justify-center mb-4`}>
                  <f.icon className={`w-6 h-6 ${f.color}`} />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-cultivax-text-primary">
                  {f.title}
                </h3>
                <p className="text-sm text-cultivax-text-secondary leading-relaxed">
                  {f.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Process Flow ───────────────────────────────── */}
      <section className="py-20 px-4 bg-cultivax-surface/50" id="how-it-works">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold mb-4">How CultivaX Works</h2>
            <p className="text-cultivax-text-secondary">
              Four simple steps to smarter farming
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {PROCESS.map((p, i) => (
              <div key={p.step} className="relative text-center group">
                {/* Connector line (desktop) */}
                {i < PROCESS.length - 1 && (
                  <div className="hidden lg:block absolute top-10 left-[60%] w-[80%] h-[1px] bg-cultivax-border" />
                )}

                <div className="relative z-10">
                  <div className="w-20 h-20 mx-auto mb-4 bg-cultivax-elevated rounded-2xl flex items-center justify-center text-3xl group-hover:scale-110 transition-transform">
                    {p.icon}
                  </div>
                  <span className="text-xs font-bold text-cultivax-primary uppercase tracking-widest">
                    Step {p.step}
                  </span>
                  <h3 className="text-lg font-semibold mt-2 mb-2">{p.title}</h3>
                  <p className="text-sm text-cultivax-text-secondary">{p.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── For Providers ──────────────────────────────── */}
      <section className="py-20 px-4" id="for-providers">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">For Service Providers</h2>
          <p className="text-cultivax-text-secondary max-w-xl mx-auto mb-8">
            Reach thousands of farmers, manage your services, and build trust through transparent ratings.
          </p>
          <Link
            href="/register"
            className="btn-secondary text-base px-8 py-3 inline-flex items-center gap-2"
          >
            Register as a Provider <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* ─── Bottom CTA ─────────────────────────────────── */}
      <section className="py-20 px-4">
        <div className="max-w-3xl mx-auto text-center bg-cultivax-surface border border-cultivax-border rounded-3xl p-10 sm:p-14 relative overflow-hidden">
          {/* Glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[200px] bg-cultivax-primary/10 blur-[100px] rounded-full pointer-events-none" />

          <div className="relative">
            <h2 className="text-2xl sm:text-3xl font-bold mb-4">
              Start your first crop — it takes 2 minutes
            </h2>
            <p className="text-cultivax-text-secondary mb-8">
              Join thousands of Indian farmers using CultivaX to grow smarter.
            </p>
            <Link
              href="/register"
              className="btn-primary text-base px-10 py-3.5 inline-flex items-center gap-2 group"
            >
              Get Started Free
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
