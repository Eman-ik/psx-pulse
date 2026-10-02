import React from 'react';

interface ConfidenceBadgeProps {
  confidence: 'High' | 'Medium' | 'Low' | 'None';
  size?: 'sm' | 'md' | 'lg';
}

const confidenceColors = {
  High: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300' },
  Medium: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-300' },
  Low: { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-300' },
  None: { bg: 'bg-gray-100', text: 'text-gray-600', border: 'border-gray-300' },
};

const sizeClasses = {
  sm: 'px-2 py-1 text-xs',
  md: 'px-3 py-1.5 text-sm',
  lg: 'px-4 py-2 text-base',
};

const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ confidence, size = 'md' }) => {
  const colors = confidenceColors[confidence];
  const sizeClass = sizeClasses[size];

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border ${colors.bg} ${colors.text} ${colors.border} ${sizeClass} font-medium`}
    >
      <span
        className={`w-2 h-2 rounded-full ${
          confidence === 'High'
            ? 'bg-green-500'
            : confidence === 'Medium'
              ? 'bg-yellow-500'
              : confidence === 'Low'
                ? 'bg-orange-500'
                : 'bg-gray-400'
        }`}
      />
      {confidence}
    </span>
  );
};

export default ConfidenceBadge;
