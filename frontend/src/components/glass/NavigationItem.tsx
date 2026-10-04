import React from 'react';
import Link from 'next/link';
import clsx from 'clsx';

interface NavigationItemProps {
  href: string;
  label: string;
  icon?: React.ReactNode;
  isActive?: boolean;
  badge?: string;
  disabled?: boolean;
  onClick?: () => void;
}

export function NavigationItem({
  href,
  label,
  icon,
  isActive,
  badge,
  disabled,
  onClick,
}: NavigationItemProps) {
  const content = (
    <>
      {icon && <span className="text-base flex-shrink-0">{icon}</span>}
      <span className="flex-1">{label}</span>
      {badge && (
        <span className="ml-auto rounded-md bg-[#B4C0D5]/40 px-1.5 py-0.5 text-[9px] font-semibold uppercase text-[#566680]">
          {badge}
        </span>
      )}
    </>
  );

  const className = clsx(
    'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all',
    isActive
      ? 'bg-[#10161A] text-[#DAE1EE] shadow-md shadow-[#10161A]/15'
      : disabled
        ? 'cursor-not-allowed text-[#8E9CB7]/60'
        : 'text-[#566680] hover:bg-white/60 hover:text-[#10161A]'
  );

  if (disabled) {
    return <div className={className}>{content}</div>;
  }

  return (
    <Link href={href} className={className} onClick={onClick}>
      {content}
    </Link>
  );
}
