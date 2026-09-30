'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, AlertCircle, CheckCircle } from 'lucide-react'

interface TechnicalSignal {
  symbol: string
  name: string
  sector: string
  price: number
  change_pct: number
  price_vs_20dma: number
  price_vs_50dma: number
  price_vs_200dma: number
  rsi?: number
  volume_vs_avg: number
  above_200dma: boolean
  price_near_52week_high: boolean
  price_near_52week_low: boolean
  volume_spike: boolean
  technical_score: number
}

export default function TechnicalScreenerView() {
  const [data, setData] = useState<{ signals: TechnicalSignal[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [minScore, setMinScore] = useState(60)
  const [above200dma, setAbove200dma] = useState(true)
  const [rsiOversold, setRsiOversold] = useState(false)
  const [volumeSpike, setVolumeSpike] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const params = new URLSearchParams({
          min_score: minScore.toString(),
          above_200dma: above200dma.toString(),
          rsi_oversold: rsiOversold.toString(),
          volume_spike: volumeSpike.toString(),
        })
        const response = await fetch(
          `http://localhost:5000/screeners/technical/filter?${params}`
        )
        const result = await response.json()
        setData(result)
      } catch (error) {
        console.error('Failed to load technical screener:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [minScore, above200dma, rsiOversold, volumeSpike])

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-surface p-8">
        <div className="flex items-center justify-center gap-2 text-sm text-muted">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-accent border-r-transparent"></div>
          Loading technical signals...
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border border-border bg-surface p-5">
        <h3 className="text-lg font-bold">Technical Screener</h3>
        <p className="mt-1 text-xs text-muted">
          Price action, momentum, and volume analysis
        </p>
      </div>

      {/* Filters */}
      <div className="rounded-lg border border-border bg-surface p-5 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label className="text-xs font-semibold">Min Score</label>
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

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={above200dma}
            onChange={(e) => setAbove200dma(e.target.checked)}
            className="h-4 w-4"
          />
          <span className="text-xs font-semibold">Above 200 DMA</span>
        </label>

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={rsiOversold}
            onChange={(e) => setRsiOversold(e.target.checked)}
            className="h-4 w-4"
          />
          <span className="text-xs font-semibold">RSI &lt; 30</span>
        </label>

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={volumeSpike}
            onChange={(e) => setVolumeSpike(e.target.checked)}
            className="h-4 w-4"
          />
          <span className="text-xs font-semibold">Vol Spike</span>
        </label>
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
                <th className="px-4 py-3 text-left font-medium">Price</th>
                <th className="px-4 py-3 text-center font-medium">Change</th>
                <th className="px-4 py-3 text-center font-medium">vs 200 DMA</th>
                <th className="px-4 py-3 text-center font-medium">RSI</th>
                <th className="px-4 py-3 text-center font-medium">Vol</th>
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
                  <td className="px-4 py-3 font-mono text-xs">
                    {signal.price.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`text-xs font-semibold ${
                        signal.change_pct >= 0 ? 'text-positive' : 'text-negative'
                      }`}
                    >
                      {signal.change_pct >= 0 ? '+' : ''}
                      {signal.change_pct.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`text-xs font-semibold ${
                        signal.price_vs_200dma > 0 ? 'text-positive' : 'text-negative'
                      }`}
                    >
                      {signal.price_vs_200dma > 0 ? '+' : ''}
                      {signal.price_vs_200dma.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center text-xs">
                    {signal.rsi ? signal.rsi.toFixed(1) : '—'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {signal.volume_spike ? (
                      <span className="text-xs font-semibold text-positive">Spike</span>
                    ) : (
                      <span className="text-xs text-muted">Normal</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-flex items-center justify-center h-6 w-6 rounded-full text-xs font-bold ${
                        signal.technical_score >= 75
                          ? 'bg-positive/20 text-positive'
                          : signal.technical_score >= 60
                          ? 'bg-accent/20 text-accent'
                          : 'bg-muted/20 text-muted'
                      }`}
                    >
                      {signal.technical_score.toFixed(0)}
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
