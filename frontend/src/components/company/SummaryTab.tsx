import type { CompanyOverview } from "@/lib/api";
import { latestValue as latest } from "@/lib/financials";
import CatalystsRisksPanel from "./CatalystsRisksPanel";

interface Metric {
  label: string;
  value: string | null;
  caption?: string;
}

export default function SummaryTab({ data }: { data: CompanyOverview }) {
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

  const metrics: Metric[] = [
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
    { label: "Free Float", value: data.free_float_pct != null ? `${data.free_float_pct.toFixed(1)}%` : null, caption: "reported" },
    { label: "Volume (last session)", value: volume != null ? volume.toLocaleString() : null, caption: "psxdata live" },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {metrics.map((m) => (
          <div key={m.label} className="rounded-2xl border border-border bg-surface p-4">
            <p className="mb-1 text-xs text-muted">{m.label}</p>
            <p className="text-lg font-semibold">{m.value ?? "—"}</p>
            {m.value != null && m.caption && <p className="mt-1 text-[10px] text-muted">{m.caption}</p>}
          </div>
        ))}
      </div>

      <CatalystsRisksPanel thesis={data.thesis} />
    </div>
  );
}
