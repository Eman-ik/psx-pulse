'use client'

import React, { useState } from 'react'
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react'

export interface FundamentalScorecardData {
  fundamental_scorecard: {
    component_scores: Record<string, number>
    weighted_scores: Record<string, number>
    total_score: number
    overall_rating: string
    weights_used: Record<string, number>
  }
  summary: {
    total_score: number
    overall_rating: string
    sector: string
  }
}

interface FundamentalScorecardSectionProps {
  data?: FundamentalScorecardData
  isLoading?: boolean
}

export default function FundamentalScorecardSection({
  data,
  isLoading = false
}: FundamentalScorecardSectionProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'components' | 'weights'>('overview')

  if (isLoading) {
    return (
      <div className="p-6 bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700 min-h-96 flex items-center justify-center">
        <div className="animate-pulse text-slate-400">Loading fundamental scorecard...</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="p-6 bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700">
        <div className="text-slate-400">No scorecard data available</div>
      </div>
    )
  }

  const score = data.summary.total_score || 0
  const rating = data.summary.overall_rating || 'Unknown'
  const sector = data.summary.sector || 'Unknown'

  const ratingColor = {
    'Exceptional': 'text-green-400 bg-green-950',
    'Strong': 'text-emerald-400 bg-emerald-950',
    'Good': 'text-blue-400 bg-blue-950',
    'Fair': 'text-yellow-400 bg-yellow-950',
    'Weak': 'text-red-400 bg-red-950'
  }[rating] || 'text-slate-400 bg-slate-800'

  const scoreColor = score >= 8 ? 'text-green-400' : score >= 7 ? 'text-emerald-400' : score >= 6 ? 'text-blue-400' : score >= 5 ? 'text-yellow-400' : 'text-red-400'

  const getComponentColor = (componentScore: number) => {
    if (componentScore >= 8) return 'bg-green-950/30 border-green-600/30'
    if (componentScore >= 7) return 'bg-emerald-950/30 border-emerald-600/30'
    if (componentScore >= 6) return 'bg-blue-950/30 border-blue-600/30'
    if (componentScore >= 5) return 'bg-yellow-950/30 border-yellow-600/30'
    return 'bg-red-950/30 border-red-600/30'
  }

  const getComponentTextColor = (componentScore: number) => {
    if (componentScore >= 8) return 'text-green-400'
    if (componentScore >= 7) return 'text-emerald-400'
    if (componentScore >= 6) return 'text-blue-400'
    if (componentScore >= 5) return 'text-yellow-400'
    return 'text-red-400'
  }

  const components = data.fundamental_scorecard.component_scores || {}
  const sortedComponents = Object.entries(components)
    .sort(([, a], [, b]) => (b as number) - (a as number))

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg border border-slate-700 p-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white">Fundamental Scorecard</h3>
          <div className="text-sm text-slate-400">Sector: {sector}</div>
        </div>

        <div className="flex items-center gap-8">
          <div>
            <div className="text-6xl font-bold mb-2">
              <span className={scoreColor}>{score.toFixed(1)}</span>
              <span className="text-2xl text-slate-400">/10</span>
            </div>
            <div className={`text-2xl font-bold ${ratingColor} rounded-full px-4 py-2 inline-block`}>
              {rating}
            </div>
          </div>

          <div className="flex-1">
            <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  score >= 8 ? 'bg-green-500' :
                  score >= 7 ? 'bg-emerald-500' :
                  score >= 6 ? 'bg-blue-500' :
                  score >= 5 ? 'bg-yellow-500' :
                  'bg-red-500'
                }`}
                style={{ width: `${Math.min(score / 10 * 100, 100)}%` }}
              />
            </div>
            <div className="text-xs text-slate-400 mt-2">
              {score >= 8 && 'Exceptional quality company'}
              {score >= 7 && score < 8 && 'Strong fundamental quality'}
              {score >= 6 && score < 7 && 'Good quality company'}
              {score >= 5 && score < 6 && 'Fair fundamental quality'}
              {score < 5 && 'Weak fundamental quality'}
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-slate-700">
        {(['overview', 'components', 'weights'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-3 font-medium text-sm transition-colors ${
              activeTab === tab
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            {tab === 'overview' && 'Quality Assessment'}
            {tab === 'components' && 'Component Scores'}
            {tab === 'weights' && 'Weighting Model'}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg border border-slate-700 p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <p className="text-slate-300">
              Comprehensive fundamental scorecard combining 12 quality dimensions weighted by sector-specific importance.
            </p>

            <div className={`rounded-lg p-4 border ${ratingColor.split(' ')[1]}`}>
              <div className="flex gap-3">
                {score >= 7 && <TrendingUp className={`w-5 h-5 flex-shrink-0 mt-1 ${scoreColor}`} />}
                {score < 7 && <BarChart3 className={`w-5 h-5 flex-shrink-0 mt-1 ${scoreColor}`} />}
                <div>
                  <h4 className={`font-semibold mb-1 ${scoreColor}`}>{rating} Quality Profile</h4>
                  <p className="text-slate-300 text-sm">
                    {score >= 8 && 'Exceptional company with strong performance across all quality metrics. Minimal fundamental concerns.'}
                    {score >= 7 && score < 8 && 'Strong fundamentals with consistent performance. Good quality characteristics across multiple dimensions.'}
                    {score >= 6 && score < 7 && 'Solid company with good quality metrics. Mixed performance in some areas.'}
                    {score >= 5 && score < 6 && 'Fair quality company with moderate fundamentals. Several areas for improvement.'}
                    {score < 5 && 'Weak fundamentals requiring careful analysis. Notable concerns across quality metrics.'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'components' && (
          <div className="space-y-4">
            <p className="text-slate-300 mb-6">Individual component scores (0-10 scale). Higher is better.</p>
            <div className="space-y-3">
              {sortedComponents.map(([component, score]) => (
                <div
                  key={component}
                  className={`rounded-lg p-4 border ${getComponentColor(score as number)}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="text-slate-300 font-medium capitalize">{component.replace(/_/g, ' ')}</h5>
                    <span className={`text-lg font-bold ${getComponentTextColor(score as number)}`}>
                      {(score as number).toFixed(1)}/10
                    </span>
                  </div>
                  <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        (score as number) >= 8 ? 'bg-green-500' :
                        (score as number) >= 7 ? 'bg-emerald-500' :
                        (score as number) >= 6 ? 'bg-blue-500' :
                        (score as number) >= 5 ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${((score as number) / 10) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'weights' && (
          <div className="space-y-4">
            <p className="text-slate-300 mb-6">
              Sector-adjusted weighting model for {sector}. Weights represent importance in quality assessment.
            </p>
            <div className="space-y-3">
              {Object.entries(data.fundamental_scorecard.weights_used || {})
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .map(([component, weight]) => {
                  const weightPct = ((weight as number) * 100).toFixed(1)
                  return (
                    <div key={component} className="bg-slate-700/30 rounded p-4 border border-slate-600/50">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="text-slate-300 font-medium capitalize">{component.replace(/_/g, ' ')}</h5>
                        <span className="text-slate-300 font-semibold">{weightPct}%</span>
                      </div>
                      <div className="h-2 bg-slate-600 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500"
                          style={{ width: `${parseFloat(weightPct)}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
            </div>

            <div className="bg-blue-950/30 border border-blue-600/30 rounded p-4 mt-6">
              <p className="text-blue-400 text-sm font-semibold mb-2">Weighting Methodology</p>
              <p className="text-slate-300 text-sm">
                Weights are sector-specific and reflect the relative importance of each quality dimension. For {sector} sector, valuation receives {((data.fundamental_scorecard.weights_used.valuation || 0) * 100).toFixed(1)}% weight, emphasizing the importance of attractive entry prices.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
