"use client";
import React from "react";
import { Activity, TrendingUp } from "lucide-react";

interface CapitalAllocationData {
  cash_deployment: {
    reinvestment?: number;
    dividend_payout?: number;
    debt_repayment?: number;
  };
  allocation_assessment: {
    allocation_quality: string;
    focus_area: string;
    recommendations: string[];
  };
}

export function CapitalAllocationSection({ data }: { data?: CapitalAllocationData }) {
  if (!data) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Capital allocation analysis requires workspace data</p>
      </div>
    );
  }

  const deployment = data.cash_deployment;
  const assessment = data.allocation_assessment;

  return (
    <div className="space-y-6">
      {/* Assessment */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="font-bold text-xl mb-2">Capital Allocation Quality</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              How management deploys shareholder capital
            </p>
          </div>
          <div>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 capitalize">
              {assessment.allocation_quality}
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              {assessment.focus_area.replace("_", " ")}
            </p>
          </div>
        </div>

        {assessment.recommendations.length > 0 && (
          <div className="p-4 bg-white dark:bg-slate-800 rounded-lg border border-blue-200 dark:border-blue-700">
            <h4 className="font-semibold mb-3">Capital Allocation Insights</h4>
            <ul className="space-y-2">
              {assessment.recommendations.map((rec, idx) => (
                <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                  <TrendingUp className="w-4 h-4 mt-0.5 flex-shrink-0 text-blue-600" />
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Deployment Breakdown */}
      <div className="grid grid-cols-3 gap-4">
        {deployment.reinvestment !== undefined && (
          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Reinvestment %</p>
            <p className="text-2xl font-bold">{deployment.reinvestment?.toFixed(0)}%</p>
            <p className="text-xs text-gray-500 mt-2">of cash flow</p>
          </div>
        )}
        {deployment.dividend_payout !== undefined && (
          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Dividend %</p>
            <p className="text-2xl font-bold">{deployment.dividend_payout?.toFixed(0)}%</p>
            <p className="text-xs text-gray-500 mt-2">to shareholders</p>
          </div>
        )}
        {deployment.debt_repayment !== undefined && (
          <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Debt Paydown %</p>
            <p className="text-2xl font-bold">{deployment.debt_repayment?.toFixed(0)}%</p>
            <p className="text-xs text-gray-500 mt-2">debt reduction</p>
          </div>
        )}
      </div>

      {/* Framework */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
        <h4 className="font-semibold mb-3">Capital Allocation Choices</h4>
        <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
          <p className="font-semibold">Management has 5 choices with excess cash:</p>
          <ol className="list-decimal list-inside space-y-1 ml-2">
            <li>Reinvest in the business (growth)</li>
            <li>Acquire another business (expansion)</li>
            <li>Repay debt (deleveraging)</li>
            <li>Pay dividends (shareholder returns)</li>
            <li>Repurchase shares (EPS accretion)</li>
          </ol>
          <p className="mt-3 font-semibold text-blue-600 dark:text-blue-400">
            Determine whether decisions created value.
          </p>
        </div>
      </div>

      {/* Quality Indicators */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
        <h4 className="font-semibold mb-3">Signs of Good Capital Allocation</h4>
        <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
          <p>✓ Reinvestment at high ROIC (returns exceed cost of capital)</p>
          <p>✓ Conservative payout during growth phase</p>
          <p>✓ Strategic acquisitions that create synergies</p>
          <p>✓ Debt reduction with improving financial health</p>
          <p>✓ Sustainable dividend growth aligned with earnings</p>
        </div>
      </div>
    </div>
  );
}
