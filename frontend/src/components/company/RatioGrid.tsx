"use client";

import { Line, LineChart, ResponsiveContainer } from "recharts";
import type { RatioBenchmark, RatioSeries } from "@/lib/api";

// Ratios where a HIGHER value is worse (e.g. leverage) — used to flip the Healthy/Elevated
// direction relative to the peer mean instead of always treating "above average" as good.
const LOWER_IS_BETTER = new Set(["debt_to_equity", "debt_to_assets", "price_to_earnings", "price_to_book", "price_to_sales"]);

const CATEGORY_LABELS: Record<string, string> = {
  profitability: "Profitability",
  growth: "Growth",
  liquidity: "Liquidity",
  leverage: "Leverage",
  efficiency: "Efficiency",
  cash_flow: "Cash Flow",
  per_share: "Per Share",
  valuation: "Valuation",
};

const CATEGORY_ORDER = [
  "profitability",
  "growth",
  "liquidity",
  "leverage",
  "efficiency",
  "cash_flow",
  "per_share",
  "valuation",
];

function formatValue(value: number, unit: string) {
  if (unit === "percent") return `${value.toFixed(1)}%`;
  if (unit === "PKR") return `PKR ${value.toFixed(2)}`;
  return value.toFixed(2) + "x";
}

function benchmarkBadge(key: string, latestValue: number, benchmark: RatioBenchmark | undefined) {
  if (!benchmark || benchmark.count < 2) return null;
  const diffPct = (latestValue - benchmark.mean) / (Math.abs(benchmark.mean) || 1);
  const better = LOWER_IS_BETTER.has(key) ? diffPct < 0 : diffPct > 0;
  const label = Math.abs(diffPct) < 0.1 ? "Average" : better ? "Healthy" : "Watch";
  const tone =
    label === "Average" ? "bg-surface-alt text-muted" : label === "Healthy" ? "bg-positive/10 text-positive" : "bg-accent-yellow/10 text-accent-yellow";
  return (
    <span
      title={`Peer mean across ${benchmark.count} companies: ${benchmark.mean.toFixed(2)}`}
      className={`ml-1.5 rounded-full px-1.5 py-0.5 text-[9px] font-medium ${tone}`}
    >
      {label}
    </span>
  );
}

export default function RatioGrid({
  ratios,
  benchmarks = {},
}: {
  ratios: Record<string, RatioSeries>;
  benchmarks?: Record<string, RatioBenchmark>;
}) {
  const grouped: Record<string, { key: string; series: RatioSeries }[]> = {};
  for (const [key, series] of Object.entries(ratios)) {
    grouped[series.category] ??= [];
    grouped[series.category].push({ key, series });
  }

  const categories = CATEGORY_ORDER.filter((c) => grouped[c]?.length);
  if (categories.length === 0) {
    return <p className="text-xs text-muted">No ratios computed for this company yet.</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {categories.map((category) => (
        <div key={category} className="rounded-2xl border border-border bg-surface p-5">
          <h4 className="mb-3 text-sm font-semibold">{CATEGORY_LABELS[category] ?? category}</h4>
          <div className="flex flex-col gap-3">
            {grouped[category].map(({ key, series }) => {
              const sorted = [...series.values].sort((a, b) => a.period_end.localeCompare(b.period_end));
              const latest = sorted[sorted.length - 1];
              const isReported = key.endsWith("_reported") || key === "peg_reported";
              return (
                <div key={key} className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-xs text-muted" title={series.formula}>
                      {series.name}
                    </p>
                    <p className="text-sm font-medium">
                      {latest ? formatValue(latest.value, series.unit) : "—"}
                      {isReported && (
                        <span className="ml-1.5 rounded-full bg-surface-alt px-1.5 py-0.5 text-[9px] font-medium text-muted">
                          reported
                        </span>
                      )}
                      {latest && !isReported && benchmarkBadge(key, latest.value, benchmarks[key])}
                    </p>
                    {series.formula && <p className="truncate text-[10px] text-muted/70">{series.formula}</p>}
                  </div>
                  {sorted.length > 1 && (
                    <div className="h-8 w-20 shrink-0">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={sorted}>
                          <Line
                            type="monotone"
                            dataKey="value"
                            stroke={isReported ? "#8b92a5" : "#4f7cff"}
                            strokeWidth={1.5}
                            dot={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
