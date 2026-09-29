"use client";
import React, { useState } from "react";
import {
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Shield,
  Activity,
} from "lucide-react";

interface BalanceSheetData {
  leverage_analysis: {
    debt_to_equity?: { current?: number; trend?: any[]; direction?: string };
    debt_to_ebitda?: { current?: number };
    interest_coverage?: { current?: number };
  };
  liquidity_analysis: {
    current_ratio?: { current?: number; health?: string };
    quick_ratio?: { current?: number; health?: string };
  };
  balance_sheet_scorecard: {
    leverage_health: string;
    liquidity_health: string;
    financial_risk: string;
    overall_balance_sheet_score: number;
    recommendations: string[];
  };
}

const MetricCard = ({ label, value, unit, health }: any) => {
  const getHealthColor = () => {
    switch (health) {
      case "healthy":
        return "bg-green-100 dark:bg-green-900";
      case "adequate":
        return "bg-yellow-100 dark:bg-yellow-900";
      case "concerning":
        return "bg-red-100 dark:bg-red-900";
      default:
        return "bg-gray-100 dark:bg-gray-900";
    }
  };

  return (
    <div className={`rounded-lg p-4 border border-gray-200 dark:border-slate-700 ${getHealthColor()}`}>
      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">{label}</p>
      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        {value === null ? "—" : `${value.toFixed(2)}${unit}`}
      </p>
      {health && <p className="text-xs mt-2 capitalize font-semibold">{health}</p>}
    </div>
  );
};

const RiskBadge = ({ level }: any) => {
  const getColor = () => {
    switch (level) {
      case "low":
        return "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200";
      case "moderate":
        return "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200";
      case "elevated":
        return "bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200";
      case "high":
        return "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200";
      default:
        return "bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200";
    }
  };

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${getColor()}`}>
      {level} Risk
    </span>
  );
};

export function BalanceSheetStrengthSection({ data }: { data?: BalanceSheetData }) {
  const [activeTab, setActiveTab] = useState<"leverage" | "liquidity">("leverage");

  if (!data) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Balance sheet analysis requires workspace data</p>
      </div>
    );
  }

  const scorecard = data.balance_sheet_scorecard;

  return (
    <div className="space-y-6">
      {/* Balance Sheet Scorecard */}
      <div className="bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-950 dark:to-red-950 rounded-lg p-6 border border-orange-200 dark:border-orange-800">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="font-bold text-xl mb-2">Balance Sheet Strength</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Financial resilience and solvency assessment
            </p>
          </div>
          <div>
            <div className="flex items-center gap-3">
              <div>
                <div className="text-4xl font-bold text-orange-600 dark:text-orange-400">
                  {scorecard.overall_balance_sheet_score}
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400">/ 100</p>
              </div>
              <div>
                <RiskBadge level={scorecard.financial_risk} />
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">Leverage</p>
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                scorecard.leverage_health === "excellent"
                  ? "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200"
                  : scorecard.leverage_health === "good"
                    ? "bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200"
                    : scorecard.leverage_health === "moderate"
                      ? "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200"
                      : "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200"
              }`}
            >
              {scorecard.leverage_health}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">Liquidity</p>
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                scorecard.liquidity_health === "healthy"
                  ? "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200"
                  : scorecard.liquidity_health === "adequate"
                    ? "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200"
                    : "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200"
              }`}
            >
              {scorecard.liquidity_health}
            </span>
          </div>
        </div>

        {scorecard.recommendations.length > 0 && (
          <div className="p-4 bg-white dark:bg-slate-800 rounded-lg border border-orange-200 dark:border-orange-700">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <Shield className="w-4 h-4" />
              Balance Sheet Insights
            </h4>
            <ul className="space-y-2">
              {scorecard.recommendations.map((rec, idx) => (
                <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-orange-600 dark:text-orange-400" />
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-slate-700">
        <button
          onClick={() => setActiveTab("leverage")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "leverage"
              ? "border-orange-600 text-orange-600 dark:text-orange-400"
              : "border-transparent text-gray-600 dark:text-gray-400"
          }`}
        >
          <BarChart3 className="w-4 h-4 inline mr-2" />
          Leverage
        </button>
        <button
          onClick={() => setActiveTab("liquidity")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "liquidity"
              ? "border-orange-600 text-orange-600 dark:text-orange-400"
              : "border-transparent text-gray-600 dark:text-gray-400"
          }`}
        >
          <Activity className="w-4 h-4 inline mr-2" />
          Liquidity
        </button>
      </div>

      {/* Leverage Tab */}
      {activeTab === "leverage" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {data.leverage_analysis.debt_to_equity?.current !== undefined && (
              <MetricCard
                label="Debt-to-Equity"
                value={data.leverage_analysis.debt_to_equity.current}
                unit="x"
              />
            )}
            {data.leverage_analysis.debt_to_ebitda?.current !== undefined && (
              <MetricCard
                label="Debt-to-EBITDA"
                value={data.leverage_analysis.debt_to_ebitda.current}
                unit="x"
              />
            )}
            {data.leverage_analysis.interest_coverage?.current !== undefined && (
              <MetricCard
                label="Interest Coverage"
                value={data.leverage_analysis.interest_coverage.current}
                unit="x"
              />
            )}
          </div>

          {data.leverage_analysis.debt_to_equity?.trend && (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
              <h4 className="font-semibold mb-3">Debt-to-Equity Trend</h4>
              <div className="space-y-2">
                {data.leverage_analysis.debt_to_equity.trend.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <span className="text-sm text-gray-700 dark:text-gray-300">{item.period}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                        <div
                          className="bg-orange-600 h-2 rounded-full"
                          style={{ width: `${Math.min(item.ratio, 2) / 2 * 100}%` }}
                        />
                      </div>
                      <span className="font-semibold text-sm w-12 text-right">
                        {item.ratio.toFixed(2)}x
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-xs text-gray-600 dark:text-gray-400">
                {data.leverage_analysis.debt_to_equity.direction === "increasing"
                  ? "⚠️ Leverage is increasing - monitor debt trends"
                  : data.leverage_analysis.debt_to_equity.direction === "decreasing"
                    ? "✓ Deleveraging trend - positive for financial health"
                    : "→ Stable leverage levels"}
              </p>
            </div>
          )}

          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
            <h4 className="font-semibold mb-2">Leverage Guidelines</h4>
            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <p>• <strong>D/E &lt; 0.5:</strong> Conservative - strong balance sheet</p>
              <p>• <strong>D/E 0.5-1.0:</strong> Moderate - manageable debt levels</p>
              <p>• <strong>D/E 1.0-1.5:</strong> Elevated - monitor closely</p>
              <p>• <strong>D/E &gt; 1.5:</strong> High - increased financial risk</p>
              <p>• <strong>Interest Coverage &gt; 5:</strong> Comfortable debt servicing</p>
              <p>• <strong>Interest Coverage &lt; 2:</strong> Risky - debt servicing concerns</p>
            </div>
          </div>
        </div>
      )}

      {/* Liquidity Tab */}
      {activeTab === "liquidity" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {data.liquidity_analysis.current_ratio?.current !== undefined && (
              <MetricCard
                label="Current Ratio"
                value={data.liquidity_analysis.current_ratio.current}
                unit=""
                health={data.liquidity_analysis.current_ratio.health}
              />
            )}
            {data.liquidity_analysis.quick_ratio?.current !== undefined && (
              <MetricCard
                label="Quick Ratio"
                value={data.liquidity_analysis.quick_ratio.current}
                unit=""
                health={data.liquidity_analysis.quick_ratio.health}
              />
            )}
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
            <h4 className="font-semibold mb-2">Liquidity Guidelines</h4>
            <div className="space-y-3 text-sm">
              <div>
                <p className="font-semibold text-gray-700 dark:text-gray-300">Current Ratio</p>
                <p className="text-gray-600 dark:text-gray-400">How many times current liabilities covered by current assets</p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">• Healthy: 1.5-3.0 • Adequate: 1.0-1.5 • Concerning: &lt;1.0</p>
              </div>
              <div>
                <p className="font-semibold text-gray-700 dark:text-gray-300">Quick Ratio</p>
                <p className="text-gray-600 dark:text-gray-400">Can company cover short-term obligations with liquid assets</p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">• Healthy: ≥1.0 • Adequate: 0.5-1.0 • Concerning: &lt;0.5</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-orange-200 dark:border-orange-700 bg-orange-50 dark:bg-orange-950 p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-orange-600 dark:text-orange-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-orange-900 dark:text-orange-100">Liquidity Check</p>
                <p className="text-sm text-orange-800 dark:text-orange-200 mt-1">
                  A company with strong operating cash flow can operate with lower ratios. Review cash flow alongside these ratios for complete picture.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
