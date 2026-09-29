"use client";
import React, { useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Target,
  CheckCircle,
  AlertTriangle,
  BarChart3,
} from "lucide-react";

interface EarningsQualityData {
  reported_earnings_analysis: {
    trend?: Array<{ period: string; ni?: number }>;
    volatility?: number;
    consistency?: string;
    note?: string;
  };
  operating_earnings_analysis: {
    operating_margin?: number;
    net_margin?: number;
    margin_difference?: number;
    quality?: string;
    note?: string;
    trend?: Array<{ period: string; op?: number }>;
    growth_pct?: number;
    direction?: string;
  };
  earning_persistence_analysis: {
    positive_growth_ratio?: number;
    sustainability?: string;
    note?: string;
  };
  margin_quality_analysis: {
    trend?: Array<{ period: string; margin?: number }>;
    stability?: string;
    avg_change?: number;
  };
  normalized_eps: {
    current_eps?: number;
    normalized_eps?: number;
    quality_adjustment?: number;
  };
  earnings_quality_scorecard: {
    consistency_rating: string;
    persistence_rating: string;
    quality_rating: string;
    overall_earnings_quality_score: number;
    recommendations: string[];
  };
}

const QualityBadge = ({ rating }: any) => {
  const getColor = () => {
    switch (rating) {
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
    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${getColor()}`}>
      {rating}
    </span>
  );
};

const MetricCard = ({ label, value, unit }: any) => (
  <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
    <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">{label}</p>
    <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
      {value === null || value === undefined ? "—" : `${value.toFixed(2)}${unit}`}
    </p>
  </div>
);

export function EarningsQualitySection({ data }: { data?: EarningsQualityData }) {
  const [activeTab, setActiveTab] = useState<"consistency" | "operating" | "normalized">(
    "consistency"
  );

  if (!data) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Earnings quality analysis requires workspace data</p>
      </div>
    );
  }

  const scorecard = data.earnings_quality_scorecard;

  return (
    <div className="space-y-6">
      {/* Earnings Quality Scorecard */}
      <div className="bg-gradient-to-br from-cyan-50 to-blue-50 dark:from-cyan-950 dark:to-blue-950 rounded-lg p-6 border border-cyan-200 dark:border-cyan-800">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="font-bold text-xl mb-2">Earnings Quality Scorecard</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Sustainability and reliability of reported earnings
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-cyan-600 dark:text-cyan-400">
              {scorecard.overall_earnings_quality_score}
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400">/ 100</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Consistency</p>
            <QualityBadge rating={scorecard.consistency_rating} />
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Persistence</p>
            <QualityBadge rating={scorecard.persistence_rating} />
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Operating</p>
            <QualityBadge rating={scorecard.quality_rating} />
          </div>
        </div>

        {scorecard.recommendations.length > 0 && (
          <div className="p-4 bg-white dark:bg-slate-800 rounded-lg border border-cyan-200 dark:border-cyan-700">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <Target className="w-4 h-4" />
              Earnings Quality Insights
            </h4>
            <ul className="space-y-2">
              {scorecard.recommendations.map((rec, idx) => (
                <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-cyan-600 dark:text-cyan-400" />
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
          onClick={() => setActiveTab("consistency")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "consistency"
              ? "border-cyan-600 text-cyan-600 dark:text-cyan-400"
              : "border-transparent text-gray-600 dark:text-gray-400"
          }`}
        >
          <Activity className="w-4 h-4 inline mr-2" />
          Consistency
        </button>
        <button
          onClick={() => setActiveTab("operating")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "operating"
              ? "border-cyan-600 text-cyan-600 dark:text-cyan-400"
              : "border-transparent text-gray-600 dark:text-gray-400"
          }`}
        >
          <BarChart3 className="w-4 h-4 inline mr-2" />
          Operating vs Reported
        </button>
        <button
          onClick={() => setActiveTab("normalized")}
          className={`px-4 py-3 font-semibold text-sm border-b-2 transition-colors ${
            activeTab === "normalized"
              ? "border-cyan-600 text-cyan-600 dark:text-cyan-400"
              : "border-transparent text-gray-600 dark:text-gray-400"
          }`}
        >
          <Activity className="w-4 h-4 inline mr-2" />
          Normalized
        </button>
      </div>

      {/* Consistency Tab */}
      {activeTab === "consistency" && (
        <div className="space-y-4">
          <div>
            <h3 className="font-bold mb-4">Earnings Consistency</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Predictability and stability of earnings over time
            </p>

            {data.reported_earnings_analysis.volatility !== undefined && (
              <MetricCard
                label="Earnings Volatility"
                value={data.reported_earnings_analysis.volatility}
                unit="%"
              />
            )}

            {data.reported_earnings_analysis.consistency && (
              <div className="mt-4 bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <p className="font-semibold">Consistency Rating</p>
                  <QualityBadge rating={data.reported_earnings_analysis.consistency} />
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {data.reported_earnings_analysis.note}
                </p>
              </div>
            )}

            {data.earning_persistence_analysis.sustainability && (
              <div className="mt-4 bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <p className="font-semibold">Earnings Sustainability</p>
                  <QualityBadge rating={data.earning_persistence_analysis.sustainability} />
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                  {data.earning_persistence_analysis.note}
                </p>
                {data.earning_persistence_analysis.positive_growth_ratio !== undefined && (
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Positive growth in{" "}
                    {Math.round(data.earning_persistence_analysis.positive_growth_ratio * 100)}% of
                    periods
                  </p>
                )}
              </div>
            )}

            <div className="rounded-lg border border-cyan-200 dark:border-cyan-700 bg-cyan-50 dark:bg-cyan-950 p-4">
              <p className="text-sm font-semibold text-cyan-900 dark:text-cyan-100 mb-2">
                💡 What This Means
              </p>
              <p className="text-xs text-cyan-800 dark:text-cyan-200">
                High consistency indicates a predictable business with stable operations. Low consistency
                suggests external factors or operational challenges affecting earnings stability.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Operating vs Reported Tab */}
      {activeTab === "operating" && (
        <div className="space-y-4">
          <div>
            <h3 className="font-bold mb-4">Operating Earnings Quality</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Impact of non-recurring items on reported vs operating earnings
            </p>

            {data.operating_earnings_analysis.operating_margin !== undefined && (
              <div className="grid grid-cols-2 gap-4">
                <MetricCard
                  label="Operating Margin"
                  value={data.operating_earnings_analysis.operating_margin}
                  unit="%"
                />
                <MetricCard
                  label="Reported Net Margin"
                  value={data.operating_earnings_analysis.net_margin}
                  unit="%"
                />
              </div>
            )}

            {data.operating_earnings_analysis.margin_difference !== undefined && (
              <div className="mt-4 bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <p className="font-semibold">Margin Gap (Non-Recurring Impact)</p>
                  <p className="text-2xl font-bold">
                    {data.operating_earnings_analysis.margin_difference.toFixed(2)}%
                  </p>
                </div>
                {data.operating_earnings_analysis.quality && (
                  <div className="flex items-center gap-2">
                    <p className="text-sm text-gray-700 dark:text-gray-300">Quality:</p>
                    <QualityBadge quality={data.operating_earnings_analysis.quality} />
                  </div>
                )}
                {data.operating_earnings_analysis.note && (
                  <p className="text-sm text-gray-700 dark:text-gray-300 mt-2">
                    {data.operating_earnings_analysis.note}
                  </p>
                )}
              </div>
            )}

            {data.operating_earnings_analysis.trend && (
              <div className="mt-4 bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <h4 className="font-semibold mb-3">Operating Profit Trend</h4>
                <div className="space-y-2">
                  {data.operating_earnings_analysis.trend.map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center">
                      <span className="text-sm text-gray-700 dark:text-gray-300">{item.period}</span>
                      <span className="font-semibold text-sm">
                        {(item.op! / 1000000).toFixed(0)}M
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="rounded-lg border border-cyan-200 dark:border-cyan-700 bg-cyan-50 dark:bg-cyan-950 p-4">
              <p className="text-sm font-semibold text-cyan-900 dark:text-cyan-100 mb-2">
                ℹ️ Margin Gap Guide
              </p>
              <div className="text-xs text-cyan-800 dark:text-cyan-200 space-y-1">
                <p>• <strong>&lt;2%:</strong> Minimal non-recurring items - clean earnings</p>
                <p>• <strong>2-5%:</strong> Some non-recurring items but manageable</p>
                <p>• <strong>&gt;5%:</strong> Significant impact - investigate one-time items</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Normalized EPS Tab */}
      {activeTab === "normalized" && (
        <div className="space-y-4">
          <div>
            <h3 className="font-bold mb-4">Normalized Earnings Power</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Recurring earnings adjusted for quality and one-time items
            </p>

            {data.normalized_eps.current_eps !== undefined && (
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Reported EPS</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {data.normalized_eps.current_eps?.toFixed(2)}
                  </p>
                </div>
                <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Normalized EPS</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {data.normalized_eps.normalized_eps?.toFixed(2)}
                  </p>
                </div>
              </div>
            )}

            {data.normalized_eps.quality_adjustment !== undefined && (
              <div className="mt-4 bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <div className="flex items-center justify-between">
                  <p className="font-semibold">Quality Adjustment</p>
                  <p
                    className={`text-xl font-bold ${
                      data.normalized_eps.quality_adjustment <= 0
                        ? "text-orange-600 dark:text-orange-400"
                        : "text-green-600 dark:text-green-400"
                    }`}
                  >
                    {data.normalized_eps.quality_adjustment > 0 ? "+" : ""}
                    {data.normalized_eps.quality_adjustment}%
                  </p>
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 mt-2">
                  {data.normalized_eps.quality_adjustment === 0
                    ? "Reported EPS is reliable - minimal quality issues"
                    : data.normalized_eps.quality_adjustment < 0
                      ? "Quality concerns warrant conservative valuation"
                      : "Premium quality earnings for reliable valuation"}
                </p>
              </div>
            )}

            <div className="rounded-lg border border-cyan-200 dark:border-cyan-700 bg-cyan-50 dark:bg-cyan-950 p-4">
              <p className="text-sm font-semibold text-cyan-900 dark:text-cyan-100 mb-2">
                📊 Normalized EPS for Valuation
              </p>
              <p className="text-xs text-cyan-800 dark:text-cyan-200">
                Use normalized EPS instead of reported EPS for P/E ratio calculations to get a truer
                picture of earning power, especially when one-time items distort reported results.
              </p>
            </div>

            <div className="rounded-lg border border-blue-200 dark:border-blue-700 bg-blue-50 dark:bg-blue-950 p-4">
              <p className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
                💡 Quality Framework
              </p>
              <div className="text-xs text-blue-800 dark:text-blue-200 space-y-1">
                <p>
                  <strong>Excellent (0% adj):</strong> Reported earnings = recurring earnings
                </p>
                <p>
                  <strong>Good (-2% adj):</strong> Minor one-time items, still reliable
                </p>
                <p>
                  <strong>Fair (-5% adj):</strong> Moderate adjustments needed for comparison
                </p>
                <p>
                  <strong>Poor (-10% adj):</strong> Significant distortions, use normalized only
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
