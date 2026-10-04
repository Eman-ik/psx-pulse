import React from 'react';
import clsx from 'clsx';
import { GlassCard } from './GlassCard';

interface LoadingCardProps {
  message?: string;
  className?: string;
}

export function LoadingCard({ message = 'Loading...', className }: LoadingCardProps) {
  return (
    <GlassCard className={clsx('flex flex-col items-center justify-center py-12', className)}>
      <div className="flex items-center gap-3">
        <div className="flex gap-1">
          <div className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
          <div className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '0.15s' }} />
          <div className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '0.3s' }} />
        </div>
        <span className="text-sm text-[var(--text-secondary)]">{message}</span>
      </div>
    </GlassCard>
  );
}
