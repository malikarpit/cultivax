'use client';

import Link from 'next/link';
import { ArrowLeft, LifeBuoy, Mail, Phone, MessageSquare, Leaf } from 'lucide-react';
import Footer from '@/components/Footer';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import LanguageSwitcher from '@/components/LanguageSwitcher';

export default function SupportPage() {
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
          <LifeBuoy className="w-6 h-6 text-cultivax-primary" />
        </div>
        <h1 className="text-4xl font-bold text-cultivax-text-primary">{t('support.title', 'Help & Support')}</h1>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
        {/* Email Support */}
        <div className="glass-card rounded-2xl p-6 border border-cultivax-border hover:border-cultivax-primary/30 transition-colors">
          <Mail className="w-8 h-8 text-cultivax-primary mb-4" />
          <h3 className="text-lg font-bold text-cultivax-text-primary mb-2">{t('support.email.title', 'Email Us')}</h3>
          <p className="text-sm text-cultivax-text-secondary mb-4">{t('support.email.desc', 'For general inquiries, feature requests, or complex account issues.')}</p>
          <div className="flex flex-col gap-2">
            <a href="mailto:support-ticket@cultivax.notreal" className="text-cultivax-primary font-medium hover:underline break-all">support-ticket@cultivax.notreal</a>
            <span className="text-xs text-cultivax-text-muted mt-2 border-t border-cultivax-border pt-2 block">
              {t('support.alternateContact', 'Alternate Contact:')} <a href="mailto:malikarpit40@icloud.com" className="text-cultivax-text-secondary hover:text-cultivax-primary transition-colors">malikarpit40@icloud.com</a>
            </span>
          </div>
        </div>

        {/* Toll Free Support */}
        <div className="glass-card rounded-2xl p-6 border border-cultivax-border hover:border-cultivax-primary/30 transition-colors">
          <Phone className="w-8 h-8 text-cultivax-primary mb-4" />
          <h3 className="text-lg font-bold text-cultivax-text-primary mb-2">{t('support.phone.title', 'Toll-Free Helpline')}</h3>
          <p className="text-sm text-cultivax-text-secondary mb-4">{t('support.phone.desc', 'Available 24/7 for urgent marketplace or crop emergency support.')}</p>
          <a href="tel:555019847253" className="text-cultivax-primary font-medium hover:underline">+1 (555) 019-8472-53</a>
        </div>
      </div>

      <div className="glass-card rounded-2xl p-8 border border-cultivax-border">
        <div className="flex items-center gap-3 mb-6">
          <MessageSquare className="w-5 h-5 text-cultivax-primary" />
          <h2 className="text-xl font-bold text-cultivax-text-primary">{t('support.faq.title', 'Frequently Asked Questions')}</h2>
        </div>
        <div className="space-y-6 text-cultivax-text-secondary">
          <div>
            <h4 className="font-bold text-cultivax-text-primary mb-1">{t('support.faq.q1.title', 'How accurate is the CultivaX CTIS Risk Model calculations?')}</h4>
            <p className="text-sm">{t('support.faq.q1.desc', 'Our ML Inference Runtime determines crop risk trajectories based on real-time factors: weather predictions, current stress expectations, and any Drift you log (`stage_offset_days`). By feeding this through the regional cluster pipeline, our models actively learn and reduce prediction variability over time.')}</p>
          </div>
          <div>
            <h4 className="font-bold text-cultivax-text-primary mb-1">{t('support.faq.q2.title', 'My SOE Provider/Farmer Account was automatically suspended. Why?')}</h4>
            <p className="text-sm">{t('support.faq.q2.desc', 'CultivaX runs an automated Trust Engine that processes transaction delays, completed date anomalies (`completed_at`), and negative reviews. If the Fraud Detector or Escalation Policy triggers due to a rolling-window threshold breach, your marketplace rights are suspended to guarantee Fairness Distribution exposure for legitimate users. Contact support to appeal an automated lock.')}</p>
          </div>
          <div>
            <h4 className="font-bold text-cultivax-text-primary mb-1">{t('support.faq.q3.title', 'What happens to my actions if I am completely Offline in the field?')}</h4>
            <p className="text-sm">{t('support.faq.q3.desc', 'Continue using your Dashboard normally! The offline sync engine will intercept any timeline changes and queue them via Service Workers. The moment network is restored, those queued actions are fed safely into the asynchronous Dead-Letter Queue (DLQ) dispatcher, preserving exact Event Order partition rules and updating the main database seamlessly.')}</p>
          </div>
        </div>
      </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}
