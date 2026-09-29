"use client";
import React, { useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Target,
  Activity,
} from "lucide-react";

interface CAGRValues {
  "1y"?: number;
  "3y_cagr"?: number;
  "5y_cagr"?: number;
  "10y_cagr"?: number;
  "max_cagr"?: number;
  "ni_1y"?: number;
  "ni_5y_cagr"?: number;
}

interface GrowthData {
  growth_metrics: {
    revenue_growth: CAGRValues;
    profit_growth: CAGRValues;
    eps_growth: CAGRValues;
    historical_data: Record<string, Array<[number, string]>>;
  };
  margin_analysis: {
    gross_margin: Array<{ period: string; margin: number }>;
    operating_margin: Array<{ period: string; margin: number }>;
    net_margin: Array<{ period: string; margin: number }>;
    margin_trends: Record<string, any>;
  };
  dilution_analysis: {
    eps_vs_earnings_growth: Record<string, any>;
    dilution_analysis: Record<string, any>;
    has_dilution: boolean;
  };
  growth_scorecard: {
    revenue_health: string;
    profit_health: string;
    margin_health: string;
    dilution_health: string;
    overall_growth_score: number;
    recommendations: string[];
  };
}

const MetricCard = ({ label, value, unit, trend, color }: any) => (
  <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
    <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">{label}</p>
    <div className="flex items-center justify-between">
      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        {value === null ? "—" : `${value.toFixed(1)}${unit}`}
      </p>
      {trend !== undefined && (
        <div className={`flex items-center gap-1 ${trend >= 0 ? "text-green-600" : "text-red-600"}`}>
          {trend >= 0 ? (
            <TrendingUp className="w-4 h-4" />
          ) : (
            <TrendingDown className="w-4 h-4" />
          )}
          <span className="text-sm font-semibold">{Math.abs(trend).toFixed(1)}%</span>
        </div>
      )}
    </div>
  </div>
);

const HealthBadge = ({ status, label }: any) => {
  const getColor = () => {
    switch (status) {
      case "excellent":
      case "improving":
      case "healthy":
        return "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200";
      case "good":
      case "stable":
        return "bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200";
      case "moderate":
        return "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200";
      case "deteriorating":
      case "warning":
        return "bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200";
      case "weak":
      case "declining":
        return "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200";
      default:
        return "bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200";
    }
  };

  return (
    <div className="flex items-center gap-2">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">{label}</p>
      <span
        className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${getColor()}`}
      >
        {status}
      </span>
    </div>
  );
};

export function FinancialGrowthSection({ data }: { data?: GrowthData }) {
  const [activeTab, setActiveTab] = useState<"growth" | "margins" | "dilution">("growth");

  if (!data) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Financial growth analysis requires integration with research workspace data</p>
      </div>
    );
  }

  const scorecard = data.growth_scorecard;
  const growth = data.growth_metrics;
  const margins = data.margin_analysis;
  const dilution = data.dilution_analysis;

  return (
    <div className="space-y-6">
      {/* Overall Growth Scorecard */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="font-bold text-xl mb-2">Financial Growth Scorecard</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              5-year analysis of revenue, profit, and margin health
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-blue-600 dark:text-blue-400">
              {scorecard.overall_growth_score}
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400">/ 100</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <HealthBadge status={scorecard.revenue_health} label="Revenue" />
          <HealthBadge status={scorecard.profit_health} label="Profit" />
          <HealthBadge status={scorecard.margin_health} label="Margins" />
          <HealthBadge status={scorecard.dilution_health} label="Dilution" />
        </div>

        {scorecard.recommendations.length > 0 && (
          <div className="mt-6 p-4 bg-white dark:bg-slate-800 rounded-lg border border-blue-200 dark:border-blue-700">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <Target className="w-4 h-4" />
              Key Insights
            </h4>
            <ul className="space-y-2">
              {scorecard.recommendations.map((rec, idx) => (
                <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-blue-600 dark:text-blue-400" />
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
          onClick={() => setActiveTab("growth")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "growth"
              ? "border-blue-600 text-blue-600 dark:text-blue-400"
              : "border-transparent text-gray-600 dark:text-gray-400"
          }`}
        >
          <BarChart3 className="w-4 h-4 inline mr-2" />
          Growth Metrics
        </button>
        <button
          onClick={() => setActiveTab("margins")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "margins"
              ? "border-blue-600 text-blue-600 dark:text-blue-400"
              : "border-transparent text-gray-600 dark:text-gray-400"
          }`}
        >
          <Activity className="w-4 h-4 inline mr-2" />
          Margin Trends
        </button>
        <button
          onClick={() => setActiveTab("dilution")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "dilution"
              ? "border-blue-600 text-blue-600 dark:text-blue-400"
              : "border-transparent text-gray-600 dark:text-gray-400"
          }`}
        >
          <AlertTriangle className="w-4 h-4 inline mr-2" />
          Dilution Analysis
        </button>
      </div>

      {/* Growth Metrics Tab */}
      {activeTab === "growth" && (
        <div className="space-y-6">
          <div>
            <h3 className="font-bold mb-4">Revenue Growth (CAGR)</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                label="1-Year"
                value={growth.revenue_growth["1y"]}
                unit="%"
              />
              <MetricCard
                label="3-Year CAGR"
                value={growth.revenue_growth["3y_cagr"]}
                unit="%"
              />
              <MetricCard
                label="5-Year CAGR"
                value={growth.revenue_growth["5y_cagr"]}
                unit="%"
              />
              <MetricCard
                label="10-Year CAGR"
                value={growth.revenue_growth["10y_cagr"]}
                unit="%"
              />
            </div>
          </div>

          <div>
            <h3 className="font-bold mb-4">Profit Growth (CAGR)</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                label="Operating Profit 1Y"
                value={growth.profit_growth["1y"]}
                unit="%"
              />
              <MetricCard
                label="Operating Profit 5Y CAGR"
                value={growth.profit_growth["5y_cagr"]}
                unit="%"
              />
              <MetricCard
                label="Net Income 1Y"
                value={growth.profit_growth["ni_1y"]}
                unit="%"
              />
              <MetricCard
                label="Net Income 5Y CAGR"
                value={growth.profit_growth["ni_5y_cagr"]}
                unit="%"
              />
            </div>
          </div>

          <div>
            <h3 className="font-bold mb-4">EPS Growth (CAGR)</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                label="1-Year"
                value={growth.eps_growth["1y"]}
                unit="%"
              />
              <MetricCard
                label="3-Year CAGR"
                value={growth.eps_growth["3y_cagr"]}
                unit="%"
              />
              <MetricCard
                label="5-Year CAGR"
                value={growth.eps_growth["5y_cagr"]}
                unit="%"
              />
            </div>
          </div>
        </div>
      )}

      {/* Margin Trends Tab */}
      {activeTab === "margins" && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 border border-gray-200 dark:border-slate-700">
            <h3 className="font-bold mb-4">Gross Margin Trend (Last 5 Periods)</h3>
            {margins.gross_margin.length > 0 ? (
              <div className="space-y-2">
                {margins.gross_margin.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <span className="text-sm text-gray-700 dark:text-gray-300">{item.period}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{ width: `${Math.min(item.margin, 100)}%` }}
                        />
                      </div>
                      <span className="font-semibold text-sm w-12 text-right">
                        {item.margin.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400">No data available</p>
            )}
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 border border-gray-200 dark:border-slate-700">
            <h3 className="font-bold mb-4">Operating Margin Trend (Last 5 Periods)</h3>
            {margins.operating_margin.length > 0 ? (
              <div className="space-y-2">
                {margins.operating_margin.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <span className="text-sm text-gray-700 dark:text-gray-300">{item.period}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${Math.min(Math.max(item.margin, 0), 100)}%` }}
                        />
                      </div>
                      <span className="font-semibold text-sm w-12 text-right">
                        {item.margin.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400">No data available</p>
            )}
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 border border-gray-200 dark:border-slate-700">
            <h3 className="font-bold mb-4">Net Margin Trend (Last 5 Periods)</h3>
            {margins.net_margin.length > 0 ? (
              <div className="space-y-2">
                {margins.net_margin.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <span className="text-sm text-gray-700 dark:text-gray-300">{item.period}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full"
                          style={{ width: `${Math.min(Math.max(item.margin, 0), 100)}%` }}
                        />
                      </div>
                      <span className="font-semibold text-sm w-12 text-right">
                        {item.margin.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400">No data available</p>
            )}
          </div>

          {margins.margin_trends.net_margin_trend && (
            <div
              className={`rounded-lg p-4 ${
                margins.margin_trends.net_margin_trend.direction === "improving"
                  ? "bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800"
                  : "bg-orange-50 dark:bg-orange-950 border border-orange-200 dark:border-orange-800"
              }`}
            >
              <p className="font-semibold mb-2">Margin Trend Summary</p>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                Net margin is <strong>{margins.margin_trends.net_margin_trend.direction}</strong>{" "}
                ({margins.margin_trends.net_margin_trend.change_points > 0 ? "+" : ""}
                {margins.margin_trends.net_margin_trend.change_points.toFixed(2)} percentage points)
              </p>
            </div>
          )}
        </div>
      )}

      {/* Dilution Analysis Tab */}
      {activeTab === "dilution" && (
        <div className="space-y-6">
          {dilution.eps_vs_earnings_growth.eps_cagr !== undefined && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <MetricCard
                label="Net Income CAGR"
                value={dilution.eps_vs_earnings_growth.net_income_cagr}
                unit="%"
              />
              <MetricCard
                label="EPS CAGR"
                value={dilution.eps_vs_earnings_growth.eps_cagr}
                unit="%"
              />
            </div>
          )}

          {dilution.dilution_analysis.status && (
            <div
              className={`rounded-lg p-6 border-2 ${
                dilution.dilution_analysis.status === "no_dilution"
                  ? "bg-green-50 dark:bg-green-950 border-green-300 dark:border-green-700"
                  : dilution.dilution_analysis.status === "dilution_detected"
                    ? "bg-orange-50 dark:bg-orange-950 border-orange-300 dark:border-orange-700"
                    : "bg-blue-50 dark:bg-blue-950 border-blue-300 dark:border-blue-700"
              }`}
            >
              <div className="flex items-start gap-3">
                {dilution.dilution_analysis.status === "no_dilution" ? (
                  <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400 flex-shrink-0 mt-1" />
                ) : (
                  <AlertTriangle className="w-6 h-6 text-orange-600 dark:text-orange-400 flex-shrink-0 mt-1" />
                )}
                <div>
                  <h4 className="font-bold mb-2 text-lg capitalize">
                    {dilution.dilution_analysis.status.replace(/_/g, " ")}
                  </h4>
                  <p className="text-gray-800 dark:text-gray-200">
                    {dilution.dilution_analysis.message}
                  </p>
                  {dilution.dilution_analysis.difference !== undefined && (
                    <p className="mt-2 text-sm font-semibold">
                      Difference: {Math.abs(dilution.dilution_analysis.difference).toFixed(1)}%
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
