'use client';

import Link from 'next/link';
import { ArrowLeft, Shield, Leaf } from 'lucide-react';
import Footer from '@/components/Footer';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import LanguageSwitcher from '@/components/LanguageSwitcher';

export default function PrivacyPolicy() {
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
          <Shield className="w-6 h-6 text-cultivax-primary" />
        </div>
        <h1 className="text-4xl font-bold text-cultivax-text-primary">{t('privacy.title', 'Privacy Policy')}</h1>
      </div>
      <div className="prose prose-invert prose-m3 max-w-none text-cultivax-text-secondary pr-4">
        <p className="text-lg mb-6">{t('privacy.lastUpdated', 'Last updated: April 2026')}</p>
        <div className="glass-card rounded-2xl p-8 border border-cultivax-border">
          <h2 className="text-xl font-bold text-cultivax-text-primary mb-4">{t('privacy.section1.title', '1. Data Collection & Offline Syncing')}</h2>
          <p className="mb-6">{t('privacy.section1.desc', 'At CultivaX, data collection begins on the farm. As you perform tasks (irrigation, weeding, nutrient application), our Service Worker Background Sync captures these offline actions. Your local cache queues these mutations securely and relays them to our asynchronous event dispatcher when connectivity is restored, ensuring zero data loss without risking manual data manipulation.')}</p>

          <h2 className="text-xl font-bold text-cultivax-text-primary mb-4">{t('privacy.section2.title', '2. The SOE Trust Engine & Fraud Telemetry')}</h2>
          <p className="mb-6">{t('privacy.section2.desc', 'For providers and farmers engaging in the marketplace, our System Of Engagement (SOE) collects telemetry natively. This includes tracking preferred dates against exact completion dates (`completed_at`). This data fuels our Trust Engine and Fraud Detection pipelines—analyzing behavioral deviations to enforce fairness and suspend malicious actors securely.')}</p>

          <h2 className="text-xl font-bold text-cultivax-text-primary mb-4">{t('privacy.section3.title', '3. ML Inference & Regional Cluster Auditing')}</h2>
          <p className="mb-6">{t('privacy.section3.desc', 'Your localized yield results and stage offset delays dictate the dynamic prospective updates to your region\'s `RegionalClusters`. While individual crop parameters (stress scores, anomaly penalties) are deeply analyzed by our Machine Learning inference runtime, all global ML audit traces remain completely obfuscated, retaining mathematical outcomes while dissolving personally identifiable data.')}</p>

          <h2 className="text-xl font-bold text-cultivax-text-primary mb-4">{t('privacy.section4.title', '4. Deterministic State Mutations & Integrity')}</h2>
          <p className="mb-4">{t('privacy.section4.desc', 'You have full authority over your data. Because CultivaX natively enforces strictly event-driven state mutations and prohibits direct arbitrary database writes, your historical timeline and risk indicators are mathematically auditable. You can permanently export your CTIS replay logs or initiate a fully compliant data deletion request from your account menu directly.')}</p>
        </div>
      </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}
