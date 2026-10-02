import React from 'react';
import ConfidenceBadge from './ConfidenceBadge';
import CoverageBar from './CoverageBar';

interface EngineResult {
  name: string;
  assessment?: string;
  score?: number;
  confidence?: 'High' | 'Medium' | 'Low' | 'None';
  data_coverage_pct?: number;
  missing_critical_metrics?: string[];
  narrative?: string;
  status?: string;
}

interface EngineResultCardProps {
  result: EngineResult;
  compact?: boolean;
}

const EngineResultCard: React.FC<EngineResultCardProps> = ({ result, compact = false }) => {
  const {
    name,
    assessment,
    score,
    confidence = 'None',
    data_coverage_pct = 0,
    missing_critical_metrics = [],
    narrative,
    status,
  } = result;

  // Handle status cases
  if (status === 'insufficient_data' || status === 'mock_data_gated') {
    return (
      <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
        <h4 className="font-medium text-yellow-900">{name}</h4>
        <p className="text-sm text-yellow-700 mt-1">{result.reason || 'Data unavailable'}</p>
      </div>
    );
  }

  if (compact) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-3 space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-gray-900">{name}</h4>
          {score !== undefined && <span className="text-sm font-bold text-gray-700">{score.toFixed(0)}</span>}
        </div>
        {assessment && <p className="text-sm text-gray-600">{assessment}</p>}
        <div className="flex items-center justify-between">
          <div className="w-full">
            <CoverageBar percentage={data_coverage_pct || 0} showLabel={false} />
          </div>
          <ConfidenceBadge confidence={confidence} size="sm" />
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 space-y-4">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="text-lg font-semibold text-gray-900">{name}</h4>
          {score !== undefined && (
            <div className="text-right">
              <div className="text-3xl font-bold text-gray-900">{score.toFixed(0)}</div>
              <div className="text-xs text-gray-500">/ 100</div>
            </div>
          )}
        </div>
        {assessment && <p className="text-base text-gray-700 font-medium">{assessment}</p>}
      </div>

      <div className="space-y-3">
        <ConfidenceBadge confidence={confidence} size="md" />

        <div className="bg-gray-50 rounded-lg p-3">
          <CoverageBar
            percentage={data_coverage_pct || 0}
            missingMetrics={missing_critical_metrics}
            showLabel={true}
          />
        </div>
      </div>

      {narrative && (
        <div className="pt-4 border-t">
          <p className="text-sm text-gray-600 leading-relaxed">{narrative}</p>
        </div>
      )}
    </div>
  );
};

export default EngineResultCard;
