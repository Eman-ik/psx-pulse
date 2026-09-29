'use client'

import React, { useState } from 'react'
import { AlertCircle, CheckCircle, Shield, TrendingDown } from 'lucide-react'

export interface GovernanceData {
  ownership_structure: {
    sponsor_concentration: string
    free_float: number | null
    public_holding: number | null
    concentration_risk: string
  }
  governance_assessment: {
    governance_risk_level: string
    red_flags: string[]
    positive_factors: string[]
    governance_score: number
  }
  risk_factors: Record<string, any>
  summary: {
    governance_risk_level: string
    governance_score: number
    red_flags: string[]
    positive_factors: string[]
  }
}

interface ManagementGovernanceSectionProps {
  data?: GovernanceData
  isLoading?: boolean
}

export default function ManagementGovernanceSection({
  data,
  isLoading = false
}: ManagementGovernanceSectionProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'ownership' | 'risks'>('overview')

  if (isLoading) {
    return (
      <div className="p-6 bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700 min-h-96 flex items-center justify-center">
        <div className="animate-pulse text-slate-400">Loading governance analysis...</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="p-6 bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700">
        <div className="text-slate-400">No governance data available</div>
      </div>
    )
  }

  const riskLevel = data.summary.governance_risk_level || 'unknown'
  const riskColor = {
    low: 'text-green-400 bg-green-950',
    moderate: 'text-yellow-400 bg-yellow-950',
    elevated: 'text-orange-400 bg-orange-950',
    high: 'text-red-400 bg-red-950',
    unknown: 'text-slate-400 bg-slate-800'
  }[riskLevel] || 'text-slate-400 bg-slate-800'

  const scoreColor = data.summary.governance_score >= 70 ? 'text-green-400' : data.summary.governance_score >= 50 ? 'text-yellow-400' : 'text-red-400'

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg border border-slate-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white">Management & Corporate Governance</h3>
          <div className={`px-4 py-2 rounded-full text-sm font-semibold ${riskColor} flex items-center gap-2`}>
            {riskLevel === 'low' && <CheckCircle className="w-4 h-4" />}
            {riskLevel === 'moderate' && <AlertCircle className="w-4 h-4" />}
            {(riskLevel === 'elevated' || riskLevel === 'high') && <TrendingDown className="w-4 h-4" />}
            {riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)} Risk
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-slate-400 text-sm mb-1">Governance Score</div>
            <div className={`text-4xl font-bold ${scoreColor}`}>{data.summary.governance_score}</div>
            <div className="text-slate-400 text-xs mt-1">out of 100</div>
          </div>
          <div>
            <div className="text-slate-400 text-sm mb-1">Risk Level</div>
            <div className={`text-xl font-semibold ${riskColor}`}>
              {riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)}
            </div>
          </div>
          <div>
            <div className="text-slate-400 text-sm mb-1">Concentration Risk</div>
            <div className="text-xl font-semibold text-slate-300 capitalize">
              {data.ownership_structure.concentration_risk.charAt(0).toUpperCase() + data.ownership_structure.concentration_risk.slice(1)}
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-slate-700">
        {(['overview', 'ownership', 'risks'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-3 font-medium text-sm transition-colors ${
              activeTab === tab
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            {tab === 'overview' && 'Assessment'}
            {tab === 'ownership' && 'Ownership Structure'}
            {tab === 'risks' && 'Risk Factors'}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg border border-slate-700 p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div>
              <h4 className="text-slate-300 font-semibold mb-4 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                Positive Factors
              </h4>
              {data.summary.positive_factors.length > 0 ? (
                <div className="space-y-2">
                  {data.summary.positive_factors.map((factor, idx) => (
                    <div key={idx} className="bg-green-950/30 border border-green-600/30 rounded p-3 flex gap-3">
                      <div className="w-2 h-2 rounded-full bg-green-400 mt-1.5 flex-shrink-0"></div>
                      <p className="text-slate-300 text-sm">{factor}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-400 text-sm">No positive factors identified</p>
              )}
            </div>

            {data.summary.red_flags.length > 0 && (
              <div>
                <h4 className="text-slate-300 font-semibold mb-4 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400" />
                  Red Flags & Monitoring Items
                </h4>
                <div className="space-y-2">
                  {data.summary.red_flags.map((flag, idx) => (
                    <div key={idx} className="bg-red-950/30 border border-red-600/30 rounded p-3 flex gap-3">
                      <div className="w-2 h-2 rounded-full bg-red-400 mt-1.5 flex-shrink-0"></div>
                      <p className="text-slate-300 text-sm">{flag}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'ownership' && (
          <div className="space-y-6">
            <div className="space-y-4">
              <h4 className="text-slate-300 font-semibold">Ownership Concentration</h4>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-700/30 rounded p-4 border border-slate-600/50">
                  <div className="text-slate-400 text-sm mb-2">Public Ownership (Free Float)</div>
                  <div className="text-3xl font-bold text-white">
                    {data.ownership_structure.free_float !== null ? `${data.ownership_structure.free_float.toFixed(1)}%` : 'N/A'}
                  </div>
                  <div className="text-xs text-slate-400 mt-2">Share available for public trading</div>
                </div>

                <div className="bg-slate-700/30 rounded p-4 border border-slate-600/50">
                  <div className="text-slate-400 text-sm mb-2">Sponsor/Promoter Holding</div>
                  <div className="text-3xl font-bold text-white">
                    {data.ownership_structure.free_float !== null ? `${(100 - data.ownership_structure.free_float).toFixed(1)}%` : 'N/A'}
                  </div>
                  <div className="text-xs text-slate-400 mt-2">Promoter/institutional ownership</div>
                </div>
              </div>

              <div className="bg-blue-950/30 border border-blue-600/30 rounded p-4">
                <h5 className="text-blue-400 font-semibold text-sm mb-2">Concentration Assessment</h5>
                <p className="text-slate-300 text-sm">
                  {data.ownership_structure.concentration_risk === 'low' &&
                    'Well-distributed ownership supports good governance and minority shareholder protection.'}
                  {data.ownership_structure.concentration_risk === 'moderate' &&
                    'Moderate concentration - monitor key board decisions and related-party transactions.'}
                  {data.ownership_structure.concentration_risk === 'high' &&
                    'High concentration - elevated minority shareholder risk. Close monitoring of governance required.'}
                </p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'risks' && (
          <div className="space-y-4">
            <p className="text-slate-300 mb-6">
              Key governance risk factors to monitor in investment decisions.
            </p>

            {Object.entries(data.risk_factors).map(([factor, details]: [string, any]) => (
              <div key={factor} className="bg-slate-700/30 rounded p-4 border border-slate-600/50">
                <h5 className="text-slate-300 font-semibold mb-1 capitalize">{factor.replace(/_/g, ' ')}</h5>
                <p className="text-slate-400 text-sm mb-2">{details.description}</p>
                {details.high_risk && (
                  <div className="text-xs text-orange-400 bg-orange-950/30 rounded px-2 py-1 inline-block">
                    High Risk: {details.high_risk}
                  </div>
                )}
                {details.optimal && (
                  <div className="text-xs text-green-400 bg-green-950/30 rounded px-2 py-1 inline-block ml-2">
                    Optimal: {details.optimal}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
