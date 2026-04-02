'use client';

/**
 * ProgressBar — Horizontal progress bar with label
 */

import clsx from 'clsx';

interface ProgressBarProps {
  value: number; // 0-100
  label?: string;
  showPercentage?: boolean;
  color?: 'green' | 'amber' | 'red' | 'blue';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const colorClasses = {
  green: 'bg-emerald-500',
  amber: 'bg-amber-500',
  red: 'bg-red-500',
  blue: 'bg-blue-500',
};

const sizeClasses = {
  sm: 'h-1.5',
  md: 'h-2',
  lg: 'h-3',
};

export default function ProgressBar({
  value,
  label,
  showPercentage = false,
  color = 'green',
  size = 'md',
  className,
}: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value));

  return (
    <div className={clsx('w-full', className)}>
      {(label || showPercentage) && (
        <div className="flex items-center justify-between mb-1.5">
          {label && (
            <span className="text-xs text-cultivax-text-muted">{label}</span>
          )}
          {showPercentage && (
            <span className="text-xs font-medium text-cultivax-text-secondary">
              {Math.round(clamped)}%
            </span>
          )}
        </div>
      )}
      <div
        className={clsx(
          'bg-cultivax-elevated rounded-full overflow-hidden',
          sizeClasses[size]
        )}
      >
        <div
          className={clsx(
            'rounded-full transition-all duration-500 ease-out',
            sizeClasses[size],
            colorClasses[color]
          )}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
