'use client';

/**
 * FilterChips — Horizontally scrollable filter pill buttons
 */

import clsx from 'clsx';

interface FilterChipsProps {
  options: { label: string; value: string }[];
  selected: string;
  onChange: (value: string) => void;
  className?: string;
}

export default function FilterChips({
  options,
  selected,
  onChange,
  className,
}: FilterChipsProps) {
  return (
    <div
      className={clsx(
        'flex gap-2 overflow-x-auto no-scrollbar pb-1',
        className
      )}
    >
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={clsx(
            selected === opt.value ? 'chip-active' : 'chip-default',
            'whitespace-nowrap'
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
