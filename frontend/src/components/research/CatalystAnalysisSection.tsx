"use client";
import React from "react";
import { Activity, Zap, TrendingUp, Clock } from "lucide-react";

interface CatalystData {
  catalysts: Array<{
    name: string;
    description: string;
    likelihood: string;
    impact_potential: string;
    timeframe: string;
    catalyst_score: number;
  }>;
  catalyst_summary: {
    total_catalysts: number;
    top_3_catalysts: string[];
    highest_probability: string;
    highest_impact: string;
  };
}

const getLikelihoodColor = (likelihood: string) => {
  if (likelihood === "high") return "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200";
  if (likelihood === "moderate") return "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200";
  return "bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200";
};

export function CatalystAnalysisSection({ data }: { data?: CatalystData }) {
  if (!data) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Catalyst analysis requires workspace data</p>
      </div>
    );
  }

  const summary = data.catalyst_summary;
  const catalysts = data.catalysts;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-950 dark:to-amber-950 rounded-lg p-6 border border-orange-200 dark:border-orange-800">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="font-bold text-xl mb-2">Value Catalysts</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Identify potential drivers for value recognition
            </p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
              {summary.total_catalysts}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400">potential catalysts</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-white dark:bg-slate-800 rounded border border-orange-200 dark:border-orange-700">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Highest Probability</p>
            <p className="font-semibold text-sm">{summary.highest_probability}</p>
          </div>
          <div className="p-3 bg-white dark:bg-slate-800 rounded border border-orange-200 dark:border-orange-700">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Highest Impact</p>
            <p className="font-semibold text-sm">{summary.highest_impact}</p>
          </div>
        </div>
      </div>

      {/* Top 3 */}
      <div>
        <h3 className="font-bold text-lg mb-3">Top 3 Catalysts</h3>
        <div className="space-y-2">
          {summary.top_3_catalysts.map((catalyst, idx) => (
            <div key={idx} className="flex items-center gap-3 p-3 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="text-lg font-bold text-blue-600 dark:text-blue-400">#{idx + 1}</div>
              <p className="font-semibold text-blue-900 dark:text-blue-100">{catalyst}</p>
            </div>
          ))}
        </div>
      </div>

      {/* All Catalysts */}
      <div>
        <h3 className="font-bold text-lg mb-3">Catalyst Details</h3>
        <div className="space-y-2">
          {catalysts.map((cat, idx) => (
            <div key={idx} className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <p className="font-semibold text-gray-900 dark:text-gray-100">{cat.name}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{cat.description}</p>
                </div>
                <span className="text-xs font-bold px-2 py-1 rounded bg-gray-100 dark:bg-gray-900">
                  {cat.catalyst_score}/5
                </span>
              </div>

              <div className="flex gap-3 mt-3 text-xs">
                <span className={`px-2 py-1 rounded-full font-semibold ${getLikelihoodColor(cat.likelihood)}`}>
                  {cat.likelihood} likelihood
                </span>
                <span className={`px-2 py-1 rounded-full font-semibold ${
                  cat.impact_potential === "high"
                    ? "bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200"
                    : "bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200"
                }`}>
                  {cat.impact_potential} impact
                </span>
                <span className="px-2 py-1 rounded-full font-semibold bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {cat.timeframe}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Catalyst Framework */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
        <h4 className="font-semibold mb-3 flex items-center gap-2">
          <Zap className="w-4 h-4" />
          Identifying Catalysts
        </h4>
        <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
          <p><strong>Key insight:</strong> Cheap stocks sometimes stay cheap for years without catalysts.</p>
          <p className="mt-3">Look for:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Earnings recovery potential</li>
            <li>Capacity expansions coming online</li>
            <li>Debt reduction milestone</li>
            <li>Dividend restoration/growth</li>
            <li>New product launches</li>
            <li>Asset monetization opportunities</li>
            <li>Regulatory/industry changes</li>
            <li>Commodity price recovery</li>
            <li>M&A opportunities</li>
            <li>Management/operational improvements</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
