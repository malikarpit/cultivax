'use client';

import Link from 'next/link';
import { ArrowLeft, FileText, Leaf } from 'lucide-react';
import Footer from '@/components/Footer';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import LanguageSwitcher from '@/components/LanguageSwitcher';

export default function TermsOfService() {
  const router = useRouter();
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-cultivax-bg text-cultivax-text-primary flex flex-col">
      <nav className="h-16 border-b border-cultivax-border flex items-center px-4 sm:px-6 bg-cultivax-bg/80 backdrop-blur-lg fixed top-0 w-full z-50 justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-cultivax-primary/15 rounded-lg flex items-center justify-center">
            <Leaf className="w-5 h-5 text-cultivax-primary" />
          </div>
          <span className="font-bold text-lg">CultivaX</span>
        </Link>
        <div className="flex items-center gap-3">
          <LanguageSwitcher compact />
        </div>
      </nav>
      <div className="flex-1 pt-24 px-4 pb-12">
        <div className="max-w-4xl mx-auto w-full">
      <button onClick={() => router.back()} className="inline-flex items-center gap-2 text-cultivax-primary hover:underline mb-8 font-medium bg-transparent border-none cursor-pointer p-0">
        <ArrowLeft className="w-4 h-4" /> {t('btn.back', 'Go Back')}
      </button>
      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 rounded-xl bg-cultivax-primary/10 flex items-center justify-center">
          <FileText className="w-6 h-6 text-cultivax-primary" />
        </div>
        <h1 className="text-4xl font-bold text-cultivax-text-primary">{t('terms.title', 'Terms of Service')}</h1>
      </div>
      <div className="prose prose-invert prose-m3 max-w-none text-cultivax-text-secondary pr-4">
        <p className="text-lg mb-6">{t('terms.lastUpdated', 'Last updated: April 2026')}</p>
        <div className="glass-card rounded-2xl p-8 border border-cultivax-border space-y-6">
          <div>
            <h2 className="text-xl font-bold text-cultivax-text-primary mb-2">{t('terms.section1.title', '1. Agreement to Terms & Architecture Compliance')}</h2>
            <p>{t('terms.section1.desc', 'By accessing or using CultivaX, you agree to be bound by these Terms of Service. CultivaX operates on a strictly event-driven state architecture (CTIS). Data inputs are evaluated through our Risk Pipeline and processed sequentially. Any attempts to subvert or bypass the event dispatch mechanics are prohibited.')}</p>
          </div>
          <div>
            <h2 className="text-xl font-bold text-cultivax-text-primary mb-2">{t('terms.section2.title', '2. CTIS Analytics & Risk Model Disclaimer')}</h2>
            <p>{t('terms.section2.desc', 'CultivaX provides AI-driven Crop Timeline Intelligence (CTIS) via our interconnected Stress Engine, Drift clamp analysis, and ML inference runtime. While we leverage dynamically updated `RegionalClusters` for hyper-local accuracy, all forecasts (including What-If replay computations) are for guidance only. You remain fully responsible for physical farming decisions. CultivaX is not liable for weather anomalies, crop failures, or deviations from predicted ML yields.')}</p>
          </div>
          <div>
            <h2 className="text-xl font-bold text-cultivax-text-primary mb-2">{t('terms.section3.title', '3. Marketplace Trust Engine & Anti-Fraud')}</h2>
            <p>{t('terms.section3.desc', 'Our System of Engagement (SOE) utilizes a strict Trust Engine and dynamic Fairness Distribution algorithms to govern equipment/labor booking. Users are subject to automated Fraud Detector evaluations and Escalation Policies. CultivaX reserves the right to automatically suspend offending Provider or Farmer accounts based on complaint density, transaction timeouts, or identified malicious behavior within the rolling distribution windows.')}</p>
          </div>
          <div>
            <h2 className="text-xl font-bold text-cultivax-text-primary mb-2">{t('terms.section4.title', '4. User Accounts & Offline Usage')}</h2>
            <p>{t('terms.section4.desc', 'You are responsible for safeguarding your login credentials (HTTPOnly authenticated). While CultivaX supports offline action queuing via Service Workers, you remain responsible for ensuring eventual network connections to allow global synchronization. CultivaX relies on your operational security and timely synching as the first line of defense against data drift.')}</p>
          </div>
        </div>
      </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}
