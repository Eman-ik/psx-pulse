"use client";
import React from "react";
import { Activity, TrendingUp, CheckCircle } from "lucide-react";

interface DividendData {
  dividend_metrics: {
    current_yield?: number;
    payout_ratio?: number;
    dividend_growth?: number;
    sustainability?: string;
    fcf_coverage?: number;
  };
  dividend_scorecard: {
    yield_assessment: string;
    growth_assessment: string;
    sustainability_rating: string;
    overall_dividend_score: number;
    recommendations: string[];
  };
}

export function DividendAnalysisSection({ data }: { data?: DividendData }) {
  if (!data) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Dividend analysis requires workspace data</p>
      </div>
    );
  }

  const metrics = data.dividend_metrics;
  const scorecard = data.dividend_scorecard;

  return (
    <div className="space-y-6">
      {/* Scorecard */}
      <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 rounded-lg p-6 border border-green-200 dark:border-green-800">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="font-bold text-xl mb-2">Dividend Analysis</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Sustainability and growth of dividend payments
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-green-600 dark:text-green-400">
              {scorecard.overall_dividend_score}
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400">/ 100</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Yield</p>
            <p className="font-bold text-sm capitalize">{scorecard.yield_assessment}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Growth</p>
            <p className="font-bold text-sm capitalize">{scorecard.growth_assessment}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Sustainability</p>
            <p className="font-bold text-sm capitalize">{scorecard.sustainability_rating}</p>
          </div>
        </div>

        {scorecard.recommendations.length > 0 && (
          <div className="p-4 bg-white dark:bg-slate-800 rounded-lg border border-green-200 dark:border-green-700">
            <h4 className="font-semibold mb-3">Dividend Insights</h4>
            <ul className="space-y-2">
              {scorecard.recommendations.map((rec, idx) => (
                <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-green-600" />
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.current_yield !== undefined && (
          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Dividend Yield</p>
            <p className="text-2xl font-bold">{metrics.current_yield?.toFixed(2)}%</p>
          </div>
        )}
        {metrics.payout_ratio !== undefined && (
          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Payout Ratio</p>
            <p className="text-2xl font-bold">{metrics.payout_ratio?.toFixed(1)}%</p>
          </div>
        )}
        {metrics.dividend_growth !== undefined && (
          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">10-Yr Growth</p>
            <p className="text-2xl font-bold flex items-center gap-1">
              {metrics.dividend_growth?.toFixed(1)}% <TrendingUp className="w-4 h-4 text-green-600" />
            </p>
          </div>
        )}
        {metrics.fcf_coverage !== undefined && (
          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">FCF Coverage</p>
            <p className="text-2xl font-bold">{metrics.fcf_coverage?.toFixed(2)}x</p>
          </div>
        )}
      </div>

      {/* Guidelines */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
        <h4 className="font-semibold mb-3">Dividend Sustainability Check</h4>
        <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
          <p>✓ <strong>Payout Ratio &lt; 50%:</strong> Sustainable dividend with growth room</p>
          <p>✓ <strong>Payout Ratio 50-75%:</strong> Moderate - monitor closely</p>
          <p>⚠️ <strong>Payout Ratio &gt; 75%:</strong> High risk of cuts</p>
          <p>✓ <strong>FCF Coverage &gt; 1.0x:</strong> Dividend covered by cash flow</p>
        </div>
      </div>
    </div>
  );
}
