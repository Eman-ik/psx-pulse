"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Area, AreaChart, Bar, CartesianGrid, ComposedChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { Minus, TrendingDown, TrendingUp, Zap } from "lucide-react";
import { fetchPrices, type PriceBar } from "@/lib/api";
import { computeTechnicals, type IndicatorResult } from "@/lib/technicals";

// Recharts has no built-in candlestick: this is the standard "floating bar" pattern
// -- a single Bar keyed to the [low, high] range (so Recharts positions x/y/height
// correctly for that range) with a custom shape that then derives the open/close
// body proportionally from the same pixel range, rather than needing a second
// synced series.
function Candle(props: {
  x?: number; y?: number; width?: number; height?: number;
  payload?: { open: number; high: number; low: number; close: number };
}) {
  const { x, y, width, height, payload } = props;
  if (x == null || y == null || width == null || height == null || !payload) return null;
  const { open, high, low, close } = payload;
  const isUp = close >= open;
  const color = isUp ? "#22c55e" : "#ef4444";
  const centerX = x + width / 2;

  if (high === low) {
    return <line x1={x} y1={y} x2={x + width} y2={y} stroke={color} strokeWidth={1} />;
  }

  const priceToY = (price: number) => y + (height * (high - price)) / (high - low);
  const bodyTop = priceToY(Math.max(open, close));
  const bodyBottom = priceToY(Math.min(open, close));
  const bodyHeight = Math.max(bodyBottom - bodyTop, 1);
  const bodyWidth = Math.max(width * 0.6, 2);

  return (
    <g>
      <line x1={centerX} y1={y} x2={centerX} y2={y + height} stroke={color} strokeWidth={1} />
      <rect x={centerX - bodyWidth / 2} y={bodyTop} width={bodyWidth} height={bodyHeight} fill={color} />
    </g>
  );
}

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
  const [chartView, setChartView] = useState<"area" | "candles">("area");
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
    .map((b) => ({ date: b.date.slice(5), close: b.close, open: b.open, high: b.high, low: b.low }));

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-2xl border border-border bg-surface p-5">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="font-semibold">Price ({activeBars.length} sessions)</h3>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 rounded-full bg-surface-alt p-0.5 text-xs">
              <button
                onClick={() => setChartView("area")}
                className={`rounded-full px-2.5 py-1 ${chartView === "area" ? "bg-accent text-white" : "text-muted"}`}
              >
                Area
              </button>
              <button
                onClick={() => setChartView("candles")}
                className={`rounded-full px-2.5 py-1 ${chartView === "candles" ? "bg-accent text-white" : "text-muted"}`}
              >
                Candles
              </button>
            </div>
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
            {chartView === "area" ? (
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
            ) : (
              <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: "#8b92a5", fontSize: 10 }} axisLine={false} tickLine={false} minTickGap={30} />
                <YAxis domain={["auto", "auto"]} tick={{ fill: "#8b92a5", fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#161a26", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, fontSize: 12 }}
                  labelStyle={{ color: "#8b92a5" }}
                  formatter={(_value, _name, item) => {
                    const p = item?.payload as { open: number; high: number; low: number; close: number } | undefined;
                    if (!p) return [null, null];
                    return [`O ${p.open.toFixed(2)} · H ${p.high.toFixed(2)} · L ${p.low.toFixed(2)} · C ${p.close.toFixed(2)}`, "OHLC"];
                  }}
                />
                <Bar dataKey={(d: { low: number; high: number }) => [d.low, d.high]} shape={Candle} isAnimationActive={false} />
              </ComposedChart>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      <div>
        <h4 className="mb-3 text-sm font-semibold">Trend &amp; Key Levels</h4>
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
          <div className="rounded-2xl border border-border bg-surface p-4">
            <p className="mb-2 text-xs text-muted">Trend classification</p>
            {technicals.trendClassification.available ? (
              <>
                <div className="flex items-center gap-2">
                  {technicals.trendClassification.trend === "uptrend" && <TrendingUp className="h-4 w-4 text-positive" />}
                  {technicals.trendClassification.trend === "downtrend" && <TrendingDown className="h-4 w-4 text-negative" />}
                  {technicals.trendClassification.trend === "sideways" && <Minus className="h-4 w-4 text-muted" />}
                  <p className="text-sm font-semibold capitalize">
                    {technicals.trendClassification.trend} · {technicals.trendClassification.strength}
                  </p>
                </div>
                <ul className="mt-2 space-y-0.5">
                  {technicals.trendClassification.reasoning.map((r, i) => (
                    <li key={i} className="text-[11px] text-muted">· {r}</li>
                  ))}
                </ul>
              </>
            ) : (
              <p className="text-xs text-muted">
                Needs {technicals.trendClassification.requiredBars} days ({technicals.trendClassification.availableBars} on file)
              </p>
            )}
          </div>
          <div className="rounded-2xl border border-border bg-surface p-4">
            <p className="mb-2 text-xs text-muted">Breakout</p>
            {technicals.breakout.available ? (
              technicals.breakout.recentBreakout ? (
                <>
                  <div className="flex items-center gap-2">
                    <Zap className={`h-4 w-4 ${technicals.breakout.recentBreakout.direction === "bullish" ? "text-positive" : "text-negative"}`} />
                    <p className="text-sm font-semibold capitalize">
                      {technicals.breakout.recentBreakout.direction} break
                    </p>
                  </div>
                  <p className="mt-1 text-[11px] text-muted">
                    Closed {technicals.breakout.recentBreakout.closePrice.toFixed(2)} through PKR {technicals.breakout.recentBreakout.level.toFixed(2)} on {technicals.breakout.recentBreakout.date.slice(5)}
                  </p>
                  <p className="mt-1 text-[11px] text-muted">
                    {technicals.breakout.recentBreakout.volumeConfirmed === null
                      ? "No volume data to confirm"
                      : technicals.breakout.recentBreakout.volumeConfirmed
                        ? "Volume-confirmed (≥1.5× 20-day average)"
                        : "Not volume-confirmed — below 1.5× 20-day average"}
                  </p>
                </>
              ) : (
                <p className="text-xs text-muted">No level crossed in the last 5 sessions.</p>
              )
            ) : (
              <p className="text-xs text-muted">
                Needs {technicals.breakout.requiredBars} days ({technicals.breakout.availableBars} on file)
              </p>
            )}
          </div>
          <div className="rounded-2xl border border-border bg-surface p-4">
            <p className="mb-2 text-xs text-muted">Support &amp; resistance</p>
            {technicals.supportResistance.available ? (
              technicals.supportResistance.levels.length > 0 ? (
                <ul className="space-y-1">
                  {technicals.supportResistance.levels.map((l, i) => (
                    <li key={i} className="flex items-center justify-between text-[11px]">
                      <span className={l.type === "resistance" ? "text-negative" : "text-positive"}>
                        {l.type === "resistance" ? "Resistance" : "Support"}
                      </span>
                      <span className="font-semibold tabular-nums">PKR {l.price.toFixed(2)}</span>
                      <span className="text-muted">{l.touches}× · last {l.lastTouchDate.slice(5)}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-muted">No swing levels found near the current price yet.</p>
              )
            ) : (
              <p className="text-xs text-muted">
                Needs {technicals.supportResistance.requiredBars} days ({technicals.supportResistance.availableBars} on file)
              </p>
            )}
          </div>
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
