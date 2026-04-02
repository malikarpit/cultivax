'use client';

/**
 * StatCard — Premium stat card component
 * Matches the Stitch mockup design with icon, value, trend, and glow effects.
 */

import { LucideIcon } from 'lucide-react';
import clsx from 'clsx';

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  trend?: string;
  trendDirection?: 'up' | 'down' | 'neutral';
  color?: 'green' | 'amber' | 'red' | 'blue' | 'default';
  subtitle?: string;
  className?: string;
}

const colorMap = {
  green: {
    icon: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    border: 'hover:border-emerald-500/30',
    shadow: 'hover:shadow-glow-green',
    trend: 'text-emerald-400',
  },
  amber: {
    icon: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'hover:border-amber-500/30',
    shadow: 'hover:shadow-glow-amber',
    trend: 'text-amber-400',
  },
  red: {
    icon: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'hover:border-red-500/30',
    shadow: 'hover:shadow-glow-red',
    trend: 'text-red-400',
  },
  blue: {
    icon: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'hover:border-blue-500/30',
    shadow: 'hover:shadow-glow-blue',
    trend: 'text-blue-400',
  },
  default: {
    icon: 'text-cultivax-text-secondary',
    bg: 'bg-cultivax-elevated',
    border: 'hover:border-cultivax-border-highlight',
    shadow: '',
    trend: 'text-cultivax-text-secondary',
  },
};

export default function StatCard({
  icon: Icon,
  label,
  value,
  trend,
  trendDirection = 'neutral',
  color = 'default',
  subtitle,
  className,
}: StatCardProps) {
  const colors = colorMap[color];

  return (
    <div
      className={clsx(
        'card-stat group animate-fade-in',
        colors.border,
        colors.shadow,
        className
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div className={clsx('p-2.5 rounded-lg', colors.bg)}>
          <Icon className={clsx('w-5 h-5', colors.icon)} />
        </div>
        {trend && (
          <span
            className={clsx(
              'text-xs font-semibold px-2 py-0.5 rounded-full',
              trendDirection === 'up' && 'bg-emerald-500/15 text-emerald-400',
              trendDirection === 'down' && 'bg-red-500/15 text-red-400',
              trendDirection === 'neutral' && 'bg-gray-500/15 text-gray-400'
            )}
          >
            {trendDirection === 'up' && '↑ '}
            {trendDirection === 'down' && '↓ '}
            {trend}
          </span>
        )}
      </div>

      <div>
        <p className="text-2xl font-bold text-cultivax-text-primary tracking-tight">
          {value}
        </p>
        <p className="text-sm text-cultivax-text-muted mt-0.5">{label}</p>
        {subtitle && (
          <p className="text-xs text-cultivax-text-muted mt-1">{subtitle}</p>
        )}
      </div>
    </div>
  );
}
