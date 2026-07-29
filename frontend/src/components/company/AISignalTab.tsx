"use client";

import { useEffect, useMemo, useState } from "react";
import type { CompanyOverview, IndexPrices, PriceBar, SignalResearch } from "@/lib/api";
import { computeTechnicals } from "@/lib/technicals";
import {
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

// Tooltip wrapper — shows an explanatory bubble on hover
function Tip({ children, text }: { children: React.ReactNode; text: string }) {
  return (
    <div className="group relative w-full">
      {children}
      <div className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 w-64 -translate-x-1/2 rounded-xl border border-border bg-[#0d1018] px-3 py-2.5 text-xs opacity-0 shadow-2xl transition-opacity duration-150 group-hover:opacity-100">
        <p className="leading-relaxed text-muted/90">{text}</p>
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-[5px] border-transparent border-t-[#0d1018]" />
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

function indexReturn(index: IndexPrices | null, days: number): number | null {
  if (!index || index.bars.length < 2) return null;
  const sorted = [...index.bars].sort((a, b) => a.date.localeCompare(b.date));
  const latest = sorted[sorted.length - 1];
  const anchor = sorted[Math.max(0, sorted.length - 1 - days)];
  if (!latest || !anchor || anchor.close === 0) return null;
  return ((latest.close - anchor.close) / anchor.close) * 100;
}

export default function AISignalTab({
  signal,
  prices,
  data,
  kseIndex,
  fertixIndex,
}: {
  signal: SignalResearch | null;
  prices: PriceBar[];
  data: CompanyOverview;
  kseIndex: IndexPrices | null;
  fertixIndex: IndexPrices | null;
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
  // Always compute technicals on the full history so indicators panel and
  // pattern detection use the same RSI/SMA20/MACD values (fixes the inconsistency
  // where a short timeframe slice produced different indicator readings).
  const tech = useMemo(() => computeTechnicals(sortedBars), [sortedBars]);
  const linReg = useMemo(() => computeLinearRegression(sortedBars), [sortedBars]);
  const logistic = useMemo(() => signal ? computeLogisticModel(signal) : null, [signal]);
  const knn = useMemo(() => computeKnnModel(sortedBars), [sortedBars]);
  const neural = useMemo(() => signal ? computeNeuralModel(signal) : null, [signal]);
  // Pass full history; timeframe controls the MACD crossover lookback window
  const patterns = useMemo(
    () => detectPatterns(sortedBars, TIMEFRAME_BARS[timeframe]),
    [sortedBars, timeframe],
  );
  const tradeSetup = useMemo(() =>
    signal ? computeTradeSetup(sortedBars, signal, signal.composite_signal) : null,
    [sortedBars, signal]);

  const quote = data.live_quote;
  const price = quote?.price ?? sortedBars[sortedBars.length - 1]?.close ?? null;
  const changePct = quote?.change_pct ?? null;

  const rsi = tech.rsi14.latest;
  const macd = tech.macd.latest;
  const sma20 = tech.sma20.latest;
  const atrVal = tech.atr14.latest;
  const volPct = price && atrVal ? (atrVal / price) * 100 : null;

  const DIMS = [
    { key: "quality_score"          as const, label: "Quality",          desc: "Earnings quality vs peers — measures accruals, ROIC, and profit consistency" },
    { key: "growth_score"           as const, label: "Growth",           desc: "Revenue & earnings growth vs sector peers — 3-year CAGR basis" },
    { key: "financial_health_score" as const, label: "Financial Health", desc: "Balance sheet strength — leverage, liquidity, and interest coverage vs peers" },
    { key: "valuation_score"        as const, label: "Valuation",        desc: "P/E and P/B vs sector peers — higher score = more attractively valued" },
    { key: "catalyst_risk_score"    as const, label: "Catalyst / Risk",  desc: "Macro & sector catalysts: gas pricing, SBP policy, and subsidy environment" },
    { key: "momentum_score"         as const, label: "Momentum",         desc: "180-day price return vs sector peers — raw trailing momentum signal" },
    { key: "risk_score"             as const, label: "Risk (Beta)",      desc: "Systematic risk vs KSE-100 — lower beta scores higher (less market sensitivity)" },
  ];

  // ── Pillar 1: Fundamental score (0-100, average of dimension scores) ─────────
  const fundamentalScore = useMemo(() => {
    if (!signal) return null;
    const vals = DIMS.map((d) => signal[d.key] as number | null).filter((v): v is number => v != null);
    return vals.length > 0 ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : null;
  }, [signal]);

  // ── Pillar 2: Technical score (0-100, from indicator signals) ────────────────
  const technicalScore = useMemo(() => {
    const sigs: number[] = [];
    if (rsi != null) sigs.push(rsi < 30 ? 1 : rsi > 70 ? -1 : 0);
    if (macd != null) sigs.push(macd.histogram > 0 ? 1 : -1);
    if (price != null) {
      if (sma20 != null) sigs.push(price > sma20 ? 1 : -1);
      if (tech.sma50.latest != null) sigs.push(price > tech.sma50.latest ? 1 : -1);
      if (tech.ema200.latest != null) sigs.push(price > tech.ema200.latest ? 1 : -1);
      if (tech.vwap.latest != null) sigs.push(price > tech.vwap.latest ? 0.5 : -0.5);
    }
    if (tech.adx.latest != null && tech.adx.latest.adx > 20)
      sigs.push(tech.adx.latest.plusDI > tech.adx.latest.minusDI ? 1 : -1);
    if (tech.obv.latest != null) sigs.push(tech.obv.latest > 0 ? 0.5 : -0.5);
    if (tech.mfi.latest != null) sigs.push(tech.mfi.latest < 20 ? 1 : tech.mfi.latest > 80 ? -1 : 0);
    if (tech.stochRsi.latest != null) sigs.push(tech.stochRsi.latest.k < 20 ? 1 : tech.stochRsi.latest.k > 80 ? -1 : 0);
    if (tech.bollinger.latest != null && price != null)
      sigs.push(price < tech.bollinger.latest.lower ? 1 : price > tech.bollinger.latest.upper ? -1 : 0);
    if (sigs.length === 0) return null;
    return Math.round(50 + (sigs.reduce((a, b) => a + b, 0) / sigs.length) * 50);
  }, [rsi, macd, sma20, price, tech]);

  // ── Pillar 3: ML score (0-100) ────────────────────────────────────────────────
  const aiSig = signal?.composite_signal ?? "no_signal";
  const mlConsensus = useMemo(() =>
    computeMLConsensus(linReg, logistic, knn, neural, aiSig),
    [linReg, logistic, knn, neural, aiSig]);

  const mlScore = useMemo(() => {
    const base = mlConsensus.signal === "BUY" ? 100 : mlConsensus.signal === "SELL" ? 0 : 50;
    return Math.round(base * (mlConsensus.agreementPct / 100) + 50 * (1 - mlConsensus.agreementPct / 100));
  }, [mlConsensus]);

  // ── Pillar 4: Macro score (0-100) ────────────────────────────────────────────
  const macroScore = useMemo(() => {
    const retToScore = (r: number | null) => r == null ? null : Math.min(100, Math.max(0, 50 + r * 2.5));
    const kse90 = retToScore(indexReturn(kseIndex, 90));
    const fx90  = retToScore(indexReturn(fertixIndex, 90));
    const vals  = [kse90, fx90].filter((v): v is number => v != null);
    return vals.length > 0 ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : null;
  }, [kseIndex, fertixIndex]);

  // ── Composite 4-pillar recommendation ────────────────────────────────────────
  const { compositeScore, compositeSignal } = useMemo(() => {
    const parts: { score: number; weight: number }[] = [];
    if (fundamentalScore != null) parts.push({ score: fundamentalScore, weight: 0.40 });
    if (technicalScore   != null) parts.push({ score: technicalScore,   weight: 0.30 });
    parts.push({ score: mlScore, weight: 0.20 });
    if (macroScore != null) parts.push({ score: macroScore, weight: 0.10 });
    const tw = parts.reduce((s, p) => s + p.weight, 0);
    const cs = tw > 0 ? Math.round(parts.reduce((s, p) => s + p.score * p.weight, 0) / tw) : 50;
    const sig = cs >= 62 ? "buy" : cs <= 38 ? "sell" : "hold";
    return { compositeScore: cs, compositeSignal: sig };
  }, [fundamentalScore, technicalScore, mlScore, macroScore]);

  const sigMeta = SIGNAL_META[compositeSignal] ?? SIGNAL_META.hold;
  const riskLevel = signal ? computeRiskLevel(signal) : "MEDIUM";
  const riskMeta = RISK_META[riskLevel];

  // ── 5-component confidence formula ───────────────────────────────────────────
  const confidence = useMemo(() => {
    const agreement  = mlConsensus.agreementPct;                                  // 30%
    const probMargin = fundamentalScore != null ? Math.min(100, Math.abs(fundamentalScore - 50) * 2.5) : 40; // 25%
    const dataQual   = signal ? (DIMS.map(d => signal[d.key]).filter(v => v != null).length / 7) * 100 : 40; // 20%
    const stability  = (dataQual >= 70 ? 90 : dataQual >= 40 ? 70 : 50);          // 15%
    const volScore   = volPct != null ? Math.max(0, 100 - volPct * 15) : 60;      // 10%
    return Math.round(0.30 * agreement + 0.25 * probMargin + 0.20 * dataQual + 0.15 * stability + 0.10 * volScore);
  }, [mlConsensus, fundamentalScore, signal, volPct]);

  // ── Bullish / Bearish factors (top 5 each) ───────────────────────────────────
  const { bullishFactors, bearishFactors } = useMemo(() => {
    const bull: string[] = [], bear: string[] = [];
    if (signal) {
      if ((signal.growth_score ?? 0) > 65)      bull.push(`Strong revenue & earnings growth (score ${signal.growth_score?.toFixed(0)})`);
      if ((signal.growth_score ?? 100) < 35)     bear.push(`Weak earnings growth vs peers (score ${signal.growth_score?.toFixed(0)})`);
      if ((signal.valuation_score ?? 0) > 65)    bull.push(`Attractive valuation vs peers (score ${signal.valuation_score?.toFixed(0)})`);
      if ((signal.valuation_score ?? 100) < 35)  bear.push(`Expensive relative valuation (score ${signal.valuation_score?.toFixed(0)})`);
      if ((signal.financial_health_score ?? 0) > 65)   bull.push(`Strong balance sheet & low leverage (score ${signal.financial_health_score?.toFixed(0)})`);
      if ((signal.financial_health_score ?? 100) < 35)  bear.push(`Elevated leverage vs sector peers (score ${signal.financial_health_score?.toFixed(0)})`);
      if ((signal.momentum_score ?? 0) > 65)     bull.push(`Positive 180-day price momentum (score ${signal.momentum_score?.toFixed(0)})`);
      if ((signal.momentum_score ?? 100) < 35)   bear.push(`Lagging price momentum vs peers (score ${signal.momentum_score?.toFixed(0)})`);
      if ((signal.quality_score ?? 0) > 65)      bull.push(`High earnings quality & ROIC (score ${signal.quality_score?.toFixed(0)})`);
    }
    if (rsi != null && rsi < 30) bull.push(`RSI oversold at ${rsi.toFixed(1)} — mean-reversion setup`);
    if (rsi != null && rsi > 70) bear.push(`RSI overbought at ${rsi.toFixed(1)} — near-term exhaustion risk`);
    if (macd != null && macd.histogram > 0) bull.push("MACD histogram positive — bullish momentum");
    if (macd != null && macd.histogram < 0) bear.push("MACD histogram negative — bearish momentum");
    if (price != null && sma20 != null) { if (price > sma20) bull.push("Price above SMA20 — near-term uptrend intact"); else bear.push("Price below SMA20 — near-term trend broken"); }
    if (price != null && tech.ema200.latest != null) { if (price > tech.ema200.latest) bull.push("Price above EMA200 — long-term uptrend"); else bear.push("Price below EMA200 — long-term downtrend"); }
    if (tech.obv.latest != null && tech.obv.latest > 0) bull.push("Positive OBV — institutional accumulation signal");
    if (tech.obv.latest != null && tech.obv.latest < 0) bear.push("Negative OBV — distribution pressure in volume");
    if (mlConsensus.signal === "BUY" && mlConsensus.agreementPct >= 75) bull.push(`${mlConsensus.agreementPct}% of quantitative models agree: BUY`);
    if (mlConsensus.signal === "SELL" && mlConsensus.agreementPct >= 75) bear.push(`${mlConsensus.agreementPct}% of quantitative models agree: SELL`);
    return { bullishFactors: bull.slice(0, 5), bearishFactors: bear.slice(0, 5) };
  }, [signal, rsi, macd, sma20, price, tech, mlConsensus]);

  const insights = useMemo(() =>
    signal ? generateInsights(signal, tech.rsi14.latest, tech.macd.latest?.histogram ?? null) : [],
    [signal, tech]);

  const avgScore = fundamentalScore;

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

      {/* ── 2. AI Recommendation Block (4-pillar) ─────────────────────────── */}
      <div className="rounded-2xl border p-5" style={{ backgroundColor: sigMeta.bg, borderColor: sigMeta.border }}>

        {/* Header row */}
        <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-widest text-muted/70">AI Recommendation</p>
            <div className="flex items-center gap-3">
              <span className="text-4xl font-bold tracking-tight" style={{ color: sigMeta.color }}>{sigMeta.label}</span>
              <span className="text-lg opacity-60" style={{ color: sigMeta.color }}>{sigMeta.icon}</span>
            </div>
            {signal?.as_of_date && (
              <p className="mt-1 text-xs text-muted">Updated {signal.as_of_date} · Policy v{signal.policy_version}</p>
            )}
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted">Confidence</span>
                <span className="rounded-full px-2.5 py-0.5 text-xs font-bold" style={{ color: sigMeta.color, backgroundColor: sigMeta.bg }}>{confidence}%</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted">Risk</span>
                <Badge label={riskMeta.label} color={riskMeta.color} bg={riskMeta.bg} />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted">Composite</span>
                <span className="rounded-full px-2.5 py-0.5 text-xs font-bold" style={{ color: sigMeta.color, backgroundColor: sigMeta.bg }}>{compositeScore}/100</span>
              </div>
            </div>
          </div>
          <ScoreRing score={compositeScore} size={88} />
        </div>

        {/* 4-pillar scorecard */}
        <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            { label: "Fundamental", score: fundamentalScore, weight: "40%",
              tip: "Average of 7 dimension scores (Quality, Growth, Financial Health, Valuation, Catalyst/Risk, Momentum, Beta-Risk) — all peer-relative within the fertilizer pilot universe." },
            { label: "Technical", score: technicalScore, weight: "30%",
              tip: "Derived from price-based indicators: RSI, MACD histogram, price vs SMA20/50/EMA200, VWAP, ADX direction, OBV, MFI, Stoch RSI, and Bollinger Band position." },
            { label: "ML Models", score: mlScore, weight: "20%",
              tip: "Blended signal from 4 quantitative models (Linear Regression, Logistic, KNN, Neural). Score anchors near 50 when agreement is split; moves toward 0 or 100 as consensus strengthens." },
            { label: "Macro", score: macroScore, weight: "10%",
              tip: "90-day rolling returns of KSE-100 and FERTIX equally weighted. Captures sector tailwinds/headwinds from the broader market and fertilizer sub-index." },
          ].map(({ label, score, weight, tip }) => {
            const c = score == null ? "#6b7280" : score >= 62 ? "#22c55e" : score >= 42 ? "#f59e0b" : "#ef4444";
            return (
              <Tip key={label} text={tip}>
                <div className="rounded-xl bg-black/15 p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-muted/80">{label}</p>
                    <p className="text-[10px] text-muted/50">{weight}</p>
                  </div>
                  <p className="text-xl font-bold tabular-nums" style={{ color: c }}>{score != null ? score : "—"}</p>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-black/20">
                    {score != null && <div className="h-full rounded-full" style={{ width: `${score}%`, backgroundColor: c }} />}
                  </div>
                </div>
              </Tip>
            );
          })}
        </div>

        {/* Why? — bullish/bearish factor breakdown */}
        {(bullishFactors.length > 0 || bearishFactors.length > 0) && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {bullishFactors.length > 0 && (
              <div className="rounded-xl bg-emerald-400/8 border border-emerald-400/20 p-3">
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-emerald-500">Bullish Factors</p>
                <ul className="space-y-1">
                  {bullishFactors.map((f, i) => (
                    <li key={i} className="flex gap-2 text-xs text-emerald-300/80">
                      <span className="mt-0.5 shrink-0 text-emerald-500">▲</span>
                      <span className="leading-relaxed">{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {bearishFactors.length > 0 && (
              <div className="rounded-xl bg-red-400/8 border border-red-400/20 p-3">
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-red-500">Bearish Factors</p>
                <ul className="space-y-1">
                  {bearishFactors.map((f, i) => (
                    <li key={i} className="flex gap-2 text-xs text-red-300/80">
                      <span className="mt-0.5 shrink-0 text-red-500">▼</span>
                      <span className="leading-relaxed">{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {signal?.suppression_reasons && signal.suppression_reasons.length > 0 && (
          <div className="mt-3 rounded-xl bg-black/20 px-4 py-3">
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

        {/* Momentum row */}
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted/60">Momentum &amp; Oscillators</p>
        <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {[
            {
              label: "RSI (14)",
              value: rsi != null ? rsi.toFixed(1) : null,
              sub: rsi == null ? null : rsi > 70 ? "Overbought" : rsi < 30 ? "Oversold" : "Neutral",
              color: rsi == null ? undefined : rsi > 70 ? "#ef4444" : rsi < 30 ? "#22c55e" : "#f59e0b",
              tip: "Relative Strength Index (14-period, Wilder smoothing). Above 70 = overbought — momentum may be exhausted. Below 30 = oversold — potential mean-reversion. RSI flags stretched conditions, not direction alone.",
            },
            {
              label: "MACD",
              value: macd != null ? macd.macd.toFixed(2) : null,
              sub: macd == null ? null : `Hist: ${macd.histogram > 0 ? "+" : ""}${macd.histogram.toFixed(2)}`,
              color: macd == null ? undefined : macd.histogram > 0 ? "#22c55e" : "#ef4444",
              tip: "MACD = 12-day EMA minus 26-day EMA. Histogram = MACD minus its 9-day signal line. Positive and growing histogram = strengthening bullish momentum. Negative and falling = bearish momentum building.",
            },
            {
              label: "Stoch RSI %K",
              value: tech.stochRsi.latest != null ? tech.stochRsi.latest.k.toFixed(1) : null,
              sub: tech.stochRsi.latest == null ? null
                : tech.stochRsi.latest.k > 80 ? "Overbought"
                : tech.stochRsi.latest.k < 20 ? "Oversold" : `%D ${tech.stochRsi.latest.d.toFixed(1)}`,
              color: tech.stochRsi.latest == null ? undefined
                : tech.stochRsi.latest.k > 80 ? "#ef4444"
                : tech.stochRsi.latest.k < 20 ? "#22c55e" : "#f59e0b",
              tip: "Stochastic RSI applies the Stochastic formula to RSI values (14-period). %K above 80 = overbought; below 20 = oversold. More sensitive than plain RSI — useful for spotting short-term turning points within a trend.",
            },
            {
              label: "MFI (14)",
              value: tech.mfi.latest != null ? tech.mfi.latest.toFixed(1) : null,
              sub: tech.mfi.latest == null ? null
                : tech.mfi.latest > 80 ? "Overbought"
                : tech.mfi.latest < 20 ? "Oversold" : "Neutral",
              color: tech.mfi.latest == null ? undefined
                : tech.mfi.latest > 80 ? "#ef4444"
                : tech.mfi.latest < 20 ? "#22c55e" : "#f59e0b",
              tip: "Money Flow Index — a volume-weighted RSI. MFI above 80 = buying exhaustion (overbought); below 20 = heavy selling pressure (oversold). Requires volume data; shows '—' when unavailable.",
            },
            {
              label: "ADX (14)",
              value: tech.adx.latest != null ? tech.adx.latest.adx.toFixed(1) : null,
              sub: tech.adx.latest == null ? null
                : tech.adx.latest.adx > 25 ? `Trending · +DI ${tech.adx.latest.plusDI.toFixed(0)} −DI ${tech.adx.latest.minusDI.toFixed(0)}`
                : "Weak trend",
              color: tech.adx.latest == null ? undefined
                : tech.adx.latest.adx > 25 ? (tech.adx.latest.plusDI > tech.adx.latest.minusDI ? "#22c55e" : "#ef4444")
                : "#f59e0b",
              tip: "Average Directional Index measures trend strength (0–100), not direction. ADX > 25 = strong trend (direction from +DI vs −DI). ADX < 20 = market is ranging and trend-following signals are less reliable.",
            },
          ].map(({ label, value, sub, color, tip }: { label: string; value: string | null; sub: string | null; color: string | undefined; tip: string }) => (
            <Tip key={label} text={tip}>
              <div className="rounded-xl bg-surface-alt p-4">
                <p className="mb-2 text-xs text-muted">{label}</p>
                <p className="text-lg font-bold tabular-nums" style={{ color: color ?? "inherit" }}>{value ?? "—"}</p>
                {sub && <p className="mt-1 text-[10px]" style={{ color: color ?? "#6b7280" }}>{sub}</p>}
              </div>
            </Tip>
          ))}
        </div>

        {/* Moving averages row */}
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted/60">Moving Averages vs Price</p>
        <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {(["sma20","sma50","sma200","ema20","ema50","ema200"] as const).map((key) => {
            const result = tech[key];
            const val = result.latest;
            const above = price != null && val != null && price > val;
            const color = val == null ? undefined : above ? "#22c55e" : "#ef4444";
            const MA_TIPS: Record<string, string> = {
              sma20:  "Simple Moving Average (20-day). Short-term trend reference. Price above SMA20 = near-term uptrend; below = near-term downtrend. Commonly used as a dynamic support/resistance level.",
              sma50:  "Simple Moving Average (50-day). Medium-term trend indicator. A cross of SMA20 above SMA50 = 'Golden Cross' (bullish); below = 'Death Cross' (bearish).",
              sma200: "Simple Moving Average (200-day). The standard long-term trend filter. Price above SMA200 = in a structural bull trend; below = bear trend. Institutional investors watch this level closely.",
              ema20:  "Exponential Moving Average (20-day). Like SMA20 but reacts faster to recent price changes due to exponential weighting. Used for dynamic support in trending markets.",
              ema50:  "Exponential Moving Average (50-day). Medium-term trend with more weight on recent prices versus SMA50. Useful for trailing stop placement in trending positions.",
              ema200: "Exponential Moving Average (200-day). Long-term trend reference that reacts faster than SMA200. Price above EMA200 = bullish structure; below = bearish. This platform uses EMA200 as the long-term pillar in the technical score.",
            };
            return (
              <Tip key={key} text={MA_TIPS[key]}>
                <div className="rounded-xl bg-surface-alt p-3">
                  <p className="mb-1 text-[10px] text-muted uppercase">{key.replace("sma","SMA ").replace("ema","EMA ")}</p>
                  <p className="text-sm font-bold tabular-nums" style={{ color }}>
                    {val != null ? `PKR ${val.toFixed(1)}` : "—"}
                  </p>
                  {val != null && price != null && (
                    <p className="mt-0.5 text-[10px]" style={{ color }}>{above ? "▲ above" : "▼ below"}</p>
                  )}
                </div>
              </Tip>
            );
          })}
        </div>

        {/* Volume / volatility row */}
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted/60">Volatility &amp; Volume</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            {
              label: "ATR Volatility",
              value: volPct != null ? `${volPct.toFixed(2)}%` : null,
              sub: volPct == null ? null : volPct > 3 ? "High" : volPct > 1.5 ? "Moderate" : "Low",
              color: volPct == null ? undefined : volPct > 3 ? "#ef4444" : volPct > 1.5 ? "#f59e0b" : "#22c55e",
              tip: "Average True Range expressed as a % of price (ATR÷Price×100). Measures recent daily price swing size. >3% = high volatility (wider stops needed); 1.5–3% = moderate; <1.5% = low. Used to calibrate position size and stop-loss distance.",
            },
            {
              label: "Bollinger Band",
              value: tech.bollinger.latest != null
                ? `${tech.bollinger.latest.lower.toFixed(1)} – ${tech.bollinger.latest.upper.toFixed(1)}`
                : null,
              sub: tech.bollinger.latest != null && price != null
                ? price > tech.bollinger.latest.upper ? "Above upper band"
                  : price < tech.bollinger.latest.lower ? "Below lower band"
                  : `Mid ${tech.bollinger.latest.middle.toFixed(1)}`
                : null,
              color: tech.bollinger.latest != null && price != null
                ? price > tech.bollinger.latest.upper ? "#ef4444"
                  : price < tech.bollinger.latest.lower ? "#22c55e"
                  : "#f59e0b"
                : undefined,
              tip: "Bollinger Bands = SMA20 ± 2 standard deviations. Shows the range prices are expected to trade in 95% of the time. Price touching the upper band = extended; lower band = compressed/oversold. Bands widen in high volatility, narrow in low.",
            },
            {
              label: "VWAP (20-day)",
              value: tech.vwap.latest != null ? `PKR ${tech.vwap.latest.toFixed(2)}` : null,
              sub: tech.vwap.latest != null && price != null
                ? price > tech.vwap.latest ? "Price above VWAP" : "Price below VWAP"
                : null,
              color: tech.vwap.latest != null && price != null
                ? price > tech.vwap.latest ? "#22c55e" : "#ef4444"
                : undefined,
              tip: "Volume-Weighted Average Price over a rolling 20-day window. Represents the average price at which shares have traded, weighted by volume. Institutions use VWAP as a benchmark — price above = bullish bias; below = bearish. Requires volume data.",
            },
            {
              label: "OBV",
              value: tech.obv.latest != null
                ? `${tech.obv.latest >= 0 ? "+" : ""}${(tech.obv.latest / 1_000_000).toFixed(1)} mn`
                : null,
              sub: tech.obv.latest == null ? null
                : tech.obv.latest > 0 ? "Buying pressure" : "Selling pressure",
              color: tech.obv.latest == null ? undefined : tech.obv.latest > 0 ? "#22c55e" : "#ef4444",
              tip: "On-Balance Volume: adds volume on up-days, subtracts on down-days. A rising OBV into a rising price confirms the trend. Divergence (e.g. price rising but OBV falling) is a warning of distribution by institutional sellers. Requires volume data.",
            },
          ].map(({ label, value, sub, color, tip }: { label: string; value: string | null; sub: string | null; color: string | undefined; tip: string }) => (
            <Tip key={label} text={tip}>
              <div className="rounded-xl bg-surface-alt p-4">
                <p className="mb-2 text-xs text-muted">{label}</p>
                <p className="text-sm font-bold tabular-nums" style={{ color: color ?? "inherit" }}>{value ?? "—"}</p>
                {sub && <p className="mt-1 text-[10px]" style={{ color: color ?? "#6b7280" }}>{sub}</p>}
              </div>
            </Tip>
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

      {/* ── Market Context ───────────────────────────────────────────────────── */}
      {(kseIndex || fertixIndex) && (() => {
        const kse20d  = indexReturn(kseIndex,    20);
        const kse90d  = indexReturn(kseIndex,    90);
        const kse180d = indexReturn(kseIndex,   180);
        const fx20d   = indexReturn(fertixIndex,  20);
        const fx90d   = indexReturn(fertixIndex,  90);
        const fx180d  = indexReturn(fertixIndex, 180);
        const fmtPct = (v: number | null) =>
          v == null ? "—" : `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
        const retColor = (v: number | null) =>
          v == null ? undefined : v > 0 ? "#22c55e" : "#ef4444";
        return (
          <div className="rounded-2xl border border-border bg-surface p-5">
            <h4 className="mb-1 text-sm font-semibold">Market Context</h4>
            <p className="mb-4 text-xs text-muted">Index returns over rolling windows — shows the macro tailwind or headwind for this sector.</p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left">
                    <th className="pb-2 pr-6 text-xs font-normal text-muted">Index</th>
                    <th className="pb-2 px-4 text-xs font-normal text-muted text-right">20-day</th>
                    <th className="pb-2 px-4 text-xs font-normal text-muted text-right">90-day</th>
                    <th className="pb-2 px-4 text-xs font-normal text-muted text-right">180-day</th>
                  </tr>
                </thead>
                <tbody>
                  {kseIndex && (
                    <tr className="border-b border-border/40">
                      <td className="py-2.5 pr-6 font-medium">KSE-100 (EOD)</td>
                      {[kse20d, kse90d, kse180d].map((v, i) => (
                        <td key={i} className="py-2.5 px-4 text-right tabular-nums font-semibold" style={{ color: retColor(v) }}>{fmtPct(v)}</td>
                      ))}
                    </tr>
                  )}
                  {fertixIndex && (
                    <tr>
                      <td className="py-2.5 pr-6 font-medium">FERTIX (custom)</td>
                      {[fx20d, fx90d, fx180d].map((v, i) => (
                        <td key={i} className="py-2.5 px-4 text-right tabular-nums font-semibold" style={{ color: retColor(v) }}>{fmtPct(v)}</td>
                      ))}
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-[10px] text-muted">
              KSE-100 and FERTIX returns help contextualise company-specific signals. A stock declining
              alongside the index requires less concern than one underperforming a rising index.
              Data for USD/PKR, policy rate, and gas/urea prices is not yet wired — these will be
              added when macroeconomic data feeds are integrated.
            </p>
          </div>
        );
      })()}

      {/* ── Footer note ─────────────────────────────────────────────────────── */}
      <p className="text-[11px] text-muted leading-relaxed">
        Scores are peer-relative within the fertilizer pilot universe (50 = sector mean).
        Quantitative models use price history and dimensional scores; they are deterministic, not
        learned from labelled data. Not investment advice — always conduct independent due diligence.
      </p>

    </div>
  );
}
