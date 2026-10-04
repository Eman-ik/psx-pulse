import React, { InputHTMLAttributes } from 'react';
import clsx from 'clsx';

interface GlassInputProps extends InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
  error?: string;
  helperText?: string;
  label?: string;
}

export function GlassInput({
  icon,
  error,
  helperText,
  label,
  className,
  ...props
}: GlassInputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[var(--text-secondary)]">
            {icon}
          </div>
        )}
        <input
          className={clsx(
            'glass-input w-full',
            icon && 'pl-10',
            error && 'border-[var(--negative)] bg-[rgba(180,111,120,0.05)]',
            className
          )}
          {...props}
        />
      </div>
      {error && (
        <p className="mt-2 text-xs text-[var(--negative)]">{error}</p>
      )}
      {helperText && !error && (
        <p className="mt-2 text-xs text-[var(--text-secondary)]">{helperText}</p>
      )}
    </div>
  );
}
