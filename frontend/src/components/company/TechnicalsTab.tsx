"use client";

import { useMemo } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PriceBar } from "@/lib/api";
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

export default function TechnicalsTab({ bars, dataDelayNotice }: { bars: PriceBar[]; dataDelayNotice: string }) {
  const technicals = useMemo(() => computeTechnicals(bars), [bars]);

  if (bars.length === 0) {
    return <p className="text-xs text-muted">No price history on file for this company yet.</p>;
  }

  const chartData = [...bars]
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((b) => ({ date: b.date.slice(5), close: b.close }));

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-2xl border border-border bg-surface p-5">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="font-semibold">Price ({bars.length} sessions)</h3>
          <span className="text-[10px] text-muted">{dataDelayNotice}</span>
        </div>
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
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <IndicatorCard label="SMA 20" unit="PKR" result={technicals.sma20} />
          <IndicatorCard label="SMA 50" unit="PKR" result={technicals.sma50} />
          <IndicatorCard label="SMA 200" unit="PKR" result={technicals.sma200} />
          <IndicatorCard label="EMA 20" unit="PKR" result={technicals.ema20} />
          <IndicatorCard label="EMA 50" unit="PKR" result={technicals.ema50} />
        </div>
      </div>

      <div>
        <h4 className="mb-3 text-sm font-semibold">Momentum &amp; Volatility</h4>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <IndicatorCard label="RSI (14)" result={technicals.rsi14} />
          <div className="rounded-2xl border border-border bg-surface p-4">
            <p className="mb-1 text-xs text-muted">MACD</p>
            {technicals.macd.available ? (
              <p className="text-sm font-semibold">
                {technicals.macd.latest!.macd.toFixed(2)} / sig {technicals.macd.latest!.signal.toFixed(2)}
              </p>
            ) : (
              <p className="text-xs text-muted">
                Insufficient history ({technicals.macd.availableBars}/{technicals.macd.requiredBars} days)
              </p>
            )}
          </div>
          <div className="rounded-2xl border border-border bg-surface p-4">
            <p className="mb-1 text-xs text-muted">Bollinger (20, 2σ)</p>
            {technicals.bollinger.available ? (
              <p className="text-sm font-semibold">
                {technicals.bollinger.latest!.lower.toFixed(1)} – {technicals.bollinger.latest!.upper.toFixed(1)}
              </p>
            ) : (
              <p className="text-xs text-muted">
                Insufficient history ({technicals.bollinger.availableBars}/{technicals.bollinger.requiredBars} days)
              </p>
            )}
          </div>
          <IndicatorCard label="ATR (14)" unit="PKR" result={technicals.atr14} />
        </div>
      </div>

      <p className="text-[10px] text-muted">
        Indicators computed from delayed EOD closes on file for this company. Fewer trading
        sessions than an indicator&apos;s window means it is marked unavailable rather than
        computed on a shortened window.
      </p>
    </div>
  );
}
