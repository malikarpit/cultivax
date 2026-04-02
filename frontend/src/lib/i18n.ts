/**
 * i18n Configuration — CultivaX Internationalization
 *
 * Uses i18next with HTTP backend to load translations
 * from the backend API at /api/v1/translations/{locale}.
 *
 * Initialization flow:
 *  1. Browser language detector sets initial language
 *  2. AuthContext overrides with user.preferred_language
 *  3. Translations loaded via API (cached in memory)
 *  4. English fallback strings embedded for offline/fast boot
 *
 * Usage in components:
 *   import { useTranslation } from 'react-i18next';
 *   const { t } = useTranslation();
 *   <h1>{t('dashboard.welcome')}</h1>
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import HttpBackend from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

i18n
  .use(HttpBackend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    supportedLngs: ['en', 'hi', 'ta', 'te', 'mr'],
    defaultNS: 'translation',
    debug: process.env.NODE_ENV === 'development',

    interpolation: {
      escapeValue: false, // React already escapes
    },

    backend: {
      loadPath: `${API_URL}/api/v1/translations/{{lng}}`,
      // Transform API response — our backend returns { locale, strings: { ... } }
      parse: (data: string) => {
        try {
          const parsed = JSON.parse(data);
          return parsed.strings || parsed;
        } catch {
          return {};
        }
      },
    },

    detection: {
      order: ['localStorage', 'cookie', 'navigator'],
      lookupLocalStorage: 'cultivax_locale',
      lookupCookie: 'locale',
      caches: ['localStorage'],
    },

    // Embedded English fallback — ensures core UI renders even if API fails
    resources: {
      en: {
        translation: {
          // ─── Navigation ───
          'nav.dashboard': 'Dashboard',
          'nav.crops': 'My Crops',
          'nav.services': 'Services',
          'nav.weather': 'Weather',
          'nav.alerts': 'Alerts',
          'nav.provider': 'Provider',
          'nav.admin': 'Admin',

          // ─── Dashboard ───
          'dashboard.welcome': 'Welcome to CultivaX',
          'dashboard.subtitle': 'Manage your crops intelligently',
          'dashboard.total_crops': 'Total Crops',
          'dashboard.active_crops': 'Active Crops',
          'dashboard.alerts': 'Alerts',
          'dashboard.risk_score': 'Risk Score',

          // ─── Crops ───
          'crops.title': 'My Crops',
          'crops.new': 'New Crop',
          'crops.create': 'Create Crop',
          'crops.no_crops': 'No crops yet',
          'crops.sowing_date': 'Sowing Date',
          'crops.crop_type': 'Crop Type',
          'crops.region': 'Region',
          'crops.stage': 'Stage',
          'crops.actions': 'Actions',
          'crops.history': 'History',
          'crops.simulate': 'Simulate',
          'crops.log_action': 'Log Action',

          // ─── Services ───
          'services.title': 'Service Marketplace',
          'services.request': 'Request Service',
          'services.providers': 'Providers',
          'services.browse': 'Browse Services',

          // ─── Common ───
          'btn.save': 'Save',
          'btn.cancel': 'Cancel',
          'btn.submit': 'Submit',
          'btn.delete': 'Delete',
          'btn.edit': 'Edit',
          'btn.back': 'Back',
          'btn.next': 'Next',
          'btn.loading': 'Loading...',

          // ─── Auth ───
          'auth.login': 'Log In',
          'auth.register': 'Register',
          'auth.logout': 'Log Out',
          'auth.phone': 'Phone Number',
          'auth.password': 'Password',
          'auth.otp': 'Enter OTP',

          // ─── Accessibility ───
          'a11y.title': 'Accessibility',
          'a11y.large_text': 'Large Text',
          'a11y.high_contrast': 'High Contrast',
          'a11y.reduce_motion': 'Reduce Motion',
          'a11y.dark_mode': 'Dark Mode',
          'a11y.light_mode': 'Light Mode',

          // ─── Simulation ───
          'simulation.title': 'What-If Simulation',
          'simulation.subtitle': 'Test hypothetical actions without affecting your actual crop data.',
          'simulation.results': 'Simulation Results',
          'simulation.addAction': '+ Add Action',
          'simulation.runSimulation': 'Run Simulation',
          'simulation.running': 'Running...',
          'simulation.removeAction': 'Remove action',
          'simulation.actionsApplied': '{{count}} hypothetical action(s) applied. Live crop data remains unchanged.',
          'simulation.current': 'Current',
          'simulation.projected': 'Projected',
          'simulation.stateLabel': 'State',
          'simulation.stressLabel': 'Stress',
          'simulation.riskLabel': 'Risk',
          'simulation.dayLabel': 'Day',
          'simulation.stageLabel': 'Stage',
          'simulation.dateLabel': 'Date',
          'simulation.detailsLabel': 'Details',
          'simulation.notAvailable': 'N/A',
          'simulation.notSpecified': 'Not specified',
          'simulation.stressDelta': 'Stress Delta',
          'simulation.riskDelta': 'Risk Delta',
          'simulation.dayDelta': 'Day Delta',
          'simulation.stageChanged': 'Stage Changed',
          'simulation.stageTransitions': 'Stage Transitions',
          'simulation.transitionRow': 'Day {{day}}: {{from}} -> {{to}} (action {{action}})',
          'simulation.actionBreakdown': 'Action Breakdown',
          'simulation.warnings': 'Warnings',
          'simulation.actionTypes.irrigation': 'Irrigation',
          'simulation.actionTypes.fertilizer': 'Fertilizer',
          'simulation.actionTypes.pesticide': 'Pesticide',
          'simulation.actionTypes.weeding': 'Weeding',
          'simulation.actionTypes.inspection': 'Inspection',
          'simulation.actionTypes.delayed_action': 'Delayed Action',

          // ─── Yield ───
          'yield.loadingCrop': 'Loading crop details...',
          'yield.backToCrops': 'Back to Crops',
          'yield.submittedTitle': 'Yield Submitted!',
          'yield.submittedMessage': 'Your harvest data for {{crop}} has been recorded successfully.',
          'yield.verificationSummary': 'Verification Summary',
          'yield.reportedLabel': 'Reported',
          'yield.mlYieldLabel': 'ML Yield',
          'yield.biologicalCapLabel': 'Biological Cap',
          'yield.capAppliedLabel': 'Cap Applied',
          'yield.verificationScoreLabel': 'Verification Score',
          'yield.notAvailable': 'N/A',
          'yield.viewCrop': 'View Crop',
          'yield.dashboard': 'Dashboard',
          'yield.readyToHarvestRequired': 'Yield submission is enabled only when crop state is ReadyToHarvest.',

          // ─── Misc ───
          'error.generic': 'Something went wrong',
          'error.network': 'Network error. Please try again.',
          'error.session_expired': 'Session expired. Please log in again.',
        },
      },
    },
  });

export default i18n;
