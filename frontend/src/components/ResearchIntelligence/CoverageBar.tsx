import React from 'react';

interface CoverageBarProps {
  percentage: number;
  missingMetrics?: string[];
  showLabel?: boolean;
}

const CoverageBar: React.FC<CoverageBarProps> = ({ percentage, missingMetrics = [], showLabel = true }) => {
  const safePercentage = Math.min(100, Math.max(0, percentage));

  // Determine color based on coverage
  const getColor = (pct: number) => {
    if (pct >= 80) return 'bg-green-500';
    if (pct >= 60) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        {showLabel && <span className="text-sm font-medium text-gray-700">Data Coverage</span>}
        <span className="text-sm text-gray-600">{safePercentage}%</span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${getColor(safePercentage)}`}
          style={{ width: `${safePercentage}%` }}
        />
      </div>

      {missingMetrics.length > 0 && (
        <details className="mt-2">
          <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-800">
            Missing metrics ({missingMetrics.length})
          </summary>
          <ul className="mt-1 pl-4 text-xs text-gray-500 space-y-1">
            {missingMetrics.map((metric) => (
              <li key={metric} className="flex items-start gap-2">
                <span className="text-red-400 mt-0.5">✕</span>
                <span>{metric}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
};

export default CoverageBar;
