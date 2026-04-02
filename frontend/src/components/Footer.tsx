'use client';

/**
 * Footer — Unified footer for all pages
 * © 2026 CultivaX Agricultural Intelligence
 */

import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="border-t border-cultivax-border mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Copyright */}
          <p className="text-sm text-cultivax-text-muted">
            © 2026 CultivaX Agricultural Intelligence. All rights reserved.
          </p>

          {/* Links */}
          <div className="flex items-center gap-4 text-sm text-cultivax-text-muted">
            <Link
              href="#"
              className="hover:text-cultivax-text-secondary transition-colors"
            >
              Privacy Policy
            </Link>
            <span className="text-cultivax-border">|</span>
            <Link
              href="#"
              className="hover:text-cultivax-text-secondary transition-colors"
            >
              Terms of Service
            </Link>
            <span className="text-cultivax-border">|</span>
            <Link
              href="#"
              className="hover:text-cultivax-text-secondary transition-colors"
            >
              Support
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
