import React from 'react';

interface ValidationIndicatorProps {
  valid: boolean;
  issues?: string[];
  warnings?: string[];
  compact?: boolean;
}

const ValidationIndicator: React.FC<ValidationIndicatorProps> = ({
  valid,
  issues = [],
  warnings = [],
  compact = false,
}) => {
  if (compact) {
    return (
      <div className="flex items-center gap-1">
        {valid ? (
          <>
            <span className="w-2 h-2 bg-green-500 rounded-full" />
            <span className="text-xs text-green-700 font-medium">Valid</span>
          </>
        ) : (
          <>
            <span className="w-2 h-2 bg-red-500 rounded-full" />
            <span className="text-xs text-red-700 font-medium">Issues</span>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="flex items-start gap-3">
        <div className={`w-3 h-3 rounded-full mt-1 flex-shrink-0 ${valid ? 'bg-green-500' : 'bg-red-500'}`} />
        <div className="flex-1">
          <h4 className={`font-medium ${valid ? 'text-green-800' : 'text-red-800'}`}>
            {valid ? 'Analysis Valid' : 'Validation Issues'}
          </h4>
          <p className={`text-sm ${valid ? 'text-green-700' : 'text-red-700'}`}>
            {valid ? 'No contradictions detected across engines.' : `${issues.length} issue(s) found.`}
          </p>
        </div>
      </div>

      {issues.length > 0 && (
        <div className="pl-6 space-y-2 border-t pt-3">
          <h5 className="text-sm font-medium text-red-700">Issues:</h5>
          <ul className="space-y-1">
            {issues.map((issue, idx) => (
              <li key={idx} className="text-xs text-red-600 flex items-start gap-2">
                <span className="text-red-500 mt-0.5">!</span>
                <span>{issue}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="pl-6 space-y-2 border-t pt-3">
          <h5 className="text-sm font-medium text-yellow-700">Warnings:</h5>
          <ul className="space-y-1">
            {warnings.map((warning, idx) => (
              <li key={idx} className="text-xs text-yellow-600 flex items-start gap-2">
                <span className="text-yellow-500 mt-0.5">⚠</span>
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ValidationIndicator;
