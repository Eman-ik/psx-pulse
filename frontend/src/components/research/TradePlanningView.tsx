'use client'

import { API_BASE_URL } from "@/lib/config"
import { useState } from "react"

interface TradePlan {
  ticker: string
  entry_price: number
  stop_loss: number
  take_profit_1: number
  take_profit_2?: number
  portfolio_value: number
  risk_percent: number
}

interface TradeResult {
  ticker: string
  entry_price: number
  stop_loss: number
  take_profits: number[]
  position_shares: number
  risk_amount: number
  max_loss: number
  reward_potential: number[]
  risk_reward_ratio: number
  position_size_pct: number
  is_valid: boolean
  warnings: string[]
  confidence: string
}

export default function TradePlanningView({ ticker }: { ticker: string }) {
  const [entry, setEntry] = useState(500)
  const [stop, setStop] = useState(450)
  const [tp1, setTp1] = useState(550)
  const [tp2, setTp2] = useState(600)
  const [portfolio, setPortfolio] = useState(100000)
  const [riskPct, setRiskPct] = useState(1)
  const [result, setResult] = useState<TradeResult | null>(null)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleCalculate = async () => {
    setLoading(true)
    setError("")
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research/trade/planning`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker,
          entry_price: entry,
          stop_loss: stop,
          take_profit_1: tp1,
          take_profit_2: tp2 || null,
          portfolio_value: portfolio,
          risk_percent: riskPct,
        }),
      })
      if (!response.ok) throw new Error(`${response.status}`)
      setResult(await response.json())
    } catch (e) {
      setError(`Could not calculate: ${e instanceof Error ? e.message : "unknown error"}`)
    } finally {
      setLoading(false)
    }
  }

  const confidenceColor = result
    ? result.confidence === "High"
      ? "text-positive"
      : result.confidence === "Medium"
      ? "text-warning"
      : "text-negative"
    : ""

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-surface p-5">
        <h3 className="text-lg font-bold">Trade Planning & Position Sizing</h3>
        <p className="mt-1 text-xs text-muted">
          Calculate position size based on risk management rules. Validates entry, stop, targets against portfolio limits.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 rounded-lg border border-border bg-surface p-5">
        <div>
          <label className="block text-xs font-semibold text-muted">Entry Price (PKR)</label>
          <input
            type="number"
            value={entry}
            onChange={(e) => setEntry(Number(e.target.value))}
            className="mt-1 w-full rounded border border-border bg-input px-3 py-2 text-sm"
            step="0.01"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-muted">Stop Loss (PKR)</label>
          <input
            type="number"
            value={stop}
            onChange={(e) => setStop(Number(e.target.value))}
            className="mt-1 w-full rounded border border-border bg-input px-3 py-2 text-sm"
            step="0.01"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-muted">Take Profit 1 (PKR)</label>
          <input
            type="number"
            value={tp1}
            onChange={(e) => setTp1(Number(e.target.value))}
            className="mt-1 w-full rounded border border-border bg-input px-3 py-2 text-sm"
            step="0.01"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-muted">Take Profit 2 (PKR)</label>
          <input
            type="number"
            value={tp2}
            onChange={(e) => setTp2(Number(e.target.value))}
            className="mt-1 w-full rounded border border-border bg-input px-3 py-2 text-sm"
            step="0.01"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-muted">Portfolio Value (PKR)</label>
          <input
            type="number"
            value={portfolio}
            onChange={(e) => setPortfolio(Number(e.target.value))}
            className="mt-1 w-full rounded border border-border bg-input px-3 py-2 text-sm"
            step="1000"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-muted">Risk per Trade (%)</label>
          <input
            type="number"
            value={riskPct}
            onChange={(e) => setRiskPct(Number(e.target.value))}
            className="mt-1 w-full rounded border border-border bg-input px-3 py-2 text-sm"
            min="0.1"
            max="5"
            step="0.1"
          />
        </div>
      </div>

      <button
        onClick={handleCalculate}
        disabled={loading}
        className="w-full rounded-lg bg-accent px-4 py-2 font-semibold text-white hover:bg-accent/90 disabled:opacity-50"
      >
        {loading ? "Calculating..." : "Calculate Position Size"}
      </button>

      {error && <p className="text-sm text-negative">{error}</p>}

      {result && (
        <div className="space-y-4">
          <div className="rounded-lg border border-border bg-surface p-5">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold">Trade Confirmation</h4>
              <span className={`font-bold ${confidenceColor}`}>{result.confidence}</span>
            </div>

            <div className="mt-4 grid grid-cols-3 gap-4">
              <div>
                <p className="text-xs text-muted">Position Size</p>
                <p className="text-lg font-bold">{result.position_shares.toLocaleString()} shares</p>
                <p className="text-xs text-muted">{result.position_size_pct.toFixed(1)}% of portfolio</p>
              </div>
              <div>
                <p className="text-xs text-muted">Risk / Reward</p>
                <p className="text-lg font-bold">{result.risk_reward_ratio.toFixed(2)}:1</p>
                <p className="text-xs text-muted">
                  Max loss PKR {result.max_loss.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted">Potential Rewards</p>
                <div className="text-sm">
                  {result.reward_potential.map((r, i) => (
                    <p key={i} className="font-semibold">
                      TP{i + 1}: PKR {r.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </p>
                  ))}
                </div>
              </div>
            </div>

            {result.warnings.length > 0 && (
              <div className="mt-4 rounded bg-warning/10 p-3">
                <p className="text-xs font-semibold text-warning">⚠ Warnings:</p>
                <ul className="mt-1 space-y-1 text-xs text-warning">
                  {result.warnings.map((w, i) => (
                    <li key={i}>• {w}</li>
                  ))}
                </ul>
              </div>
            )}

            {!result.is_valid && (
              <div className="mt-4 rounded bg-negative/10 p-3">
                <p className="text-xs font-semibold text-negative">❌ Trade is not valid. Check warnings above.</p>
              </div>
            )}
          </div>

          <div className="rounded-lg border border-border bg-surface p-5 text-sm">
            <h5 className="font-semibold">Trade Details</h5>
            <table className="mt-3 w-full text-xs">
              <tbody className="divide-y divide-border">
                <tr className="hover:bg-input/30">
                  <td className="py-2 text-muted">Entry</td>
                  <td className="text-right font-mono">PKR {result.entry_price.toFixed(2)}</td>
                </tr>
                <tr className="hover:bg-input/30">
                  <td className="py-2 text-muted">Stop Loss</td>
                  <td className="text-right font-mono">PKR {result.stop_loss.toFixed(2)}</td>
                </tr>
                {result.take_profits.map((tp, i) => (
                  <tr key={i} className="hover:bg-input/30">
                    <td className="py-2 text-muted">Take Profit {i + 1}</td>
                    <td className="text-right font-mono">PKR {tp.toFixed(2)}</td>
                  </tr>
                ))}
                <tr className="hover:bg-input/30">
                  <td className="py-2 text-muted">Risk Amount</td>
                  <td className="text-right font-mono">
                    PKR {result.risk_amount.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
