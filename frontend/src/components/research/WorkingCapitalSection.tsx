"use client";
import React from "react";
import { Activity, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react";

interface WorkingCapitalData {
  receivable_days_analysis: { current?: number };
  inventory_days_analysis: { current?: number };
  payable_days_analysis: { current?: number };
  cash_conversion_cycle_analysis: { current?: number; trend?: any[] };
  working_capital_scorecard: {
    receivable_health: string;
    inventory_health: string;
    ccc_health: string;
    overall_wc_score: number;
    recommendations: string[];
  };
}

const MetricCard = ({ label, value, interpretation }: any) => (
  <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
    <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">{label}</p>
    <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
      {value === null ? "—" : `${value.toFixed(0)} days`}
    </p>
    <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">{interpretation}</p>
  </div>
);

export function WorkingCapitalSection({ data }: { data?: WorkingCapitalData }) {
  if (!data) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Working capital analysis requires workspace data</p>
      </div>
    );
  }

  const scorecard = data.working_capital_scorecard;
  const rec_days = data.receivable_days_analysis.current;
  const inv_days = data.inventory_days_analysis.current;
  const ccc = data.cash_conversion_cycle_analysis.current;

  return (
    <div className="space-y-6">
      {/* WC Scorecard */}
      <div className="bg-gradient-to-br from-cyan-50 to-teal-50 dark:from-cyan-950 dark:to-teal-950 rounded-lg p-6 border border-cyan-200 dark:border-cyan-800">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="font-bold text-xl mb-2">Working Capital Efficiency</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Cash conversion cycle and operational efficiency
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-cyan-600 dark:text-cyan-400">
              {scorecard.overall_wc_score}
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400">/ 100</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Receivables</p>
            <span className={`px-2 py-1 rounded text-xs font-bold ${
              scorecard.receivable_health === 'excellent' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
            }`}>
              {scorecard.receivable_health}
            </span>
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Inventory</p>
            <span className={`px-2 py-1 rounded text-xs font-bold ${
              scorecard.inventory_health === 'excellent' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
            }`}>
              {scorecard.inventory_health}
            </span>
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">CCC</p>
            <span className={`px-2 py-1 rounded text-xs font-bold ${
              scorecard.ccc_health === 'excellent' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
            }`}>
              {scorecard.ccc_health}
            </span>
          </div>
        </div>

        {scorecard.recommendations.length > 0 && (
          <div className="p-4 bg-white dark:bg-slate-800 rounded-lg border border-cyan-200 dark:border-cyan-700">
            <h4 className="font-semibold mb-3">Working Capital Insights</h4>
            <ul className="space-y-2">
              {scorecard.recommendations.map((rec, idx) => (
                <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0 text-cyan-600" />
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Components */}
      <div className="grid grid-cols-3 gap-4">
        <MetricCard
          label="Receivable Days (DSO)"
          value={rec_days}
          interpretation={rec_days && rec_days < 30 ? "Fast collection" : "Average collection"}
        />
        <MetricCard
          label="Inventory Days (DIO)"
          value={inv_days}
          interpretation={inv_days && inv_days < 30 ? "Efficient turnover" : "Standard inventory"}
        />
        <MetricCard
          label="Cash Conversion Cycle"
          value={ccc}
          interpretation={ccc && ccc < 30 ? "Excellent" : ccc && ccc < 60 ? "Good" : "Needs monitoring"}
        />
      </div>

      {/* Education */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
        <h4 className="font-semibold mb-3">Cash Conversion Cycle Guide</h4>
        <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
          <p>
            <strong>CCC = DIO + DSO - DPO</strong>
          </p>
          <p>Lower CCC means less cash tied up in operations. Negative CCC is ideal (collect cash before paying suppliers).</p>
          <p className="text-xs text-gray-500">• &lt;30 days: Excellent efficiency</p>
          <p className="text-xs text-gray-500">• 30-60 days: Good management</p>
          <p className="text-xs text-gray-500">• &gt;60 days: Needs attention</p>
        </div>
      </div>
    </div>
  );
}
