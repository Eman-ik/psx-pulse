'use client'

import React, { useState } from 'react'
import { TrendingUp, TrendingDown, AlertCircle, CheckCircle } from 'lucide-react'

export interface PeerComparisonData {
  peer_metrics: {
    company_ticker: string
    peer_count: number
    metric_rankings: Record<string, any>
    relative_valuation: Record<string, any>
    quality_comparison: Record<string, any>
  }
  relative_valuation: {
    premium_discount: Record<string, any>
    quality_vs_price: Record<string, any>
    investment_case: string
  }
  summary: {
    peers_in_universe: number
    investment_case: string
    valuation_context: string
  }
}

interface PeerComparisonSectionProps {
  data?: PeerComparisonData
  isLoading?: boolean
}

export default function PeerComparisonSection({
  data,
  isLoading = false
}: PeerComparisonSectionProps) {
  const [activeTab, setActiveTab] = useState<'metrics' | 'valuation' | 'case'>('metrics')

  if (isLoading) {
    return (
      <div className="p-6 bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700 min-h-96 flex items-center justify-center">
        <div className="animate-pulse text-slate-400">Loading peer comparison...</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="p-6 bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700">
        <div className="text-slate-400">No peer comparison data available</div>
      </div>
    )
  }

  const investmentCaseColor = {
    attractive: 'text-green-400 bg-green-950',
    concerning: 'text-red-400 bg-red-950',
    fairly_valued: 'text-blue-400 bg-blue-950'
  }[data.relative_valuation.investment_case] || 'text-slate-400 bg-slate-800'

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg border border-slate-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Peer Comparison Overview</h3>
          <div className={`px-4 py-2 rounded-full text-sm font-semibold ${investmentCaseColor}`}>
            {data.relative_valuation.investment_case === 'attractive' && (
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Attractive Valuation
              </div>
            )}
            {data.relative_valuation.investment_case === 'concerning' && (
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Concerning Valuation
              </div>
            )}
            {data.relative_valuation.investment_case === 'fairly_valued' && (
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Fairly Valued
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-slate-400 text-sm mb-1">Peers in Universe</div>
            <div className="text-3xl font-bold text-white">{data.summary.peers_in_universe}</div>
          </div>
          <div>
            <div className="text-slate-400 text-sm mb-1">Investment Case</div>
            <div className="text-xl font-semibold text-blue-400 capitalize">
              {data.relative_valuation.investment_case}
            </div>
          </div>
          <div>
            <div className="text-slate-400 text-sm mb-1">Analysis Context</div>
            <div className="text-sm text-slate-300">{data.summary.valuation_context}</div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-slate-700">
        {(['metrics', 'valuation', 'case'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-3 font-medium text-sm transition-colors ${
              activeTab === tab
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            {tab === 'metrics' && 'Metric Rankings'}
            {tab === 'valuation' && 'Valuation vs Peers'}
            {tab === 'case' && 'Investment Case'}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg border border-slate-700 p-6">
        {activeTab === 'metrics' && (
          <div className="space-y-4">
            <p className="text-slate-300 mb-6">
              Company metrics compared against peer group medians and averages.
            </p>
            {Object.entries(data.peer_metrics.metric_rankings).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(data.peer_metrics.metric_rankings).map(([metric, info]: [string, any]) => (
                  <div key={metric} className="bg-slate-700/30 rounded p-4 border border-slate-600/50">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="text-slate-300 font-medium capitalize">{metric.replace(/_/g, ' ')}</h4>
                      <span className="text-xs text-slate-400">vs {info.peer_count} peers</span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-slate-400">Peer Median</div>
                        <div className="text-white font-semibold">{info.peer_median?.toFixed(2) || 'N/A'}</div>
                      </div>
                      <div>
                        <div className="text-slate-400">Peer Average</div>
                        <div className="text-white font-semibold">{info.peer_average?.toFixed(2) || 'N/A'}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-400">No metric ranking data available</p>
            )}
          </div>
        )}

        {activeTab === 'valuation' && (
          <div className="space-y-4">
            <p className="text-slate-300 mb-6">
              Valuation premium/discount relative to peer group based on P/E and quality metrics.
            </p>
            {data.relative_valuation.premium_discount?.pe_comparison && (
              <div className="bg-slate-700/30 rounded p-4 border border-slate-600/50">
                <h4 className="text-slate-300 font-medium mb-4">P/E Comparison</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-slate-400">Company P/E</div>
                    <div className="text-white font-semibold">
                      {data.relative_valuation.premium_discount.pe_comparison.company_pe?.toFixed(2) || 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div className="text-slate-400">Peer Avg P/E</div>
                    <div className="text-white font-semibold">
                      {data.relative_valuation.premium_discount.pe_comparison.peer_avg_pe?.toFixed(2) || 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div className="text-slate-400">Discount %</div>
                    <div className={`font-semibold ${
                      (data.relative_valuation.premium_discount.pe_comparison.discount_pct || 0) > 0
                        ? 'text-green-400'
                        : 'text-red-400'
                    }`}>
                      {data.relative_valuation.premium_discount.pe_comparison.discount_pct?.toFixed(1) || 0}%
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'case' && (
          <div className="space-y-4">
            <p className="text-slate-300 mb-6">
              Investment case assessment based on quality metrics and valuation relative to peers.
            </p>
            <div className={`rounded-lg p-4 border ${
              data.relative_valuation.investment_case === 'attractive'
                ? 'bg-green-950/30 border-green-600/30'
                : data.relative_valuation.investment_case === 'concerning'
                ? 'bg-red-950/30 border-red-600/30'
                : 'bg-blue-950/30 border-blue-600/30'
            }`}>
              <div className="flex gap-3">
                {data.relative_valuation.investment_case === 'attractive' && (
                  <>
                    <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-1" />
                    <div>
                      <h4 className="text-green-400 font-semibold mb-1">Attractive Valuation Case</h4>
                      <p className="text-slate-300 text-sm">
                        Company demonstrates superior quality metrics relative to its valuation discount vs peers.
                      </p>
                    </div>
                  </>
                )}
                {data.relative_valuation.investment_case === 'concerning' && (
                  <>
                    <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-1" />
                    <div>
                      <h4 className="text-red-400 font-semibold mb-1">Concerning Valuation Case</h4>
                      <p className="text-slate-300 text-sm">
                        Company quality lags peers despite trading at a premium valuation.
                      </p>
                    </div>
                  </>
                )}
                {data.relative_valuation.investment_case === 'fairly_valued' && (
                  <>
                    <TrendingUp className="w-5 h-5 text-blue-400 flex-shrink-0 mt-1" />
                    <div>
                      <h4 className="text-blue-400 font-semibold mb-1">Fairly Valued vs Peers</h4>
                      <p className="text-slate-300 text-sm">
                        Company valuation reasonably aligned with peer quality metrics.
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
