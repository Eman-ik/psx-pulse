"use client";
import React, { useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Target,
  CheckCircle,
  Activity,
} from "lucide-react";

interface ReturnData {
  roe_analysis: {
    current?: number;
    trend?: Array<{ period: string; roe: number }>;
    direction?: string;
    change_points?: number;
  };
  roa_analysis: {
    current?: number;
    trend?: Array<{ period: string; roa: number }>;
    direction?: string;
  };
  roic_analysis: {
    current?: number;
    trend?: Array<{ period: string; roic: number }>;
    direction?: string;
  };
  return_scorecard: {
    roe_health: string;
    roa_health: string;
    roic_health: string;
    overall_return_score: number;
    recommendations: string[];
  };
}

const MetricCard = ({ label, value, unit, trend }: any) => (
  <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
    <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">{label}</p>
    <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
      {value === null ? "—" : `${value.toFixed(1)}%`}
    </p>
    {trend !== undefined && (
      <div className={`flex items-center gap-1 mt-2 ${trend >= 0 ? "text-green-600" : "text-red-600"}`}>
        {trend >= 0 ? (
          <TrendingUp className="w-4 h-4" />
        ) : (
          <TrendingDown className="w-4 h-4" />
        )}
        <span className="text-sm font-semibold">{Math.abs(trend).toFixed(1)}%</span>
      </div>
    )}
  </div>
);

const HealthBadge = ({ status, label }: any) => {
  const getColor = () => {
    switch (status) {
      case "excellent":
        return "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200";
      case "good":
        return "bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200";
      case "moderate":
        return "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200";
      case "weak":
        return "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200";
      default:
        return "bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200";
    }
  };

  return (
    <div className="flex items-center gap-2">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">{label}</p>
      <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${getColor()}`}>
        {status}
      </span>
    </div>
  );
};

export function ReturnsOnCapitalSection({ data }: { data?: ReturnData }) {
  const [activeTab, setActiveTab] = useState<"roe" | "roa" | "roic">("roe");

  if (!data) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Returns on capital analysis requires workspace data</p>
      </div>
    );
  }

  const scorecard = data.return_scorecard;

  return (
    <div className="space-y-6">
      {/* Overall Returns Scorecard */}
      <div className="bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-950 dark:to-indigo-950 rounded-lg p-6 border border-purple-200 dark:border-purple-800">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="font-bold text-xl mb-2">Returns on Capital Scorecard</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Management efficiency in deploying shareholder capital
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-purple-600 dark:text-purple-400">
              {scorecard.overall_return_score}
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400">/ 100</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <HealthBadge status={scorecard.roe_health} label="ROE" />
          <HealthBadge status={scorecard.roa_health} label="ROA" />
          <HealthBadge status={scorecard.roic_health} label="ROIC" />
        </div>

        {scorecard.recommendations.length > 0 && (
          <div className="mt-6 p-4 bg-white dark:bg-slate-800 rounded-lg border border-purple-200 dark:border-purple-700">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <Target className="w-4 h-4" />
              Capital Efficiency Insights
            </h4>
            <ul className="space-y-2">
              {scorecard.recommendations.map((rec, idx) => (
                <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-purple-600 dark:text-purple-400" />
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
          onClick={() => setActiveTab("roe")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "roe"
              ? "border-purple-600 text-purple-600 dark:text-purple-400"
              : "border-transparent text-gray-600 dark:text-gray-400"
          }`}
        >
          <BarChart3 className="w-4 h-4 inline mr-2" />
          ROE
        </button>
        <button
          onClick={() => setActiveTab("roa")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "roa"
              ? "border-purple-600 text-purple-600 dark:text-purple-400"
              : "border-transparent text-gray-600 dark:text-gray-400"
          }`}
        >
          <BarChart3 className="w-4 h-4 inline mr-2" />
          ROA
        </button>
        <button
          onClick={() => setActiveTab("roic")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "roic"
              ? "border-purple-600 text-purple-600 dark:text-purple-400"
              : "border-transparent text-gray-600 dark:text-gray-400"
          }`}
        >
          <BarChart3 className="w-4 h-4 inline mr-2" />
          ROIC
        </button>
      </div>

      {/* ROE Tab */}
      {activeTab === "roe" && (
        <div className="space-y-4">
          <div>
            <h3 className="font-bold mb-4">Return on Equity (ROE)</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Net Income / Shareholders' Equity - How much profit per rupee of equity
            </p>
            <div className="grid grid-cols-2 gap-4">
              <MetricCard
                label="Current ROE"
                value={data.roe_analysis.current}
                unit="%"
              />
              {data.roe_analysis.trend && data.roe_analysis.trend.length > 0 && (
                <MetricCard
                  label="5-Year Trend"
                  value={data.roe_analysis.change_points}
                  unit="pp change"
                  trend={data.roe_analysis.change_points}
                />
              )}
            </div>

            {data.roe_analysis.trend && data.roe_analysis.trend.length > 0 && (
              <div className="mt-4 bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <h4 className="font-semibold mb-3">5-Year ROE Trend</h4>
                <div className="space-y-2">
                  {data.roe_analysis.trend.map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center">
                      <span className="text-sm text-gray-700 dark:text-gray-300">{item.period}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-32 bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-purple-600 h-2 rounded-full"
                            style={{ width: `${Math.min(item.roe, 50) / 50 * 100}%` }}
                          />
                        </div>
                        <span className="font-semibold text-sm w-12 text-right">
                          {item.roe.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ROA Tab */}
      {activeTab === "roa" && (
        <div className="space-y-4">
          <div>
            <h3 className="font-bold mb-4">Return on Assets (ROA)</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Net Income / Total Assets - How efficiently assets generate profit
            </p>
            <MetricCard
              label="Current ROA"
              value={data.roa_analysis.current}
              unit="%"
            />

            {data.roa_analysis.trend && data.roa_analysis.trend.length > 0 && (
              <div className="mt-4 bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <h4 className="font-semibold mb-3">5-Year ROA Trend</h4>
                <div className="space-y-2">
                  {data.roa_analysis.trend.map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center">
                      <span className="text-sm text-gray-700 dark:text-gray-300">{item.period}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-32 bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-indigo-600 h-2 rounded-full"
                            style={{ width: `${Math.min(item.roa, 20) / 20 * 100}%` }}
                          />
                        </div>
                        <span className="font-semibold text-sm w-12 text-right">
                          {item.roa.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ROIC Tab */}
      {activeTab === "roic" && (
        <div className="space-y-4">
          <div>
            <h3 className="font-bold mb-4">Return on Invested Capital (ROIC)</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Operating Profit / Invested Capital - Core business return on deployment
            </p>
            <MetricCard
              label="Current ROIC"
              value={data.roic_analysis.current}
              unit="%"
            />

            {data.roic_analysis.trend && data.roic_analysis.trend.length > 0 && (
              <div className="mt-4 bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <h4 className="font-semibold mb-3">5-Year ROIC Trend</h4>
                <div className="space-y-2">
                  {data.roic_analysis.trend.map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center">
                      <span className="text-sm text-gray-700 dark:text-gray-300">{item.period}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-32 bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-fuchsia-600 h-2 rounded-full"
                            style={{ width: `${Math.min(item.roic, 30) / 30 * 100}%` }}
                          />
                        </div>
                        <span className="font-semibold text-sm w-12 text-right">
                          {item.roic.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
                <p className="mt-4 text-xs text-gray-600 dark:text-gray-400">
                  High ROIC with ability to reinvest at similarly high returns indicates a moat and compounding potential.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
