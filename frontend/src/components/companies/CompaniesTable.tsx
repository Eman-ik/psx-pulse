"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Lock, Search } from "lucide-react";
import type { ComparisonRow } from "@/lib/api";
import { formatLiveRatio, formatMarketCap, formatPct, formatPercent, formatPrice } from "@/lib/format";

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
              <th className="px-4 py-3 font-medium">Market Cap</th>
              <th className="px-4 py-3 font-medium">P/E</th>
              <th className="px-4 py-3 font-medium">ROE</th>
              <th className="px-4 py-3 font-medium">Div. Yield</th>
              <th className="px-4 py-3 font-medium">
                <span className="inline-flex items-center gap-1">
                  <Lock size={11} /> AI Signal
                </span>
              </th>
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
                  <span
                    title="AI signal output is built but hidden pending SECP/PSX compliance review — not a fabricated rating."
                    className="inline-flex cursor-help items-center gap-1 rounded-full bg-surface-alt px-2 py-1 text-[10px] font-medium text-muted"
                  >
                    <Lock size={10} /> Locked
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
