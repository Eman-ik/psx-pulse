"use client";

import { useState } from "react";
import { CirclePlay, Loader2, ShieldAlert, ShieldCheck } from "lucide-react";
import type { QuantForecast } from "@/lib/api";
import { fetchQuantForecast } from "@/lib/api";

const SIGNAL_META: Record<string, { label: string; color: string; bg: string; border: string }> = {
  BUY:       { label: "Buy",       color: "#22c55e", bg: "rgba(34,197,94,0.08)",   border: "rgba(34,197,94,0.25)" },
  SELL:      { label: "Sell",      color: "#ef4444", bg: "rgba(239,68,68,0.08)",   border: "rgba(239,68,68,0.25)" },
  HOLD:      { label: "Hold",      color: "#f59e0b", bg: "rgba(245,158,11,0.08)",  border: "rgba(245,158,11,0.25)" },
  NO_SIGNAL: { label: "No Signal", color: "#6b7280", bg: "rgba(107,114,128,0.06)", border: "rgba(107,114,128,0.20)" },
};

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl bg-surface-alt p-4">
      <p className="mb-1 text-xs text-muted">{label}</p>
      <p className="text-lg font-bold tabular-nums">{value}</p>
      {sub && <p className="mt-1 text-[10px] text-muted">{sub}</p>}
    </div>
  );
}

export default function QuantForecastTab({ ticker }: { ticker: string | null }) {
  const [loading, setLoading] = useState(false);
  const [forecast, setForecast] = useState<QuantForecast | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    const result = await fetchQuantForecast(ticker);
    if (!result) {
      setError("Could not reach the forecast backend.");
    } else if (!result.ok) {
      setError(result.reason ?? "Forecast unavailable for this ticker.");
    } else {
      setForecast(result);
    }
    setLoading(false);
  };

  if (!ticker) {
    return (
      <div className="rounded-2xl border border-border bg-surface p-5">
        <p className="text-sm text-muted">No ticker on file for this company — quant forecast unavailable.</p>
      </div>
    );
  }

  const qual = forecast?.signal_qualification;
  const meta = SIGNAL_META[qual?.signal ?? "NO_SIGNAL"];

  return (
    <div className="flex flex-col gap-5">
      <div className="rounded-2xl border border-border bg-surface p-5">
        <p className="mb-1 text-[11px] font-semibold uppercase tracking-widest text-muted/70">
          Kronos Quant Forecast
        </p>
        <p className="mb-4 text-xs text-muted">
          A fine-tuned Kronos foundation-model ensemble (15 independent real stochastic
          forecasts), gated by a real walk-forward Signal Qualification check — a raw
          bullish/bearish reading is never presented as a BUY/SELL call unless this
          ticker&apos;s historical track record actually clears a statistical significance
          bar. Runs on demand (a real ~5-30s inference), not pre-cached.
        </p>

        {!forecast && !loading && (
          <button
            onClick={run}
            className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-accent/80"
          >
            <CirclePlay className="h-4 w-4" /> Run Forecast for {ticker}
          </button>
        )}

        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted">
            <Loader2 className="h-4 w-4 animate-spin" /> Running real Kronos ensemble (15 samples)…
          </div>
        )}

        {error && !loading && (
          <div className="flex items-start gap-2 rounded-lg border border-negative/20 bg-negative/5 p-3 text-sm text-negative">
            <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {forecast?.ok && qual && (
          <>
            <div
              className="mb-4 flex items-start gap-3 rounded-xl border p-4"
              style={{ backgroundColor: meta.bg, borderColor: meta.border }}
            >
              {qual.qualified ? (
                <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0" style={{ color: meta.color }} />
              ) : (
                <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-muted" />
              )}
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-widest text-muted/70">
                  {qual.qualified ? "Qualified Signal" : "Not a Validated Signal"}
                </p>
                <p className="text-2xl font-bold" style={{ color: qual.qualified ? meta.color : "#6b7280" }}>
                  {meta.label}
                </p>
                <p className="mt-1 text-xs text-muted">{qual.reason}</p>
              </div>
            </div>

            <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Stat
                label="P(positive return)"
                value={forecast.p_positive_return != null ? `${(forecast.p_positive_return * 100).toFixed(0)}%` : "—"}
              />
              <Stat
                label={`Expected ${forecast.horizon_days}D return`}
                value={forecast.expected_return_pct != null ? `${forecast.expected_return_pct > 0 ? "+" : ""}${forecast.expected_return_pct.toFixed(2)}%` : "—"}
              />
              <Stat
                label="Downside VaR (5th pct)"
                value={forecast.downside_var_pct != null ? `${forecast.downside_var_pct.toFixed(2)}%` : "—"}
              />
              <Stat
                label="Expected volatility"
                value={forecast.expected_volatility_pct != null ? `${forecast.expected_volatility_pct.toFixed(2)}%` : "—"}
              />
            </div>

            {qual.track_record && (
              <div className="rounded-xl bg-surface-alt p-4">
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-muted/70">
                  Real Walk-Forward Track Record
                </p>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
                  <div>
                    <p className="text-muted">Observations</p>
                    <p className="font-semibold tabular-nums">{qual.track_record.n_observations}</p>
                  </div>
                  <div>
                    <p className="text-muted">Accuracy</p>
                    <p className="font-semibold tabular-nums">{(qual.track_record.accuracy * 100).toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-muted">p-value vs. random</p>
                    <p className="font-semibold tabular-nums">{qual.track_record.p_value_vs_random.toFixed(3)}</p>
                  </div>
                  <div>
                    <p className="text-muted">Significant @ 10%</p>
                    <p className="font-semibold">{qual.track_record.significant_at_10pct ? "Yes" : "No"}</p>
                  </div>
                </div>
              </div>
            )}

            <p className="mt-4 text-[11px] text-muted">
              As of real close {forecast.as_of_date} (PKR {forecast.last_real_close}) ·
              Model: {forecast.model_source} · {forecast.n_samples} independent samples
            </p>

            <button
              onClick={run}
              className="mt-4 flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 text-xs text-muted transition-colors hover:text-foreground"
            >
              <CirclePlay className="h-3.5 w-3.5" /> Re-run
            </button>
          </>
        )}
      </div>
    </div>
  );
}
