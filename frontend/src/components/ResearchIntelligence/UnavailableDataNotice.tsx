import React from 'react';

interface UnavailableDataNoticeProps {
  metric: string;
  reason?: string;
  compact?: boolean;
}

/**
 * Display when data is not available
 * Enforces NO MOCK DATA rule — shows actual unavailable state instead of synthetic data
 */
const UnavailableDataNotice: React.FC<UnavailableDataNoticeProps> = ({
  metric,
  reason,
  compact = false,
}) => {
  if (compact) {
    return (
      <div className="text-xs text-gray-500 italic">
        {metric}: Unavailable
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
      <div className="flex items-start gap-3">
        <div className="w-3 h-3 rounded-full mt-1.5 bg-gray-400 flex-shrink-0" />
        <div className="flex-1">
          <h4 className="font-medium text-gray-700">
            {metric}
          </h4>
          <p className="text-sm text-gray-600 mt-1">
            {reason || 'Data not available'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default UnavailableDataNotice;
