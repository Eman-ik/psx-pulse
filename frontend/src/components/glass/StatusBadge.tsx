import React from 'react';
import clsx from 'clsx';

interface StatusBadgeProps {
  status: 'positive' | 'negative' | 'warning' | 'neutral';
  label: string;
  icon?: React.ReactNode;
  className?: string;
}

export function StatusBadge({ status, label, icon, className }: StatusBadgeProps) {
  const badgeClass = {
    positive: 'badge-positive',
    negative: 'badge-negative',
    warning: 'badge-warning',
    neutral: 'badge-muted',
  }[status];

  return (
    <span className={clsx('badge-status', badgeClass, className)}>
      {icon && <span>{icon}</span>}
      {label}
    </span>
  );
}
