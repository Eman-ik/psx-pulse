'use client'

import { API_BASE_URL } from "@/lib/config";
import { useEffect, useState } from 'react'
import { ChevronRight, TrendingUp, AlertCircle, Zap } from 'lucide-react'
import Link from 'next/link'

interface TechnicalSignal {
  symbol: string
  name: string
  price: number
  change_pct: number | null
  price_vs_20dma: number | null
  price_vs_50dma: number | null
  price_vs_200dma: number | null
  rsi: number | null
  volume_vs_avg: number | null
  lookback_days: number
  lookback_complete: boolean
  near_lookback_high: boolean
  near_lookback_low: boolean
}

interface Payload {
  freshness: { as_of: string | null; sources: string[]; stale: boolean }
  total_screened: number
  signals: TechnicalSignal[]
}

interface CategorizationResult {
  momentum_leaders: TechnicalSignal[]
  oversold_watch: TechnicalSignal[]
  breakout_watch: TechnicalSignal[]
}

const MISSING = 'Not enough price history to compute'

function categorizeSignals(signals: TechnicalSignal[]): CategorizationResult {
  const momentum_leaders: TechnicalSignal[] = []
  const oversold_watch: TechnicalSignal[] = []
  const breakout_watch: TechnicalSignal[] = []

  signals.forEach((s) => {
    const has200dma = s.price_vs_200dma != null && s.price_vs_200dma > 0
    const hasHighRsi = s.rsi != null && s.rsi > 60
    const hasVolumeSpike = s.volume_vs_avg != null && s.volume_vs_avg > 1.5
    const hasOversoldRsi = s.rsi != null && s.rsi < 30
    const isNearHigh = s.near_lookback_high

    // Categorize: prioritize momentum leaders, then oversold, then breakout
    if ((has200dma || hasHighRsi) && hasVolumeSpike && !hasOversoldRsi) {
      momentum_leaders.push(s)
    } else if (hasOversoldRsi || (s.price_vs_200dma != null && s.price_vs_200dma < -10)) {
      oversold_watch.push(s)
    } else if (isNearHigh && hasVolumeSpike) {
      breakout_watch.push(s)
    }
  })

  return {
    momentum_leaders: momentum_leaders.sort((a, b) => (b.rsi || 0) - (a.rsi || 0)).slice(0, 4),
    oversold_watch: oversold_watch.sort((a, b) => (a.rsi || 100) - (b.rsi || 100)).slice(0, 4),
    breakout_watch: breakout_watch.sort((a, b) => (b.volume_vs_avg || 0) - (a.volume_vs_avg || 0)).slice(0, 4),
  }
}

function Pct({ value }: { value: number | null }) {
  if (value == null) return <span className="text-muted" title={MISSING}>—</span>
  return (
    <span className={`font-semibold ${value >= 0 ? 'text-positive' : 'text-negative'}`}>
      {value > 0 ? '+' : ''}
      {value.toFixed(1)}%
    </span>
  )
}

function SignalCard({ signal, category }: { signal: TechnicalSignal; category: 'momentum' | 'oversold' | 'breakout' }) {
  const borderColor = category === 'momentum' ? 'border-positive/30' : category === 'oversold' ? 'border-negative/30' : 'border-accent/30'
  const bgColor = category === 'momentum' ? 'bg-positive/5' : category === 'oversold' ? 'bg-negative/5' : 'bg-accent/5'
  const icon = category === 'momentum' ? <TrendingUp className="h-4 w-4 text-positive" /> : category === 'oversold' ? <AlertCircle className="h-4 w-4 text-negative" /> : <Zap className="h-4 w-4 text-accent" />

  return (
    <Link href={`/research?t=${signal.symbol}`}>
      <div className={`group rounded-lg border ${borderColor} ${bgColor} p-4 transition-all hover:border-foreground/30 cursor-pointer`}>
        <div className="mb-3 flex items-start justify-between gap-2">
          <div>
            <p className="font-semibold text-foreground">{signal.symbol}</p>
            <p className="text-xs text-muted">{signal.name}</p>
          </div>
          <ChevronRight className="h-4 w-4 text-muted opacity-0 transition group-hover:opacity-100" />
        </div>

        <p className="mb-3 text-sm font-bold tabular-nums text-foreground">PKR {signal.price.toFixed(2)}</p>

        <div className="space-y-1.5 text-xs">
          {signal.price_vs_200dma != null && signal.price_vs_200dma > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-positive">🟢</span>
              <span className="text-foreground">Above 200DMA <span className="text-muted">{signal.price_vs_200dma > 0 ? '+' : ''}{signal.price_vs_200dma.toFixed(1)}%</span></span>
            </div>
          )}
          {signal.rsi != null && signal.rsi > 60 && (
            <div className="flex items-center gap-2">
              <span className="text-positive">🟢</span>
              <span className="text-foreground">RSI {signal.rsi.toFixed(0)} (Strong)</span>
            </div>
          )}
          {signal.rsi != null && signal.rsi < 30 && (
            <div className="flex items-center gap-2">
              <span className="text-negative">🔴</span>
              <span className="text-foreground">RSI {signal.rsi.toFixed(0)} (Oversold)</span>
            </div>
          )}
          {signal.volume_vs_avg != null && signal.volume_vs_avg > 1.5 && (
            <div className="flex items-center gap-2">
              <span className="text-positive">🟢</span>
              <span className="text-foreground">Volume {signal.volume_vs_avg.toFixed(1)}× avg</span>
            </div>
          )}
          {signal.near_lookback_high && (
            <div className="flex items-center gap-2">
              <span className="text-accent">🟡</span>
              <span className="text-foreground">Near 52-week high</span>
            </div>
          )}
          {signal.near_lookback_low && (
            <div className="flex items-center gap-2">
              <span className="text-accent">🟡</span>
              <span className="text-foreground">Near 52-week low</span>
            </div>
          )}
        </div>

        <p className={`mt-3 text-xs ${signal.change_pct != null && signal.change_pct >= 0 ? 'text-positive' : 'text-negative'}`}>
          {signal.change_pct != null ? `${signal.change_pct > 0 ? '+' : ''}${signal.change_pct.toFixed(2)}%` : '—'} on the day
        </p>
      </div>
    </Link>
  )
}

export default function TechnicalScreenerView() {
  const [data, setData] = useState<Payload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [above200dma, setAbove200dma] = useState(false)
  const [rsiOversold, setRsiOversold] = useState(false)
  const [volumeSpike, setVolumeSpike] = useState(false)

  useEffect(() => {
    const params = new URLSearchParams({
      above_200dma: String(above200dma),
      rsi_oversold: String(rsiOversold),
      volume_spike: String(volumeSpike),
    })
    fetch(`${API_BASE_URL}/api/v1/research/screeners/technical/filter?${params}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => {
        setData(d)
        setError(null)
      })
      .catch(() => setError(`Could not reach the API at ${API_BASE_URL}.`))
  }, [above200dma, rsiOversold, volumeSpike])

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-surface p-5">
        <h3 className="text-lg font-bold">Technical Screener</h3>
        <p className="mt-1 text-xs text-muted">
          Indicators from end-of-day closes{data?.freshness.as_of ? ` as of ${data.freshness.as_of}` : ''}. Each is shown
          on its own; there is no combined score, because no blend of these has been tested against returns.
        </p>
        {data?.freshness.stale && <p className="mt-2 text-xs text-negative">Prices are stale.</p>}
      </div>

      <fieldset className="flex flex-wrap gap-6 rounded-lg border border-border bg-surface p-5 text-xs font-semibold">
        <legend className="sr-only">Filters</legend>
        {[
          ['Above 200-day average', above200dma, setAbove200dma],
          ['RSI below 30', rsiOversold, setRsiOversold],
          ['Volume over 2× prior 20-day average', volumeSpike, setVolumeSpike],
        ].map(([label, checked, set]) => (
          <label key={label as string} className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={checked as boolean}
              onChange={(e) => (set as (v: boolean) => void)(e.target.checked)}
              className="h-4 w-4"
            />
            {label as string}
          </label>
        ))}
        <span className="font-normal text-muted">Stocks without enough history for a filter are excluded by it.</span>
      </fieldset>

      {error && (
        <div className="rounded-lg border border-negative/30 bg-negative/5 p-4">
          <p className="text-sm text-negative">{error}</p>
        </div>
      )}

      {!data?.signals.length ? (
        <div className="rounded-lg border border-border bg-surface p-8 text-center">
          <p className="text-sm text-muted">{data ? 'No stocks match these filters.' : 'Loading…'}</p>
        </div>
      ) : (
        <>
          {(() => {
            const categorized = categorizeSignals(data.signals)
            return (
              <div className="space-y-8">
                {/* Momentum Leaders */}
                {categorized.momentum_leaders.length > 0 && (
                  <div>
                    <div className="mb-4 flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-positive" />
                      <h3 className="text-lg font-semibold text-foreground">Momentum Leaders</h3>
                      <span className="text-xs text-muted">({categorized.momentum_leaders.length})</span>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                      {categorized.momentum_leaders.map((s) => (
                        <SignalCard key={s.symbol} signal={s} category="momentum" />
                      ))}
                    </div>
                  </div>
                )}

                {/* Oversold Watch */}
                {categorized.oversold_watch.length > 0 && (
                  <div>
                    <div className="mb-4 flex items-center gap-2">
                      <AlertCircle className="h-5 w-5 text-negative" />
                      <h3 className="text-lg font-semibold text-foreground">Oversold Watch</h3>
                      <span className="text-xs text-muted">({categorized.oversold_watch.length})</span>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                      {categorized.oversold_watch.map((s) => (
                        <SignalCard key={s.symbol} signal={s} category="oversold" />
                      ))}
                    </div>
                    <p className="mt-2 text-xs text-muted">Potential reversal candidates — not a recommendation.</p>
                  </div>
                )}

                {/* Breakout Watch */}
                {categorized.breakout_watch.length > 0 && (
                  <div>
                    <div className="mb-4 flex items-center gap-2">
                      <Zap className="h-5 w-5 text-accent" />
                      <h3 className="text-lg font-semibold text-foreground">Breakout Watch</h3>
                      <span className="text-xs text-muted">({categorized.breakout_watch.length})</span>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                      {categorized.breakout_watch.map((s) => (
                        <SignalCard key={s.symbol} signal={s} category="breakout" />
                      ))}
                    </div>
                  </div>
                )}

                {/* Disclaimer */}
                <div className="rounded-lg border border-border/50 bg-surface/30 p-4">
                  <p className="text-xs text-muted">
                    These signals are technical indicators only and do not constitute investment recommendations.
                    Click any stock to view full research and analysis. All prices as of {data.freshness.as_of ? new Date(data.freshness.as_of).toLocaleDateString() : 'unknown date'}.
                  </p>
                </div>
              </div>
            )
          })()}

          <p className="text-xs text-muted">
            Analyzed {data.total_screened} active securities. Stocks are categorized by dominant signal; stocks matching multiple categories appear in their strongest category.
          </p>
        </>
      )}
    </div>
  )
}
