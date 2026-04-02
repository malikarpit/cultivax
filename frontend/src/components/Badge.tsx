'use client';

/**
 * Badge — Color-coded pill badges for status display
 */

import clsx from 'clsx';

export type BadgeVariant = 'green' | 'amber' | 'red' | 'blue' | 'gray' | 'teal' | 'purple' | 'slate' | 'primary' | 'neutral';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  dot?: boolean;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  green: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  amber: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
  red: 'bg-red-500/15 text-red-400 border-red-500/20',
  blue: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  gray: 'bg-gray-500/15 text-gray-400 border-gray-500/20',
  teal: 'bg-teal-500/15 text-teal-400 border-teal-500/20',
  purple: 'bg-purple-500/15 text-purple-400 border-purple-500/20',
  slate: 'bg-slate-500/15 text-slate-400 border-slate-500/20',
  primary: 'bg-cultivax-primary/15 text-cultivax-primary border-cultivax-primary/20',
  neutral: 'bg-gray-500/15 text-gray-400 border-gray-500/20',
};

const dotColors: Record<BadgeVariant, string> = {
  green: 'bg-emerald-400',
  amber: 'bg-amber-400',
  red: 'bg-red-400',
  blue: 'bg-blue-400',
  gray: 'bg-gray-400',
  teal: 'bg-teal-400',
  purple: 'bg-purple-400',
  slate: 'bg-slate-400',
  primary: 'bg-cultivax-primary',
  neutral: 'bg-gray-400',
};

// Convenience: auto-map common status strings to badge variants
export function getStatusVariant(status: string): BadgeVariant {
  const s = (status || '').toLowerCase();
  if (['active', 'healthy', 'verified', 'completed', 'pass'].includes(s)) return 'green';
  if (['pending', 'delayed', 'warning', 'draft', 'in_progress'].includes(s)) return 'amber';
  if (['atrisk', 'at risk', 'critical', 'suspended', 'failed', 'error'].includes(s)) return 'red';
  if (['info', 'created', 'new'].includes(s)) return 'blue';
  if (['closed', 'archived', 'inactive'].includes(s)) return 'gray';
  if (['readytoharvest', 'ready to harvest', 'harvested'].includes(s)) return 'teal';
  return 'gray';
}

export default function Badge({
  children,
  variant = 'gray',
  size = 'sm',
  dot = false,
  className,
}: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full border font-medium',
        variantClasses[variant],
        size === 'sm' && 'px-2.5 py-0.5 text-xs',
        size === 'md' && 'px-3 py-1 text-sm',
        className
      )}
    >
      {dot && (
        <span
          className={clsx('w-1.5 h-1.5 rounded-full', dotColors[variant])}
        />
      )}
      {children}
    </span>
  );
}
