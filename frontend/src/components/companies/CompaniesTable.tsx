"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import type { ComparisonRow } from "@/lib/api";
import { formatLiveRatio, formatMarketCap, formatPct, formatPercent, formatPrice } from "@/lib/format";

function SignalPill({ signal }: { signal: string | null }) {
  if (!signal) {
    return <span className="text-xs text-muted">—</span>;
  }
  const label = signal.replace("_", " ");
  const colorClass =
    signal === "STRONG_BUY" || signal === "BUY"
      ? "bg-emerald-500/15 text-emerald-400"
      : signal === "STRONG_SELL" || signal === "SELL"
      ? "bg-red-500/15 text-red-400"
      : "bg-surface-alt text-muted";
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${colorClass}`}>
      {label}
    </span>
  );
}

export default function CompaniesTable({ rows }: { rows: ComparisonRow[] }) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) => r.name.toLowerCase().includes(q) || (r.symbol ?? "").toLowerCase().includes(q));
  }, [rows, query]);

  return (
    <div>
      <div className="mb-4 flex max-w-xs items-center gap-2 rounded-full border border-border bg-surface px-4 py-2">
        <Search size={15} className="text-muted" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search ticker or company name..."
          className="w-full bg-transparent text-sm text-foreground placeholder:text-muted focus:outline-none"
        />
      </div>

      <div className="overflow-x-auto rounded-2xl border border-border bg-surface">
        <table className="w-full min-w-[880px] text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs text-muted">
              <th className="px-4 py-3 font-medium">Company</th>
              <th className="px-4 py-3 font-medium">Price</th>
              <th className="px-4 py-3 font-medium">Chg %</th>
              <th className="px-4 py-3 font-medium">Market Cap <span className="font-normal text-muted/60">(est.)</span></th>
              <th className="px-4 py-3 font-medium">P/E</th>
              <th className="px-4 py-3 font-medium">ROE</th>
              <th className="px-4 py-3 font-medium">Div. Yield</th>
              <th className="px-4 py-3 font-medium">AI Signal</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-6 text-center text-xs text-muted">
                  No companies match &quot;{query}&quot;.
                </td>
              </tr>
            )}
            {filtered.map((row) => (
              <tr key={row.id} className="hover:bg-surface-alt/60">
                <td className="px-4 py-3">
                  <Link href={`/companies/${row.id}`} className="flex items-center gap-2">
                    {row.symbol && (
                      <span className="rounded-md bg-accent/15 px-1.5 py-0.5 text-[10px] font-semibold text-accent">
                        {row.symbol}
                      </span>
                    )}
                    <span className="font-medium hover:text-accent">{row.name}</span>
                  </Link>
                </td>
                <td className="px-4 py-3">{formatPrice(row.price)}</td>
                <td className={`px-4 py-3 font-medium ${(row.change_pct ?? 0) >= 0 ? "text-positive" : "text-negative"}`}>
                  {formatPct(row.change_pct)}
                </td>
                <td className="px-4 py-3">{formatMarketCap(row.market_cap)}</td>
                <td className="px-4 py-3">{formatLiveRatio(row.pe_ratio, 2, "x")}</td>
                <td className="px-4 py-3">{row.roe != null ? formatPercent(row.roe) : "—"}</td>
                <td className="px-4 py-3">{formatLiveRatio(row.dividend_yield, 2, "%")}</td>
                <td className="px-4 py-3">
                  <SignalPill signal={row.ai_signal} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
