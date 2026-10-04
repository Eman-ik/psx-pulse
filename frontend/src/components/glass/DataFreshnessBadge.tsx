import React from 'react';
import { Clock } from 'lucide-react';
import clsx from 'clsx';

interface DataFreshnessBadgeProps {
  timestamp?: string | Date | null;
  status?: 'fresh' | 'stale' | 'unavailable';
  className?: string;
}

export function DataFreshnessBadge({
  timestamp,
  status = 'fresh',
  className,
}: DataFreshnessBadgeProps) {
  const formatTime = (date: string | Date) => {
    const d = typeof date === 'string' ? new Date(date) : date;
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return d.toLocaleDateString();
  };

  const statusLabel = {
    fresh: 'Fresh Data',
    stale: 'Stale Data',
    unavailable: 'Insufficient Data',
  }[status];

  return (
    <span className={clsx('badge-freshness', className)}>
      <Clock size={11} className="opacity-70" />
      {timestamp ? formatTime(timestamp) : statusLabel}
    </span>
  );
}
