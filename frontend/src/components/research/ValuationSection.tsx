"use client";
import React from "react";
import { Activity, TrendingDown, TrendingUp } from "lucide-react";

interface ValuationData {
  valuation_metrics: { pe_ratio?: number; fcf_yield?: number };
  valuation_assessment: {
    valuation_status: string;
    vs_history: string;
    vs_peers: string;
    recommendation: string;
  };
}

export function ValuationSection({ data }: { data?: ValuationData }) {
  if (!data) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Valuation analysis requires workspace data</p>
      </div>
    );
  }

  const metrics = data.valuation_metrics;
  const assess = data.valuation_assessment;

  const getStatusColor = (status: string) => {
    if (status === "attractive" || status === "cheap") return "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200";
    if (status === "expensive") return "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200";
    return "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200";
  };

  return (
    <div className="space-y-6">
      {/* Main Assessment */}
      <div className={`rounded-lg p-6 border-2 ${getStatusColor(assess.valuation_status)}`}>
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-bold text-xl mb-2">Valuation Assessment</h3>
            <p className="text-sm mb-3">{assess.recommendation}</p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold capitalize">{assess.valuation_status}</p>
            {assess.valuation_status === "attractive" ? (
              <TrendingUp className="w-6 h-6 mx-auto text-green-600 mt-2" />
            ) : (
              <TrendingDown className="w-6 h-6 mx-auto text-red-600 mt-2" />
            )}
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-4">
        {metrics.pe_ratio !== undefined && (
          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">P/E Ratio</p>
            <p className="text-2xl font-bold">{metrics.pe_ratio?.toFixed(1)}x</p>
          </div>
        )}
        {metrics.fcf_yield !== undefined && (
          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">FCF Yield</p>
            <p className="text-2xl font-bold">{metrics.fcf_yield?.toFixed(2)}%</p>
          </div>
        )}
      </div>

      {/* Comparisons */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
          <p className="text-sm font-semibold mb-2">vs History</p>
          <p className="text-lg capitalize font-bold text-blue-600 dark:text-blue-400">{assess.vs_history}</p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
          <p className="text-sm font-semibold mb-2">vs Peers</p>
          <p className="text-lg capitalize font-bold text-blue-600 dark:text-blue-400">{assess.vs_peers}</p>
        </div>
      </div>

      {/* Framework */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
        <h4 className="font-semibold mb-3">Valuation Triangulation</h4>
        <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
          <p>✓ DCF: Intrinsic value based on cash flows</p>
          <p>✓ Historical P/E: Relative to own 5-year average</p>
          <p>✓ Peer P/E: Relative to industry peers</p>
          <p>✓ EV/EBITDA: For capital-intensive comparison</p>
          <p>✓ FCF Yield: Absolute yield comparison</p>
          <p className="mt-3 font-semibold">Use multiple methods for robust valuation range.</p>
        </div>
      </div>
    </div>
  );
}
