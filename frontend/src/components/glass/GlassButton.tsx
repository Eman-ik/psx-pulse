import React, { ButtonHTMLAttributes } from 'react';
import clsx from 'clsx';

interface GlassButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  loading?: boolean;
  fullWidth?: boolean;
}

export function GlassButton({
  variant = 'primary',
  size = 'md',
  icon,
  loading,
  fullWidth,
  className,
  children,
  disabled,
  ...props
}: GlassButtonProps) {
  const variantClass = {
    primary: 'glass-btn-primary',
    secondary: 'glass-btn-secondary',
  }[variant];

  const sizeClass = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  }[size];

  return (
    <button
      className={clsx(
        variantClass,
        sizeClass,
        fullWidth && 'w-full',
        disabled && 'opacity-60 cursor-not-allowed',
        'flex items-center justify-center gap-2 font-medium rounded-[14px] transition-all',
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg
          className="w-4 h-4 animate-spin"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {!loading && icon && <span>{icon}</span>}
      {children}
    </button>
  );
}
