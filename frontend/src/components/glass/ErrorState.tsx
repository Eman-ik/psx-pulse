import React, { ReactNode } from 'react';
import { AlertCircle } from 'lucide-react';
import { GlassCard } from './GlassCard';

interface ErrorStateProps {
  title?: string;
  description: string;
  action?: ReactNode;
  error?: Error | string;
}

export function ErrorState({
  title = 'Something went wrong',
  description,
  action,
  error,
}: ErrorStateProps) {
  return (
    <GlassCard className="border border-[var(--negative-soft)] bg-[rgba(180,111,120,0.05)]">
      <div className="flex items-start gap-4">
        <AlertCircle className="w-5 h-5 text-[var(--negative)] flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-base font-semibold text-[var(--text-primary)] mb-1">
            {title}
          </h3>
          <p className="text-sm text-[var(--text-secondary)] mb-4">
            {description}
          </p>
          {error && (
            <details className="text-xs text-[var(--text-secondary)] mb-4 opacity-70">
              <summary className="cursor-pointer hover:underline">Error details</summary>
              <pre className="mt-2 p-2 bg-black/10 rounded text-xs overflow-x-auto whitespace-pre-wrap break-words">
                {typeof error === 'string' ? error : error.message}
              </pre>
            </details>
          )}
          {action && <div>{action}</div>}
        </div>
      </div>
    </GlassCard>
  );
}
