"use client";
import React, { useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Target,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";

interface CashFlowData {
  operating_cash_flow_analysis: {
    current?: number;
    trend?: Array<{ period: string; ocf?: number }>;
    growth_pct?: number;
    direction?: string;
  };
  free_cash_flow_analysis: {
    current?: number;
    trend?: Array<{ period: string; fcf?: number }>;
    growth_pct?: number;
    status?: string;
  };
  cash_conversion_analysis: {
    current?: number;
    quality?: string;
    note?: string;
    trend?: Array<{ period: string; ratio?: number }>;
  };
  capex_intensity_analysis: {
    current?: number;
    level?: string;
  };
  cash_flow_scorecard: {
    ocf_health: string;
    fcf_health: string;
    conversion_quality: string;
    overall_cash_flow_score: number;
    recommendations: string[];
  };
}

const MetricCard = ({ label, value, unit, status }: any) => {
  const getStatusColor = () => {
    if (status === "positive")
      return "bg-green-100 dark:bg-green-900";
    if (status === "negative")
      return "bg-red-100 dark:bg-red-900";
    return "bg-white dark:bg-slate-800";
  };

  return (
    <div className={`rounded-lg p-4 border border-gray-200 dark:border-slate-700 ${getStatusColor()}`}>
      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">{label}</p>
      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        {value === null || value === undefined ? "—" : `${value.toFixed(0)}${unit}`}
      </p>
    </div>
  );
};

const QualityBadge = ({ quality }: any) => {
  const getColor = () => {
    switch (quality) {
      case "excellent":
        return "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200";
      case "good":
        return "bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200";
      case "moderate":
        return "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200";
      case "poor":
        return "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200";
      default:
        return "bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200";
    }
  };

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${getColor()}`}>
      {quality}
    </span>
  );
};

export function CashFlowHealthSection({ data }: { data?: CashFlowData }) {
  const [activeTab, setActiveTab] = useState<"ocf" | "fcf" | "quality">("ocf");

  if (!data) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Cash flow analysis requires workspace data</p>
      </div>
    );
  }

  const scorecard = data.cash_flow_scorecard;

  return (
    <div className="space-y-6">
      {/* Cash Flow Scorecard */}
      <div className="bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-950 dark:to-teal-950 rounded-lg p-6 border border-emerald-200 dark:border-emerald-800">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="font-bold text-xl mb-2">Cash Flow Health</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Operating, investing, and free cash flow quality
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-emerald-600 dark:text-emerald-400">
              {scorecard.overall_cash_flow_score}
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400">/ 100</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Operating Cash</p>
            <p className="text-sm font-bold capitalize">{scorecard.ocf_health}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Free Cash</p>
            <p className="text-sm font-bold capitalize">{scorecard.fcf_health}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Conversion</p>
            <p className="text-sm font-bold capitalize">{scorecard.conversion_quality}</p>
          </div>
        </div>

        {scorecard.recommendations.length > 0 && (
          <div className="p-4 bg-white dark:bg-slate-800 rounded-lg border border-emerald-200 dark:border-emerald-700">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <Target className="w-4 h-4" />
              Cash Flow Insights
            </h4>
            <ul className="space-y-2">
              {scorecard.recommendations.map((rec, idx) => (
                <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-600 dark:text-emerald-400" />
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
          onClick={() => setActiveTab("ocf")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "ocf"
              ? "border-emerald-600 text-emerald-600 dark:text-emerald-400"
              : "border-transparent text-gray-600 dark:text-gray-400"
          }`}
        >
          <Activity className="w-4 h-4 inline mr-2" />
          Operating CF
        </button>
        <button
          onClick={() => setActiveTab("fcf")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "fcf"
              ? "border-emerald-600 text-emerald-600 dark:text-emerald-400"
              : "border-transparent text-gray-600 dark:text-gray-400"
          }`}
        >
          <Activity className="w-4 h-4 inline mr-2" />
          Free CF
        </button>
        <button
          onClick={() => setActiveTab("quality")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "quality"
              ? "border-emerald-600 text-emerald-600 dark:text-emerald-400"
              : "border-transparent text-gray-600 dark:text-gray-400"
          }`}
        >
          <Activity className="w-4 h-4 inline mr-2" />
          Conversion
        </button>
      </div>

      {/* Operating CF Tab */}
      {activeTab === "ocf" && (
        <div className="space-y-4">
          <div>
            <h3 className="font-bold mb-4">Operating Cash Flow</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Cash generated from core business operations (before capex)
            </p>
            <MetricCard
              label="Current OCF"
              value={data.operating_cash_flow_analysis.current}
              unit=""
            />

            {data.operating_cash_flow_analysis.growth_pct !== undefined && (
              <div className="mt-4 bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold">5-Year Growth</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {data.operating_cash_flow_analysis.direction === "improving"
                        ? "Growing steadily"
                        : "Stable or declining"}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">
                      {data.operating_cash_flow_analysis.growth_pct?.toFixed(1)}%
                    </p>
                    {data.operating_cash_flow_analysis.growth_pct! > 0 ? (
                      <TrendingUp className="w-4 h-4 text-green-600 mx-auto" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-red-600 mx-auto" />
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Free CF Tab */}
      {activeTab === "fcf" && (
        <div className="space-y-4">
          <div>
            <h3 className="font-bold mb-4">Free Cash Flow</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              OCF minus capital expenditures - cash available for dividends/debt/growth
            </p>
            <div className="grid grid-cols-2 gap-4">
              <MetricCard
                label="Current FCF"
                value={data.free_cash_flow_analysis.current}
                unit=""
                status={data.free_cash_flow_analysis.status}
              />
              {data.capex_intensity_analysis.current !== undefined && (
                <MetricCard
                  label="CapEx Intensity"
                  value={data.capex_intensity_analysis.current}
                  unit="%"
                />
              )}
            </div>

            {data.free_cash_flow_analysis.trend && (
              <div className="mt-4 bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <h4 className="font-semibold mb-3">5-Year FCF Trend</h4>
                <div className="space-y-2">
                  {data.free_cash_flow_analysis.trend.map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center">
                      <span className="text-sm text-gray-700 dark:text-gray-300">{item.period}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-32 bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                          <div
                            className={item.fcf! >= 0 ? "bg-emerald-600" : "bg-red-600"}
                            style={{
                              width: `${Math.min(Math.abs(item.fcf!), 1000) / 1000 * 100}%`,
                            }}
                          />
                        </div>
                        <span className="font-semibold text-sm w-16 text-right">
                          {(item.fcf! / 1000000).toFixed(1)}M
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="rounded-lg border border-emerald-200 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-950 p-4">
              <p className="text-sm font-semibold text-emerald-900 dark:text-emerald-100 mb-2">
                {data.free_cash_flow_analysis.status === "positive"
                  ? "✓ Positive FCF - Strong cash generation"
                  : "⚠️ Negative FCF - CapEx exceeds operating cash"}
              </p>
              {data.free_cash_flow_analysis.status === "positive" && (
                <p className="text-xs text-emerald-800 dark:text-emerald-200">
                  Company can invest in growth, pay dividends, or reduce debt
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Conversion Quality Tab */}
      {activeTab === "quality" && (
        <div className="space-y-4">
          <div>
            <h3 className="font-bold mb-4">Cash Conversion Quality</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Operating Cash Flow vs Net Income - Quality of earnings
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">OCF/NI Ratio</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {data.cash_conversion_analysis.current?.toFixed(0)}%
                </p>
              </div>
              <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Quality Rating</p>
                <QualityBadge quality={data.cash_conversion_analysis.quality} />
              </div>
            </div>

            {data.cash_conversion_analysis.note && (
              <div className="mt-4 bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <p className="font-semibold mb-2">Assessment</p>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {data.cash_conversion_analysis.note}
                </p>
              </div>
            )}

            <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
              <h4 className="font-semibold mb-3">Conversion Quality Guide</h4>
              <div className="space-y-2 text-sm">
                <p>
                  <strong className="text-emerald-600 dark:text-emerald-400">≥100%:</strong> OCF exceeds
                  reported earnings - highest quality
                </p>
                <p>
                  <strong className="text-blue-600 dark:text-blue-400">80-100%:</strong> OCF tracking
                  earnings - good quality
                </p>
                <p>
                  <strong className="text-yellow-600 dark:text-yellow-400">50-80%:</strong> Some divergence
                  - moderate concerns
                </p>
                <p>
                  <strong className="text-red-600 dark:text-red-400">&lt;50%:</strong> Big gap between profit
                  and cash - investigate
                </p>
              </div>
            </div>

            {data.cash_conversion_analysis.trend && (
              <div className="mt-4 bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <h4 className="font-semibold mb-3">Conversion Ratio Trend</h4>
                <div className="space-y-2">
                  {data.cash_conversion_analysis.trend.map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center">
                      <span className="text-sm text-gray-700 dark:text-gray-300">{item.period}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-indigo-600 h-2 rounded-full"
                            style={{ width: `${Math.min(item.ratio!, 150) / 150 * 100}%` }}
                          />
                        </div>
                        <span className="font-semibold text-sm w-12 text-right">
                          {item.ratio?.toFixed(0)}%
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
    </div>
  );
}
