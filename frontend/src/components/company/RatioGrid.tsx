"use client";

import { Line, LineChart, ResponsiveContainer } from "recharts";
import type { RatioSeries } from "@/lib/api";

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

export default function RatioGrid({ ratios }: { ratios: Record<string, RatioSeries> }) {
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
                    <p className="truncate text-xs text-muted">{series.name}</p>
                    <p className="text-sm font-medium">
                      {latest ? formatValue(latest.value, series.unit) : "—"}
                      {isReported && (
                        <span className="ml-1.5 rounded-full bg-surface-alt px-1.5 py-0.5 text-[9px] font-medium text-muted">
                          reported
                        </span>
                      )}
                    </p>
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
