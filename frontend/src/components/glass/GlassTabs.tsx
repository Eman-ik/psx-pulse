import React from 'react';
import clsx from 'clsx';

interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

interface GlassTabsProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  className?: string;
}

export function GlassTabs({
  tabs,
  activeTab,
  onTabChange,
  className,
}: GlassTabsProps) {
  return (
    <div className={clsx('glass-tabs', className)}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={clsx(
            'glass-tab',
            activeTab === tab.id && 'active',
            'flex items-center gap-2'
          )}
        >
          {tab.icon && <span className="text-sm">{tab.icon}</span>}
          {tab.label}
        </button>
      ))}
    </div>
  );
}
