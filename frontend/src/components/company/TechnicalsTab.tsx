"use client";

import { useEffect, useMemo, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchPrices, type PriceBar } from "@/lib/api";
import { computeTechnicals, type IndicatorResult } from "@/lib/technicals";

function IndicatorCard({ label, unit, result }: { label: string; unit?: string; result: IndicatorResult }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-4">
      <p className="mb-1 text-xs text-muted">{label}</p>
      {result.available ? (
        <p className="text-lg font-semibold">
          {result.latest!.toFixed(2)}
          {unit && <span className="ml-1 text-xs font-normal text-muted">{unit}</span>}
        </p>
      ) : (
        <p className="text-xs text-muted">
          Insufficient history ({result.availableBars}/{result.requiredBars} days)
        </p>
      )}
    </div>
  );
}

export default function TechnicalsTab({
  bars,
  dataDelayNotice,
  securityId,
}: {
  bars: PriceBar[];
  dataDelayNotice: string;
  securityId: number | null;
}) {
  const [adjusted, setAdjusted] = useState(false);
  const [adjustedBars, setAdjustedBars] = useState<PriceBar[] | null>(null);
  const [actionsOnFile, setActionsOnFile] = useState<number | null>(null);
  const [adjustError, setAdjustError] = useState(false);
  const fetchAttempted = adjustedBars !== null || adjustError;
  const loading = adjusted && !fetchAttempted && securityId != null;

  useEffect(() => {
    if (!adjusted || fetchAttempted || securityId == null) return;
    let cancelled = false;
    fetchPrices(securityId, true).then((res) => {
      if (cancelled) return;
      // An empty bars array with no reported actions count means the request failed (e.g. the
      // backend rejected the cross-origin call) rather than that the company genuinely has no
      // corporate actions on file — those are very different facts and must not be conflated.
      if (res.bars.length === 0 && res.corporate_actions_on_file === undefined) {
        setAdjustError(true);
        return;
      }
      setAdjustedBars(res.bars);
      setActionsOnFile(res.corporate_actions_on_file ?? 0);
    });
    return () => {
      cancelled = true;
    };
  }, [adjusted, fetchAttempted, securityId]);

  const activeBars = adjusted && adjustedBars ? adjustedBars : bars;
  const technicals = useMemo(() => computeTechnicals(activeBars), [activeBars]);

  if (bars.length === 0) {
    return <p className="text-xs text-muted">No price history on file for this company yet.</p>;
  }

  const chartData = [...activeBars]
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((b) => ({ date: b.date.slice(5), close: b.close }));

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-2xl border border-border bg-surface p-5">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="font-semibold">Price ({activeBars.length} sessions)</h3>
          <div className="flex items-center gap-3">
            {securityId != null && (
              <div className="flex items-center gap-1 rounded-full bg-surface-alt p-0.5 text-xs">
                <button
                  onClick={() => setAdjusted(false)}
                  className={`rounded-full px-2.5 py-1 ${!adjusted ? "bg-accent text-white" : "text-muted"}`}
                >
                  Raw
                </button>
                <button
                  onClick={() => setAdjusted(true)}
                  className={`rounded-full px-2.5 py-1 ${adjusted ? "bg-accent text-white" : "text-muted"}`}
                >
                  {loading ? "Loading…" : "Adjusted"}
                </button>
              </div>
            )}
            <span className="text-[10px] text-muted">{dataDelayNotice}</span>
          </div>
        </div>
        {adjusted && adjustedBars && (
          <p className="mb-2 text-[10px] text-muted">
            {actionsOnFile
              ? `Backward-adjusted for ${actionsOnFile} cash dividend${actionsOnFile === 1 ? "" : "s"} on file (PSX face-value % convention). No bonus/rights/split events are on file for this pilot yet.`
              : "No corporate actions on file for this company — adjusted series is identical to raw."}
          </p>
        )}
        {adjusted && adjustError && (
          <p className="mb-2 text-[10px] text-negative">
            Couldn&apos;t load the adjusted series — showing raw prices instead.
          </p>
        )}
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="closeFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4f7cff" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#4f7cff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: "#8b92a5", fontSize: 10 }} axisLine={false} tickLine={false} minTickGap={30} />
              <YAxis domain={["auto", "auto"]} tick={{ fill: "#8b92a5", fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: "#161a26", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, fontSize: 12 }}
                labelStyle={{ color: "#8b92a5" }}
              />
              <Area type="monotone" dataKey="close" name="Close" stroke="#4f7cff" strokeWidth={2} fill="url(#closeFill)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div>
        <h4 className="mb-3 text-sm font-semibold">Moving Averages</h4>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <IndicatorCard label="SMA 20" unit="PKR" result={technicals.sma20} />
          <IndicatorCard label="SMA 50" unit="PKR" result={technicals.sma50} />
          <IndicatorCard label="SMA 200" unit="PKR" result={technicals.sma200} />
          <IndicatorCard label="EMA 20" unit="PKR" result={technicals.ema20} />
          <IndicatorCard label="EMA 50" unit="PKR" result={technicals.ema50} />
          <IndicatorCard label="EMA 200" unit="PKR" result={technicals.ema200} />
        </div>
      </div>

      <div>
        <h4 className="mb-3 text-sm font-semibold">Momentum &amp; Oscillators</h4>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          <IndicatorCard label="RSI (14)" result={technicals.rsi14} />
          <div className="rounded-2xl border border-border bg-surface p-4">
            <p className="mb-1 text-xs text-muted">MACD (12/26/9)</p>
            {technicals.macd.available ? (
              <>
                <p className="text-sm font-semibold">{technicals.macd.latest!.macd.toFixed(2)}</p>
                <p className="mt-0.5 text-[10px] text-muted">
                  Signal {technicals.macd.latest!.signal.toFixed(2)} · Hist {technicals.macd.latest!.histogram.toFixed(2)}
                </p>
              </>
            ) : (
              <p className="text-xs text-muted">Needs {technicals.macd.requiredBars} days ({technicals.macd.availableBars} on file)</p>
            )}
          </div>
          <div className="rounded-2xl border border-border bg-surface p-4">
            <p className="mb-1 text-xs text-muted">Stoch RSI (14/14/3/3)</p>
            {technicals.stochRsi.available ? (
              <>
                <p className="text-sm font-semibold">%K {technicals.stochRsi.latest!.k.toFixed(1)}</p>
                <p className="mt-0.5 text-[10px] text-muted">%D {technicals.stochRsi.latest!.d.toFixed(1)}</p>
              </>
            ) : (
              <p className="text-xs text-muted">Needs {technicals.stochRsi.requiredBars} days ({technicals.stochRsi.availableBars} on file)</p>
            )}
          </div>
          <IndicatorCard label="MFI (14)" result={technicals.mfi} />
        </div>
      </div>

      <div>
        <h4 className="mb-3 text-sm font-semibold">Volatility &amp; Volume</h4>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          <div className="rounded-2xl border border-border bg-surface p-4">
            <p className="mb-1 text-xs text-muted">Bollinger (20, 2σ)</p>
            {technicals.bollinger.available ? (
              <>
                <p className="text-sm font-semibold">
                  {technicals.bollinger.latest!.lower.toFixed(1)} – {technicals.bollinger.latest!.upper.toFixed(1)}
                </p>
                <p className="mt-0.5 text-[10px] text-muted">Mid {technicals.bollinger.latest!.middle.toFixed(1)}</p>
              </>
            ) : (
              <p className="text-xs text-muted">Needs {technicals.bollinger.requiredBars} days ({technicals.bollinger.availableBars} on file)</p>
            )}
          </div>
          <IndicatorCard label="ATR (14)" unit="PKR" result={technicals.atr14} />
          <div className="rounded-2xl border border-border bg-surface p-4">
            <p className="mb-1 text-xs text-muted">ADX (14)</p>
            {technicals.adx.available ? (
              <>
                <p className="text-sm font-semibold">{technicals.adx.latest!.adx.toFixed(1)}</p>
                <p className="mt-0.5 text-[10px] text-muted">
                  +DI {technicals.adx.latest!.plusDI.toFixed(1)} · −DI {technicals.adx.latest!.minusDI.toFixed(1)}
                </p>
              </>
            ) : (
              <p className="text-xs text-muted">Needs {technicals.adx.requiredBars} days ({technicals.adx.availableBars} on file)</p>
            )}
          </div>
          <div className="rounded-2xl border border-border bg-surface p-4">
            <p className="mb-1 text-xs text-muted">VWAP (20-day rolling)</p>
            {technicals.vwap.available ? (
              <p className="text-sm font-semibold">PKR {technicals.vwap.latest!.toFixed(2)}</p>
            ) : (
              <p className="text-xs text-muted">No volume data on file</p>
            )}
          </div>
          <div className="rounded-2xl border border-border bg-surface p-4">
            <p className="mb-1 text-xs text-muted">OBV</p>
            {technicals.obv.available ? (
              <p className="text-sm font-semibold tabular-nums">
                {technicals.obv.latest! >= 0 ? "+" : ""}{(technicals.obv.latest! / 1_000_000).toFixed(1)} mn
              </p>
            ) : (
              <p className="text-xs text-muted">No volume data on file</p>
            )}
          </div>
        </div>
      </div>

      <p className="text-[10px] text-muted">
        All indicators computed from delayed EOD OHLCV data on file. Volume-based indicators
        (OBV, VWAP, MFI) are marked unavailable when volume data is absent. Fewer trading
        sessions than an indicator&apos;s window means it is reported unavailable rather than
        computed on a shortened window.
      </p>
    </div>
  );
}
