'use client';

/**
 * ComingSoon — Overlay for features not yet integrated with real data
 *
 * Renders a translucent overlay over its children with a
 * "Coming Soon" label. Preserves the parent's visual layout
 * while making it clear the data is decorative.
 */

import { Sparkles } from 'lucide-react';

interface ComingSoonProps {
  children: React.ReactNode;
  label?: string;
  className?: string;
}

export default function ComingSoon({ children, label = 'Coming Soon', className }: ComingSoonProps) {
  return (
    <div className={`relative ${className || ''}`}>
      {children}
      <div className="absolute inset-0 bg-cultivax-bg/70 backdrop-blur-[2px] z-10 flex flex-col items-center justify-center rounded-[inherit]">
        <div className="flex items-center gap-2 px-4 py-2 bg-cultivax-elevated/80 border border-cultivax-border rounded-full">
          <Sparkles className="w-4 h-4 text-cultivax-primary animate-pulse" />
          <span className="text-sm font-medium text-cultivax-text-secondary">{label}</span>
        </div>
      </div>
    </div>
  );
}
