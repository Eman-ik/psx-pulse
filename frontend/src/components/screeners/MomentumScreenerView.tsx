'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface MomentumSignal {
  symbol: string
  name: string
  sector: string
  price: number
  return_1m?: number
  return_3m?: number
  return_6m?: number
  return_12m?: number
  momentum_score: number
  strongest_period: string
  trend: string
}

export default function MomentumScreenerView() {
  const [data, setData] = useState<{ signals: MomentumSignal[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [minScore, setMinScore] = useState(60)
  const [min1mReturn, setMin1mReturn] = useState(0)
  const [selectedTrend, setSelectedTrend] = useState<string | null>(null)

  const trends = [
    'Strong Uptrend',
    'Uptrend',
    'Neutral',
    'Downtrend',
    'Strong Downtrend',
  ]

  useEffect(() => {
    const fetchData = async () => {
      try {
        const params = new URLSearchParams({
          min_score: minScore.toString(),
          min_1m_return: min1mReturn.toString(),
        })
        if (selectedTrend) {
          params.append('trend', selectedTrend)
        }
        const response = await fetch(
          `http://localhost:5000/screeners/momentum/filter?${params}`
        )
        const result = await response.json()
        setData(result)
      } catch (error) {
        console.error('Failed to load momentum screener:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [minScore, min1mReturn, selectedTrend])

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-surface p-8">
        <div className="flex items-center justify-center gap-2 text-sm text-muted">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-accent border-r-transparent"></div>
          Loading momentum signals...
        </div>
      </div>
    )
  }

  const getTrendColor = (trend: string) => {
    if (trend === 'Strong Uptrend') return 'text-positive'
    if (trend === 'Uptrend') return 'text-positive opacity-70'
    if (trend === 'Neutral') return 'text-muted'
    if (trend === 'Downtrend') return 'text-negative opacity-70'
    if (trend === 'Strong Downtrend') return 'text-negative'
    return 'text-muted'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border border-border bg-surface p-5">
        <h3 className="text-lg font-bold">Momentum Screener</h3>
        <p className="mt-1 text-xs text-muted">
          Multi-period return analysis (1M, 3M, 6M, 12M)
        </p>
      </div>

      {/* Filters */}
      <div className="rounded-lg border border-border bg-surface p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-semibold">Min Momentum Score</label>
            <input
              type="range"
              min="0"
              max="100"
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-full mt-2"
            />
            <p className="text-xs text-muted mt-1">{minScore}/100</p>
          </div>

          <div>
            <label className="text-xs font-semibold">Min 1-Month Return</label>
            <input
              type="range"
              min="-50"
              max="50"
              value={min1mReturn}
              onChange={(e) => setMin1mReturn(Number(e.target.value))}
              className="w-full mt-2"
            />
            <p className="text-xs text-muted mt-1">{min1mReturn}%</p>
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold block mb-2">Trend Filter</label>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedTrend(null)}
              className={`px-3 py-1 rounded-md text-xs font-semibold border ${
                selectedTrend === null
                  ? 'border-accent bg-accent/10 text-accent'
                  : 'border-border bg-surface-alt text-muted hover:text-foreground'
              }`}
            >
              All Trends
            </button>
            {trends.map((trend) => (
              <button
                key={trend}
                onClick={() => setSelectedTrend(trend)}
                className={`px-3 py-1 rounded-md text-xs font-semibold border ${
                  selectedTrend === trend
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-border bg-surface-alt text-muted hover:text-foreground'
                }`}
              >
                {trend}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="rounded-lg border border-border bg-surface overflow-hidden">
        {!data?.signals?.length ? (
          <div className="p-8 text-center text-sm text-muted">
            No signals match current filters
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-xs text-muted">
                <th className="px-4 py-3 text-left font-medium">Symbol</th>
                <th className="px-4 py-3 text-center font-medium">1M</th>
                <th className="px-4 py-3 text-center font-medium">3M</th>
                <th className="px-4 py-3 text-center font-medium">6M</th>
                <th className="px-4 py-3 text-center font-medium">12M</th>
                <th className="px-4 py-3 text-center font-medium">Trend</th>
                <th className="px-4 py-3 text-center font-medium">Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data.signals.map((signal) => (
                <tr key={signal.symbol} className="hover:bg-surface-alt/50">
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-semibold text-accent">{signal.symbol}</p>
                      <p className="text-xs text-muted">{signal.name}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {signal.return_1m !== null && signal.return_1m !== undefined ? (
                      <span
                        className={`text-xs font-semibold ${
                          signal.return_1m >= 0 ? 'text-positive' : 'text-negative'
                        }`}
                      >
                        {signal.return_1m >= 0 ? '+' : ''}
                        {signal.return_1m.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-xs text-muted">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {signal.return_3m !== null && signal.return_3m !== undefined ? (
                      <span
                        className={`text-xs font-semibold ${
                          signal.return_3m >= 0 ? 'text-positive' : 'text-negative'
                        }`}
                      >
                        {signal.return_3m >= 0 ? '+' : ''}
                        {signal.return_3m.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-xs text-muted">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {signal.return_6m !== null && signal.return_6m !== undefined ? (
                      <span
                        className={`text-xs font-semibold ${
                          signal.return_6m >= 0 ? 'text-positive' : 'text-negative'
                        }`}
                      >
                        {signal.return_6m >= 0 ? '+' : ''}
                        {signal.return_6m.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-xs text-muted">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {signal.return_12m !== null && signal.return_12m !== undefined ? (
                      <span
                        className={`text-xs font-semibold ${
                          signal.return_12m >= 0 ? 'text-positive' : 'text-negative'
                        }`}
                      >
                        {signal.return_12m >= 0 ? '+' : ''}
                        {signal.return_12m.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-xs text-muted">—</span>
                    )}
                  </td>
                  <td className={`px-4 py-3 text-center text-xs font-semibold ${getTrendColor(signal.trend)}`}>
                    {signal.trend}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-flex items-center justify-center h-6 w-6 rounded-full text-xs font-bold ${
                        signal.momentum_score >= 75
                          ? 'bg-positive/20 text-positive'
                          : signal.momentum_score >= 60
                          ? 'bg-accent/20 text-accent'
                          : 'bg-muted/20 text-muted'
                      }`}
                    >
                      {signal.momentum_score.toFixed(0)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Summary */}
      <div className="text-xs text-muted">
        Showing {data?.signals?.length || 0} signals out of{' '}
        {data && 'results_count' in data ? data.results_count : 'N/A'}
      </div>
    </div>
  )
}
