'use client'

import React, { useState } from 'react'
import { TrendingUp, TrendingDown, Info } from 'lucide-react'

export interface HistoricalValuationData {
  historical_multiples: {
    current_multiple: number | null
    historical_averages: Record<string, number>
    multiple_deviation: number | null
    valuation_signal: string
  }
  multiple_drivers: {
    likely_drivers: string[]
    risk_factors: string[]
    opportunity_factors: string[]
  }
  summary: {
    current_multiple: number | null
    valuation_signal: string
    multiple_deviation_pct: number | null
    key_drivers: string[]
  }
}

interface HistoricalValuationSectionProps {
  data?: HistoricalValuationData
  isLoading?: boolean
}

export default function HistoricalValuationSection({
  data,
  isLoading = false
}: HistoricalValuationSectionProps) {
  const [activeTab, setActiveTab] = useState<'multiples' | 'drivers' | 'signal'>('multiples')

  if (isLoading) {
    return (
      <div className="p-6 bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700 min-h-96 flex items-center justify-center">
        <div className="animate-pulse text-slate-400">Loading historical valuation...</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="p-6 bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700">
        <div className="text-slate-400">No historical valuation data available</div>
      </div>
    )
  }

  const signal = data.summary.valuation_signal || 'unknown'
  const signalColor = {
    significantly_undervalued: 'text-green-400 bg-green-950',
    undervalued: 'text-emerald-400 bg-emerald-950',
    fairly_valued: 'text-blue-400 bg-blue-950',
    overvalued: 'text-orange-400 bg-orange-950',
    significantly_overvalued: 'text-red-400 bg-red-950',
    unknown: 'text-slate-400 bg-slate-800'
  }[signal] || 'text-slate-400 bg-slate-800'

  const deviation = data.summary.multiple_deviation_pct || 0
  const deviationColor = deviation < -20 ? 'text-green-400' : deviation < -10 ? 'text-emerald-400' : deviation > 20 ? 'text-red-400' : deviation > 10 ? 'text-orange-400' : 'text-blue-400'

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg border border-slate-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white">Historical Valuation Analysis</h3>
          <div className={`px-4 py-2 rounded-full text-sm font-semibold ${signalColor}`}>
            {signal === 'significantly_undervalued' && (
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Significantly Undervalued
              </div>
            )}
            {signal === 'undervalued' && (
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Undervalued
              </div>
            )}
            {signal === 'fairly_valued' && (
              <div className="flex items-center gap-2">
                <Info className="w-4 h-4" />
                Fairly Valued
              </div>
            )}
            {signal === 'overvalued' && (
              <div className="flex items-center gap-2">
                <TrendingDown className="w-4 h-4" />
                Overvalued
              </div>
            )}
            {signal === 'significantly_overvalued' && (
              <div className="flex items-center gap-2">
                <TrendingDown className="w-4 h-4" />
                Significantly Overvalued
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-slate-400 text-sm mb-1">Current Multiple (P/E)</div>
            <div className="text-3xl font-bold text-white">
              {data.summary.current_multiple?.toFixed(2) || 'N/A'}
            </div>
          </div>
          <div>
            <div className="text-slate-400 text-sm mb-1">Historical Avg (P/E)</div>
            <div className="text-3xl font-bold text-slate-300">
              {data.historical_multiples.historical_averages['5_year_average']?.toFixed(2) || 'N/A'}
            </div>
          </div>
          <div>
            <div className="text-slate-400 text-sm mb-1">Deviation from Avg</div>
            <div className={`text-3xl font-bold ${deviationColor}`}>
              {deviation > 0 ? '+' : ''}{deviation.toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-slate-700">
        {(['multiples', 'drivers', 'signal'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-3 font-medium text-sm transition-colors ${
              activeTab === tab
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            {tab === 'multiples' && 'Historical Multiples'}
            {tab === 'drivers' && 'Multiple Drivers'}
            {tab === 'signal' && 'Valuation Signal'}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg border border-slate-700 p-6">
        {activeTab === 'multiples' && (
          <div className="space-y-4">
            <p className="text-slate-300 mb-6">
              Compare current valuation multiples to historical averages over multiple time periods.
            </p>
            <div className="grid grid-cols-3 gap-4">
              {Object.entries(data.historical_multiples.historical_averages).map(([period, value]) => (
                <div key={period} className="bg-slate-700/30 rounded p-4 border border-slate-600/50">
                  <div className="text-slate-400 text-sm mb-2 capitalize">
                    {period.replace(/_/g, ' ')}
                  </div>
                  <div className="text-2xl font-bold text-white">{(value as number)?.toFixed(2) || 'N/A'}</div>
                  <div className="text-xs text-slate-400 mt-2">
                    {data.summary.current_multiple && (
                      <>
                        {((data.summary.current_multiple - (value as number)) / (value as number) * 100).toFixed(1)}%
                        {((data.summary.current_multiple - (value as number)) / (value as number) * 100) > 0 ? ' higher' : ' lower'}
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'drivers' && (
          <div className="space-y-6">
            <p className="text-slate-300 mb-6">
              Factors driving the difference between current and historical valuation multiples.
            </p>

            {data.multiple_drivers.opportunity_factors.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-slate-300 font-semibold flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-green-400" />
                  Opportunity Factors
                </h4>
                <div className="space-y-2">
                  {data.multiple_drivers.opportunity_factors.map((factor, idx) => (
                    <div key={idx} className="bg-green-950/30 border border-green-600/30 rounded p-3 flex gap-3">
                      <div className="w-2 h-2 rounded-full bg-green-400 mt-1 flex-shrink-0"></div>
                      <p className="text-slate-300 text-sm">{factor}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.multiple_drivers.risk_factors.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-slate-300 font-semibold flex items-center gap-2">
                  <TrendingDown className="w-4 h-4 text-red-400" />
                  Risk Factors
                </h4>
                <div className="space-y-2">
                  {data.multiple_drivers.risk_factors.map((factor, idx) => (
                    <div key={idx} className="bg-red-950/30 border border-red-600/30 rounded p-3 flex gap-3">
                      <div className="w-2 h-2 rounded-full bg-red-400 mt-1 flex-shrink-0"></div>
                      <p className="text-slate-300 text-sm">{factor}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'signal' && (
          <div className="space-y-4">
            <p className="text-slate-300 mb-6">
              Valuation signal based on current multiple relative to historical averages.
            </p>

            <div className={`rounded-lg p-4 border ${
              signal === 'significantly_undervalued' || signal === 'undervalued'
                ? 'bg-green-950/30 border-green-600/30'
                : signal === 'fairly_valued'
                ? 'bg-blue-950/30 border-blue-600/30'
                : 'bg-red-950/30 border-red-600/30'
            }`}>
              <div className="flex gap-3">
                {(signal === 'significantly_undervalued' || signal === 'undervalued') && (
                  <>
                    <TrendingUp className={`w-5 h-5 flex-shrink-0 mt-1 ${signal === 'significantly_undervalued' ? 'text-green-400' : 'text-emerald-400'}`} />
                    <div>
                      <h4 className={`font-semibold mb-1 ${signal === 'significantly_undervalued' ? 'text-green-400' : 'text-emerald-400'}`}>
                        {signal === 'significantly_undervalued' ? 'Significantly Undervalued' : 'Undervalued'}
                      </h4>
                      <p className="text-slate-300 text-sm">
                        Current valuation is trading at a discount to historical averages. May represent attractive entry opportunity if fundamentals support the valuation.
                      </p>
                    </div>
                  </>
                )}
                {signal === 'fairly_valued' && (
                  <>
                    <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-1" />
                    <div>
                      <h4 className="text-blue-400 font-semibold mb-1">Fairly Valued</h4>
                      <p className="text-slate-300 text-sm">
                        Current valuation is aligned with historical averages. Pricing appears reasonable relative to past levels.
                      </p>
                    </div>
                  </>
                )}
                {(signal === 'overvalued' || signal === 'significantly_overvalued') && (
                  <>
                    <TrendingDown className={`w-5 h-5 flex-shrink-0 mt-1 ${signal === 'significantly_overvalued' ? 'text-red-400' : 'text-orange-400'}`} />
                    <div>
                      <h4 className={`font-semibold mb-1 ${signal === 'significantly_overvalued' ? 'text-red-400' : 'text-orange-400'}`}>
                        {signal === 'significantly_overvalued' ? 'Significantly Overvalued' : 'Overvalued'}
                      </h4>
                      <p className="text-slate-300 text-sm">
                        Current valuation is trading at a premium to historical averages. Watch for normalization or ensure fundamentals justify the premium.
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
