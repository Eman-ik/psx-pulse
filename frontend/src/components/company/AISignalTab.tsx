"use client";

import { useEffect, useMemo, useState } from "react";
import type { CompanyOverview, PriceBar, SignalResearch } from "@/lib/api";
import { computeTechnicals } from "@/lib/technicals";
import {
  computeConfidence,
  computeKnnModel,
  computeLinearRegression,
  computeLogisticModel,
  computeMLConsensus,
  computeNeuralModel,
  computeRiskLevel,
  computeTradeSetup,
  detectPatterns,
  generateInsights,
} from "@/lib/signal-analysis";

// ─── Config ──────────────────────────────────────────────────────────────────

const SIGNAL_META: Record<string, { label: string; color: string; bg: string; border: string; icon: string }> = {
  strong_buy:  { label: "Strong Buy",  color: "#10b981", bg: "rgba(16,185,129,0.08)",  border: "rgba(16,185,129,0.25)", icon: "▲▲" },
  buy:         { label: "Buy",         color: "#22c55e", bg: "rgba(34,197,94,0.08)",   border: "rgba(34,197,94,0.25)",  icon: "▲"  },
  hold:        { label: "Hold",        color: "#f59e0b", bg: "rgba(245,158,11,0.08)",  border: "rgba(245,158,11,0.25)", icon: "●"  },
  sell:        { label: "Sell",        color: "#f97316", bg: "rgba(249,115,22,0.08)",  border: "rgba(249,115,22,0.25)", icon: "▼"  },
  strong_sell: { label: "Strong Sell", color: "#ef4444", bg: "rgba(239,68,68,0.08)",   border: "rgba(239,68,68,0.25)",  icon: "▼▼" },
  no_signal:   { label: "No Signal",  color: "#6b7280", bg: "rgba(107,114,128,0.06)", border: "rgba(107,114,128,0.20)", icon: "—" },
};

const RISK_META = {
  LOW:    { label: "LOW",    color: "#10b981", bg: "rgba(16,185,129,0.12)"  },
  MEDIUM: { label: "MEDIUM", color: "#f59e0b", bg: "rgba(245,158,11,0.12)" },
  HIGH:   { label: "HIGH",   color: "#ef4444", bg: "rgba(239,68,68,0.12)"  },
};

const TIMEFRAME_BARS: Record<string, number> = { "1W": 5, "1M": 21, "3M": 63, "6M": 126, "1Y": 250 };

const ML_SIGNAL_COLOR: Record<string, string> = { BUY: "#22c55e", HOLD: "#f59e0b", SELL: "#ef4444" };

// ─── Small primitives ─────────────────────────────────────────────────────────

function Badge({ label, color, bg }: { label: string; color: string; bg: string }) {
  return (
    <span className="rounded-full px-2.5 py-0.5 text-xs font-semibold" style={{ color, backgroundColor: bg }}>
      {label}
    </span>
  );
}

function ScoreRing({ score, size = 80 }: { score: number; size?: number }) {
  const r = (size / 2) - 8;
  const circ = 2 * Math.PI * r;
  const fill = (score / 100) * circ;
  const color = score >= 62 ? "#22c55e" : score >= 42 ? "#f59e0b" : "#ef4444";
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={7} />
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={7}
        strokeDasharray={`${fill} ${circ}`} strokeLinecap="round"
        transform={`rotate(-90 ${size/2} ${size/2})`} />
      <text x={size/2} y={size/2 + 5} textAnchor="middle" fontSize={size * 0.22}
        fontWeight="700" fill={color}>{score.toFixed(0)}</text>
    </svg>
  );
}

function DimBar({ label, score, desc }: { label: string; score: number | null; desc: string }) {
  if (score == null) return (
    <div className="flex items-center gap-3" title={desc}>
      <span className="w-44 shrink-0 text-sm text-muted">{label}</span>
      <span className="text-xs text-muted/40">No data</span>
    </div>
  );
  const color = score >= 65 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444";
  return (
    <div className="flex items-center gap-3" title={desc}>
      <span className="w-44 shrink-0 text-sm">{label}</span>
      <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-surface-alt">
        <div className="absolute left-1/2 top-0 h-full w-px bg-border/50" />
        <div className="h-full rounded-full" style={{ width: `${Math.min(100, score)}%`, backgroundColor: color }} />
      </div>
      <span className="w-8 text-right text-sm tabular-nums font-medium" style={{ color }}>{score.toFixed(0)}</span>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function AISignalTab({
  signal,
  prices,
  data,
}: {
  signal: SignalResearch | null;
  prices: PriceBar[];
  data: CompanyOverview;
}) {
  const [timeframe, setTimeframe] = useState<string>("1M");
  const [watchlisted, setWatchlisted] = useState(false);

  const issuerId = data.issuer.id;

  useEffect(() => {
    const list: number[] = JSON.parse(localStorage.getItem("psx_watchlist") ?? "[]");
    setWatchlisted(list.includes(issuerId));
  }, [issuerId]);

  function toggleWatchlist() {
    const list: number[] = JSON.parse(localStorage.getItem("psx_watchlist") ?? "[]");
    const next = watchlisted ? list.filter((id) => id !== issuerId) : [...list, issuerId];
    localStorage.setItem("psx_watchlist", JSON.stringify(next));
    setWatchlisted(!watchlisted);
  }

  const sortedBars = useMemo(() => [...prices].sort((a, b) => a.date.localeCompare(b.date)), [prices]);
  const patternBars = useMemo(() => sortedBars.slice(-TIMEFRAME_BARS[timeframe]), [sortedBars, timeframe]);

  const tech = useMemo(() => computeTechnicals(sortedBars), [sortedBars]);
  const linReg = useMemo(() => computeLinearRegression(sortedBars), [sortedBars]);
  const logistic = useMemo(() => signal ? computeLogisticModel(signal) : null, [signal]);
  const knn = useMemo(() => computeKnnModel(sortedBars), [sortedBars]);
  const neural = useMemo(() => signal ? computeNeuralModel(signal) : null, [signal]);
  const patterns = useMemo(() => detectPatterns(patternBars), [patternBars]);
  const tradeSetup = useMemo(() =>
    signal ? computeTradeSetup(sortedBars, signal, signal.composite_signal) : null,
    [sortedBars, signal]);

  const aiSig = signal?.composite_signal ?? "no_signal";
  const sigMeta = SIGNAL_META[aiSig] ?? SIGNAL_META.no_signal;
  const confidence = signal ? computeConfidence(signal) : 0;
  const riskLevel = signal ? computeRiskLevel(signal) : "MEDIUM";
  const riskMeta = RISK_META[riskLevel];

  const mlConsensus = useMemo(() =>
    computeMLConsensus(linReg, logistic, knn, neural, aiSig),
    [linReg, logistic, knn, neural, aiSig]);

  const insights = useMemo(() =>
    signal ? generateInsights(signal, tech.rsi14.latest, tech.macd.latest?.histogram ?? null) : [],
    [signal, tech]);

  const quote = data.live_quote;
  const price = quote?.price ?? sortedBars[sortedBars.length - 1]?.close ?? null;
  const changePct = quote?.change_pct ?? null;

  const rsi = tech.rsi14.latest;
  const macd = tech.macd.latest;
  const sma20 = tech.sma20.latest;
  const atrVal = tech.atr14.latest;
  const volPct = price && atrVal ? (atrVal / price) * 100 : null;

  const DIMS = [
    { key: "quality_score"          as const, label: "Quality",          desc: "Earnings quality vs peers" },
    { key: "growth_score"           as const, label: "Growth",           desc: "Revenue & earnings growth vs peers" },
    { key: "financial_health_score" as const, label: "Financial Health", desc: "Leverage & liquidity vs peers" },
    { key: "valuation_score"        as const, label: "Valuation",        desc: "P/E, P/B attractiveness vs peers" },
    { key: "catalyst_risk_score"    as const, label: "Catalyst / Risk",  desc: "Macro & sector catalysts" },
    { key: "momentum_score"         as const, label: "Momentum",         desc: "180-day price return vs peers" },
    { key: "risk_score"             as const, label: "Risk (Beta)",      desc: "Lower systematic risk = higher score" },
  ];

  const avgScore = signal
    ? DIMS.map((d) => signal[d.key] as number | null).filter((v): v is number => v != null).reduce(
        (a, b, _, arr) => a + b / arr.length, 0) : null;

  return (
    <div className="flex flex-col gap-5">

      {/* ── 1. Quote Bar ───────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-surface px-5 py-4">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-widest text-muted">{data.symbol ?? "—"}</p>
          <p className="text-base font-semibold">{data.issuer.short_name ?? data.issuer.name}</p>
        </div>
        <div className="flex items-center gap-6">
          {price != null && (
            <div>
              <p className="text-xl font-bold tabular-nums">PKR {price.toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
              {changePct != null && (
                <p className={`text-right text-xs font-medium tabular-nums ${changePct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {changePct >= 0 ? "+" : ""}{changePct.toFixed(2)}%
                </p>
              )}
            </div>
          )}
          <button
            onClick={toggleWatchlist}
            className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
              watchlisted
                ? "border-amber-400/40 bg-amber-400/10 text-amber-400"
                : "border-border bg-surface-alt text-muted hover:border-accent/40 hover:text-accent"
            }`}
          >
            {watchlisted ? "★ Watchlisted" : "☆ Add to Watchlist"}
          </button>
        </div>
      </div>

      {/* ── 2. AI Recommendation Block ─────────────────────────────────────── */}
      <div className="rounded-2xl border p-5" style={{ backgroundColor: sigMeta.bg, borderColor: sigMeta.border }}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-widest text-muted/70">AI Recommendation</p>
            <div className="flex items-center gap-3">
              <span className="text-4xl font-bold tracking-tight" style={{ color: sigMeta.color }}>
                {sigMeta.label}
              </span>
              <span className="text-lg opacity-60" style={{ color: sigMeta.color }}>{sigMeta.icon}</span>
            </div>
            {signal?.as_of_date && (
              <p className="mt-1 text-xs text-muted">Updated {signal.as_of_date} · Policy v{signal.policy_version}</p>
            )}
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted">Confidence</span>
                <span className="rounded-full px-2.5 py-0.5 text-xs font-bold" style={{ color: sigMeta.color, backgroundColor: sigMeta.bg }}>
                  {confidence}%
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted">Risk</span>
                <Badge label={riskMeta.label} color={riskMeta.color} bg={riskMeta.bg} />
              </div>
            </div>
          </div>
          {avgScore != null && <ScoreRing score={avgScore} size={88} />}
        </div>

        {signal?.suppression_reasons && signal.suppression_reasons.length > 0 && (
          <div className="mt-4 rounded-xl bg-black/20 px-4 py-3">
            <p className="mb-1 text-xs font-medium text-muted">Dimensions with missing data:</p>
            <ul className="list-inside list-disc space-y-0.5 text-xs text-muted/80">
              {signal.suppression_reasons.map((r) => <li key={r}>{r}</li>)}
            </ul>
          </div>
        )}
      </div>

      {/* ── 3. Analysis Insights ────────────────────────────────────────────── */}
      {insights.length > 0 && (
        <div className="rounded-2xl border border-border bg-surface p-5">
          <h4 className="mb-3 text-sm font-semibold">Analysis Insights</h4>
          <ul className="space-y-2.5">
            {insights.map((ins, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <span className="mt-0.5 shrink-0 text-accent">›</span>
                <span className="text-muted/90 leading-relaxed">{ins}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── 4. ML Models Consensus ──────────────────────────────────────────── */}
      <div className="rounded-2xl border border-border bg-surface p-5">
        <h4 className="mb-4 text-sm font-semibold">Quantitative Models Consensus</h4>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-8">
            <div>
              <p className="text-2xl font-bold" style={{ color: ML_SIGNAL_COLOR[mlConsensus.signal] }}>
                {mlConsensus.signal}
              </p>
              <p className="text-xs text-muted">Model consensus</p>
            </div>
            <div>
              <p className="text-2xl font-bold tabular-nums">{mlConsensus.agreementPct}%</p>
              <p className="text-xs text-muted">Agreement</p>
            </div>
            <div>
              <p className="text-2xl font-bold tabular-nums">{mlConsensus.confidence}%</p>
              <p className="text-xs text-muted">Confidence</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {(["BUY", "HOLD", "SELL"] as const).map((v) => (
              <div key={v} className="rounded-lg px-3 py-2 text-center" style={{ backgroundColor: `${ML_SIGNAL_COLOR[v]}15` }}>
                <p className="text-sm font-bold tabular-nums" style={{ color: ML_SIGNAL_COLOR[v] }}>{mlConsensus.votes[v]}</p>
                <p className="text-[10px] text-muted">{v}</p>
              </div>
            ))}
          </div>
        </div>

        {/* AI vs ML comparison */}
        <div className={`mt-4 flex items-start gap-3 rounded-xl px-4 py-3 ${
          mlConsensus.agreesWithAI ? "bg-emerald-400/8 border border-emerald-400/20" : "bg-amber-400/8 border border-amber-400/20"
        }`}>
          <span className="mt-0.5 text-lg">{mlConsensus.agreesWithAI ? "✓" : "⚠"}</span>
          <div>
            <p className="text-sm font-medium" style={{ color: mlConsensus.agreesWithAI ? "#10b981" : "#f59e0b" }}>
              {mlConsensus.agreesWithAI ? "AI & Models Agree" : "AI / Model Divergence"}
            </p>
            <p className="text-xs text-muted mt-0.5">
              {mlConsensus.agreesWithAI
                ? `AI signal (${sigMeta.label}) aligns with quantitative model consensus (${mlConsensus.signal}). Convergence increases signal reliability.`
                : `AI signal (${sigMeta.label}) diverges from quantitative consensus (${mlConsensus.signal}). Treat both signals with additional caution and await confirmation.`}
            </p>
          </div>
        </div>
      </div>

      {/* ── 5. Individual Model Cards ───────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">

        {/* Linear Regression (Trend Model) */}
        <div className="rounded-2xl border border-border bg-surface p-5">
          <div className="mb-1 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Trend Model</p>
            <p className="text-[10px] text-muted">Linear Regression</p>
          </div>
          {linReg ? (
            <>
              <p className="mt-2 text-xl font-bold" style={{ color: ML_SIGNAL_COLOR[linReg.signal] }}>{linReg.signal}</p>
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <div><p className="text-muted">Confidence</p><p className="font-semibold tabular-nums">{linReg.confidence}%</p></div>
                <div><p className="text-muted">Predicted 30d</p>
                  <p className={`font-semibold tabular-nums ${linReg.predictedReturn30d >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {linReg.predictedReturn30d >= 0 ? "+" : ""}{linReg.predictedReturn30d.toFixed(2)}%
                  </p>
                </div>
                <div><p className="text-muted">Validation MAE</p><p className="font-semibold tabular-nums">PKR {linReg.mae.toFixed(2)}</p></div>
                <div><p className="text-muted">R²</p><p className="font-semibold tabular-nums">{(linReg.r2 * 100).toFixed(1)}%</p></div>
              </div>
            </>
          ) : <p className="mt-3 text-xs text-muted">Insufficient price history (need ≥ 15 bars).</p>}
        </div>

        {/* Logistic Regression (Score Classifier) */}
        <div className="rounded-2xl border border-border bg-surface p-5">
          <div className="mb-1 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Score Classifier</p>
            <p className="text-[10px] text-muted">Logistic Regression</p>
          </div>
          {logistic ? (
            <>
              <p className="mt-2 text-xl font-bold" style={{ color: ML_SIGNAL_COLOR[logistic.signal] }}>{logistic.signal}</p>
              <div className="mt-3 space-y-1.5">
                {(["BUY", "HOLD", "SELL"] as const).map((s) => {
                  const prob = s === "BUY" ? logistic.buyProb : s === "HOLD" ? logistic.holdProb : logistic.sellProb;
                  return (
                    <div key={s} className="flex items-center gap-2 text-xs">
                      <span className="w-10 font-medium" style={{ color: ML_SIGNAL_COLOR[s] }}>{s}</span>
                      <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-surface-alt">
                        <div className="h-full rounded-full" style={{ width: `${prob}%`, backgroundColor: ML_SIGNAL_COLOR[s] }} />
                      </div>
                      <span className="w-8 text-right tabular-nums">{prob}%</span>
                    </div>
                  );
                })}
              </div>
            </>
          ) : <p className="mt-3 text-xs text-muted">Need ≥ 3 dimension scores.</p>}
        </div>

        {/* KNN Pattern Matcher */}
        <div className="rounded-2xl border border-border bg-surface p-5">
          <div className="mb-1 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Pattern Matcher</p>
            <p className="text-[10px] text-muted">KNN (20-day window)</p>
          </div>
          {knn ? (
            <>
              <p className="mt-2 text-xl font-bold" style={{ color: ML_SIGNAL_COLOR[knn.signal] }}>{knn.signal}</p>
              <div className="mt-3 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted">Avg subsequent return</span>
                  <span className={`font-semibold tabular-nums ${knn.avgSubsequentReturn >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {knn.avgSubsequentReturn >= 0 ? "+" : ""}{knn.avgSubsequentReturn.toFixed(2)}%
                  </span>
                </div>
                {knn.matches.map((m, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg bg-surface-alt px-2 py-1.5">
                    <span className="text-muted">{m.startDate.slice(0, 7)} · {m.similarity}% sim.</span>
                    <span className={`font-medium tabular-nums ${m.return30d >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {m.return30d >= 0 ? "+" : ""}{m.return30d.toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </>
          ) : <p className="mt-3 text-xs text-muted">Need ≥ 65 price bars for pattern matching.</p>}
        </div>

        {/* Neural / Ensemble */}
        <div className="rounded-2xl border border-border bg-surface p-5">
          <div className="mb-1 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Ensemble Model</p>
            <p className="text-[10px] text-muted">Neural Network</p>
          </div>
          {neural ? (
            <>
              <p className="mt-2 text-xl font-bold" style={{ color: ML_SIGNAL_COLOR[neural.signal] }}>{neural.signal}</p>
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <div><p className="text-muted">Confidence</p><p className="font-semibold tabular-nums">{neural.confidence}%</p></div>
                <div><p className="text-muted">Validation accuracy</p><p className="font-semibold tabular-nums">{neural.accuracy}%</p></div>
              </div>
            </>
          ) : <p className="mt-3 text-xs text-muted">Need ≥ 2 dimension scores.</p>}
        </div>
      </div>

      {/* ── 6. Dimension Score Breakdown ────────────────────────────────────── */}
      {signal?.as_of_date && (
        <div className="rounded-2xl border border-border bg-surface p-5">
          <div className="mb-1 flex items-center justify-between">
            <h4 className="text-sm font-semibold">Dimension Scores</h4>
            <span className="text-xs text-muted">0 = weakest · 50 = sector avg · 100 = strongest</span>
          </div>
          <div className="mt-4 flex flex-col gap-3.5">
            {DIMS.map((d) => (
              <DimBar key={d.key} label={d.label} score={signal[d.key] as number | null} desc={d.desc} />
            ))}
          </div>
        </div>
      )}

      {/* ── 7. Trade Setup ──────────────────────────────────────────────────── */}
      {tradeSetup && (
        <div className="rounded-2xl border border-border bg-surface p-5">
          <h4 className="mb-4 text-sm font-semibold">Trade Setup</h4>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-surface-alt p-4">
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted">Entry</p>
              <p className="text-xl font-bold tabular-nums">PKR {tradeSetup.entryPrice.toFixed(2)}</p>
              <p className="mt-1 text-xs text-muted">Range: {tradeSetup.entryRangeLow} – {tradeSetup.entryRangeHigh} (±2%)</p>
            </div>
            <div className="rounded-xl bg-emerald-400/8 border border-emerald-400/20 p-4">
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-emerald-500">Target</p>
              <p className="text-xl font-bold tabular-nums text-emerald-400">PKR {tradeSetup.targetPrice.toFixed(2)}</p>
              <p className="mt-1 text-xs text-muted">Gain: {tradeSetup.targetGainPct >= 0 ? "+" : ""}{tradeSetup.targetGainPct.toFixed(2)}%</p>
            </div>
            <div className="rounded-xl bg-red-400/8 border border-red-400/20 p-4">
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-red-500">Stop Loss</p>
              <p className="text-xl font-bold tabular-nums text-red-400">PKR {tradeSetup.stopPrice.toFixed(2)}</p>
              <p className="mt-1 text-xs text-muted">Risk: {tradeSetup.stopRiskPct.toFixed(2)}%</p>
            </div>
          </div>
          <div className="mt-3 flex items-center gap-2 rounded-xl bg-surface-alt px-4 py-3">
            <span className="text-xs font-semibold text-accent">{tradeSetup.horizon.toUpperCase()}</span>
            <span className="text-xs text-muted">Time horizon · {tradeSetup.horizonDays}</span>
          </div>
        </div>
      )}

      {/* ── 8. Technical Indicators ─────────────────────────────────────────── */}
      <div className="rounded-2xl border border-border bg-surface p-5">
        <h4 className="mb-4 text-sm font-semibold">Technical Indicators</h4>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            {
              label: "RSI (14)",
              value: rsi != null ? rsi.toFixed(1) : null,
              sub: rsi == null ? null : rsi > 70 ? "Overbought" : rsi < 30 ? "Oversold" : "Neutral",
              color: rsi == null ? undefined : rsi > 70 ? "#ef4444" : rsi < 30 ? "#22c55e" : "#f59e0b",
            },
            {
              label: "MACD",
              value: macd != null ? macd.macd.toFixed(2) : null,
              sub: macd == null ? null : `Signal: ${macd.signal.toFixed(2)}`,
              color: macd == null ? undefined : macd.histogram > 0 ? "#22c55e" : "#ef4444",
            },
            {
              label: "SMA 20",
              value: sma20 != null ? `PKR ${sma20.toFixed(2)}` : null,
              sub: price != null && sma20 != null ? (price > sma20 ? "Price above" : "Price below") : null,
              color: price != null && sma20 != null ? (price > sma20 ? "#22c55e" : "#ef4444") : undefined,
            },
            {
              label: "Volatility (ATR)",
              value: volPct != null ? `${volPct.toFixed(2)}%` : null,
              sub: volPct == null ? null : volPct > 3 ? "High" : volPct > 1.5 ? "Moderate" : "Low",
              color: volPct == null ? undefined : volPct > 3 ? "#ef4444" : volPct > 1.5 ? "#f59e0b" : "#22c55e",
            },
          ].map(({ label, value, sub, color }) => (
            <div key={label} className="rounded-xl bg-surface-alt p-4">
              <p className="mb-2 text-xs text-muted">{label}</p>
              <p className="text-lg font-bold tabular-nums" style={{ color: color ?? "inherit" }}>
                {value ?? "—"}
              </p>
              {sub && <p className="mt-1 text-[10px] font-medium" style={{ color: color ?? "#6b7280" }}>{sub}</p>}
            </div>
          ))}
        </div>
      </div>

      {/* ── 9. Chart Pattern Recognition ────────────────────────────────────── */}
      <div className="rounded-2xl border border-border bg-surface p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h4 className="text-sm font-semibold">Chart Pattern Recognition</h4>
            <p className="text-xs text-muted">{patterns.length} pattern{patterns.length !== 1 ? "s" : ""} detected</p>
          </div>
          <div className="flex items-center gap-1 rounded-full bg-surface-alt p-0.5 text-xs">
            {Object.keys(TIMEFRAME_BARS).map((tf) => (
              <button key={tf} onClick={() => setTimeframe(tf)}
                className={`rounded-full px-3 py-1 transition-colors ${
                  timeframe === tf ? "bg-accent text-white" : "text-muted hover:text-foreground"
                }`}>
                {tf}
              </button>
            ))}
          </div>
        </div>

        {patterns.length === 0 ? (
          <p className="text-xs text-muted">No patterns detected for the selected timeframe. Try a longer window.</p>
        ) : (
          <div className="flex flex-col gap-4">
            {patterns.map((p, i) => {
              const dirColor = p.direction === "BULLISH" ? "#22c55e" : p.direction === "BEARISH" ? "#ef4444" : "#f59e0b";
              const dirBg = p.direction === "BULLISH" ? "rgba(34,197,94,0.08)" : p.direction === "BEARISH" ? "rgba(239,68,68,0.08)" : "rgba(245,158,11,0.08)";
              return (
                <div key={i} className="rounded-xl border border-border p-4">
                  {/* Pattern header */}
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-sm">{p.name}</span>
                    <span className="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase"
                      style={{ color: dirColor, backgroundColor: dirBg }}>{p.direction}</span>
                    <span className="rounded-full bg-surface-alt px-2 py-0.5 text-[10px] text-muted">
                      {p.confidence}% confidence
                    </span>
                    <span className="ml-auto text-[10px] text-muted">{p.detectedDate}</span>
                  </div>

                  <p className="mb-3 text-xs text-muted leading-relaxed">{p.description}</p>

                  {/* Target / Stop */}
                  <div className="mb-3 flex gap-3 text-xs">
                    <div className="flex-1 rounded-lg bg-emerald-400/8 border border-emerald-400/20 px-3 py-2">
                      <p className="text-emerald-500 font-medium">Target</p>
                      <p className="font-bold tabular-nums text-emerald-400">PKR {p.targetPrice.toFixed(2)}</p>
                      <p className="text-muted">{p.targetPct >= 0 ? "+" : ""}{p.targetPct.toFixed(2)}% from current</p>
                    </div>
                    <div className="flex-1 rounded-lg bg-red-400/8 border border-red-400/20 px-3 py-2">
                      <p className="text-red-500 font-medium">Stop Loss</p>
                      <p className="font-bold tabular-nums text-red-400">PKR {p.stopPrice.toFixed(2)}</p>
                      <p className="text-muted">{p.stopPct.toFixed(2)}% from current</p>
                    </div>
                  </div>

                  {/* Key Implications */}
                  <div>
                    <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted">Key Implications</p>
                    <ul className="space-y-1">
                      {p.implications.map((imp, j) => (
                        <li key={j} className="flex gap-2 text-xs text-muted/90">
                          <span className="mt-0.5 shrink-0 text-accent">›</span>
                          <span className="leading-relaxed">{imp}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Footer note ─────────────────────────────────────────────────────── */}
      <p className="text-[11px] text-muted leading-relaxed">
        Scores are peer-relative within the fertilizer pilot universe (50 = sector mean).
        Quantitative models use price history and dimensional scores; they are deterministic, not
        learned from labelled data. Not investment advice — always conduct independent due diligence.
      </p>

    </div>
  );
}
