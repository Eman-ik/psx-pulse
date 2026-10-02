import React, { useState, useEffect } from 'react';
import EngineResultCard from './EngineResultCard';
import ValidationIndicator from './ValidationIndicator';
import ConfidenceBadge from './ConfidenceBadge';

interface ResearchData {
  ticker: string;
  status: string;
  confidence_score: number;
  executive_summary?: {
    business_health?: string;
    earnings_trend?: string;
    earnings_quality?: string;
    valuation_assessment?: string;
    risk_level?: number;
    key_insight?: string;
  };
  intelligence?: {
    [key: string]: any;
  };
  thesis?: {
    bull_case?: string;
    bear_case?: string;
    confirmation_triggers?: string[];
  };
}

interface ResearchIntelligenceDashboardProps {
  ticker: string;
  apiUrl?: string;
}

const ResearchIntelligenceDashboard: React.FC<ResearchIntelligenceDashboardProps> = ({
  ticker,
  apiUrl = 'http://localhost:5000',
}) => {
  const [data, setData] = useState<ResearchData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${apiUrl}/research-intelligence/${ticker.toUpperCase()}/analysis`);

        if (!response.ok) {
          throw new Error(`Failed to fetch: ${response.statusText}`);
        }

        const data = await response.json();
        setData(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch research data');
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [ticker, apiUrl]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="space-y-3 text-center">
          <div className="animate-spin w-8 h-8 border-4 border-gray-200 border-t-blue-500 rounded-full mx-auto" />
          <p className="text-gray-600">Loading research intelligence...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <h3 className="font-semibold text-red-900">Error Loading Research</h3>
        <p className="text-sm text-red-700 mt-1">{error || 'No data available'}</p>
      </div>
    );
  }

  const intelligence = data.intelligence || {};
  const summary = data.executive_summary || {};
  const thesis = data.thesis || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-gray-900">{data.ticker}</h1>
          <ConfidenceBadge confidence="High" size="lg" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <p className="text-xs text-gray-500 uppercase">Business Health</p>
            <p className="text-lg font-semibold text-gray-900">{summary.business_health || '—'}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-gray-500 uppercase">Earnings Quality</p>
            <p className="text-lg font-semibold text-gray-900">{summary.earnings_quality || '—'}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-gray-500 uppercase">Valuation</p>
            <p className="text-sm font-semibold text-gray-900">{summary.valuation_assessment || '—'}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-gray-500 uppercase">Risk Level</p>
            <p className="text-lg font-semibold text-gray-900">{summary.risk_level || 0}</p>
          </div>
        </div>
      </div>

      {/* Key Insight */}
      {summary.key_insight && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <h3 className="font-semibold text-blue-900 mb-2">Critical Debate</h3>
          <p className="text-sm text-blue-800">{summary.key_insight}</p>
        </div>
      )}

      {/* Intelligence Engines Grid */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Intelligence Engines</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(intelligence).map(([key, engine]) => {
            if (key === 'investment_case') return null; // Handle separately
            return <EngineResultCard key={key} result={{ name: formatEngineName(key), ...engine }} />;
          })}
        </div>
      </div>

      {/* Investment Case */}
      {intelligence.investment_case && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-lg border border-green-200 bg-green-50 p-4">
            <h3 className="font-semibold text-green-900 mb-3">Bull Case</h3>
            <p className="text-sm text-green-800">{intelligence.investment_case.bull?.thesis}</p>
          </div>
          <div className="rounded-lg border border-red-200 bg-red-50 p-4">
            <h3 className="font-semibold text-red-900 mb-3">Bear Case</h3>
            <p className="text-sm text-red-800">{intelligence.investment_case.bear?.thesis}</p>
          </div>
        </div>
      )}

      {/* Invalidation Triggers */}
      {thesis.confirmation_triggers && thesis.confirmation_triggers.length > 0 && (
        <div className="rounded-lg border border-orange-200 bg-orange-50 p-4">
          <h3 className="font-semibold text-orange-900 mb-3">Thesis Invalidation Triggers</h3>
          <ul className="space-y-2">
            {thesis.confirmation_triggers.map((trigger: string, idx: number) => (
              <li key={idx} className="text-sm text-orange-800 flex items-start gap-2">
                <span className="text-orange-500 mt-0.5">→</span>
                <span>{trigger}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

function formatEngineName(key: string): string {
  return key
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export default ResearchIntelligenceDashboard;
