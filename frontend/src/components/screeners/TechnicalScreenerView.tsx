'use client'

import { API_BASE_URL } from "@/lib/config";
import { useEffect, useState } from 'react'


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

const MISSING = 'Not enough price history to compute'

function Pct({ value }: { value: number | null }) {
  if (value == null) return <span className="text-muted" title={MISSING}>—</span>
  return (
    <span className={`font-semibold ${value >= 0 ? 'text-positive' : 'text-negative'}`}>
      {value > 0 ? '+' : ''}
      {value.toFixed(1)}%
    </span>
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
    fetch(`${API_BASE_URL}/screeners/technical/filter?${params}`)
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

      {error && <p className="text-sm text-negative">{error}</p>}

      <div className="overflow-x-auto rounded-lg border border-border bg-surface">
        {!data?.signals.length ? (
          <p className="p-8 text-center text-sm text-muted">{data ? 'No stocks match these filters.' : 'Loading…'}</p>
        ) : (
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="border-b border-border text-xs text-muted">
                <th className="px-4 py-3 text-left font-medium">Symbol</th>
                <th className="px-4 py-3 text-right font-medium">Close</th>
                <th className="px-4 py-3 text-right font-medium">Day</th>
                <th className="px-4 py-3 text-right font-medium">vs 20d</th>
                <th className="px-4 py-3 text-right font-medium">vs 50d</th>
                <th className="px-4 py-3 text-right font-medium">vs 200d</th>
                <th className="px-4 py-3 text-right font-medium">RSI 14</th>
                <th className="px-4 py-3 text-right font-medium">Vol ×</th>
                <th className="px-4 py-3 text-left font-medium">Range</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data.signals.map((s) => (
                <tr key={s.symbol}>
                  <td className="px-4 py-3">
                    <p className="font-semibold text-accent">{s.symbol}</p>
                    <p className="text-xs text-muted">{s.name}</p>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs">{s.price.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right text-xs"><Pct value={s.change_pct} /></td>
                  <td className="px-4 py-3 text-right text-xs"><Pct value={s.price_vs_20dma} /></td>
                  <td className="px-4 py-3 text-right text-xs"><Pct value={s.price_vs_50dma} /></td>
                  <td className="px-4 py-3 text-right text-xs"><Pct value={s.price_vs_200dma} /></td>
                  <td className="px-4 py-3 text-right text-xs">{s.rsi == null ? <span title={MISSING}>—</span> : s.rsi.toFixed(1)}</td>
                  <td className="px-4 py-3 text-right text-xs">
                    {s.volume_vs_avg == null ? <span title={MISSING}>—</span> : `${s.volume_vs_avg.toFixed(2)}×`}
                  </td>
                  <td className="px-4 py-3 text-xs">
                    {s.near_lookback_high ? 'Near high' : s.near_lookback_low ? 'Near low' : 'Mid'}
                    <span className="text-muted"> ({s.lookback_complete ? '52 wk' : `${s.lookback_days} d only`})</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {data && (
        <p className="text-xs text-muted">
          {data.signals.length} of {data.total_screened} active securities shown. Near high/low means within 5% of the
          range extreme.
        </p>
      )}
    </div>
  )
}
