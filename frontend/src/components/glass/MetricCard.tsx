import React from 'react';
import clsx from 'clsx';

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  change?: number;
  status?: 'positive' | 'negative' | 'neutral';
  className?: string;
  icon?: React.ReactNode;
}

export function MetricCard({
  label,
  value,
  unit,
  change,
  status,
  className,
  icon,
}: MetricCardProps) {
  return (
    <div className={clsx('metric-card', className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="metric-label">{label}</div>
          <div className="flex items-baseline gap-2 mt-2">
            <div className="metric-value">{value}</div>
            {unit && <span className="text-sm text-[var(--text-secondary)]">{unit}</span>}
          </div>
        </div>
        {icon && (
          <div className="text-[var(--text-secondary)] opacity-60">
            {icon}
          </div>
        )}
      </div>

      {change !== undefined && (
        <div className={clsx(
          'text-xs font-semibold mt-3 pt-3 border-t border-[rgba(255,255,255,0.3)]',
          status === 'positive' && 'text-[var(--positive)]',
          status === 'negative' && 'text-[var(--negative)]',
          status === 'neutral' && 'text-[var(--text-secondary)]',
          !status && 'text-[var(--text-secondary)]'
        )}>
          {change > 0 ? '+' : ''}{change.toFixed(2)}%
        </div>
      )}
    </div>
  );
}
