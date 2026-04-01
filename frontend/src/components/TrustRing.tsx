'use client';

/**
 * TrustRing — SVG circular progress ring for trust scores
 * 0.0–1.0 scale, color-coded: green (>0.8), amber (0.5–0.8), red (<0.5)
 */

import clsx from 'clsx';

interface TrustRingProps {
  score: number; // 0.0 to 1.0
  size?: number; // px
  strokeWidth?: number;
  showLabel?: boolean;
  labelFormat?: 'percentage' | 'decimal' | 'outOf10';
  className?: string;
}

export default function TrustRing({
  score,
  size = 56,
  strokeWidth = 4,
  showLabel = true,
  labelFormat = 'decimal',
  className,
}: TrustRingProps) {
  const normalizedScore = Math.max(0, Math.min(1, score));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - normalizedScore);

  // Color based on score thresholds
  const getColor = () => {
    if (normalizedScore >= 0.8) return { stroke: '#10B981', text: 'text-emerald-400' };
    if (normalizedScore >= 0.5) return { stroke: '#F59E0B', text: 'text-amber-400' };
    return { stroke: '#EF4444', text: 'text-red-400' };
  };

  const { stroke, text } = getColor();

  const formatLabel = () => {
    switch (labelFormat) {
      case 'percentage': return `${Math.round(normalizedScore * 100)}%`;
      case 'outOf10': return `${(normalizedScore * 10).toFixed(1)}`;
      default: return normalizedScore.toFixed(1);
    }
  };

  return (
    <div className={clsx('relative inline-flex items-center justify-center', className)}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          fill="none"
          stroke="currentColor"
          className="text-cultivax-elevated"
        />
        {/* Progress arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          fill="none"
          stroke={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-700 ease-out"
        />
      </svg>
      {showLabel && (
        <span
          className={clsx(
            'absolute font-bold',
            text,
            size <= 48 ? 'text-xs' : size <= 64 ? 'text-sm' : 'text-base'
          )}
        >
          {formatLabel()}
        </span>
      )}
    </div>
  );
}
