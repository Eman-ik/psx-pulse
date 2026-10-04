import React, { ReactNode } from 'react';
import clsx from 'clsx';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumb?: Array<{ label: string; href?: string }>;
  status?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function SectionHeader({
  title,
  subtitle,
  breadcrumb,
  status,
  action,
  className,
}: SectionHeaderProps) {
  return (
    <div className={clsx('mb-8', className)}>
      {breadcrumb && (
        <nav className="flex items-center gap-2 mb-4">
          {breadcrumb.map((item, idx) => (
            <React.Fragment key={idx}>
              {idx > 0 && <span className="text-[var(--text-muted)]">/</span>}
              {item.href ? (
                <a href={item.href} className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
                  {item.label}
                </a>
              ) : (
                <span className="text-sm text-[var(--text-secondary)]">
                  {item.label}
                </span>
              )}
            </React.Fragment>
          ))}
        </nav>
      )}

      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-3xl md:text-4xl font-bold text-[var(--text-primary)] mb-2">
            {title}
          </h1>
          {subtitle && (
            <p className="text-base text-[var(--text-secondary)]">
              {subtitle}
            </p>
          )}
        </div>

        <div className="flex items-center gap-3">
          {status && <div className="flex-shrink-0">{status}</div>}
          {action && <div className="flex-shrink-0">{action}</div>}
        </div>
      </div>
    </div>
  );
}
