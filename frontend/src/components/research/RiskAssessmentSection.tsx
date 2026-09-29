"use client";
import React from "react";
import { AlertTriangle, Activity, CheckCircle } from "lucide-react";

interface RiskData {
  key_risks: Array<{
    category: string;
    level: string;
    description: string;
    specific_risks: string[];
    score: number;
  }>;
  risk_assessment: {
    overall_risk_level: string;
    average_risk_score: number;
  };
}

const getRiskColor = (level: string) => {
  if (level === "low") return "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200";
  if (level === "moderate") return "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200";
  if (level === "elevated") return "bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200";
  return "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200";
};

export function RiskAssessmentSection({ data }: { data?: RiskData }) {
  if (!data) {
    return (
      <div className="p-6 text-center text-gray-500 dark:text-gray-400">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>Risk assessment requires workspace data</p>
      </div>
    );
  }

  const assessment = data.risk_assessment;
  const risks = data.key_risks;

  return (
    <div className="space-y-6">
      {/* Overall Risk */}
      <div className={`rounded-lg p-6 border-2 ${getRiskColor(assessment.overall_risk_level)}`}>
        <div className="flex items-start gap-4">
          <AlertTriangle className="w-6 h-6 mt-1 flex-shrink-0" />
          <div>
            <h3 className="font-bold text-xl mb-2">Overall Risk Profile</h3>
            <p className="font-semibold capitalize text-lg">{assessment.overall_risk_level}</p>
            <p className="text-sm mt-2">Risk Score: {assessment.average_risk_score.toFixed(0)}/100</p>
            <p className="text-xs mt-2 opacity-80">Higher score indicates higher risk</p>
          </div>
        </div>
      </div>

      {/* Risk Categories */}
      <div className="space-y-3">
        <h3 className="font-bold text-lg">Risk Categories</h3>
        {risks.map((risk, idx) => (
          <div key={idx} className={`rounded-lg p-4 border border-gray-200 dark:border-slate-700 ${getRiskColor(risk.level)}`}>
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="font-semibold">{risk.category}</p>
                <p className="text-xs mt-1 opacity-80">{risk.description}</p>
              </div>
              <span className="px-2 py-1 rounded text-xs font-bold bg-white/20 backdrop-blur">
                {risk.score}/100
              </span>
            </div>
            {risk.specific_risks.length > 0 && (
              <div className="mt-2 text-sm space-y-1">
                {risk.specific_risks.map((r, i) => (
                  <p key={i} className="flex items-start gap-2">
                    <span className="opacity-60">•</span> {r}
                  </p>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Risk Thesis */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
        <h4 className="font-semibold mb-3 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          Investment Risk Thesis
        </h4>
        <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
          <p>Document your risk thesis before investing:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>What is the primary risk to your thesis?</li>
            <li>What would prove your thesis wrong?</li>
            <li>How would you know if risks are materializing?</li>
            <li>What is your exit trigger if risks escalate?</li>
          </ul>
        </div>
      </div>

      {/* Risk Categories Guide */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
        <h4 className="font-semibold mb-3">Risk Categories to Monitor</h4>
        <div className="space-y-2 text-xs text-gray-700 dark:text-gray-300">
          <p><strong>Business:</strong> Competition, market share, execution</p>
          <p><strong>Financial:</strong> Debt, liquidity, solvency</p>
          <p><strong>Currency:</strong> Foreign exchange exposure</p>
          <p><strong>Commodity:</strong> Raw material price volatility</p>
          <p><strong>Regulatory:</strong> Law changes, compliance</p>
          <p><strong>Geopolitical:</strong> Political instability, sanctions</p>
          <p><strong>Customer/Supplier:</strong> Concentration risk</p>
          <p><strong>Technology:</strong> Disruption risk</p>
        </div>
      </div>
    </div>
  );
}
