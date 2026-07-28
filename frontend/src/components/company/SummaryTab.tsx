"use client";

import { useMemo, useState } from "react";
import { Info } from "lucide-react";
import type { CompanyOverview, PriceBar } from "@/lib/api";
import { latestValue as latest } from "@/lib/financials";
import { GLOSSARY } from "@/lib/glossary";
import { computeTechnicals } from "@/lib/technicals";
import CatalystsRisksPanel from "./CatalystsRisksPanel";

interface Metric {
  label: string;
  value: string | null;
  caption?: string;
  title?: string;
}

function MetricGrid({ metrics }: { metrics: Metric[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {metrics.map((m) => {
        const definition = GLOSSARY[m.label];
        const tooltip = [definition, m.title].filter(Boolean).join(" — ");
        return (
          <div key={m.label} className="rounded-2xl border border-border bg-surface p-4" title={tooltip || undefined}>
            <p className="mb-1 flex items-center gap-1 text-xs text-muted">
              {m.label}
              {definition && <Info size={11} className="shrink-0 opacity-60" />}
            </p>
            <p className="text-lg font-semibold">{m.value ?? "—"}</p>
            {m.value != null && m.caption && <p className="mt-1 text-[10px] text-muted">{m.caption}</p>}
          </div>
        );
      })}
    </div>
  );
}

export default function SummaryTab({ data, prices }: { data: CompanyOverview; prices: PriceBar[] }) {
  const [lens, setLens] = useState<"long_term" | "short_term">("long_term");

  const marketCap = latest(data.financials["market_cap"]);
  const eps = latest(data.financials["eps"]);
  const pe = data.ratios["price_to_earnings"]?.values.length
    ? latest(data.ratios["price_to_earnings"].values)
    : null;
  const roe = data.ratios["roe"]?.values.length ? latest(data.ratios["roe"].values) : null;
  const roa = data.ratios["roa"]?.values.length ? latest(data.ratios["roa"].values) : null;
  const debtToEquity = data.ratios["debt_to_equity"]?.values.length
    ? latest(data.ratios["debt_to_equity"].values)
    : null;
  const currentRatio = data.ratios["current_ratio"]?.values.length
    ? latest(data.ratios["current_ratio"].values)
    : null;
  const dividendYield = data.live_quote?.dividend_yield ?? null;
  const volume = data.live_quote?.volume ?? null;

  const sharesLatest = latest(data.financials["shares_outstanding"]);
  const freeFloatShares =
    sharesLatest != null && data.free_float_pct != null
      ? sharesLatest * (data.free_float_pct / 100)
      : null;
  const fmtShares = (n: number | null) =>
    n == null ? null : n >= 1e9 ? `${(n / 1e9).toFixed(2)} bn` : `${(n / 1e6).toFixed(1)} mn`;

  const longTermMetrics: Metric[] = [
    { label: "Market Cap", value: marketCap != null ? `PKR ${(marketCap / 1_000_000).toFixed(1)} bn` : null, caption: "reported" },
    { label: "Trailing P/E", value: pe != null ? `${pe.toFixed(2)}x` : null, caption: "calculated" },
    {
      label: "Dividend Yield",
      value: dividendYield != null && dividendYield !== 0 ? `${dividendYield.toFixed(2)}%` : null,
      caption: "psxdata live",
    },
    { label: "EPS", value: eps != null ? `PKR ${eps.toFixed(2)}` : null, caption: "reported" },
    { label: "ROE", value: roe != null ? `${roe.toFixed(1)}%` : null, caption: "calculated" },
    { label: "ROA", value: roa != null ? `${roa.toFixed(1)}%` : null, caption: "calculated" },
    { label: "Debt-to-Equity", value: debtToEquity != null ? `${debtToEquity.toFixed(2)}x` : null, caption: "calculated" },
    { label: "Current Ratio", value: currentRatio != null ? `${currentRatio.toFixed(2)}x` : null, caption: "calculated" },
    { label: "Shares Outstanding", value: fmtShares(sharesLatest), caption: "PSX snapshot" },
    { label: "Free Float", value: data.free_float_pct != null ? `${data.free_float_pct.toFixed(1)}%` : null, caption: "reported" },
    { label: "Free Float Shares", value: fmtShares(freeFloatShares), caption: "derived" },
    {
      label: "Beta (vs KSE-100)",
      value: data.beta != null ? data.beta.value.toFixed(2) : null,
      caption: data.beta ? `as of ${data.beta.as_of_date}` : undefined,
      title: data.beta?.source_note,
    },
  ];

  const technicals = useMemo(() => computeTechnicals(prices), [prices]);
  const changePct = data.live_quote?.change_pct ?? null;

  const shortTermMetrics: Metric[] = [
    {
      label: "Day Change",
      value: changePct != null ? `${changePct >= 0 ? "+" : ""}${changePct.toFixed(2)}%` : null,
      caption: "psxdata live",
    },
    { label: "Volume (last session)", value: volume != null ? volume.toLocaleString() : null, caption: "psxdata live" },
    {
      label: "RSI (14)",
      value: technicals.rsi14.available ? technicals.rsi14.latest!.toFixed(1) : null,
      caption: technicals.rsi14.available ? "calculated" : `needs ${technicals.rsi14.requiredBars} sessions`,
    },
    {
      label: "MACD",
      value: technicals.macd.available
        ? `${technicals.macd.latest!.macd.toFixed(2)} / sig ${technicals.macd.latest!.signal.toFixed(2)}`
        : null,
      caption: technicals.macd.available ? "calculated" : `needs ${technicals.macd.requiredBars} sessions`,
    },
    {
      label: "ATR (14)",
      value: technicals.atr14.available ? `PKR ${technicals.atr14.latest!.toFixed(2)}` : null,
      caption: technicals.atr14.available ? "calculated" : `needs ${technicals.atr14.requiredBars} sessions`,
    },
    {
      label: "SMA 20",
      value: technicals.sma20.available ? `PKR ${technicals.sma20.latest!.toFixed(2)}` : null,
      caption: technicals.sma20.available ? "calculated" : `needs ${technicals.sma20.requiredBars} sessions`,
    },
    { label: "Beta (vs KSE-100)", value: data.beta != null ? data.beta.value.toFixed(2) : null, title: data.beta?.source_note },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 rounded-full bg-surface-alt p-0.5 text-xs">
          <button
            onClick={() => setLens("long_term")}
            className={`rounded-full px-3 py-1.5 ${lens === "long_term" ? "bg-accent text-white" : "text-muted"}`}
          >
            Long-term
          </button>
          <button
            onClick={() => setLens("short_term")}
            className={`rounded-full px-3 py-1.5 ${lens === "short_term" ? "bg-accent text-white" : "text-muted"}`}
          >
            Short-term
          </button>
        </div>
        <p className="text-[10px] text-muted">
          {lens === "long_term"
            ? "Emphasizes quality & valuation — for buy-and-hold research."
            : "Emphasizes momentum & volatility — for near-term trading context."}
        </p>
      </div>

      <MetricGrid metrics={lens === "long_term" ? longTermMetrics : shortTermMetrics} />

      <CatalystsRisksPanel thesis={data.thesis} />
    </div>
  );
}
