'use client';

/**
 * MiniChart — Small inline chart for stat cards using Recharts
 * Dark themed with green gradient bars.
 */

import {
  BarChart,
  Bar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface MiniChartProps {
  data: { name: string; value: number }[];
  color?: string;
  height?: number;
  showTooltip?: boolean;
  className?: string;
}

export default function MiniChart({
  data,
  color = '#10B981',
  height = 40,
  showTooltip = true,
  className,
}: MiniChartProps) {
  return (
    <div className={className} style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <BarChart data={data} barGap={1}>
          {showTooltip && (
            <Tooltip
              contentStyle={{
                background: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#F9FAFB',
              }}
              cursor={{ fill: 'rgba(16, 185, 129, 0.05)' }}
            />
          )}
          <Bar
            dataKey="value"
            fill={color}
            radius={[2, 2, 0, 0]}
            opacity={0.8}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
