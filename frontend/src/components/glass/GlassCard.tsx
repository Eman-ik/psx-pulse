import React, { ReactNode } from 'react';
import clsx from 'clsx';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
  variant?: 'primary' | 'strong' | 'soft';
  interactive?: boolean;
  elevation?: 1 | 2 | 3;
}

export function GlassCard({
  children,
  className,
  onClick,
  variant = 'primary',
  interactive = false,
  elevation = 1,
}: GlassCardProps) {
  const variantClass = {
    primary: 'glass-card',
    strong: 'glass-strong',
    soft: 'glass-soft',
  }[variant];

  const elevationClass = {
    1: 'elevation-1',
    2: 'elevation-2',
    3: 'elevation-3',
  }[elevation];

  return (
    <div
      className={clsx(
        variantClass,
        elevationClass,
        interactive && 'glass-card--interactive cursor-pointer',
        'rounded-[var(--radius-md)] p-6',
        className
      )}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {children}
    </div>
  );
}
