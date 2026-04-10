'use client';

/**
 * Footer — Unified footer for all pages
 * © 2026 CultivaX Agricultural Intelligence
 */

import Link from 'next/link';
import { useTranslation } from 'react-i18next';

export default function Footer() {
  const { t } = useTranslation();
  return (
    <footer className="border-t border-cultivax-border mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Copyright */}
          <p className="text-sm text-cultivax-text-muted">
            {t('footer.copyright', '© 2026 CultivaX Agricultural Intelligence. All rights reserved.')}
          </p>

          {/* Links */}
          <div className="flex items-center gap-4 text-sm text-cultivax-text-muted">
            <Link
              href="/privacy"
              className="hover:text-cultivax-text-secondary transition-colors"
            >
              {t('footer.privacy', 'Privacy Policy')}
            </Link>
            <span className="text-cultivax-border">|</span>
            <Link
              href="/terms"
              className="hover:text-cultivax-text-secondary transition-colors"
            >
              {t('footer.terms', 'Terms of Service')}
            </Link>
            <span className="text-cultivax-border">|</span>
            <Link
              href="/support"
              className="hover:text-cultivax-text-secondary transition-colors"
            >
              {t('footer.support', 'Support')}
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
