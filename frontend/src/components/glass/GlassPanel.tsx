import React, { ReactNode } from 'react';
import clsx from 'clsx';

interface GlassPanelProps {
  children: ReactNode;
  className?: string;
  title?: ReactNode;
  subtitle?: ReactNode;
}

export function GlassPanel({
  children,
  className,
  title,
  subtitle,
}: GlassPanelProps) {
  return (
    <div className={clsx('glass-strong rounded-[var(--radius-lg)] p-6', className)}>
      {(title || subtitle) && (
        <div className="mb-6 pb-4 border-b border-[rgba(142,156,183,0.2)]">
          {title && (
            <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
              {title}
            </h2>
          )}
          {subtitle && (
            <p className="text-sm text-[var(--text-secondary)]">
              {subtitle}
            </p>
          )}
        </div>
      )}
      {children}
    </div>
  );
}
